# Greenlight — Brief

A typical 200-question security questionnaire takes 3 days to answer manually. Greenlight does it in under an hour — and every questionnaire you complete makes the next one faster.

---

## The Problem

When a vendor wants to sell to a large company, the company sends a security questionnaire — sometimes 50 questions, sometimes 300+. Answering them is repetitive, slow, and usually falls on one person. The answers are almost always the same across questionnaires, just phrased differently each time. Every hour spent on this is an hour not spent closing the deal.

---

## Who This Is For

There are two types of customers, both with the same problem approached differently.

**Type 1 — Companies with an internal security team**
Series B/C SaaS companies with a dedicated GRC analyst or security engineer in-house. They receive security questionnaires regularly — sometimes 5–10 per month — and the analyst is the bottleneck. They buy Greenlight directly and use it themselves. The CISO or GRC analyst is both the buyer and the day-to-day user.

**Type 2 — Companies with no internal security team**
Smaller companies (10–100 employees) with no dedicated security person. When a questionnaire arrives from a big prospect, they hire a GRC consulting firm to handle it on their behalf. The consulting firm uses Greenlight across all their clients — one tool, many client workspaces, each fully isolated. The consulting firm is the buyer; their clients are the beneficiaries.

Both types feel the same pain. The difference is who in the chain feels it most directly and who makes the buying decision.

---

## Full Product Walkthrough

### Step 1 — Set up the knowledge base

Before answering any questionnaires, the team uploads their company's security documentation:

- Security policies (access control, incident response, encryption, etc.)
- Compliance reports (SOC 2, ISO 27001, pen test results)
- Any internal documents that describe how the company handles security

The system processes each document and breaks it into searchable chunks. When a question comes in later, it finds the most relevant parts of these documents and uses them to draft an answer.

**For new customers with no documents yet:** the tool includes 20 starter policy templates covering common SOC 2 and ISO 27001 topics so teams can get started immediately. A banner warns them these are generic templates and prompts them to upload their real policies.

---

### Step 2 — Upload a questionnaire

The reviewer uploads the customer's questionnaire as an Excel file. Because every company formats these differently, the tool handles this with a two-step column picker:

1. **Preview** — the tool shows the first few rows of the file so the reviewer can see what's in each column
2. **Map columns** — the reviewer clicks to mark which column is the question, which is the Yes/No answer column, and optionally which is the evidence/explanation column

This means the tool works with any Excel layout — it doesn't require a specific template.

---

### Step 3 — Draft answers

Once the questionnaire is set up, the reviewer clicks "Draft Answers." The system goes through every question and:

1. Searches the knowledge base for the most relevant policy chunks
2. Drafts a full answer (evidence/explanation)
3. Drafts a short Yes/No/Partial/N-A answer for questionnaires that have a separate column for it
4. Assigns a confidence score (High / Medium / Low) based on how closely the source documents matched the question
5. Shows which specific policy documents it used as sources

This usually takes 1–3 minutes for a full questionnaire.

---

### Step 4 — Review workspace

This is where a human reviewer goes through each drafted answer. The workspace shows:

- The original question text
- The drafted answer (editable)
- The short Yes/No answer
- A confidence badge (High / Medium / Low)
- The exact source documents and passages it pulled from, each with a match score
- The system's reasoning for why it picked those sources

For each question the reviewer can:

- **Edit** the draft answer directly in the text box
- **Approve** — marks the answer as final and includes it in the export
- **Reject / Flag** — marks it as excluded; it will not appear in the export
- **Re-draft** — asks the system to try again (useful if the first draft missed the point)
- **Assign** — send the question to a specific team member (e.g. a network question goes to the infra engineer)
- **Comment** — leave a note for teammates on a specific question

A progress counter at the top shows how many questions are approved out of the total.

---

### Step 5 — Export

When the reviewer is ready, they click Export. The tool writes the approved answers back into the original Excel file layout — the customer's column structure is preserved. Unapproved, flagged, or edited-but-not-approved answers are never included.

If the customer's questionnaire file contains Excel macros or VBA scripts (common with large financial institutions that lock cells programmatically), the tool detects this automatically and preserves the macro project in the exported file. Answers are also matched to any dropdown lists defined in the file so the output passes Excel's own data validation without manual correction.

The exported file is named with the questionnaire name and today's date, ready to send.

---

### What happens if the AI is wrong?

Nothing leaves without a human approving it. Every answer is explicitly marked as a draft until a reviewer reads it and signs off. The system is designed as a co-pilot, not an autopilot — the AI does the research and writing, the human makes every final decision.

The audit log records exactly who approved which answer, when, and from which source documents. If a customer ever questions an answer, you have a full traceable record. If an answer is later found to be wrong, you reject it and re-draft — it takes seconds, and the system learns from the correction.

The confidence scoring is there precisely for this reason: Low-confidence answers are flagged so reviewers know where to spend their attention. You are never flying blind.

---

### What makes Greenlight different — the compounding answer library

Every answer your team approves is automatically saved to a searchable library. When a similar question appears in a future questionnaire, the system surfaces the previously approved answer as a suggestion — already written, already reviewed, already trusted.

Unlike competitors that treat every questionnaire as a blank slate, Greenlight gets smarter with every one you complete. Your 10th questionnaire takes a fraction of the time your first did. Your institutional security knowledge stops living in someone's inbox and starts compounding into a permanent asset.

---

### Other features

**My Assignments**
Team members see a personal inbox of all questions assigned to them across every questionnaire — question text, confidence, and a link directly to that questionnaire.

**Trash and restore**
Deleted questionnaires and documents go to a trash bin rather than being permanently removed. Owners and admins can restore them. Nothing is lost by accident.

**Audit log**
Every action is logged — who uploaded what, who approved which answer, who exported, who assigned a question to whom, and when. Full trail for compliance purposes.

**Dashboard**
Overview of all questionnaires, total questions answered, approval rate, average confidence score, and estimated time saved.

**Knowledge base health**
A page that shows how well the knowledge base is performing — which questions had low-confidence matches, which topics have gaps, and where uploading more documentation would help.

**Team management**
Owners can invite team members by email. Three roles:
- **Owner** — full access, can manage billing and team
- **Admin** — can manage questionnaires, knowledge base, and team members
- **User** — can review and approve answers on questionnaires assigned to them

---

## Security Features Built Into the Tool Itself

Since this is a security product, I want to be transparent about how the tool itself is secured:

**Accounts and authentication**
- Passwords require: 8+ characters, at least one uppercase letter, one number, and one symbol
- Passwords are stored using Argon2id hashing — the current industry standard recommended by OWASP
- Login sessions use secure, httponly cookies (tokens are not accessible to JavaScript, protecting against XSS attacks)
- Login and registration are rate-limited (5 attempts per minute per IP) to block brute-force attacks
- Email verification required on signup
- Password reset via time-limited email token

**Data protection**
- Uploaded files (Excel questionnaires, policy documents) are stored in S3-compatible object storage — not in the database
- All data is scoped to the organisation at the database query level — every query is filtered by `org_id`, making cross-tenant data access structurally impossible without a deliberate application bypass
- For consulting firms managing multiple clients: each client is a fully isolated workspace with its own `org_id`. No query, search, or suggestion can ever surface data from one client workspace in another. The answer library, knowledge base, and all AI drafting are strictly per-org.
- Soft deletes only — data is never permanently destroyed without explicit action

**AI answer safety**
- **Negation / trap-question detection** — security questionnaires sometimes use reverse-phrasing to catch dishonest vendors (e.g. "Are there any employees exempt from background checks?"). The AI is explicitly instructed to detect this pattern and verify that its Yes/No answer reflects the company's secure, compliant posture — not accidentally admit a gap through a keyword match. Each flagged answer includes a one-line polarity note so the human reviewer knows why the answer was chosen that way.
- **Prompt injection defence** — every document uploaded to the knowledge base is sanitized before it is chunked and stored. Lines matching known injection patterns (system instruction overrides, "ignore previous instructions", model-specific tokens, Chinese-language equivalents) are stripped and logged. At generation time, retrieved document chunks are wrapped in explicit data-only boundaries so the AI is structurally prevented from treating document content as commands — even if a crafted phrase were to slip through the ingest filter.

**Application security**
- Security headers on every response: Content Security Policy, X-Frame-Options, Referrer-Policy, Permissions-Policy
- HTTPS-only mode with HSTS when deployed to production
- CORS restricted to the configured frontend domain only
- File uploads: Excel files only, 20MB maximum size limit
- All actions written to an immutable audit log

**AI retrieval quality (RAG)**

The engine that finds the right policy content for each question uses a multi-layer pipeline that goes significantly beyond what competitors ship:

- **Hybrid search** — every question is searched two ways simultaneously: semantic vector search (understands meaning) and full-text keyword search (catches exact compliance terms like "SOC 2 Type II" or "AES-256" that embedding search can miss). Results are merged using Reciprocal Rank Fusion.
- **HyDE + query expansion** — before searching, the system generates a hypothetical answer and three rephrasings of the question, then searches across all five variants. This dramatically improves recall for verbosely-worded enterprise questionnaire questions.
- **Source-aware ranking** — previously approved human-reviewed answers are ranked 35% higher than generic policy documents. Starter templates are ranked 25% lower. The more questionnaires a team completes, the more the retrieval is weighted toward their own trusted answers.
- **Feedback learning** — every time a reviewer approves an answer, the source chunks that contributed receive a positive signal. Every rejection or re-draft triggers a negative signal. Over time, chunks that consistently produce bad answers are automatically down-ranked for that organisation — the system gets smarter with every review decision, without any manual curation.
- **Parent-child retrieval** — documents are stored at two levels: small child chunks (~150 tokens) for precise retrieval, and large parent chunks (~800 tokens) for rich LLM context. The system finds answers with the precision of a small chunk but sends the full surrounding section to the AI — 5× more context per result.
- **Semantic chunking** — documents are split at structural boundaries (headers, numbered sections, paragraph breaks) rather than arbitrary token counts, so a policy clause about encryption is never split mid-sentence across two chunks.
- **Voyage reranking** — after retrieval, a dedicated reranking model re-scores the top 20 candidates for true relevance before the final selection is sent to the LLM.
- **Retrieval evaluation** — an internal dashboard (`/admin/rag-eval`) continuously measures retrieval quality against the organisation's own approved answer history. Metrics include hit rate, precision@1, and Mean Reciprocal Rank — so degradation is caught before it affects answer quality.

**Monitoring**
- Error tracking via Sentry (crash reports, never user data)
- Automated test suite runs on every code change via CI pipeline

**Team invites**
- Owners and admins generate a unique invite link from the Team page — there is no permanent "invite code"
- Each link is single-use (consumed the moment someone registers with it) and expires automatically after 48 hours
- Admins can revoke any active link at any time before it is used
- The invite token is never stored in the database — only its hash — so a database leak does not expose usable links

**Coming soon**
- MFA (authenticator app / TOTP) — opt-in per user, with org-level enforcement for admins
- Data retention / purge job — soft-deleted items auto-permanently removed after 90 days (with privacy policy disclosure)
- SSO / SAML — single sign-on via Google Workspace, Okta, Azure AD
- Org-level admin settings — force MFA for all members, configure data retention period
- Multi-sheet Excel support — questionnaires that span multiple tabs in the same file
- Word and PDF questionnaire upload — not just Excel files
- Web portal integrations — OneTrust, Vanta, Whistic (for customers who share a portal link instead of a file)
- Common framework templates — pre-built questionnaire templates for CAIQ, SIG Lite, VSA so teams can start without waiting for a customer to send one
- Australian data sovereignty — all customer data (uploaded documents, questionnaires, AI-generated content) stored exclusively on AWS Sydney region (ap-southeast-2), meeting Australian privacy and data residency requirements out of the box

---

