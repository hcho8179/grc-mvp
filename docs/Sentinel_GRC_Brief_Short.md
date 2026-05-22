# Sentinel GRC — Brief

Hi! I'm building a tool to help security teams respond to customer security questionnaires faster. I'd love your honest feedback — this should take about 5 minutes.

---

## The Problem

When a vendor wants to sell to a large company, the company sends a security questionnaire — sometimes 50, sometimes 300+ questions. Answering them is slow, repetitive, and usually falls on one person. The answers are almost always the same across questionnaires, just phrased differently each time.

---

## Who It's For

**Security teams at Series B/C SaaS companies** — a GRC analyst or security engineer who receives questionnaires regularly and is the bottleneck. They buy Sentinel and use it themselves.

**GRC consulting firms** — firms that handle questionnaires on behalf of smaller clients who have no in-house security team. One tool, many fully-isolated client workspaces. The firm buys; their clients benefit.

---

## How It Works

1. **Upload your policies** — security policies, SOC 2 reports, pen test results. The system breaks them into searchable chunks. New customers get 20 starter templates to begin immediately.
2. **Upload the questionnaire** — any Excel layout. A two-step column picker maps which column is the question, which is the Yes/No answer, which is the explanation.
3. **Draft answers** — the system searches your knowledge base and drafts a full answer plus a Yes/No/Partial short answer for every question. Usually 1–3 minutes for a full questionnaire.
4. **Review** — a human goes through each draft. They can edit, approve, reject, re-draft, assign to a teammate, or comment. Low-confidence answers are flagged with a plain-English explanation of why.
5. **Export** — approved answers are written back into the customer's original Excel layout, ready to send. Nothing unapproved is ever included.

---

## Key Features

- **Answer library** — every approved answer is saved and reused. When a similar question appears in a future questionnaire, the previously approved answer surfaces as a suggestion. Gets faster over time.
- **Answer consistency check** — flags when a new draft contradicts a previously approved answer to the same question.
- **Assign & comment** — send specific questions to the right teammate (e.g. network question → infra engineer). Leave notes per question.
- **Audit log** — every action logged: who approved what, who exported, who assigned to whom, and when.
- **Share progress link** — a read-only public URL showing real-time approval progress, for deal stakeholders who need visibility without accessing the tool.
- **Edit history** — full trail of every edit, approval, and rejection per question, with who made the change and when.
- **Knowledge base health** — shows which topics have coverage gaps and where uploading more documentation would improve answer quality.

---

## What I'd Love Your Feedback On

**1. Workflow** — does the approve/reject/assign flow match how your team actually operates? Is it one person or spread across multiple people?

**2. Knowledge base** — in practice, are company policies usually in a state where this would work? How common is "the policy says X but we actually do Y"?

**3. Low confidence** — when the system isn't sure about an answer, it flags it with an explanation. Is that the right signal? What else would be useful?

**4. Questionnaire formats** — are most questionnaires Excel files, or do you see Word, PDF, or web portals (OneTrust, Vanta, Whistic) often?

**5. Buyer vs. user** — who owns the questionnaire process at your company — CISO, GRC analyst, sales engineer? Who would buy this and who would use it day-to-day?

**6. What's missing** — is there anything obviously absent that would make this not worth using?

**7. Pricing** — per questionnaire or per seat per month? Which model fits how security teams actually budget?
