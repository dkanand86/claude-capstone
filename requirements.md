# Requirements — HelixNova Pharma Quality & Regulatory RAG Assistant

## 1. Purpose
Give HelixNova Pharma employees a grounded question-answering assistant over internal quality/regulatory policy documents (PDF/TXT). Answers must come only from the uploaded documents and cite their sources.

> All company names, thresholds and policy content are synthetic, for training only.

## 2. Users
- Manufacturing, QA, QC, Supply Chain, Regulatory Affairs, Pharmacovigilance, Engineering, IT and Supplier Quality staff.
- Capstone reviewers/trainers evaluating RAG quality.

## 3. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-01 | Users can upload one or more policy documents in **PDF** or **TXT** format. |
| FR-02 | The system extracts text from PDFs (pypdf) and TXT files (UTF-8, latin-1 fallback). |
| FR-03 | Extracted text is split into overlapping chunks; each chunk keeps its filename, chunk number and (for PDF) page number. |
| FR-04 | Chunks are embedded with **sentence-transformers**. |
| FR-05 | Embeddings are stored in a **FAISS** index held in the current session. |
| FR-06 | For each question, the system retrieves the top-K most relevant chunks. |
| FR-07 | Only the retrieved chunks (not the whole document) are sent to **Claude** as context. |
| FR-08 | Claude returns an answer grounded in the retrieved context. |
| FR-09 | Each answer shows its sources as **filename + chunk number** (plus page and similarity score). |
| FR-10 | If the answer is not in the documents, the assistant returns the agreed fallback message (§5). |
| FR-11 | Chat history (questions, answers, sources) stays visible for the current Streamlit session only, and can be cleared. |
| FR-12 | Multi-document retrieval with per-chunk source attribution. |
| FR-13 | Similarity scores can be shown for each retrieved source. |

## 4. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-01 | **Security:** no API key is hardcoded. The key is read from `st.secrets` or the `ANTHROPIC_API_KEY` environment variable. Secrets files are git-ignored. |
| NFR-02 | **Tech stack:** Python, Streamlit, Anthropic Claude API, sentence-transformers, FAISS (faiss-cpu), pypdf. No other frameworks (for example, no LangChain). |
| NFR-03 | **Deployability:** runs on Streamlit Community Cloud without changing business behavior. |
| NFR-04 | **Performance:** the embedding model is loaded once and cached; the index is rebuilt only when the uploaded files change. |
| NFR-05 | **Governance:** the assistant must not make autonomous quality decisions (policy §15.2) and must not invent answers (policy §15.3). |
| NFR-06 | **Robustness:** empty, unreadable or scanned (text-free) files and a missing API key produce clear user messages, not crashes. |
| NFR-07 | **Privacy:** documents and chat history are kept in memory for the session only and never written to disk. |

## 5. Agreed Fallback Message
> I could not find enough information in the uploaded policy document(s) to answer this question.

## 6. Acceptance Criteria

| ID | Criterion | Covers |
|----|-----------|--------|
| AC-01 | PDF and TXT uploads both work. | FR-01, FR-02 |
| AC-02 | At least one policy question is answered correctly, with source chunks. | FR-06–FR-09 |
| AC-03 | Unsupported questions return the agreed fallback message. | FR-10 |
| AC-04 | No API key is hardcoded. | NFR-01 |
| AC-05 | Sources show filename + chunk number. | FR-09 |
| AC-06 | Previous questions and answers remain visible during the session. | FR-11 |
| AC-07 | The app can be deployed to Streamlit Community Cloud without changing business functionality. | NFR-03 |

## 7. Out of Scope (v1)
- Document-level filters and an in-app RAG quality dashboard (possible later extensions).
- Persistent storage, user authentication, OCR for scanned PDFs.
