# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project
HelixNova Pharma Quality & Regulatory RAG Assistant: a Streamlit app that answers questions about uploaded PDF/TXT policy documents, using only retrieved chunks, and cites filename + chunk number.

- Requirements: `requirements.md`
- Design: `specification.md` (the source of truth for constants, prompts and the UI)
- Sample data: `helixnova_pharma_quality_policy_dataset.txt` / `.pdf` (synthetic)

## Rules
1. **Plan before code.** Update `specification.md` before making behavior changes to `app.py`.
2. **Approved stack only:** Python, Streamlit, anthropic, sentence-transformers, faiss-cpu, pypdf (plus numpy). Don't add LangChain, LlamaIndex, vector DB services, etc.
3. **Never hardcode secrets.** Read `ANTHROPIC_API_KEY` from `st.secrets`, falling back to the environment variable. Never commit `.streamlit/secrets.toml` or `.env`.
4. **Grounding:** send only retrieved chunks to Claude. Keep the exact fallback message: "I could not find enough information in the uploaded policy document(s) to answer this question."
5. **Model:** `claude-sonnet-5-5`, no `temperature` parameter (the model rejects it); use `output_config.effort`.
6. **Single file:** keep the app in `app.py` unless the spec changes.
7. **Session only:** chat history and indexes live in `st.session_state`. Nothing is persisted to disk.
8. **Governance:** the assistant is advisory and must never make autonomous quality decisions (policy §15.2).

## Commands
```bash
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
streamlit run app.py
```
Local secrets: create `.streamlit/secrets.toml` containing `ANTHROPIC_API_KEY = "..."`, or set the environment variable.

## QA
Run the questions in `qa/eval_questions.md` against the sample policy (TXT and PDF) and record the results in `QA_RESULTS.md`. Check for hardcoded keys with a search for `sk-ant`.
