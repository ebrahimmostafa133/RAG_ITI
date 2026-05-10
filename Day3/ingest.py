"""Build Chroma index from PDFs in docs/. Also extracts topic summary used for scope check."""
import os
import glob
import shutil
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

DOCS_DIR = os.getenv("DOCS_DIR", "docs")
CHROMA_DIR = os.getenv("CHROMA_DIR", "chroma_db")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
TOPIC_FILE = os.path.join(CHROMA_DIR, "topic.txt")


def load_pdfs(docs_dir: str):
    pdfs = sorted(glob.glob(os.path.join(docs_dir, "*.pdf")))
    if not pdfs:
        raise FileNotFoundError(f"No PDF files found in {docs_dir}/. Drop a PDF there and re-run.")
    docs = []
    for path in pdfs:
        print(f"Loading {path}")
        docs.extend(PyPDFLoader(path).load())
    return docs


def split(docs):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    return splitter.split_documents(docs)


def extract_topic(chunks) -> str:
    sample = "\n\n".join(c.page_content for c in chunks[:6])[:6000]
    llm = ChatOpenAI(model=CHAT_MODEL, temperature=0)
    msg = [
        SystemMessage(content="You summarize a document's domain in ONE concise sentence (max 25 words). Output the sentence only."),
        HumanMessage(content=f"Document excerpts:\n\n{sample}\n\nWhat is the document's topic/domain?"),
    ]
    return llm.invoke(msg).content.strip()


def build():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set. Copy .env.example to .env and fill it.")

    docs = load_pdfs(DOCS_DIR)
    chunks = split(docs)
    print(f"Loaded {len(docs)} pages, {len(chunks)} chunks.")

    if os.path.exists(CHROMA_DIR):
        shutil.rmtree(CHROMA_DIR)
    os.makedirs(CHROMA_DIR, exist_ok=True)

    embeddings = OpenAIEmbeddings(model=EMBED_MODEL)
    Chroma.from_documents(chunks, embedding=embeddings, persist_directory=CHROMA_DIR)
    print(f"Index written to {CHROMA_DIR}/")

    topic = extract_topic(chunks)
    with open(TOPIC_FILE, "w", encoding="utf-8") as f:
        f.write(topic)
    print(f"Topic: {topic}")


if __name__ == "__main__":
    build()
