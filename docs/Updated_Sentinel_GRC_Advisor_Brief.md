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

In this mode, every approved answer goes straight to the organisation's shared memory — there is no client isolation needed because all questionnaires are about the same company. The system gets smarter about that company's security posture automatically with every approval.

**Type 2 — GRC consulting firms**
Smaller companies (10–100 employees) with no dedicated security person hire a GRC consulting firm to handle questionnaires on their behalf. The consulting firm uses Greenlight across all their clients — one workspace, multiple clients, each fully isolated from one another. The consulting firm is the buyer; their clients are the beneficiaries.

In this mode, each questionnaire is tagged to a specific client. Approved answers build both a per-client memory and a shared generic library — isolating sensitive client-specific answers while still compounding generic policy knowledge across all clients.

**Greenlight asks which mode you are on signup — one question, one click, and the system configures itself accordingly.** Company mode hides all client management fields. Consulting firm mode enables full client isolation and the shared library toggle.

Both types feel the same pain. The difference is who in the chain feels it most directly and who makes the buying decision.

---

## Australian Market Focus

Greenlight is built specifically for the Australian market. The primary competitors — Hypercomply and Conveyor — are US-focused tools that do not cover Australian compliance frameworks at all.

Australian GRC consultants and security teams regularly receive questionnaires built around:

- **ASD Essential Eight** — the Australian Signals Directorate's eight mitigation strategies, required by almost every Australian government agency and large enterprise
- **Australian Privacy Act 1988 / Australian Privacy Principles** — mandatory for any company handling Australian personal data; includes the Notifiable Data Breaches (NDB) scheme
- **APRA CPS 234** — APRA's information security prudential standard, mandatory for all banks, insurers, and superannuation funds regulated by APRA
- **ISO 27001** — global standard but widely adopted in Australia, especially in financial services and health

A consultant using a US tool starts from zero on every Essential Eight or Privacy Act questionnaire. A consultant using Greenlight starts with 45 pre-loaded Australian-specific Q&A pairs on day one — covering all four frameworks above — plus everything they've approved in past questionnaires compounding on top.

---

## Market Position — Inbound vs Outbound TPRM

Greenlight sits inside the Third-Party Risk Management (TPRM) market, driven by APRA CPS 230 (effective July 2025) which forces every bank and insurer to formally assess their vendors.

TPRM has two sides. **Inbound** — vendors answering questionnaires sent to them — is what Greenlight solves today. Tens of thousands of AU vendors face this problem, the pain is immediate, and no AU-native tool exists. **Outbound** — enterprises sending questionnaires and scoring vendor responses — is the natural future expansion, planned once inbound is proven with paying customers.

Inbound first: there are 5,000 vendors for every 1 bank, the sales cycle is days not months, and the product already exists.

---

## Full Product Walkthrough

### Step 1 — Set up the knowledge base

Before answering any questionnaires, the team uploads their company's security documentation:

- Security policies (access control, incident response, encryption, etc.)
- Compliance reports (SOC 2, ISO 27001, pen test results)
- Any internal documents that describe how the company handles security

The system processes each document and breaks it into searchable chunks. When a question comes in later, it finds the most relevant parts of these documents and uses them to draft an answer.

**For new customers with no documents yet:** the system's Answer Library is pre-loaded with 45 Australian GRC Q&A pairs covering the Essential Eight, Privacy Act, APRA CPS 234, and ISO 27001. These are real, well-written answers to the most commonly asked Australian security questions — so the system can start drafting useful answers from the very first questionnaire, even before any documents are uploaded.

---

### Step 2 — Upload a questionnaire

Greenlight accepts questionnaires in three formats: **Excel (.xlsx)**, **Word (.docx)**, and **PDF (.pdf)**.

**Excel questionnaires** use a two-step column picker:
1. **Preview** — the tool shows the first few rows of the file so the reviewer can see what's in each column
2. **Map columns** — the reviewer clicks to mark which column is the question, which is the Yes/No answer column, and optionally which is the evidence/explanation column

This works with any Excel layout — no template required. Hidden rows (common in complex enterprise Excel questionnaires) are automatically skipped.

**Word and PDF questionnaires** skip the column picker entirely — the system reads the document, identifies every question, and presents them for confirmation before import. The reviewer sees the full extracted question list and confirms with one click.

In consulting firm mode, the reviewer also enters the customer name (e.g. "Atlas Bank") at this step, which powers the client answer isolation described below. In company mode, this field does not appear.

---

### Step 3 — Draft answers

Once the questionnaire is set up, the reviewer clicks "Draft Answers." The system goes through every question and:

1. Searches the knowledge base for the most relevant policy chunks
2. Searches the answer library for previously approved answers to similar questions
3. Drafts a full answer (evidence/explanation)
4. Drafts a short Yes/No/Partial/N-A answer for questionnaires that have a separate column for it
5. Assigns a confidence score (High / Medium / Low) based on how closely the sources matched the question
6. Shows which specific policy documents or past answers it drew from

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
- **Comment** — leave a note for teammates on a specific question

A progress counter at the top shows how many questions are approved out of the total.

---

### Step 5 — Export

When the reviewer is ready, they click Export. The tool writes the approved answers back into the original Excel file layout — the customer's column structure is preserved. Unapproved, flagged, or edited-but-not-approved answers are never included.

The exported file is named with the questionnaire name and today's date, ready to send.

---

### What happens if a draft is wrong?

Nothing leaves without a human approving it. Every answer is explicitly marked as a draft until a reviewer reads it and signs off. The system is designed as a co-pilot, not an autopilot — the system does the research and writing, the human makes every final decision.

The audit log records exactly who approved which answer, when, and from which source documents. If a customer ever questions an answer, you have a full traceable record. If an answer is later found to be wrong, you reject it and re-draft — it takes seconds, and the system learns from the correction.

The confidence scoring is there precisely for this reason: Low-confidence answers are flagged so reviewers know where to spend their attention. You are never flying blind.

---

### What makes Greenlight different — the compounding answer library

Every answer a reviewer approves is automatically saved to a searchable library. When a similar question appears in a future questionnaire, the system surfaces the previously approved answer as a suggestion — already written, already reviewed, already trusted.

Unlike competitors that treat every questionnaire as a blank slate, Greenlight gets smarter with every one you complete. Your 10th questionnaire takes a fraction of the time your first did. Your institutional security knowledge stops living in someone's inbox and starts compounding into a permanent asset.

**Two-layer answer system — client isolation built in**

For GRC consulting firms managing multiple clients, answer isolation is critical. An answer written for Atlas Bank ("our RTO is 4 hours per our contract with Atlas Bank") must never be suggested when filling out a questionnaire for AusMed Health Systems. Getting this wrong is a professional liability.

Greenlight solves this with a two-layer answer system:

- **Generic answers** — answers with no client-specific content (e.g. "Yes, we use MFA across all systems") are saved as generic and reused across every client. They compound the fastest.
- **Client-specific answers** — answers that mention the client by name, reference specific contract terms, or contain client-specific details are saved against that client only and never shown for other clients.

The system auto-detects which category an answer falls into as the reviewer types. If the draft answer contains no client-specific signals — no client name, no specific cloud regions or IP addresses, no URLs, no headcounts — a pre-checked checkbox appears: *"Looks generic — save for all clients, not just Atlas Bank?"* The reviewer can accept or override. Answers can also be promoted to generic later from the Answer Library page.

This means a consulting firm's library splits naturally over time: generic knowledge (shared, fast-compounding) and per-client knowledge (isolated, accurate). Both compound. Neither contaminates the other.

---

### Other features

**Share link — read-only progress view**
From any questionnaire, the reviewer can generate a read-only link and share it with stakeholders (a manager, a client, a subject matter expert) so they can follow along without needing a Greenlight account. The link shows the questionnaire name, questions, drafted answers, and approval status — but gives no ability to edit or approve anything. Useful for getting sign-off from someone outside the team without giving them full system access.

**Answer version history**
Every time a draft answer is edited or approved, the previous version is automatically saved. Reviewers can open the version history on any question to see exactly what changed, when, and who made the change. Useful for audits, for understanding why an answer was revised, and for recovering a previous version if an edit went the wrong way.

**KB Health**
A diagnostic page that shows how well the knowledge base is performing — which questions had low-confidence matches, which topics have gaps, and where uploading more documentation would help. Documents not updated in 90+ days show an amber staleness warning, turning red at 180+ days.

**Answer Library**
A searchable library of all approved answers across every questionnaire. Shows which client each answer is tagged to, allows promoting a client-specific answer to generic, and displays answers that may be stale if the underlying policy was recently updated.

Archiving an answer from the library also removes it from the retrieval index — it will not surface in future answer generation. Rejecting a previously approved answer does the same: both the library entry and the retrieval chunk are cleaned up automatically, so bad answers never persist in the system.

**Trash and restore**
Deleted questionnaires and documents go to a trash bin rather than being permanently removed. Owners and admins can restore them. Nothing is lost by accident.

**Audit log**
Every action is logged — who uploaded what, who approved which answer, who exported, who assigned a question to whom, and when. Full trail for compliance purposes.

**Dashboard**
Overview of all questionnaires, total questions answered, approval rate, average confidence score, and estimated time saved.

**Team management**
Owners can invite team members by email. Three roles:
- **Owner** — full access, can manage billing and team
- **Admin** — can manage questionnaires, knowledge base, and team members
- **Member** — can review and approve answers on questionnaires assigned to them

---

### How long does it actually take?

Drafting speed is fixed and measurable — with a 6-second gap between questions (to stay within rate limits), a 200-question questionnaire takes roughly 20 minutes to draft. The human review time depends heavily on knowledge base maturity and questionnaire complexity.

**Realistic time estimates:**

| Scenario | Drafting | Human review | Total |
|---|---|---|---|
| Small check (6–20 questions) | 1–2 min | 5–15 min | **~15–20 min** |
| Medium questionnaire (50–100 questions) | 5–10 min | 30–60 min | **~1 hour** |
| Large enterprise questionnaire (200 questions), first time | 20 min | 3–5 hours | **~4–6 hours** |
| Large enterprise questionnaire (200 questions), populated KB | 20 min | 1–2 hours | **~1.5–3 hours** |
| Annual renewal of a familiar questionnaire | 20 min | 30–60 min | **~1 hour** |

**Why review time varies so much:**

Not all questions are equal. In a real enterprise questionnaire, roughly:
- ~60% are straightforward — high confidence, quick to read and approve (15–30 seconds each)
- ~30% need checking — medium confidence, reviewer needs to verify the source or tweak the wording (2–5 minutes each)
- ~10% need a subject matter expert — low confidence or no KB match, requires finding the right person or writing from scratch (10–30 minutes each)

The tool doesn't eliminate the hard questions. It eliminates the easy ones, which is still the majority of the work.

**How it compounds over time:**

The first questionnaire with an empty knowledge base is the slowest — every answer is low confidence and needs manual review. By the third or fourth questionnaire, the answer library has enough approved answers that familiar questions are pre-filled and the reviewer just confirms them. Annual renewals from the same client become close to a 30-minute job.

**vs. fully manual:**
A 200-question enterprise questionnaire done manually typically takes a GRC consultant 2–3 full working days. With Greenlight and a mature knowledge base, the same questionnaire takes 1.5–3 hours — roughly 5–10x faster depending on how well-stocked the knowledge base is.

---

### How Greenlight prevents hallucinations

Hallucination — where the system confidently states something false — is a serious risk in a compliance context. A hallucinated answer on a security questionnaire could misrepresent your security posture to a customer or regulator. Greenlight has five layers of defence against this:

**1. Grounded generation only**
The system is explicitly instructed to answer solely from the retrieved document chunks and approved answers provided to it. It is told not to invent facts, fill gaps from general knowledge, or assume capabilities that aren't evidenced in the source material. If the sources don't support a claim, the system is instructed to say so rather than guess.

**2. Every source shown to the reviewer**
Every drafted answer displays the exact document passages and previously approved answers it drew from, each with a relevance match score. The reviewer can read the source alongside the answer and immediately spot if the draft has stretched or misrepresented it.

**3. Confidence scoring flags weak matches**
When the knowledge base has little or nothing relevant to a question, the retrieval scores are low — and the system reflects this with a Low confidence badge. Low-confidence answers are visually flagged so reviewers know exactly where to focus their scrutiny, rather than treating every answer with the same level of trust.

**4. "No knowledge base context" hard warning**
If the retriever finds no relevant content at all, the question is marked with a red MANUAL badge and a warning: "No documents in your knowledge base matched this question." The reviewer is told explicitly that the system had nothing to work from and the answer must be written manually. The system never silently fabricates an answer to avoid looking uncertain.

**5. Human approval gate — nothing leaves without sign-off**
Every answer stays in draft state until a human reviewer reads it and explicitly approves it. There is no automated export, no batch-send, no way for an answer to reach a customer without a person signing off. The approval is logged with the reviewer's name and timestamp. This gate exists precisely because drafted output cannot be trusted unconditionally — the system is designed around that assumption.

---

## Security Features Built Into the Tool Itself

Since this is a security product, I want to be transparent about how the tool itself is secured:

**Accounts and authentication**
- Passwords require: 8+ characters, at least one uppercase letter, one number, and one symbol
- Passwords are stored using Argon2id hashing — the current industry standard recommended by OWASP
- Login sessions use secure, httponly cookies (tokens are not accessible to JavaScript, protecting against XSS attacks)
- Login is protected by three independent rate-limiting layers that together cover every known automated attack pattern:
  - **Per-IP request limit** — 10 attempts per minute per IP, blocking basic brute-force
  - **Per-email velocity lock** — 10 failures against the same email within 15 minutes triggers a lockout regardless of source IP, blocking credential stuffing (rotating IPs, same target account)
  - **Per-IP global spray block** — 20 total failures from the same IP across any accounts within 15 minutes triggers an IP block, stopping password spraying (same IP, rotating through many email addresses)
  - Every lockout event is written to the audit log with the attacking IP and the reason triggered
- Email verification required on signup
- Password reset via time-limited email token

**Data protection**
- Uploaded files (Excel questionnaires, policy documents) are stored in S3-compatible object storage — not in the database
- All data is scoped to the workspace at the database query level — every query is filtered by `workspace_id`, making cross-tenant data access structurally impossible without a deliberate application bypass
- For consulting firms managing multiple clients: all clients share one workspace but are isolated by `customer_name` at the answer retrieval level. The RAG pipeline SQL filters approved answers so that only generic answers and the current client's answers are ever retrieved — other clients' answers are structurally invisible, not just hidden in the UI
- Soft deletes only — data is never permanently destroyed without explicit action
- **Live document replacement with staleness tracking** — when a policy changes, admins can replace the file in-place rather than deleting and re-uploading. The system drops all old chunks, re-parses and re-embeds the new content immediately, and preserves the document's ID so the audit trail remains intact

**Answer safety**
- **Negation / trap-question detection** — security questionnaires sometimes use reverse-phrasing to catch dishonest vendors (e.g. "Are there any employees exempt from background checks?"). The system is explicitly instructed to detect this pattern and verify that its Yes/No answer reflects the company's secure, compliant posture — not accidentally admit a gap through a keyword match
- **Prompt injection defence** — every document uploaded to the knowledge base is sanitized before it is chunked and stored. Lines matching known injection patterns (system instruction overrides, "ignore previous instructions", model-specific tokens) are stripped and logged. At generation time, retrieved document chunks are wrapped in explicit data-only boundaries so the system is structurally prevented from treating document content as commands

**Application security**
- Security headers on every response: Content Security Policy, X-Frame-Options, Referrer-Policy, Permissions-Policy
- HTTPS-only mode with HSTS when deployed to production
- CORS restricted to the configured frontend domain only
- File uploads: Excel files only, 20MB maximum size limit
- All actions written to an immutable audit log

**Retrieval quality (RAG)**

The engine that finds the right policy content for each question uses a multi-layer pipeline:

- **Hybrid search** — every question is searched two ways simultaneously: semantic vector search (understands meaning) and full-text keyword search (catches exact compliance terms like "SOC 2 Type II" or "AES-256" that embedding search can miss). Results are merged using Reciprocal Rank Fusion
- **HyDE + query expansion** — before searching, the system generates a hypothetical answer and three rephrasings of the question, then searches across all five variants. This dramatically improves recall for verbosely-worded enterprise questionnaire questions
- **Source-aware ranking** — previously approved human-reviewed answers are ranked 35% higher than generic policy documents. The more questionnaires a team completes, the more retrieval is weighted toward their own trusted answers
- **Client-aware retrieval** — the retrieval SQL explicitly filters answer library chunks by client name. Generic answers and the current client's answers are retrieved; other clients' answers are excluded at the query level, not just filtered in application code
- **Feedback learning** — every time a reviewer approves an answer, the source chunks that contributed receive a positive signal. Every rejection or re-draft triggers a negative signal. Over time, chunks that consistently produce bad answers are automatically down-ranked for that organisation
- **Parent-child retrieval** — documents are stored at two levels: small child chunks (~150 tokens) for precise retrieval, and large parent chunks (~800 tokens) for rich drafting context. The system finds answers with the precision of a small chunk but sends the full surrounding section to the drafting engine — 5× more context per result
- **Semantic chunking** — documents are split at structural boundaries (headers, numbered sections, paragraph breaks) rather than arbitrary token counts, so a policy clause about encryption is never split mid-sentence across two chunks
- **Reranking** — after retrieval, a dedicated reranking model re-scores the top 20 candidates for true relevance before the final selection is used for drafting

**Team invites**
- Owners and admins generate a unique invite link from the Team page — there is no permanent "invite code"
- Each link is single-use (consumed the moment someone registers with it) and expires automatically after 48 hours
- Admins can revoke any active link at any time before it is used
- The invite token is never stored in the database — only its hash — so a database leak does not expose usable links

**Current limitations**
- **Single active sheet only** — the questionnaire uploader reads the first (active) sheet of an Excel file. Questionnaires spread across multiple tabs are not yet supported (on the roadmap)
- **Sequential generation per workspace** — answer generation runs one questionnaire at a time within a workspace. For a solo consultant this is invisible; for a busy team where multiple members click Generate simultaneously, jobs queue up. Future fix is a dedicated task queue to run them in parallel
- **No stale answer detection** — if you replace a policy document in the knowledge base, approved answers that were generated from the old version are not automatically flagged as potentially outdated. Reviewers must manually check the answer library after a major policy update
- **No deadline or SLA tracking** — questionnaires have no due date field. There is no built-in reminder if a questionnaire has been sitting in draft for too long
- **No compliance framework mapping** — questions cannot yet be tagged to specific controls (e.g. ISO 27001 Annex A, Essential Eight maturity levels). Mapping is manual

**Coming soon**
- MFA (authenticator app / TOTP) — opt-in per user, with org-level enforcement for admins
- Data retention / purge job — soft-deleted items auto-permanently removed after 90 days
- SSO / SAML — single sign-on via Google Workspace, Okta, Azure AD
- Multi-sheet Excel support — questionnaires that span multiple tabs in the same file
- @mention and notifications — tag a team member directly in a comment to notify them by email; useful for routing technical questions to the right person without leaving the platform
- Web portal integrations — OneTrust, Vanta, Whistic
- Australian data sovereignty — all customer data stored exclusively on AWS Sydney region (ap-southeast-2), meeting Australian privacy and data residency requirements out of the box
- Cloud document sync — connect Google Drive or SharePoint so Greenlight automatically detects when a source policy file is updated and prompts the team to re-embed it

**Long-term vision — outbound third-party risk management**

Greenlight v1 solves the inbound questionnaire problem: a company receives a security questionnaire and needs to answer it fast and accurately. This is the core product today.

The natural expansion is the outbound side — used by GRC analysts and consultants who send questionnaires to their own vendors and need to assess the responses:

- **Vendor portal** — send questionnaires directly to vendors from Greenlight; vendors log in and answer inside the platform rather than via email and Excel attachments
- **Automated response scoring** — score vendor responses for risk level (High / Medium / Low) based on their answers, with justification
- **Vendor risk register** — maintain a live register of all third-party vendors, their current risk ratings, assessment due dates, and outstanding gaps
- **Remediation tracking** — flag gaps in vendor answers and track whether they have been addressed before the next review cycle
- **Risk rating audit trail** — full record of who scored what, when, and why — defensible in an external audit

This would expand Greenlight from a questionnaire answering tool into a complete third-party cyber risk management platform, covering both sides of the vendor relationship. It is a significant build and sits beyond the current roadmap — but it is the natural direction once the inbound product is established with paying customers.
