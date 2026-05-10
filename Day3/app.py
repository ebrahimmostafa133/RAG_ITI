"""Streamlit UI for RAG agent."""
import os
import glob
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

import ingest
from rag_agent import RAGAgent, CHROMA_DIR, TOPIC_FILE

st.set_page_config(page_title="Document RAG Agent", page_icon=":books:", layout="wide")

DOCS_DIR = os.getenv("DOCS_DIR", "docs")

BRANCH_BADGE = {
    "out_of_scope": ":grey[out of scope]",
    "answered": ":green[from document]",
    "no_context": ":orange[not in document]",
}


def index_exists() -> bool:
    return os.path.isdir(CHROMA_DIR) and any(
        f for f in os.listdir(CHROMA_DIR) if f != "topic.txt"
    )


def list_pdfs():
    return sorted(glob.glob(os.path.join(DOCS_DIR, "*.pdf")))


@st.cache_resource(show_spinner="Loading agent...")
def load_agent():
    return RAGAgent()


def reset_agent_cache():
    load_agent.clear()


# --- Sidebar ---
with st.sidebar:
    st.header("Document")
    os.makedirs(DOCS_DIR, exist_ok=True)
    uploaded = st.file_uploader("Upload PDF", type=["pdf"], accept_multiple_files=True)
    if uploaded:
        for f in uploaded:
            with open(os.path.join(DOCS_DIR, f.name), "wb") as out:
                out.write(f.getbuffer())
        st.success(f"Saved {len(uploaded)} file(s) to {DOCS_DIR}/")

    pdfs = list_pdfs()
    st.caption(f"{len(pdfs)} PDF(s) in {DOCS_DIR}/")
    for p in pdfs:
        st.write(f"- {os.path.basename(p)}")

    if st.button("Build / Rebuild Index", type="primary", disabled=not pdfs):
        with st.spinner("Indexing..."):
            try:
                ingest.build()
                reset_agent_cache()
                st.success("Index built.")
            except Exception as e:
                st.error(f"Indexing failed: {e}")

    if os.path.exists(TOPIC_FILE):
        st.divider()
        st.markdown("**Detected topic:**")
        st.info(open(TOPIC_FILE, encoding="utf-8").read().strip())

    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

# --- Main ---
st.title("Document RAG Agent")
st.caption("Ask questions about the uploaded document. Out-of-scope queries get an introduction; in-scope but unanswerable queries get 'I don't know'.")

if not os.getenv("OPENAI_API_KEY"):
    st.error("OPENAI_API_KEY missing. Set it in .env and restart.")
    st.stop()

if not index_exists():
    st.warning("No index yet. Upload a PDF in the sidebar and click **Build / Rebuild Index**.")
    st.stop()

try:
    agent = load_agent()
except Exception as e:
    st.error(str(e))
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("branch"):
            st.caption(BRANCH_BADGE.get(m["branch"], m["branch"]))
        if m.get("sources"):
            with st.expander("Sources"):
                for s in m["sources"]:
                    st.markdown(f"**p.{s.get('page')}** — {s.get('snippet')}")

if query := st.chat_input("Ask about the document..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = agent.ask(query)
        st.markdown(result["answer"])
        st.caption(BRANCH_BADGE.get(result["branch"], result["branch"]))
        if result.get("sources"):
            with st.expander("Sources"):
                for s in result["sources"]:
                    st.markdown(f"**p.{s.get('page')}** — {s.get('snippet')}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "branch": result["branch"],
        "sources": result.get("sources", []),
    })
