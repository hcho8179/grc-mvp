# Additional Strategic Positioning

Sentinel GRC is a security memory and questionnaire workflow platform for growing B2B SaaS companies.

The platform is not intended to be just another autofill tool. The longer-term goal is to help organizations accumulate reusable institutional security knowledge over time through approved answers, review history, evidence linkage, stale-answer detection, and operational trust workflows.

The core problem is not only answering questionnaires faster, but reducing duplicated work, inconsistent responses, scattered knowledge, and operational bottlenecks during enterprise security reviews.


# Sentinel GRC — Brief

Hi! I'm building a B2B SaaS tool to help security teams respond to customer security questionnaires faster. I'd love your honest feedback as someone who does this work day-to-day.

---

## The Problem I'm Solving

When a vendor wants to sell to a large company, the company often sends a security questionnaire — sometimes 50, sometimes 300+ questions like:

- "Do you encrypt data at rest?"
- "Do you have a SOC 2 report?"
- "What is your password policy?"
- "Describe your incident response process."

Answering these is repetitive, slow, and usually falls on one person. The answers are almost always the same across questionnaires, just phrased differently each time.

---

## Who This Is For

There are two types of customers, both with the same problem approached differently.

**Type 1 — Companies with an internal security team**
Series B/C SaaS companies with a dedicated GRC analyst or security engineer in-house. They receive security questionnaires regularly — sometimes 5–10 per month — and the analyst is the bottleneck. They buy Sentinel directly and use it themselves. The CISO or GRC analyst is both the buyer and the day-to-day user.

**Type 2 — Companies with no internal security team**
Smaller companies (10–100 employees) with no dedicated security person. When a questionnaire arrives from a big prospect, they hire a GRC consulting firm to handle it on their behalf. The consulting firm uses Sentinel across all their clients — one tool, many client workspaces, each fully isolated. The consulting firm is the buyer; their clients are the beneficiaries.

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

The reviewer can also **bulk approve** all high-confidence answers at once to speed up the process.

A progress counter at the top shows how many questions are approved out of the total.

---

### Step 5 — Export

When the reviewer is ready, they click Export. The tool writes the approved answers back into the original Excel file layout — the customer's column structure is preserved. Unapproved, flagged, or edited-but-not-approved answers are never included.

The exported file is named with the questionnaire name and today's date, ready to send.

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

**Answer library**
Every answer that gets approved is automatically saved to a searchable library. When a similar question appears in a future questionnaire, the system surfaces the previously approved answer as a suggestion — with a match score showing how closely it fits. Each entry tracks how many times it has been reused. Answers are grouped by category (access control, encryption, incident response, etc.) and are searchable by keyword. The library compounds over time: the more questionnaires the team completes, the faster future ones go.

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
- All data is scoped to the organisation — no data from one customer is ever visible to another
- Soft deletes only — data is never permanently destroyed without explicit action

**Application security**
- Security headers on every response: Content Security Policy, X-Frame-Options, Referrer-Policy, Permissions-Policy
- HTTPS-only mode with HSTS when deployed to production
- CORS restricted to the configured frontend domain only
- File uploads: Excel files only, 20MB maximum size limit
- All actions written to an immutable audit log

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
- Email notifications — alerts when a question is assigned to you, when a questionnaire is ready for review
- SSO / SAML — single sign-on via Google Workspace, Okta, Azure AD
- Org-level admin settings — force MFA for all members, configure data retention period
- Answer version history — full edit trail showing who changed an answer and what it said before
- Answer source traceability — each approved answer remembers which questionnaire and customer it originally came from, so reviewers can trace provenance even after the questionnaire is archived
- Archive / remove answer from library — let reviewers manually archive or delete a specific answer from the Answer Library without having to delete the whole questionnaire
- Multi-sheet Excel support — questionnaires that span multiple tabs in the same file
- Word and PDF questionnaire upload — not just Excel files
- Web portal integrations — OneTrust, Vanta, Whistic (for customers who share a portal link instead of a file)
- Common framework templates — pre-built questionnaire templates for CAIQ, SIG Lite, VSA so teams can start without waiting for a customer to send one

---

## What I'd Love Your Feedback On

### 1. Workflow — does this match reality?
In your experience, how does the questionnaire response process actually work? Is it one person doing everything, or is it spread across a team? Does my approve/reject/assign flow make sense for how teams actually operate?

### 2. The knowledge base idea
The system drafts answers by reading uploaded policy documents. In practice, are company policies usually in a state where this would work? Or are they often outdated, scattered, or inconsistent? How big a problem is "the policy says X but we actually do Y"?

### 3. Confidence and flagging
When the system isn't sure about an answer (low confidence), it flags it for manual review. Is that the right signal to surface? What other signals would be useful — e.g. "this question references a regulation I don't recognise", or "this answer contradicts something in another questionnaire"?

### 4. Questionnaire formats
Are most questionnaires Excel files? Do you see Word documents, PDFs, or web-based portals (like OneTrust, Vanta, Whistic) often? Should I be prioritising any of those formats?

### 5. Who is the buyer?
In your experience, who owns the questionnaire response process — the CISO, a GRC analyst, a sales engineer? Who would buy a tool like this and who would use it day-to-day? Are those the same person?

### 6. What's missing?
Is there anything obviously missing that would make this not worth using? Any part of the workflow that feels wrong or unrealistic?

### 7. Pricing gut-check
I'm thinking of charging per questionnaire or per seat per month. Which model makes more sense for how security teams actually budget for tools like this?

---

