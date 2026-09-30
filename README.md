# HelixNova Pharma Quality & Regulatory RAG Assistant

Streamlit app that answers questions about uploaded PDF/TXT policy documents using retrieval-augmented generation (sentence-transformers + FAISS + Claude), citing filename and chunk number.

> Synthetic training data only.

**Live app:** https://claude-capstone-mto7nqkhzvca89tutktwde.streamlit.app/

## Run locally
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
copy .streamlit\secrets.toml.example .streamlit\secrets.toml   # then add your key
streamlit run app.py
```
Alternatively set the `ANTHROPIC_API_KEY` environment variable.

## Deploy to Streamlit Community Cloud
1. Push this repo to GitHub (secrets are git-ignored).
2. Create a new app at share.streamlit.io, entry point `app.py`.
3. In **App settings → Secrets**, add `ANTHROPIC_API_KEY = "..."`.

## Docs
- `requirements.md` — requirements & acceptance criteria
- `specification.md` — design
- `CLAUDE.md` — contributor rules
- `qa/eval_questions.md` — evaluation set; `QA_RESULTS.md` — results
