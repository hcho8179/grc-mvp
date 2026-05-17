# GRC MVP — Future Phases (6-10)

**Status:** Phases 1-5 complete. Phases 6-10 are roadmap for post-MVP validation and expansion.

---

## Phase 6 — Customer Validation & Feedback (PLAN)

**Objective:** Validate product-market fit. Talk to 10 GRC/compliance managers.

**What to Do:**
1. Find 10 security/compliance managers at 50-200 person SaaS companies
   - LinkedIn: search "compliance manager" or "GRC analyst" + filter by company size + industry
   - Reddit: r/grcacademy, r/cybersecurity
   - Cold DM: "Built a tool that auto-fills security questionnaires. Not selling — just want feedback. 10 min call?"

2. Demo script (15 minutes):
   - **Intro (2 min):** "I built a tool that takes your policies + generates questionnaire answers"
   - **Demo (5 min):** Show knowledge upload → questionnaire parse → answer generation → export
   - **Questions (8 min):**
     - "Would you use this? Why / why not?"
     - "How much time would this save you per questionnaire?"
     - "What's missing? What would make you pay for this?"
     - "When does this need to be done?" (timeline / urgency)
     - "Who else would need to approve the answers?" (multi-user need?)
     - "What's your current workflow? How broken is it?"
     - "Would you pay $300-500/month? $1000/month?"

3. Collect feedback:
   - Document exact quotes (not paraphrases)
   - Note: "5/10 said approval workflow is critical" vs "2/10 mentioned it"
   - Identify patterns: What do 70%+ mention?

**Success Criteria:**
- ✅ 5+ customers say "yes, I would pay for this"
- ✅ 70%+ mention same problem/feature gap
- ✅ Clear pricing signal (would they pay $400/month? $800/month?)

**Output:**
- Customer feedback doc: `docs/customer-feedback.md` with quotes + summary
- Decision: Is there market demand? Continue to Phase 7 or pivot?

**Timeline:** 2-3 weeks (1-2 calls per week, casual)

---

## Phase 7 — Trust & Audit Layer (OPTIONAL, IF CUSTOMER DEMAND)

**Objective:** Add enterprise trust features. Production-grade for real teams.

**What to Build:**

### 7a. User Auth + Roles
```
- Simple auth: email/password (no OAuth for MVP)
- Roles: viewer, analyst, manager, admin
- Permissions:
  * viewer: see questionnaires, read answers
  * analyst: can generate + edit answers
  * manager: can approve/reject answers
  * admin: can manage users + templates
```

**Implementation:**
- SQLAlchemy: User table with hashed password (use `argon2`)
- FastAPI: `Depends(get_current_user)` on protected routes
- Templates: Conditionally show "Approve" button only if role == manager
- No OAuth for MVP (add later if customers demand it)

**Database change:**
```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL,  -- viewer, analyst, manager, admin
  created_at TIMESTAMP DEFAULT now()
);

ALTER TABLE questions ADD COLUMN analyst_id INT REFERENCES users(id);
ALTER TABLE questions ADD COLUMN manager_id INT REFERENCES users(id);
ALTER TABLE questions ADD COLUMN approved_at TIMESTAMP;
```

### 7b. Approval Workflow
```
State machine: draft → pending_analyst_review → pending_manager_review → approved

UI shows:
- Current status badge (with color)
- "This answer is waiting for [person name]'s review"
- Only manager can click "Approve"
- Analyst can suggest changes in comments
```

**Implementation:**
- Add `status` enum: draft, pending_analyst, pending_manager, approved, rejected
- Routes:
  * POST /questions/{id}/submit_for_review (analyst → manager)
  * POST /questions/{id}/approve (manager only)
  * POST /questions/{id}/request_changes (manager → analyst)
  * GET /questions/{id}/history (show all state transitions)

### 7c. Audit Trail
```
Every change logged: who, what, when, why

Audit table:
- user_id (who made the change)
- resource_type (question, document, approval)
- resource_id
- action (created, edited, approved, rejected)
- old_value / new_value (for edits)
- timestamp
- reason / comment
```

**Implementation:**
```python
# In services/audit.py
async def log_audit(
    user_id: int,
    resource_type: str,
    resource_id: int,
    action: str,
    old_value: str = None,
    new_value: str = None,
    reason: str = None
):
    audit_entry = AuditLog(
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        old_value=old_value,
        new_value=new_value,
        reason=reason,
        timestamp=datetime.utcnow()
    )
    session.add(audit_entry)
    await session.commit()

# Use in routes:
# POST /questions/{id}/approve
await log_audit(current_user.id, "question", id, "approved", reason=request.reason)
```

### 7d. Citation Display
```
UI shows: "Answer based on 3 sources"
Click → reveals:
- Chunk 1: "We maintain SOC 2 Type II certification..." (from policy_encryption.pdf)
- Chunk 5: "Audited annually by..." (from audit_policy.pdf)
With relevance scores: [0.92, 0.87, 0.76]
```

**Implementation:**
- GET /questions/{id}/sources → return chunks + relevance scores
- Template: render citations in modal or sidebar
- Add `source_relevance` column to track how confident retrieval was

**Timeline:** 3-4 weeks  
**Difficulty:** Medium (auth is easy, workflow UI is moderate)  
**Payoff:** High (enterprise will trust it more)

---

## Phase 8 — Excel Engineering & Templates (OPTIONAL, IF CUSTOMER DEMAND)

**Objective:** Handle Excel complexity. Make exports look professional.

**What to Build:**

### 8a. Format Preservation
```
Currently: export loses formatting (colors, merged cells, formulas)
Goal: export looks like input
```

**Implementation:**
- Detect input format: scan for merged cells, formulas, conditional formatting
- Store format metadata in database:
  ```
  questionnaire_templates table:
  - id, name, format_config (JSON)
  - format_config = {
      "merged_cells": [[1,2],[3,4]],
      "colors": {"A1": "rgb(255,0,0)", ...},
      "formulas": {"B5": "=SUM(B1:B4)", ...},
      "column_widths": {"A": 25, "B": 40, ...}
    }
  ```
- On export: apply saved format to new worksheet

### 8b. Template System
```
Acme Corp uses SIG Lite format: Questions in A, Answers in B, Comments in C
Apex Inc uses different format: Questions in A, Answers in B-D (multi-column)

System remembers both. When exporting for Apex, auto-format to their layout.
```

**Implementation:**
- QuestionnaireTemplate model: stores format + layout
- On first export: "Save this format as [name]?"
- On subsequent exports: "Use saved format? (yes/no)"
- Auto-detection: "This looks like SIG Lite. Use that template? (yes/no)"

### 8c. Merged Cells Handling
```
Input Excel:
  A1:C1 = "Data Security"
  A2 = "Question"
  B2 = "Answer"
  
Output Excel: preserve the merged cell layout
```

**Implementation:**
```python
# Using openpyxl
input_ws = input_wb.active
merged_ranges = list(input_ws.merged_cells.ranges)  # [(A1:C1), ...]
output_ws.merge_cells(str(merged_ranges[0]))

# Copy formatting
for merged_range in merged_ranges:
    source_cell = input_ws[merged_range.coord]
    output_ws[merged_range.coord].fill = source_cell.fill
    output_ws[merged_range.coord].font = source_cell.font
    output_ws[merged_range.coord].alignment = source_cell.alignment
```

### 8d. Formula Preservation
```
If input has formulas (e.g., =SUM(answers)), preserve them in output
```

**Implementation:**
- Detect formulas in input: `cell.data_type == 'f'`
- Store formula text: `cell.value` (contains the formula string)
- On output: re-insert formula (but note: cell references may shift)

**Timeline:** 2-3 weeks  
**Difficulty:** Medium-high (Excel quirks are tricky)  
**Payoff:** Very high (prevents customer complaints about "export looks wrong")

---

## Phase 9 — Continuous Compliance (OPTIONAL, IF CUSTOMER DEMAND)

**Objective:** Track policy changes, flag stale answers, auto-update.

**What to Build:**

### 9a. Policy Versioning
```
When a company uploads a new version of their security policy, mark it as a new version.
Track: which answers were based on which policy version?

questions table: add policy_version_ids = [1, 5, 12]  (policy chunks used)
```

**Implementation:**
```python
# When uploading policy
new_doc = Document(filename="security_policy_v2.pdf", version=2)
await db.add(new_doc)

# On retrieval, track which version was used
answer = Answer(
    question_id=id,
    draft_answer="...",
    cited_policy_versions=[1, 5, 12],  # versions, not just chunks
    generated_at=datetime.utcnow()
)
```

### 9b. Change Detection
```
Policy updated from v1 to v2.
Compare: what sections changed?
Flag answers that cite the old sections.
```

**Implementation:**
```python
# In services/compliance.py
async def detect_policy_changes(old_doc_id, new_doc_id):
    old_chunks = await get_chunks(old_doc_id)
    new_chunks = await get_chunks(new_doc_id)
    
    # Semantic similarity: which old chunks are "close to" new chunks?
    changes = []
    for old_chunk in old_chunks:
        best_match = await find_similar_chunk(old_chunk, new_chunks)
        if best_match.similarity < 0.85:  # significant change
            changes.append({
                "old": old_chunk.id,
                "new": best_match.id if best_match else None,
                "severity": "high" if best_match is None else "medium"
            })
    
    return changes

# When changes detected, flag affected answers
affected_questions = await db.query(Question).filter(
    Question.cited_policy_versions.contains(old_doc_id)
).all()

for q in affected_questions:
    q.status = "pending_compliance_review"
    q.compliance_flag = "Policy section updated"
    await db.commit()
```

### 9c. Auto-Update Suggestions
```
"Your answer to 'Do you encrypt data?' may need updating. 
Policy changed from 'AES-128' to 'AES-256'.
Current answer: 'Yes, using AES-128 at rest.'
Suggested update: 'Yes, using AES-256 at rest.'
Approve this change? [Yes] [No] [Review]"
```

**Implementation:**
- Batch job: on policy upload, find affected questions
- For each, call LLM: "Given old policy section X and new policy section Y, how should this answer change?"
- Present suggestions to manager for approval

**Timeline:** 2-3 weeks  
**Difficulty:** Medium (LLM call + batch processing)  
**Payoff:** High (prevents answers becoming outdated)

---

## Phase 10 — Semantic Cross-Questionnaire Intelligence (OPTIONAL, IF CUSTOMER DEMAND)

**Objective:** Answer "SIG Lite Q7 and ISO 27001 Q15 are asking the same thing."

**What to Build:**

### 10a. Question Similarity Matching
```
When uploading a new questionnaire, compare each question to historical questions.
"This question is 92% similar to your SIG Lite Q8 from 6 months ago.
Reuse the answer? [Yes, with edits] [No, regenerate] [Review both]"
```

**Implementation:**
```python
# On questionnaire upload
new_questions = parse_questionnaire(file)

for q in new_questions:
    # Embed the question
    embedding = await embeddings.embed(q.text)
    
    # Find similar historical questions
    similar = await db.query(Question).order_by(
        func.cosine_distance(Question.embedding, embedding)
    ).limit(5)
    
    for match in similar:
        similarity_score = cosine_similarity(embedding, match.embedding)
        if similarity_score > 0.80:  # high similarity
            # Suggest reusing the answer
            q.suggested_answer_id = match.id
            q.suggestion_confidence = similarity_score
```

### 10b. Knowledge Graph
```
Visual showing: which policies connect to which questions?
Which questions have approved answers?
Where are the gaps?

Example:
├─ Data Encryption Policy
│  ├─ SIG Q7 (answered, confident)
│  ├─ ISO Q15 (answered, low confidence)
│  └─ SOC2 Q3 (not answered)
├─ Access Control Policy
│  ├─ SIG Q12 (answered)
│  └─ ISO Q20 (answered)
```

**Implementation:**
- Dashboard page: `/knowledge-graph`
- Data: query questions + documents + answers, build node-link diagram
- Visualization: D3.js or Cytoscape.js

### 10c. Answer Reuse Workflow
```
User clicks "Reuse answer from SIG Q8?"
System shows:
- Original answer (from 6 months ago)
- Original policy chunks it was based on
- Updated policy chunks (if policy changed)
- Suggested edits (via LLM)
- Confidence score

User can: approve as-is, approve with edits, regenerate from scratch
```

**Implementation:**
- New route: POST /questions/{id}/suggest-answer-reuse
- Returns: old_answer, new_policy_chunks, suggested_edits, similarity_score
- UI: side-by-side comparison + approval buttons

**Timeline:** 2-3 weeks  
**Difficulty:** Medium (embeddings + graph visualization)  
**Payoff:** High (dramatically faster for customers with many questionnaires)

---

## Phase 11+ — Expansion (OPTIONAL)

### Potential Directions
- **CMDB Integration:** Pull actual security controls from your CMDB, use as knowledge
- **Vulnerability Integration:** Link CVEs to questionnaire answers ("we patched CVE-2024-1234")
- **Multi-tenant:** Support multiple companies in one instance (with isolation)
- **API:** Let customers query answers programmatically
- **Mobile App:** Review + approve answers on phone
- **Integrations:** Slack notifications, Teams, email digest
- **Analytics:** "You've saved X hours, spent Y dollars on LLM, had Z% answer approval rate"

---

## Prioritization (If Customer Demand Exists)

Based on **customer feedback**, prioritize in this order:

1. **Phase 6:** Do this regardless. Customer validation is free information.
2. **Phase 7:** If 5+ customers say "need approval workflow + audit trail for compliance"
3. **Phase 8:** If 5+ customers say "Excel export formatting is broken"
4. **Phase 9:** If customers mention "answers go stale" or "policy updates break things"
5. **Phase 10:** If customers fill 3+ different questionnaires and see repetition

**Don't do any of phases 7-10 without customer validation first.**

---

## Using This Roadmap

### In Claude Code (Later)
When you're ready to build Phase 7, paste this into Claude Code:

```
I'm ready to build Phase 7 (Trust & Audit Layer).

Current state:
- Phases 1-5 complete
- 10 customers validated product-market fit
- Key feedback: need approval workflow + audit trail

Phase 7 scope:
[Paste the 7a-7d section above]

Build it end-to-end: user auth, approval workflow, audit logging, citation display.

Start with 7a (auth), then 7b (workflow), then 7c (audit), then 7d (citations).
Each part should be tested before moving to the next.
```

### In README
Add this section to `docs/README.md`:

```markdown
## Roadmap

**Current Status:** MVP complete (Phases 1-5). Ready for Phase 6 (customer validation).

### Phase 6 — Customer Validation
Validate product-market fit with 10 GRC managers.
**Timeline:** 2-3 weeks  
**Success criteria:** 5+ customers say "yes, I'd use this"

### Future Phases (7-10)
Phases 7-10 are planned based on customer feedback from Phase 6.

See `docs/roadmap.md` for detailed scope of each phase.
```

---

## Questions for Your First Phase 7 Claude Code Prompt

When you come back to this:

1. "What's the first thing I should build in Phase 7?"
   → Answer: User auth (7a). Everything else depends on knowing "who is making this change?"

2. "How do I test approval workflow?"
   → Answer: Create 2 test users (analyst, manager), manually trigger state changes, verify DB updates correctly

3. "Should I add notifications?"
   → Answer: Not for MVP. Add in Phase 7.5 if customers ask.

4. "Multi-tenant in Phase 7?"
   → Answer: No. Start with single-tenant (one company per deployment). Phase 11+ if you get traction.

---

**Good luck. You built something real. Now validate it with customers.** 🚀
