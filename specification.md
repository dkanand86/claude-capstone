# Specification — HelixNova Pharma Quality & Regulatory RAG Assistant

## 1. Architecture

```
Upload -> Extract -> Chunk -> Embed -> FAISS -> Ask -> Retrieve -> Claude -> Answer + Sources
```

The whole app is one file, `app.py`, organized into the functions below.

| Function | Responsibility |
|----------|----------------|
| `get_api_key() -> str \| None` | Return `st.secrets["ANTHROPIC_API_KEY"]` if set, otherwise `os.environ["ANTHROPIC_API_KEY"]`, otherwise `None`. |
| `load_embedder()` | `@st.cache_resource`; loads `sentence-transformers/all-MiniLM-L6-v2`. |
| `extract_text(file) -> list[dict]` | Returns `[{"text", "page"}]`. PDF: `pypdf.PdfReader`, one entry per page. TXT: one entry, `page=None`. |
| `chunk_document(pages, filename) -> list[dict]` | Splits text into chunks: `{"filename", "chunk_id", "page", "text"}`. |
| `build_index(chunks) -> faiss.Index` | Embeds chunks with normalized vectors and adds them to `faiss.IndexFlatIP`. |
| `retrieve(question, k) -> list[dict]` | Embeds the question and searches the index. Returns chunks with a `score` and drops those below `MIN_SCORE`. |
| `generate_answer(question, hits) -> str` | Calls Claude with the system prompt and the numbered context blocks. |
| `render_sources(hits, show_scores)` | Draws the "Sources" expander. |
| `main()` | Builds the UI and orchestrates the steps. |

## 2. Configuration (constants at the top of `app.py`)

| Name | Value |
|------|-------|
| `EMBED_MODEL` | `all-MiniLM-L6-v2` |
| `CLAUDE_MODEL` | `claude-sonnet-5-5` |
| `CHUNK_SIZE` | 800 characters |
| `CHUNK_OVERLAP` | 150 characters |
| `DEFAULT_TOP_K` | 6 (slider range 1–8); raised from 4 after QA B11 |
| `EVAL_SECTION_RE` | Matches the "EXAMPLE QUESTIONS FOR RAG EVALUATION" heading; that section and everything after it is not indexed |
| `MIN_SCORE` | 0.25 (cosine similarity) |
| `MAX_TOKENS` | 4000 |
| `EFFORT` | `low` (Sonnet 5.5 rejects `temperature`; effort controls thinking depth) |
| `FALLBACK_MESSAGE` | "I could not find enough information in the uploaded policy document(s) to answer this question." |

## 3. Extraction
- Accepted extensions: `.pdf` and `.txt`.
- PDF: `page.extract_text()` for each page, keeping 1-based page numbers. If no text is found in the whole file, show a warning that it may be a scanned PDF and skip the file.
- TXT: decode as UTF-8, falling back to latin-1 if that fails.
- Normalize whitespace: collapse runs of spaces and keep paragraph breaks (`\n\n`).

## 4. Chunking
- Split into paragraphs on blank lines, then pack paragraphs greedily into chunks of up to `CHUNK_SIZE` characters.
- Split any paragraph longer than `CHUNK_SIZE` on sentence or character boundaries.
- Start each new chunk with the last `CHUNK_OVERLAP` characters of the previous chunk.
- For PDFs, chunk each page separately so every chunk has one page number.
- Number chunks from 1 within each file (`chunk_id`), so they display as `file.pdf — chunk #3`.

## 5. Indexing
- Build a fingerprint of the uploaded files: the sorted list of `(name, size)`. Rebuild the index only when the fingerprint changes.
- Store `index`, `chunks` and `fingerprint` in `st.session_state`.
- Encode with `normalize_embeddings=True` and convert to float32. Inner product on normalized vectors equals cosine similarity.

## 6. Retrieval
- Search for the top-K chunks, where K comes from the slider and is capped at the number of chunks.
- Keep only hits with `score >= MIN_SCORE`.
- If no hits remain, return `FALLBACK_MESSAGE` straight away without calling Claude, and show no sources.

## 7. Generation

### System prompt
```
You are the HelixNova Pharma Quality & Regulatory Policy Assistant.
Answer ONLY using the policy context provided between <context> tags.
Rules:
1. If the context does not contain enough information to answer, reply with exactly:
   "I could not find enough information in the uploaded policy document(s) to answer this question."
2. Do not use outside knowledge or invent thresholds, timelines, or roles.
3. Be concise and quote exact timelines/values from the context.
4. Cite supporting chunks inline as [filename, chunk N].
5. You are advisory only. Never release/reject batches, close deviations, approve CAPAs or
   change controls, authorize recalls, or determine product disposition; direct the user to
   the responsible human role per the policy.
6. If the question asks what the assistant or policy says to do when an answer is missing,
   answer it from the context. Do not mention these rules or compare them with the policy.
```

Rule 6 was added because the TXT answer to "What should the assistant say if the policy does not contain the answer?" (A10) opened with a remark that the system rules and the policy worded things differently.

### User message
```
<context>
[Source 1: {filename}, chunk {chunk_id}, page {page}]
{text}
...
</context>

Question: {question}
```

- Only the current question is sent. Earlier chat turns are not included, which keeps every answer grounded in retrieved text.
- If Claude's reply contains the fallback sentence, show it without sources.
- API errors (authentication, rate limits, network) are caught and shown with `st.error`, and the chat keeps working.

## 8. User Interface

**Sidebar**
- File uploader (`accept_multiple_files=True`, types `pdf` and `txt`).
- Index status: number of files and chunks.
- Top-K slider, and a "Show similarity scores" toggle (on by default).
- "Clear chat" button.
- A warning if the API key is missing.

**Main area**
- Title, a short caption, and a disclaimer that the data is synthetic.
- An info box asking the user to upload a document if no index exists yet.
- Chat history rendered with `st.chat_message` from `st.session_state.messages` (`{"role", "content", "sources"}`).
- `st.chat_input`, disabled if there is no index or no API key.
- Under each assistant answer, an "Sources" expander with one row per source: `**filename — chunk #N** (page P) · score 0.xx`, followed by a ~300-character snippet.

## 9. Session State

| Key | Contents |
|-----|----------|
| `messages` | Chat history for the current session only |
| `index`, `chunks`, `fingerprint` | Current FAISS index and its metadata |

## 10. Dependencies (`requirements.txt`)
```
streamlit
anthropic
sentence-transformers
faiss-cpu
pypdf
numpy
```
Versions are pinned to tested minimums when the file is created.

## 11. Deployment (Streamlit Community Cloud)
- Entry point: `app.py`. Python 3.11.
- Add `ANTHROPIC_API_KEY` in the app's **Secrets** settings. `.streamlit/secrets.toml.example` documents the format.
- `.gitignore` excludes `.streamlit/secrets.toml`, `.env`, `__pycache__/`, `.venv/` and model caches.

## 12. QA Plan
- `qa/eval_questions.md`: the 10 capstone questions and the 15 questions from policy §18, each with its expected answer and section, plus at least 3 out-of-scope questions that should return the fallback.
- `QA_RESULTS.md`: pass/fail for each question, the retrieved sources, and the results for AC-01 to AC-07.
- Sample expectations:

| Question | Expected | Section |
|----------|----------|---------|
| How quickly must a Critical deviation be reported? | To the Site Quality Head within 30 minutes of discovery | 2.2 |
| Target deviation investigation timeline? | 15 calendar days (extension needs QA approval; over 30 days needs Site Quality Head) | 2.3 |
| Who can approve final batch release? | Only an authorized QA release approver | 4.1 |
| Vaccine shipment outside the temperature range? | Temperature excursion: place on quality hold; notify Site QA within 1 hour; QA decides disposition | 5.2–5.4 |
| Potential recall escalation? | To the Global Recall Committee within 1 hour | 8.2 |
| Correction vs CAPA? | A correction fixes the immediate problem; CAPA addresses the root cause or a potential cause | 3.1 |
| Training record retention? | At least 7 years after completion | 11.3 |
| What is the CEO's salary? | Fallback message | — |
