# Sentinel GRC — Advisor Brief

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

## What My Tool Does

1. **Upload** — The security team uploads the questionnaire as an Excel file.
2. **Draft** — The system reads the company's own security policies and documentation, then drafts answers to each question automatically.
3. **Review** — A human reviewer reads each drafted answer, edits if needed, then approves or flags it.
4. **Export** — The completed questionnaire is exported back as an Excel file, ready to send to the customer.

Unapproved answers are never included in the export — a human always has the final say.

---

## Current Features

- Upload questionnaires in Excel format (any column layout)
- Separate columns for Yes/No answer and a longer evidence/explanation answer
- Assign individual questions to specific team members (e.g. "this network question → assign to infra engineer")
- Soft delete with a trash/restore system — nothing is permanently lost by accident
- Audit log of every action (who approved what, when)
- Knowledge base — upload your SOC 2 report, ISO policies, internal docs; the system uses these to draft answers
- Starter policy templates included so new customers can get started immediately

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

## What I Am Not Looking For

- Technical feedback (the code, the AI, the infrastructure)
- Design feedback

I just want to know: **does this solve a real problem, and does the workflow make sense to someone who actually does this work?**

---

Thanks so much for taking the time — your perspective as a working GRC analyst is exactly what I need at this stage.
