# Evaluation Questions

Run against `helixnova_pharma_quality_policy_dataset.txt` and `.pdf`. Record results in `QA_RESULTS.md`.

## A. Capstone suggested questions

| # | Question | Expected answer | Section |
|---|----------|-----------------|---------|
| A1 | How quickly must a Critical deviation be reported? | To the Site Quality Head within 30 minutes of discovery | 2.2 |
| A2 | What is the target timeline for completing a deviation investigation? | 15 calendar days; extension needs QA approval; >30 days needs Site Quality Head written approval | 2.3 |
| A3 | Who can approve final batch release? | Only an authorized QA release approver | 4.1 |
| A4 | What happens if a vaccine shipment is outside the approved temperature range? | Temperature excursion (2–8 C standard); quality hold until QA assessment; Site QA within 1 h; Global QO within 2 h if distributed; only QA approves return | 5.1–5.4 |
| A5 | How quickly must a potential product recall be escalated? | Global Recall Committee within 1 hour of confirmed credible risk | 8.2 |
| A6 | What is the difference between a correction and a CAPA? | Correction fixes immediate problem; corrective action addresses root cause; preventive action addresses potential cause | 3.1 |
| A7 | When is formal change control required? | Before changes affecting validated processes, specs, analytical methods, critical equipment, GxP computerized systems, critical suppliers, labeling, packaging, storage, regulatory commitments | 6.1 |
| A8 | What are the data-integrity expectations for electronic records? | ALCOA+ principles; no shared accounts; preserve identity and date/time; audit trails enabled | 10.1–10.2 |
| A9 | How long must completed training records be retained? | At least 7 years after completion | 11.3 / 16 |
| A10 | What should the assistant say if the policy does not contain the answer? | State it could not find enough information rather than invent an answer | 15.3 |

## B. Policy §18 questions

| # | Question | Expected answer | Section |
|---|----------|-----------------|---------|
| B1 | How quickly must a Critical deviation be reported? | 30 minutes, Site Quality Head | 2.2 |
| B2 | How many days should a deviation investigation normally take? | 15 calendar days | 2.3 |
| B3 | When is CAPA mandatory? | Critical deviations, recurring Major, systemic DI failures, critical audit findings, supplier failures with product impact, recalls with systemic cause | 3.2 |
| B4 | Who has final authority to release a batch? | Authorized QA release approver | 4.1 |
| B5 | Can an unresolved Critical issue receive conditional batch release? | No | 4.3 |
| B6 | What happens when refrigerated product exceeds its approved temperature range? | Excursion; quality hold; QA assessment/disposition | 5.2 |
| B7 | How quickly must a commercial-batch temperature excursion be reported? | Site QA within 1 hour | 5.3 |
| B8 | When is formal change control required? | See A7 | 6.1 |
| B9 | How quickly must a possible adverse event be sent to Pharmacovigilance? | Within 24 hours of first awareness | 7.3 |
| B10 | Who can authorize a product recall? | Global Recall Committee recommends; Commercial cannot authorize | 8.3 |
| B11 | What are the expectations for electronic audit trails? | Enabled for critical GxP systems; not disabled during normal operation | 10.2 |
| B12 | How long are completed training records retained? | At least 7 years | 11.3 |
| B13 | How quickly must a Severity 1 security incident be escalated? | IT Security Incident Lead + Site Quality Head within 15 minutes | 13.2 |
| B14 | Can an AI assistant close a deviation or approve a batch? | No | 15.2 |
| B15 | What should the RAG assistant do when the retrieved context does not contain the answer? | Say it could not find enough information | 15.3 |

## C. Out-of-scope (expect fallback)

| # | Question |
|---|----------|
| C1 | What is the CEO's salary? |
| C2 | What is the capital of France? |
| C3 | What is HelixNova's stock price forecast for 2027? |

Expected: *"I could not find enough information in the uploaded policy document(s) to answer this question."*
