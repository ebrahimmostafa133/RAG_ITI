"""RAG agent. Three branches:
1. Out-of-scope query  -> introduce self
2. In-scope, context has answer -> answer from context
3. In-scope, context insufficient -> say "I don't know"
"""
import os
import json
from typing import Literal, TypedDict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

CHROMA_DIR = os.getenv("CHROMA_DIR", "chroma_db")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
TOPIC_FILE = os.path.join(CHROMA_DIR, "topic.txt")

DEFAULT_TOPIC = "the loaded document"


class RAGResult(TypedDict):
    answer: str
    branch: Literal["out_of_scope", "answered", "no_context"]
    sources: list


class RAGAgent:
    def __init__(self):
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY not set.")
        if not os.path.exists(CHROMA_DIR) or not os.listdir(CHROMA_DIR):
            raise RuntimeError(f"No index at {CHROMA_DIR}/. Run `python ingest.py` first.")

        self.topic = self._load_topic()
        self.llm = ChatOpenAI(model=CHAT_MODEL, temperature=0)
        embeddings = OpenAIEmbeddings(model=EMBED_MODEL)
        self.store = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
        self.retriever = self.store.as_retriever(search_kwargs={"k": 4})

    def _load_topic(self) -> str:
        if os.path.exists(TOPIC_FILE):
            return open(TOPIC_FILE, encoding="utf-8").read().strip() or DEFAULT_TOPIC
        return DEFAULT_TOPIC

    def _classify_scope(self, query: str) -> Literal["in_scope", "out_of_scope"]:
        prompt = (
            f"Document topic: {self.topic}\n\n"
            f"User query: {query}\n\n"
            "Decide if the query is RELATED to the document topic above. "
            "Greetings, identity questions ('who are you'), unrelated subjects, or chit-chat are OUT_OF_SCOPE. "
            "Reply with exactly one word: IN_SCOPE or OUT_OF_SCOPE."
        )
        out = self.llm.invoke([
            SystemMessage(content="You are a strict scope classifier. Output one token."),
            HumanMessage(content=prompt),
        ]).content.strip().upper()
        return "in_scope" if "IN_SCOPE" in out else "out_of_scope"

    def _introduce(self) -> str:
        return (
            f"Hi, I'm a document-grounded assistant. I answer questions about: {self.topic} "
            "Ask me something about that document and I'll look it up. "
            "Out-of-scope or unrelated questions I can't help with."
        )

    def _answer_from_context(self, query: str, docs) -> tuple[str, bool]:
        if not docs:
            return "I don't know based on the provided document.", False

        context = "\n\n---\n\n".join(
            f"[Source p.{d.metadata.get('page', '?')}] {d.page_content}" for d in docs
        )
        system = (
            "You answer ONLY using the provided context. "
            "If the context does not contain the answer, reply with the JSON object "
            '{\"answer\": \"I don\'t know based on the provided document.\", \"grounded\": false}. '
            "Otherwise reply with JSON {\"answer\": <your answer with citations like (p.N)>, \"grounded\": true}. "
            "Do not use outside knowledge. Output JSON only."
        )
        user = f"Context:\n{context}\n\nQuestion: {query}"
        raw = self.llm.invoke([SystemMessage(content=system), HumanMessage(content=user)]).content.strip()

        try:
            if raw.startswith("```"):
                raw = raw.strip("`").split("\n", 1)[1] if "\n" in raw else raw.strip("`")
                if raw.startswith("json"):
                    raw = raw[4:].lstrip()
            obj = json.loads(raw)
            return obj.get("answer", "I don't know based on the provided document."), bool(obj.get("grounded"))
        except Exception:
            return raw, True

    def ask(self, query: str) -> RAGResult:
        query = (query or "").strip()
        if not query:
            return {"answer": self._introduce(), "branch": "out_of_scope", "sources": []}

        if self._classify_scope(query) == "out_of_scope":
            return {"answer": self._introduce(), "branch": "out_of_scope", "sources": []}

        docs = self.retriever.invoke(query)
        answer, grounded = self._answer_from_context(query, docs)
        if not grounded:
            return {"answer": answer, "branch": "no_context", "sources": []}

        sources = [
            {"page": d.metadata.get("page"), "source": d.metadata.get("source"), "snippet": d.page_content[:200]}
            for d in docs
        ]
        return {"answer": answer, "branch": "answered", "sources": sources}


if __name__ == "__main__":
    agent = RAGAgent()
    print(f"Topic: {agent.topic}\nType a question (Ctrl+C to quit).\n")
    while True:
        try:
            q = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            continue
        r = agent.ask(q)
        print(f"[{r['branch']}] {r['answer']}\n")
