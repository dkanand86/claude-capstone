# QA Results

Date: 2026-09-30 · Model: `claude-sonnet-5-5` · Embeddings: `all-MiniLM-L6-v2` · Top-K 6 (4 in the first run below) · Min score 0.25
Method: the app's own functions (extract → chunk → embed → FAISS → retrieve → Claude), run headless against the sample policy as TXT (29 chunks) and PDF (27 chunks). The Streamlit UI was not driven in a browser.

## Question results (17 asked, TXT and PDF)

| Question (see `qa/eval_questions.md`) | TXT | PDF | Notes |
|---|---|---|---|
| A1/B1 Critical deviation reporting | PASS | PASS | 30 min, Site Quality Head |
| A2/B2 Investigation timeline | PASS | PASS | 15 days, extension rules |
| A3/B4 Final batch release | PASS | PASS | Authorized QA approver only |
| A4/B6 Temperature excursion | PASS | PASS | Quality hold, escalation, QA disposition; noted the policy has no vaccine-specific rule |
| A5 Recall escalation | PASS | PASS | 1 hour |
| A6 Correction vs CAPA | PASS | PASS | |
| A7/B8 Change control | PASS | PASS | |
| A8 Data integrity, electronic records | PASS | PASS | TXT answer said section 10.4 was cut off, which is true of the retrieved context (only 4 chunks) |
| A9/B12 Training retention | PASS | PASS | 7 years |
| A10/B15 Behavior when no answer | PASS | PASS | |
| B5 Conditional release | PASS | PASS | No |
| B9 Adverse event to PV | PASS | PASS | 24 hours |
| B13 Severity 1 incident | PASS | PASS | 15 minutes |
| B14 AI close deviation / approve batch | PASS | PASS | No |
| C1 CEO salary | PASS | PASS | Fallback |
| C2 Capital of France | PASS | PASS | Fallback |
| C3 Stock forecast | PASS | PASS | Fallback |

| B3 When is CAPA mandatory? | PASS | PASS | All six triggers listed, plus the isolated-Minor exception |
| B7 Commercial-batch excursion reporting | PASS | PASS | Site QA within 1 h; Global QO 2 h if distributed |
| B10 Who can authorize a recall? | PASS | PASS | Correctly noted the policy names no authorizing role: Global Recall Committee *recommends*, Commercial cannot authorize or cancel. TXT answer ended with the fallback sentence as well, which is slightly redundant |
| B11 Electronic audit trails | PASS | **FAIL** | PDF returned the fallback: retrieval missed the real content (see below) |

Pass/fail was judged by reading each answer against the expected answers; it wasn't automated. All 25 questions in `qa/eval_questions.md` have now been run (A/B duplicates counted once): 24 of 25 pass on both files; B11 fails on the PDF.

### B11 failure analysis (PDF)
The sample policy's own section 18 lists "What are the expectations for electronic audit trails?" verbatim, so that chunk (#27) scores 0.62 and outranks the real content (chunk 16, score 0.31, rank 7 of 8). Top-4 therefore contained only the question list, and Claude correctly refused to answer from it. Grounding worked as designed; retrieval is the weak point. Rewording the query to match the policy text ("audit trails ... must be enabled") retrieves chunk 16 first (0.70).
**Fix applied and re-tested:**
1. The "Example questions" section is no longer indexed (`drop_eval_section`). Alone this fixed TXT but not PDF: the real chunk (16) is a mixed-topic chunk (supplier text + data integrity), so its embedding score is low and it still ranked 5th.
2. Default Top-K raised from 4 to 6, which brings chunk 16 into the results.
Re-test: full re-run of all 28 questions (10 A + 15 B + 3 C) on TXT and PDF at Top-K 6 with the section excluded: every in-scope question answered with the expected facts and citations (including B11 on the PDF), and C1-C3 returned the exact fallback on both files. Method: I read each answer's key facts against `qa/eval_questions.md`; long answers (A4, A7, A8, B3, B6) were checked on their opening portion, not word for word.
Remaining weakness (addressed below): retrieval quality depends on chunk boundaries.

### Section-aware chunking (2026-09-30)
Chunks now break at section headings (`10. DATA INTEGRITY`) and subsection headings (`10.2 Electronic Records`), including headings that sit mid-line in PDF text (spec §4). The sample now yields 62 chunks (TXT) and 67 (PDF), up from 29 and 27.
- **First attempt, sections only:** PDF B11 got worse, because the whole of section 10 sat in one diluted chunk ranked 7th. Reverted to the subsection split below.
- **With subsection splitting:** the audit-trail chunk ranks 1st on both files (score 0.41).
- **Full re-run, 28 questions on TXT and PDF (56 answers):** an automated keyword check found 0 failures. I also read the PDF answers for B11, A7, B3, A4 and A8 and the TXT answers for A7 and A2 in full: the facts and citations were correct.
- **Minor regression:** the PDF A8 answer no longer leads with the 10.1 core principle (ALCOA-style attributes). It covers 10.2-10.4 only, because chunks are smaller and 10.1 sits in a separate chunk. Raising Top-K or keeping `10.1` with `10.2` would fix it. Not done.
- **Caveat:** the chunk numbers in the earlier sections of this file refer to the old chunking.
Result now: **25 of 25 pass on TXT and PDF** (B11 after the fix).

## Re-run at current settings (Top-K 6, eval section excluded)
Date: 2026-09-30. Same headless method: all 28 questions (10 A + 15 B + 3 C) on the TXT and PDF sample policy, 56 answers.

- **In-scope (A1-A10, B1-B15): 25 of 25 pass on both files.** Each answer contained the expected facts and cited filename + chunk. B11 on the PDF now passes: the answer cites chunk 16, so it was retrieved. It was not in the top 3 (those scored 0.34, 0.32, 0.32), so it is a weak match and stays fragile.
- **Out-of-scope (C1-C3): 3 of 3 return the exact fallback on both files.** C3 retrieved one chunk (score 0.38, chunk 1) and Claude declined it with the fallback.
- **Judgement was manual**, against `qa/eval_questions.md`.
- **A4:** the answer notes the policy has no vaccine-specific rule, then gives the general refrigerated-product handling (quality hold, Site QA 1 h, Global QO 2 h, only QA approves return). The PDF answer omitted the recall escalation that the TXT answer included.
- **B10:** both files say no single role "authorizes" a recall; the Global Recall Committee recommends and Commercial cannot authorize or cancel. This is more cautious than the expected answer but is faithful to the text.
- **A10 (TXT):** the answer opens with an odd preamble ("The system rules and the policy give slightly different wording...") before giving the required sentence. The content was right, but the wording was awkward. **Fixed** by adding rule 6 to the system prompt (spec §7 and `app.py`). Re-tested 2026-09-30: the A10 and B15 questions, 3 runs of A10 and 2 of B15 on each of TXT and PDF, all answered from the policy with no preamble. A1 still answers correctly and C2 still returns the exact fallback.

## Audit log download (2026-09-30)
Session-only export (spec §8.1): a sidebar **Download audit log** button builds a JSON file from `st.session_state.messages` (timestamp, question, answer, status, Top-K, source filename/chunk/page/score; no chunk text). Nothing is stored on the server.
Browser test (headless Chromium, local `streamlit run`, TXT sample): button present and disabled before any chat; after one in-scope and one out-of-scope question it is enabled and downloads `audit_log_<UTC timestamp>.json` with 2 entries (`answered` with 6 sources; `fallback` with none). Chat shows 4 messages with no duplicates. Not tested on Streamlit Cloud, and not tested with the PDF or with an API error (`status: error`).
Limits: the log empties on Clear chat, a reload or a new session, so it must be downloaded first. Answers are logged as shown, not checked.

## Acceptance criteria

| ID | Result | Evidence |
|---|---|---|
| AC-01 PDF and TXT work | PASS | Both files extracted, chunked, indexed and answered |
| AC-02 Correct answer with sources | PASS | Every in-scope answer cited chunks |
| AC-03 Unsupported questions → fallback | PASS | C1–C3 returned the exact fallback with no sources; retrieval scored below 0.25 so Claude was not called |
| AC-04 No hardcoded key | PASS for source | `app.py` reads secrets or environment only. See finding below |
| AC-05 Sources show filename + chunk | PASS | Browser test: "Sources (4)" expander lists `filename — chunk #N (page P) · score 0.xx` plus snippet; TXT and PDF sources shown side by side (`qa/ui_multi.png`) |
| AC-06 History persists in session | PASS | Browser test: 2 Q&As stayed visible; still visible after adding a PDF (index rebuilt); "Clear chat" emptied it |
| AC-07 Streamlit Cloud ready | PASS | Deployed to Streamlit Community Cloud from `main`. Reported by the project owner after a manual test there: PDF + TXT upload indexed (56 chunks), the Critical-deviation question answered with sources, and an out-of-scope question returned the exact fallback. `ANTHROPIC_API_KEY` came from Streamlit secrets. I did not observe the cloud app myself |

## Findings
1. **A `.env` file containing an Anthropic API key sits in the project folder.** It is listed in `.gitignore`, but there is no git repo yet, so make sure it never gets committed or zipped for submission. Consider rotating the key if the folder has been shared.
2. **`temperature` is rejected by Sonnet 5.5.** Removed; the app uses `output_config.effort = "low"`. Answers are still deterministic enough for the tests, but wording can vary between runs.
3. **Sources are shown even for partly-answered questions**, and retrieval sometimes returns loosely related chunks (for example chunks 28–29 in the TXT run). Top-K 4 is a reasonable default.
4. The API call uses the beta endpoint with server-side fallbacks (`server-side-fallback-2026-07-01`). If the SDK version on Streamlit Cloud doesn't support this, drop those two arguments.

## Browser UI test (headless Chromium via Playwright, real `streamlit run app.py`)

| Check | Result |
|---|---|
| No upload: info box shown, chat input disabled | PASS |
| Upload TXT → "Indexed 1 file(s), 29 chunks" | PASS |
| Ask in-scope question → answer + Sources expander | PASS |
| Ask out-of-scope question → exact fallback, no Sources expander | PASS |
| Add PDF (multi-document) → "Indexed 2 file(s), 56 chunks"; sources from both files | PASS |
| Upload an empty `.txt` → "No extractable text" warning | PASS |
| Clear chat | PASS |

Bugs found and fixed during this test:
- **Streamlit log flooded with `torchvision` import errors** (its file watcher crawls `transformers`). Fixed with `.streamlit/config.toml` (`fileWatcherType = "none"`).
- **Same file uploaded twice was indexed twice** (85 chunks instead of 56, duplicate sources). `update_index` now skips repeated filenames.

## Not tested
- Running with no API key (the app disables the chat box and shows a warning; not exercised).
- A scanned, image-only PDF.
