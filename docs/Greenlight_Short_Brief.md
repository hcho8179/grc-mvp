# Greenlight — Product Brief

A typical 200-question security questionnaire takes 2–3 days to answer manually. Greenlight does it in under an hour — and every questionnaire you complete makes the next one faster.

**Scope today:** **Inbound** — you receive a questionnaire and need to answer it fast and accurately. Outbound vendor assessment (sending questionnaires to your vendors) is not in the product yet.

---

## The Problem

When a vendor wants to sell to a large company, the buyer sends a security questionnaire — sometimes 50 questions, sometimes 300+. Answering them is repetitive, slow, and usually falls on one person. The answers are almost always the same across questionnaires, just phrased differently each time.

---

## Built for the Australian Market

The main competitors — Hypercomply and Conveyor — are US tools with no coverage of Australian compliance frameworks. Greenlight is built for the AU market.

Every customer starts with **45 pre-loaded Australian GRC Q&A pairs** (expanded to ~270 semantic variants on registration), covering:

| Framework | Why it matters in AU |
|-----------|----------------------|
| **ASD Essential Eight** | Required by most government agencies and large enterprises |
| **Privacy Act / APPs** | Mandatory for handling Australian personal data |
| **APRA CPS 234** | Mandatory for APRA-regulated banks, insurers, super funds |
| **ISO 27001** | Widely adopted in financial services and health |

A consultant on a US tool starts from zero on Essential Eight. On Greenlight, they start with real answers on day one.

---

## How It Works

| Step | What happens |
|------|----------------|
| **1. Knowledge base** | Upload policies, SOC 2 reports, pen tests. Chunked and embedded for search. Or skip and use the AU starter library. |
| **2. Upload questionnaire** | Excel (multi-sheet), Word, or PDF. Map columns for Excel; optional **due date** for SLA tracking. |
| **3. Draft answers** | Background AI job searches KB + answer library, drafts full + Yes/No answers, confidence, and **source passages**. Poll progress in the UI. |
| **4. Review** | Human edits, approves, or rejects every answer. Flag notes for hand-offs. Nothing exports without sign-off. |
| **5. Export** | Approved answers written back into the **original Excel layout**. |

---

## Policy Freshness — How Real Teams Work

Greenlight separates **“policy content changed”** from **“policy is just old”**:

| Situation | System behaviour |
|-----------|------------------|
| **Replace or delete** a KB document | Approved answers that cited that policy are flagged **stale** in the Answer Library — re-review before reuse |
| **Upload / replace** resets **Last confirmed** | `content_updated_at` tracks when content was last uploaded or replaced |
| **90 / 180 days** without replace | Amber / red **reminder badges** on Knowledge Base — “confirm still current”. **Does not** block AI or RAG |
| **Reviewing a draft** | Source panel shows confirmation date + same age warnings |
| **KB Health** | Topic coverage scores **plus** a **Policy hygiene** panel (stale answers + docs due for confirmation) |

**Rule of thumb:** when policy text changes, use **Replace** — not delete-and-re-upload. Linked library answers are flagged automatically.

---

## The Compounding Answer Library

Every approved answer is saved to a searchable library. Similar questions in future questionnaires surface trusted, already-reviewed text.

**For GRC consulting firms:** answers split into **generic** (all clients) and **client-specific** (isolated at the **database query** level — not a UI filter). Auto-detection at approve time; promote to generic from the library later.

---

## Other Features

- **Share link** — read-only progress for clients or managers (no account)
- **Answer version history** — full edit trail per question
- **KB Health** — topic gaps + policy hygiene
- **Due dates** — optional on questionnaires; email reminders within 48 hours
- **Trash** — soft delete; auto-purge after 90 days (maintenance job)
- **Team** — Owner / Admin / Member; single-use invite links (48h expiry)
- **Audit log** — who did what, when, from which source

---

## Accuracy and Hallucination Prevention

| Guardrail | Purpose |
|-----------|---------|
| Grounded generation only | No inventing from general knowledge |
| Sources shown inline | Reviewer verifies draft against passages |
| Confidence badges | Low = spend more time here |
| **MANUAL** flag | No KB match → explicit warning, no silent fabrication |
| Human approval gate | Nothing leaves without sign-off |

The system is a **co-pilot, not an autopilot**.

---

## Data Security and Client Isolation

- Client answers isolated in **SQL retrieval** — structurally impossible to leak across clients
- Workspace-scoped data — no cross-tenant access
- Immutable audit log on approvals and exports
- S3-compatible storage; httponly cookies + CSRF double-submit

---

## Honest Limitations

- One active **generation job per questionnaire** (different questionnaires can run in parallel); worker runs in the same app process today
- Upload, knowledge ingest, and bulk generate require **verified email** (`TESTING=true` skips in dev)
- Per-question assignment removed — use **flag notes** on questions
- No compliance **framework control mapping** yet (Essential Eight level, ISO Annex A, etc.)

---

## Coming Soon

MFA, SSO (Google Workspace / Okta / Azure AD), question assignment, OneTrust / Vanta / Whistic integrations, **AWS Sydney** data residency, Google Drive / SharePoint sync, and **compliance framework mapping** — tagging approved answers to Essential Eight maturity, ISO 27001 controls, or APRA CPS 234 paragraphs alongside the questionnaire.

---

## Long-Term Vision (Not Built)

**Outbound TPRM** — send questionnaires to vendors, score responses, vendor risk register. Natural expansion after inbound is proven with paying customers.
