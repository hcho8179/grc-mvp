# Greenlight Demo Guide

5-minute demo script for prospective customers.

---

## Reset & load demo data

```bash
cd grc-mvp
python scripts/seed_demo.py   # type "yes" when prompted
uvicorn app.main:app --port 8000
```

Open `http://localhost:8000` — you'll land on the dashboard.

---

## 5-minute demo script

### 1. Dashboard (30 s)
*"This is Greenlight — our AI-powered security questionnaire tool. The dashboard shows everything at a glance: how many questionnaires we've handled, how many questions the AI has answered, average confidence, and hours saved. Those hours assume 8 minutes per question answered manually — for a 100-question SIG questionnaire, that's 13+ hours saved."*

### 2. Knowledge base (60 s)
Click **Knowledge Base**.

*"Greenlight learns from your own company documents. We've pre-loaded Acme's information security policy, data protection policy, incident response plan, and 30 past questionnaire answers. When a new question comes in, the AI retrieves the most relevant chunks and generates an answer grounded in your actual policies — it never invents certifications you don't hold."*

Click **Upload Document** and drag in a PDF or DOCX if available, or skip.

### 3. Upload a questionnaire (60 s)
Click **Questionnaires → Upload Questionnaire**.

- Name: `MegaBank Vendor Assessment`
- Customer: `MegaBank Financial Group`
- Upload `MegaBank_Vendor_Assessment_2026.xlsx` (already in the DB from seed)

*"The customer sent us this 20-question spreadsheet. We upload it, tell Greenlight which column has the questions, and we're done with the manual part."*

*(If using seeded data, just navigate to the existing MegaBank questionnaire.)*

### 4. Generate answers (90 s)
Open the MegaBank questionnaire. Click **✦ Generate Answers**.

*"Greenlight now runs each question through our knowledge base. It does a semantic search — not keyword matching — so 'describe your encryption standards' retrieves the encryption section of our security policy even though those exact words don't appear together."*

While it runs: *"Each answer gets a confidence score. High means multiple strong sources directly answered it. Medium means some inference was required. Low means it needs human review."*

### 5. Review and approve (60 s)
Show the results table.

*"Every answer is editable inline. The sources column shows exactly which knowledge base chunks were used — full traceability. If I want to tweak the answer, I just edit it here and click Approve."*

- Click a source badge to expand the chunk text
- Edit one answer, click Save, then Approve
- Show the answer status changing to Approved

*"Approved answers automatically feed back into the knowledge base. The next time a similar question comes in — from a different customer — Greenlight will use this approved answer as a source. It gets smarter over time."*

### 6. Export (30 s)
Click **↓ Export XLSX**.

*"One click gives you the original questionnaire format, with the AI-generated answers filled into the answer column. You send this directly to the customer. The whole process — for a 20-question questionnaire — just took about 2 minutes."*

---

## Common questions

**"How does it know our policies?"**
It only uses documents you upload. We embed them into a vector database and retrieve the most relevant excerpts per question. No knowledge is shared between customers.

**"What if it gets something wrong?"**
Every answer requires human review before export. You can edit, regenerate, or reject any answer. The confidence badge tells you where to focus your attention.

**"What LLM does it use?"**
Currently Gemini 2.5 Flash (configurable to Claude). For typical questionnaires, AI cost is well under $0.10.

**"Is our data sent to the LLM provider?"**
Yes — the question text and relevant policy excerpts are sent to the LLM to generate an answer, same as using ChatGPT. We don't send full documents, only the retrieved chunks.

**"Can it handle multi-sheet Excel files?"**
Currently single-sheet. Multi-sheet support is on the roadmap for Q2.

**"What's the integration story?"**
Today it's a standalone web app. The roadmap includes a Salesforce integration for auto-creating questionnaire records, and an email parser to detect incoming questionnaires.

---

## Talking points

**Time saved:** A typical 100-question SIG Lite questionnaire takes 2-3 days manually. With Greenlight, an hour — including review.

**Accuracy:** Grounded in your actual policies — no hallucinated certifications. Confidence scores make human review efficient.

**Self-improving:** Approved answers become training data. The second questionnaire from the same customer is faster and more confident than the first.

**Pricing model:** Per-questionnaire or per-seat. The AI cost per questionnaire is cents, not dollars.
