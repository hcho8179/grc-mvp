# Greenlight — Product Brief

A typical 200-question security questionnaire takes 2–3 days to answer manually. Greenlight does it in under an hour — and every questionnaire you complete makes the next one faster.

---

## The Problem

When a vendor wants to sell to a large company, the company sends a security questionnaire — sometimes 50 questions, sometimes 300+. Answering them is repetitive, slow, and usually falls on one person. The answers are almost always the same across questionnaires, just phrased differently each time.

---

## Built for the Australian Market

The main competitors — Hypercomply and Conveyor — are US tools that have no coverage of Australian compliance frameworks. Greenlight is built specifically for the AU market.

Every customer starts with 45 pre-loaded Australian GRC Q&A pairs — automatically expanded to ~270 semantic variants on registration so the system matches questions regardless of phrasing — covering the four frameworks AU clients ask about most:

- **ASD Essential Eight** — required by almost every Australian government agency and large enterprise
- **Australian Privacy Act / APPs** — mandatory for any company handling Australian personal data
- **APRA CPS 234** — mandatory for all APRA-regulated banks, insurers, and superannuation funds
- **ISO 27001** — widely adopted in AU financial services and health

A consultant using a US tool starts from zero on every Essential Eight questionnaire. A consultant using Greenlight starts with real, well-written answers on day one.

---

## How It Works

**1. Upload your knowledge base** — security policies, compliance reports, pen test results. The system breaks them into searchable chunks. New customers can skip this step entirely and use the pre-loaded AU library from day one.

**2. Upload a questionnaire** — Excel, Word, or PDF. For Excel, a column picker maps which column is the question and which is the answer. No template required.

**3. Draft answers** — one click. The system searches the knowledge base and answer library for each question, drafts a full answer and a short Yes/No, assigns a confidence score (High / Medium / Low), and shows the exact source passages it drew from.

**4. Review** — a human reads every draft, edits if needed, and approves or rejects. Nothing leaves without sign-off.

**5. Export** — the approved answers are written back into the original Excel layout, preserving the customer's column structure. Ready to send.

---

## The Compounding Answer Library

Every approved answer is saved to a searchable library. When a similar question appears in a future questionnaire, the previously approved answer surfaces as a suggestion — already written, already reviewed.

Your 10th questionnaire takes a fraction of the time your first did.

**For GRC consulting firms:** answers are automatically split into two layers — generic answers (reused across all clients) and client-specific answers (isolated to that client only). The system auto-detects which category an answer falls into as the reviewer types. Getting this wrong is a professional liability; Greenlight enforces it at the database level, not just in the UI.

---

## Other Features

- **Share link** — generate a read-only link for a client or manager to review progress without a Greenlight account
- **Answer version history** — every edit is saved; full audit trail of who changed what and when
- **KB Health** — shows which knowledge base documents are getting stale and where coverage gaps exist
- **Trash and restore** — nothing is permanently deleted without explicit action
- **Team management** — Owner / Admin / Member roles with invite links

---

## Accuracy and Hallucination Prevention

A wrong answer on a security questionnaire is a compliance liability. Greenlight has four guardrails against this:

- The AI is instructed to answer only from uploaded documents and approved past answers — it will not fill gaps from general knowledge
- Every drafted answer shows the exact source passages it drew from, so the reviewer can verify the answer against the source in the same view
- When the knowledge base has little relevant content, the answer gets a **Low confidence** badge — a signal to spend more time on it
- If there is no matching content at all, the question is flagged **MANUAL** with an explicit warning. The system never silently generates an answer when it has nothing to work from

Nothing leaves without a human approving it. The system is a co-pilot, not an autopilot.

---

## Data Security and Client Isolation

- Client answers are isolated at the database level — when generating answers for Atlas Bank, the system is structurally prevented from retrieving answers tagged to any other client. This is not a UI filter; it is enforced in the query itself
- All data is scoped to your workspace — cross-tenant access is structurally impossible
- Every action is written to an immutable audit log: who approved which answer, from which source, and when
- Uploaded files are stored in S3-compatible object storage; sessions use secure, httponly cookies with the strictest same-site policy

---

## Honest Limitations

- Excel questionnaires that span multiple tabs are not yet supported (on the roadmap)
- Answer generation runs one questionnaire at a time per workspace — parallel generation is on the roadmap
- No due date or deadline tracking on questionnaires yet

---

## Coming Soon

MFA, SSO (Google Workspace / Okta / Azure AD), multi-sheet Excel support, question assignment to team members, OneTrust / Vanta / Whistic integrations, Australian data sovereignty (AWS Sydney), Google Drive / SharePoint sync, and **compliance framework mapping** — automatically tagging each approved answer to its relevant Essential Eight strategy and maturity level, ISO 27001 Annex A control, or APRA CPS 234 paragraph, so the assessment output is produced alongside the questionnaire rather than manually after it.
