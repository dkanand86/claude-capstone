"""HelixNova Pharma Quality & Regulatory RAG Assistant.

Upload -> Extract -> Chunk -> Embed -> FAISS -> Ask -> Retrieve -> Claude -> Answer + Sources
See specification.md for the design.
"""

import io
import os
import re

import anthropic
import faiss
import numpy as np
import streamlit as st
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

# --- Configuration (specification.md §2) ---
EMBED_MODEL = "all-MiniLM-L6-v2"
CLAUDE_MODEL = "claude-sonnet-5-5"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
DEFAULT_TOP_K = 6
MIN_SCORE = 0.25
MAX_TOKENS = 4000
EFFORT = "low"  # Sonnet 5.5 rejects temperature; effort controls thinking depth
EVAL_SECTION_RE = re.compile(r"(?:\d+\.\s*)?EXAMPLE QUESTIONS FOR RAG EVALUATION", re.IGNORECASE)
FALLBACK_MESSAGE = (
    "I could not find enough information in the uploaded policy document(s) "
    "to answer this question."
)

SYSTEM_PROMPT = f"""You are the HelixNova Pharma Quality & Regulatory Policy Assistant.
Answer ONLY using the policy context provided between <context> tags.
Rules:
1. If the context does not contain enough information to answer, reply with exactly:
   "{FALLBACK_MESSAGE}"
2. Do not use outside knowledge or invent thresholds, timelines, or roles.
3. Be concise and quote exact timelines/values from the context.
4. Cite supporting chunks inline as [filename, chunk N].
5. You are advisory only. Never release/reject batches, close deviations, approve CAPAs or
   change controls, authorize recalls, or determine product disposition; direct the user to
   the responsible human role per the policy."""


def get_api_key():
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY")
        if key:
            return key
    except Exception:  # no secrets.toml present
        pass
    return os.environ.get("ANTHROPIC_API_KEY")


@st.cache_resource(show_spinner="Loading embedding model...")
def load_embedder():
    return SentenceTransformer(EMBED_MODEL)


def normalize_whitespace(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text(file):
    """Return a list of {"text", "page"} dicts for an uploaded file."""
    data = file.getvalue()
    if file.name.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        pages = []
        for i, page in enumerate(reader.pages, start=1):
            text = normalize_whitespace(page.extract_text() or "")
            if text:
                pages.append({"text": text, "page": i})
        return pages
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("latin-1")
    text = normalize_whitespace(text)
    return [{"text": text, "page": None}] if text else []


def drop_eval_section(pages):
    """Remove the trainer-only 'example questions' section so it can't outrank real policy text."""
    kept = []
    for page in pages:
        m = EVAL_SECTION_RE.search(page["text"])
        text = page["text"][: m.start()].strip() if m else page["text"]
        if text:
            kept.append({**page, "text": text})
        if m:
            break
    return kept


def split_long(paragraph):
    """Split a paragraph longer than CHUNK_SIZE on sentence boundaries, then hard-cut."""
    pieces, current = [], ""
    for sentence in re.split(r"(?<=[.!?])\s+", paragraph):
        while len(sentence) > CHUNK_SIZE:
            pieces.append(sentence[:CHUNK_SIZE])
            sentence = sentence[CHUNK_SIZE:]
        if current and len(current) + 1 + len(sentence) > CHUNK_SIZE:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        pieces.append(current)
    return pieces


def chunk_document(pages, filename):
    chunks, chunk_id = [], 0
    for page in pages:
        paragraphs = []
        for para in page["text"].split("\n\n"):
            para = para.strip()
            if para:
                paragraphs.extend(split_long(para) if len(para) > CHUNK_SIZE else [para])

        current = ""
        for para in paragraphs:
            if current and len(current) + 2 + len(para) > CHUNK_SIZE:
                chunk_id += 1
                chunks.append({"filename": filename, "chunk_id": chunk_id,
                               "page": page["page"], "text": current})
                current = current[-CHUNK_OVERLAP:] + "\n\n" + para
            else:
                current = f"{current}\n\n{para}" if current else para
        if current:
            chunk_id += 1
            chunks.append({"filename": filename, "chunk_id": chunk_id,
                           "page": page["page"], "text": current})
    return chunks


def build_index(chunks):
    embeddings = load_embedder().encode(
        [c["text"] for c in chunks], normalize_embeddings=True, show_progress_bar=False
    ).astype("float32")
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    return index


def retrieve(question, k):
    index, chunks = st.session_state.index, st.session_state.chunks
    query = load_embedder().encode([question], normalize_embeddings=True).astype("float32")
    scores, ids = index.search(query, min(k, len(chunks)))
    hits = []
    for score, idx in zip(scores[0], ids[0]):
        if idx != -1 and score >= MIN_SCORE:
            hits.append({**chunks[idx], "score": float(score)})
    return hits


def generate_answer(question, hits, api_key):
    blocks = []
    for i, h in enumerate(hits, start=1):
        page = f", page {h['page']}" if h["page"] else ""
        blocks.append(f"[Source {i}: {h['filename']}, chunk {h['chunk_id']}{page}]\n{h['text']}")
    user_message = "<context>\n" + "\n\n".join(blocks) + f"\n</context>\n\nQuestion: {question}"

    client = anthropic.Anthropic(api_key=api_key)
    response = client.beta.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=MAX_TOKENS,
        output_config={"effort": EFFORT},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    if response.stop_reason == "refusal":
        return FALLBACK_MESSAGE
    return "".join(b.text for b in response.content if b.type == "text").strip()


def render_sources(sources, show_scores):
    if not sources:
        return
    with st.expander(f"Sources ({len(sources)})"):
        for s in sources:
            page = f" (page {s['page']})" if s["page"] else ""
            score = f" · score {s['score']:.2f}" if show_scores else ""
            snippet = s["text"][:300] + ("..." if len(s["text"]) > 300 else "")
            st.markdown(f"**{s['filename']} — chunk #{s['chunk_id']}**{page}{score}")
            st.caption(snippet)


def update_index(files):
    fingerprint = sorted((f.name, f.size) for f in files)
    if st.session_state.get("fingerprint") == fingerprint:
        return
    all_chunks, seen = [], set()
    with st.spinner("Extracting, chunking and indexing documents..."):
        for f in files:
            if f.name in seen:  # same file uploaded twice: index once
                continue
            seen.add(f.name)
            try:
                pages = drop_eval_section(extract_text(f))
            except Exception as e:
                st.sidebar.error(f"Could not read {f.name}: {e}")
                continue
            if not pages:
                st.sidebar.warning(
                    f"No extractable text in {f.name} (empty file or scanned PDF). Skipped."
                )
                continue
            all_chunks.extend(chunk_document(pages, f.name))
        st.session_state.chunks = all_chunks
        st.session_state.index = build_index(all_chunks) if all_chunks else None
        st.session_state.fingerprint = fingerprint


def main():
    st.set_page_config(page_title="HelixNova Policy Assistant", page_icon="💊", layout="wide")
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("index", None)
    st.session_state.setdefault("chunks", [])

    api_key = get_api_key()

    with st.sidebar:
        st.header("Documents")
        files = st.file_uploader(
            "Upload policy PDF/TXT", type=["pdf", "txt"], accept_multiple_files=True
        )
        if files:
            update_index(files)
        else:
            st.session_state.index, st.session_state.chunks = None, []
            st.session_state.fingerprint = None

        if st.session_state.index is not None:
            n_files = len({c["filename"] for c in st.session_state.chunks})
            st.success(f"Indexed {n_files} file(s), {len(st.session_state.chunks)} chunks")

        st.header("Settings")
        top_k = st.slider("Chunks to retrieve (Top-K)", 1, 8, DEFAULT_TOP_K)
        show_scores = st.toggle("Show similarity scores", value=True)
        if st.button("Clear chat"):
            st.session_state.messages = []
            st.rerun()
        if not api_key:
            st.warning("ANTHROPIC_API_KEY not set. Add it to Streamlit secrets or the environment.")

    st.title("HelixNova Pharma Quality & Regulatory Assistant")
    st.caption("Grounded answers from your uploaded policy documents, with sources.")
    st.caption("⚠️ Synthetic training data. Verify important decisions against the approved source document.")

    if st.session_state.index is None:
        st.info("Upload a policy PDF or TXT file in the sidebar to get started.")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                render_sources(msg.get("sources"), show_scores)

    disabled = st.session_state.index is None or not api_key
    question = st.chat_input("Ask a question about the policy...", disabled=disabled)
    if not question:
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching policy and generating answer..."):
            hits = retrieve(question, top_k)
            if not hits:
                answer, sources = FALLBACK_MESSAGE, []
            else:
                try:
                    answer = generate_answer(question, hits, api_key)
                    is_fallback = answer.strip().strip('"') == FALLBACK_MESSAGE
                    sources = [] if is_fallback else hits
                except anthropic.APIError as e:
                    answer, sources = f"⚠️ Claude API error: {e}", []
        st.markdown(answer)
        render_sources(sources, show_scores)

    st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})


if __name__ == "__main__":
    main()
