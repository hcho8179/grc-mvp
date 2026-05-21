# GRC MVP — Updated Roadmap (Organizational Memory System Route)

**Status:** Phases 1-5 complete. Transitioning to organizational memory system (Phases 6-11).

---

## Phase 6 — Customer Validation & Organizational Memory Signals

**Objective:** Validate product-market fit AND validate that organizational memory/answer reuse is a real, valued problem.

### What to Do

#### Find 10 Security/Compliance Managers
- LinkedIn: search "compliance manager" or "GRC analyst" or "security operations" + filter by company size (50-200 person SaaS)
- Reddit: r/grcacademy, r/cybersecurity
- Your tutor's network: ask for 3-5 intros to GRC contacts
- Cold DM: "Built a tool that manages security questionnaires and builds organizational knowledge. Not selling — just want feedback. 15 min call?"

#### Demo Script (20 minutes)

**Intro (2 min):**
"I built a system that ingests your policies and helps you manage security questionnaires. More importantly, it learns from your answers and reuses them across multiple questionnaires while flagging when answers become outdated."

**Demo (5 min):**
- Show knowledge base ingestion (policies → parsed)
- Show questionnaire generation
- Show answer library (previous approved answers)
- Show answer reuse suggestion
- Show export

**Discovery Questions (13 min):**

*Validation of problem:*
- "How many security questionnaires does your company receive per year?"
- "How much time does your team spend on them?"
- "What's the biggest pain: speed, consistency, compliance, or knowledge loss?"

*Validation of organizational memory:*
- "How often do you answer the same question for different customers?"
- "When a policy changes, do you review your previous questionnaire answers?"
- "Do you ever answer the same question differently in different questionnaires? Why?"
- "If you could build a library of approved answers and reuse them, would that help?"
- "What would happen if someone left your team? Would you lose security knowledge?"

*Pricing and adoption:*
- "Would you use this for multiple questionnaires per quarter?"
- "What would make this worth paying for: speed, consistency, or knowledge preservation?"
- "Would you pay $300-500/month? $1000/month? $2000/month?"
- "Who else would need to approve answers? (multi-user approval workflow critical?)"

*Competitive validation:*
- "Do you use Vanta, Drata, or another GRC tool?"
- "What's missing from those tools?"
- "Would organizational memory + answer reuse be a reason to switch?"

#### Collect Feedback

Document in `docs/customer-feedback.md`:
- **Exact quotes** (not paraphrases)
- **Patterns:** "8/10 mentioned answer repetition" vs "3/10 mentioned it"
- **Critical signals:**
  - How many questionnaires/year?
  - Do they value answer reuse?
  - Do they struggle with stale answers?
  - Willingness to pay?
- **ICP signal:** Which vertical (devtools, fintech, cybersecurity startups, AI SaaS) mentioned most pain?

### Success Criteria

- ✅ 5+ customers say "yes, I would pay for this"
- ✅ **7+ mention repetition across questionnaires**
- ✅ **6+ mention answer consistency/reuse as valuable**
- ✅ **5+ struggle with policy changes making answers stale**
- ✅ **Clear pricing signal: would they pay for answer library + stale-answer detection?**
- ✅ **Clear ICP signal: which vertical has most acute pain?**

### Output

- `docs/customer-feedback.md`: quotes + summary
- **Decision:** Is organizational memory a real value driver? Continue to Phase 7 or pivot?

### Timeline

2-3 weeks (1-2 calls per week, casual)

---

## Phase 7 — Answer Library & Answer Reuse Workflow (CORE MOAT)

**Objective:** Build the foundation of organizational memory. Answers persist, accumulate, and are reusable.

**Why Phase 7:** This is where the moat is built. Competitors can copy questionnaire autofill in weeks. They can't replicate accumulated organizational knowledge.

### What to Build

#### 7a. Persistent Answer Library

Store approved answers permanently. Link them to policies, questions, and categories.

**Database Schema:**

```sql
CREATE TABLE approved_answers (
  id SERIAL PRIMARY KEY,
  company_id INT REFERENCES companies(id),
  
  -- The answer itself
  question_text TEXT NOT NULL,
  answer_text TEXT NOT NULL,
  answer_category VARCHAR(100),  -- "data-encryption", "access-control", "audit-logging", etc.
  
  -- Linkage to source policies
  cited_policy_ids INT[],  -- which policy documents this answer references
  
  -- Metadata
  created_at TIMESTAMP DEFAULT now(),
  created_by INT REFERENCES users(id),
  approved_by INT REFERENCES users(id),
  approved_at TIMESTAMP,
  is_reusable BOOLEAN DEFAULT true,  -- user can mark as "internal only" if needed
  confidence_score FLOAT,  -- how confident in this answer (0-1)
  times_reused INT DEFAULT 0,  -- track usage
  last_reviewed_at TIMESTAMP,
  status VARCHAR(50) DEFAULT 'active',  -- "active", "stale", "archived"
  
  UNIQUE(company_id, question_text)  -- prevent duplicate answers to same question
);

CREATE TABLE answer_reuse_history (
  id SERIAL PRIMARY KEY,
  source_answer_id INT REFERENCES approved_answers(id),
  questionnaire_id INT REFERENCES questionnaires(id),
  reused_by INT REFERENCES users(id),
  reused_at TIMESTAMP,
  was_customized BOOLEAN DEFAULT false,
  custom_text TEXT,  -- if customized, store the custom version
  
  UNIQUE(source_answer_id, questionnaire_id)
);
```

**Implementation:**

```python
# routes/answers.py

# When user approves an answer, save it to library
@router.post("/questions/{question_id}/approve-and-add-to-library")
async def approve_and_library(question_id: int, request: ApproveRequest, current_user = Depends(get_current_user)):
    question = await db.get(Question, question_id)
    
    approved_answer = ApprovedAnswer(
        company_id=current_user.company_id,
        question_text=question.text,
        answer_text=request.answer_text,
        answer_category=request.category,  # e.g., "data-encryption"
        cited_policy_ids=request.policy_ids,
        created_by=current_user.id,
        approved_by=current_user.id,
        approved_at=datetime.utcnow(),
        is_reusable=request.is_reusable,
        confidence_score=request.confidence
    )
    
    await db.add(approved_answer)
    await db.commit()
    
    return {"message": "Answer approved and added to library", "answer_id": approved_answer.id}

# Browse answer library
@router.get("/answers/library")
async def get_answer_library(category: str = None, current_user = Depends(get_current_user)):
    query = db.query(ApprovedAnswer).filter(
        ApprovedAnswer.company_id == current_user.company_id,
        ApprovedAnswer.is_reusable == True,
        ApprovedAnswer.status == 'active'
    )
    
    if category:
        query = query.filter(ApprovedAnswer.answer_category == category)
    
    answers = await query.all()
    return {
        "total": len(answers),
        "by_category": group_by_category(answers),
        "answers": answers
    }

# Search answer library
@router.get("/answers/search")
async def search_answers(q: str, current_user = Depends(get_current_user)):
    # Full-text search on question_text and answer_text
    answers = await db.query(ApprovedAnswer).filter(
        ApprovedAnswer.company_id == current_user.company_id,
        or_(
            ApprovedAnswer.question_text.icontains(q),
            ApprovedAnswer.answer_text.icontains(q)
        )
    ).all()
    return answers
```

**UI:**
- After approving an answer: "Add this to your answer library? [Yes] [No]"
- New page: `/answers/library` - browsable, searchable library of all approved answers
- Show per answer: question, answer text, category, times reused, last reviewed date
- Filter by category (Data Encryption, Access Control, Audit Logging, etc.)

#### 7b. Answer Reuse Workflow

When filling a new questionnaire, system suggests previous answers.

**Implementation:**

```python
# routes/questionnaires.py

# When user is filling question in new questionnaire
@router.get("/questions/{question_id}/suggest-reuse")
async def suggest_answer_reuse(question_id: int, current_user = Depends(get_current_user)):
    question = await db.get(Question, question_id)
    
    # Find similar approved answers using semantic similarity
    # (you already have embeddings from RAG)
    question_embedding = await embeddings.embed(question.text)
    
    similar_answers = await db.query(ApprovedAnswer).filter(
        ApprovedAnswer.company_id == current_user.company_id,
        ApprovedAnswer.status == 'active'
    ).all()
    
    scored_answers = []
    for answer in similar_answers:
        answer_embedding = await embeddings.embed(answer.question_text)
        similarity = cosine_similarity(question_embedding, answer_embedding)
        if similarity > 0.75:  # high similarity threshold
            scored_answers.append({
                "answer_id": answer.id,
                "question_text": answer.question_text,
                "answer_text": answer.answer_text,
                "similarity": similarity,
                "times_reused": answer.times_reused,
                "last_reviewed": answer.last_reviewed_at
            })
    
    return sorted(scored_answers, key=lambda x: x['similarity'], reverse=True)[:3]

# User chooses to reuse an answer
@router.post("/questions/{question_id}/reuse-answer")
async def reuse_answer(question_id: int, request: ReuseRequest, current_user = Depends(get_current_user)):
    question = await db.get(Question, question_id)
    approved_answer = await db.get(ApprovedAnswer, request.answer_id)
    
    # Update question with reused answer
    question.answer_text = request.answer_text  # user may have customized it
    question.status = 'draft_from_reuse'
    
    # Log reuse
    reuse_log = AnswerReuseHistory(
        source_answer_id=approved_answer.id,
        questionnaire_id=question.questionnaire_id,
        reused_by=current_user.id,
        reused_at=datetime.utcnow(),
        was_customized=request.was_customized,
        custom_text=request.answer_text if request.was_customized else None
    )
    
    # Increment reuse counter
    approved_answer.times_reused += 1
    
    await db.add(reuse_log)
    await db.commit()
    
    return {"message": "Answer reused", "question_id": question_id}
```

**UI:**
When filling questionnaire #2:
```
Question: "Do you encrypt data in transit?"

Suggested answers from your library:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SIG Lite Q7 (answered 6 months ago) — 95% similar
"Yes, we encrypt all data in transit using TLS 1.2 or higher."
[Reuse] [Customize] [Regenerate] [Ignore]

ISO 27001 Q15 (answered 3 months ago) — 91% similar
"Yes, TLS 1.2+ for all customer data in transit."
[Reuse] [Customize] [Regenerate] [Ignore]
```

#### 7c. Answer Library Dashboard

Make organizational memory **visible and tangible**.

**UI: `/answers/dashboard`**

```
Your Security Answer Library
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Approved Answers: 47
Last Updated: 2 days ago
Total Reuses: 156

By Category:
  📋 Data Encryption (12 answers, 56 reuses)
  🔐 Access Control (8 answers, 34 reuses)
  🔍 Audit & Logging (10 answers, 42 reuses)
  🛡️ Incident Response (6 answers, 15 reuses)
  📅 Other (11 answers, 9 reuses)

Your Most Reused Answers:
  1. "Do you encrypt data at rest?" — 12 reuses
  2. "Do you have MFA?" — 11 reuses
  3. "What is your backup frequency?" — 8 reuses

Knowledge Building Stats:
  Questions answered: 47
  Questionnaires filled: 8
  Average answers per questionnaire: 5.9
  Answer library coverage: 78%
  (When you fill your next questionnaire, ~78% of questions will have library suggestions)
```

**Implementation:**

```python
@router.get("/answers/dashboard")
async def get_dashboard(current_user = Depends(get_current_user)):
    company_id = current_user.company_id
    
    total_answers = await db.query(ApprovedAnswer).filter(
        ApprovedAnswer.company_id == company_id
    ).count()
    
    total_reuses = await db.query(AnswerReuseHistory).join(
        ApprovedAnswer,
        AnswerReuseHistory.source_answer_id == ApprovedAnswer.id
    ).filter(
        ApprovedAnswer.company_id == company_id
    ).count()
    
    by_category = await db.query(
        ApprovedAnswer.answer_category,
        func.count(ApprovedAnswer.id).label('count'),
        func.sum(ApprovedAnswer.times_reused).label('total_reuses')
    ).filter(
        ApprovedAnswer.company_id == company_id
    ).group_by(ApprovedAnswer.answer_category).all()
    
    most_reused = await db.query(ApprovedAnswer).filter(
        ApprovedAnswer.company_id == company_id
    ).order_by(ApprovedAnswer.times_reused.desc()).limit(5).all()
    
    return {
        "total_answers": total_answers,
        "total_reuses": total_reuses,
        "by_category": by_category,
        "most_reused": most_reused,
        "last_updated": ...
    }
```

### Success Criteria

- ✅ Answer library is being populated (after 3 questionnaires, 30+ answers stored)
- ✅ Answer reuse is happening (by questionnaire #2, 30%+ of answers are reused)
- ✅ Users explicitly value it ("This saves us time" / "This keeps us consistent")
- ✅ Design partners come back and say "we're using this every time now"

### Timeline

2-3 weeks

### Difficulty

Medium (database design is straightforward, semantic matching is copy-paste from your RAG)

### Payoff

**Very high.** This is your moat. Users now have data lock-in (accumulated answers). Switching costs go up dramatically.

---

## Phase 8 — Stale-Answer Detection (CORE MOAT)

**Objective:** Flag when previous answers become outdated due to policy changes.

**Why Phase 8:** Organizational memory only has value if it stays accurate. Stale answers are a compliance liability. This feature prevents that.

### What to Build

#### 8a. Policy Version Tracking

Track which policy versions each answer is based on.

**Database Schema:**

```sql
ALTER TABLE documents ADD COLUMN version INT DEFAULT 1;
ALTER TABLE documents ADD COLUMN updated_at TIMESTAMP;
ALTER TABLE documents ADD COLUMN change_summary TEXT;  -- "Encryption standard updated from AES-128 to AES-256"

ALTER TABLE approved_answers ADD COLUMN policy_version_ids INT[];  -- which policy versions this answer cites
ALTER TABLE approved_answers ADD COLUMN last_policy_check_at TIMESTAMP;
```

**Implementation:**

```python
# services/policy_management.py

async def upload_policy_version(company_id: int, file, user_id: int):
    """
    When user uploads a new version of a policy document:
    1. Check if we've seen this document before
    2. If yes, compare to previous version
    3. Detect what changed
    4. Flag affected answers as "potentially stale"
    """
    
    # Parse the document
    document_text = parse_document(file)
    document_embedding = await embeddings.embed(document_text)
    
    # Check if this is a new version or new document
    existing_doc = await db.query(Document).filter(
        Document.company_id == company_id,
        Document.filename == file.filename
    ).order_by(Document.version.desc()).first()
    
    if existing_doc:
        # Compare to previous version
        old_embedding = existing_doc.embedding
        similarity = cosine_similarity(document_embedding, old_embedding)
        
        if similarity < 0.95:  # significant change detected
            # This is a new version
            new_doc = Document(
                company_id=company_id,
                filename=file.filename,
                version=existing_doc.version + 1,
                document_text=document_text,
                embedding=document_embedding,
                change_summary=await detect_changes(existing_doc.document_text, document_text),
                uploaded_by=user_id,
                updated_at=datetime.utcnow()
            )
            
            # Flag answers that cite old version as "potentially stale"
            affected_answers = await db.query(ApprovedAnswer).filter(
                ApprovedAnswer.company_id == company_id,
                ApprovedAnswer.policy_version_ids.contains([existing_doc.id])
            ).all()
            
            for answer in affected_answers:
                answer.status = 'potentially_stale'
                answer.needs_review_reason = f"Policy '{file.filename}' was updated. Please review if this answer is still accurate."
                answer.last_policy_check_at = datetime.utcnow()
            
            await db.add(new_doc)
            await db.commit()
            
            return {
                "message": f"Policy version {new_doc.version} uploaded",
                "affected_answers": len(affected_answers),
                "change_summary": new_doc.change_summary
            }
    else:
        # New document
        new_doc = Document(
            company_id=company_id,
            filename=file.filename,
            version=1,
            document_text=document_text,
            embedding=document_embedding,
            uploaded_by=user_id,
            updated_at=datetime.utcnow()
        )
        await db.add(new_doc)
        await db.commit()

async def detect_changes(old_text: str, new_text: str) -> str:
    """
    Detect what changed between two versions.
    Use LLM to summarize changes.
    """
    prompt = f"""
    Old policy section:
    {old_text[:500]}
    
    New policy section:
    {new_text[:500]}
    
    What changed? Be concise. Focus on compliance-relevant changes.
    """
    
    change_summary = await llm.generate(prompt)
    return change_summary
```

#### 8b. Stale-Answer Dashboard

Show manager what answers need review due to policy changes.

**UI: `/answers/compliance-review`**

```
Compliance Review Needed
━━━━━━━━━━━━━━━━━━━━━━━━

2 answers need review due to policy updates

Policy: Data Encryption Policy (v1 → v2)
Change: "Encryption standard updated from AES-128 to AES-256"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Question: "Do you encrypt data at rest?"
   Current answer: "Yes, using AES-128 at rest."
   Status: POTENTIALLY STALE
   [Review] [Mark as still accurate] [Regenerate from new policy]

2. Question: "What encryption standards do you use?"
   Current answer: "AES-128 for legacy, AES-256 for new systems."
   Status: POTENTIALLY STALE
   [Review] [Mark as still accurate] [Regenerate from new policy]
```

**Implementation:**

```python
@router.get("/answers/compliance-review")
async def get_compliance_review(current_user = Depends(get_current_user)):
    stale_answers = await db.query(ApprovedAnswer).filter(
        ApprovedAnswer.company_id == current_user.company_id,
        ApprovedAnswer.status == 'potentially_stale'
    ).all()
    
    return {
        "total_needing_review": len(stale_answers),
        "answers": stale_answers,
        "grouped_by_policy": group_by_reason(stale_answers)
    }

@router.post("/answers/{answer_id}/compliance-review")
async def mark_compliance_reviewed(answer_id: int, request: ComplianceReviewRequest, current_user = Depends(get_current_user)):
    """
    User reviews stale answer and confirms:
    - "Still accurate" → mark as active
    - "Needs update" → regenerate from new policy
    - "Needs manual update" → leave as stale, add comment
    """
    answer = await db.get(ApprovedAnswer, answer_id)
    
    if request.action == "still_accurate":
        answer.status = 'active'
        answer.last_reviewed_at = datetime.utcnow()
    
    elif request.action == "regenerate":
        # Re-run LLM with new policy context
        new_answer = await regenerate_answer_with_policy(answer.question_text, answer.policy_version_ids)
        answer.answer_text = new_answer
        answer.status = 'active'
        answer.last_reviewed_at = datetime.utcnow()
    
    elif request.action == "needs_manual_update":
        answer.status = 'archived'  # hide from reuse until manually updated
        answer.needs_review_reason = request.comment
    
    await db.commit()
    return {"message": "Answer reviewed", "new_status": answer.status}
```

#### 8c. Automated Stale-Answer Alerts

Optional: Notify managers via Slack/email when answers become stale.

```python
# If integrated with Slack:
await send_slack_message(
    channel=user.slack_channel,
    message=f"⚠️ Policy update detected: 2 of your security answers may need review. [Review Now]"
)
```

### Success Criteria

- ✅ Policy versioning is working (upload v2 of a policy, detect changes)
- ✅ Stale answers are correctly flagged (after policy update, affected answers marked as "potentially stale")
- ✅ Managers can confirm/update answers (compliance review workflow functional)
- ✅ Users feel confident in their answer library (know answers are current)

### Timeline

2-3 weeks

### Difficulty

Medium (similar to what you've already built with RAG + policy parsing)

### Payoff

**Very high.** This solves a real compliance problem. It also strengthens the moat: users now depend on you to keep their answers compliant.

---

## Phase 9 — Trust & Audit Layer (ENTERPRISE COMPLIANCE)

**Objective:** Add approval workflows, audit trails, role-based access for enterprise compliance requirements.

**Why Phase 9 (not Phase 7):** Users need to trust the system with sensitive security knowledge. Audit trails + approvals = enterprise-grade compliance.

### What to Build

#### 9a. User Auth + Roles

```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  company_id INT REFERENCES companies(id),
  role VARCHAR(50) NOT NULL,  -- viewer, analyst, manager, admin
  created_at TIMESTAMP DEFAULT now(),
  last_login TIMESTAMP
);

-- Roles:
-- viewer: can read questionnaires + answers, cannot edit
-- analyst: can generate + edit answers, cannot approve
-- manager: can approve/reject answers, cannot manage users
-- admin: can do everything, manage users + settings
```

**Implementation:** Standard FastAPI auth pattern.

#### 9b. Approval Workflow

State machine: `draft` → `pending_review` → `approved` / `rejected`

```sql
ALTER TABLE approved_answers ADD COLUMN status VARCHAR(50) DEFAULT 'draft';
-- draft, pending_review, approved, rejected, archived

ALTER TABLE approved_answers ADD COLUMN pending_review_from INT REFERENCES users(id);
ALTER TABLE approved_answers ADD COLUMN review_comments TEXT;
ALTER TABLE approved_answers ADD COLUMN rejected_reason TEXT;
```

**UI:**
- Analyst creates answer → shows "Waiting for [Manager Name]'s approval"
- Manager sees all pending answers → can approve or request changes
- Approval is logged with timestamp + who approved

#### 9c. Audit Trail

Every action logged: who, what, when, why.

```sql
CREATE TABLE audit_logs (
  id SERIAL PRIMARY KEY,
  company_id INT REFERENCES companies(id),
  user_id INT REFERENCES users(id),
  resource_type VARCHAR(50),  -- question, answer, approval, policy
  resource_id INT,
  action VARCHAR(50),  -- created, edited, approved, rejected, reviewed
  old_value TEXT,
  new_value TEXT,
  reason TEXT,
  timestamp TIMESTAMP DEFAULT now()
);
```

This gives enterprises the traceability they need for compliance audits.

#### 9d. Citation Display

When reviewing an answer, show which policy documents it's based on.

```python
@router.get("/answers/{answer_id}/citations")
async def get_answer_citations(answer_id: int):
    answer = await db.get(ApprovedAnswer, answer_id)
    
    citations = []
    for policy_id in answer.policy_version_ids:
        policy = await db.get(Document, policy_id)
        # Get the relevant chunks from RAG
        chunks = await get_relevant_chunks(answer.question_text, policy_id)
        citations.append({
            "policy": policy.filename,
            "version": policy.version,
            "chunks": chunks,  # the actual text snippets used
            "relevance_scores": [chunk.score for chunk in chunks]
        })
    
    return citations
```

**UI:**
```
Answer Approval
━━━━━━━━━━━━━━━

Question: "Do you encrypt data at rest?"
Answer: "Yes, we encrypt all data at rest using AES-256."

Based on:
  📄 Data Encryption Policy (v2)
    - "All data at rest must be encrypted using AES-256 or equivalent" [Score: 0.94]
    - "Encryption keys are rotated annually" [Score: 0.81]

  📄 Compliance Requirements (v1)
    - "Data protection standards require encryption" [Score: 0.78]

[Approve] [Request Changes] [Reject]
```

### Timeline

3-4 weeks

### Difficulty

Medium

### Payoff

High (enterprises require this for compliance; you can now sell to regulated companies)

---

## Phase 10 — Excel Engineering & Templates

**Objective:** Handle Excel complexity. Exports look professional. Customers don't complain about formatting.

### What to Build

#### 10a. Format Preservation

Detect input format (merged cells, colors, formulas). Re-apply on export.

#### 10b. Template System

Different customers use different Excel layouts. Save templates and auto-apply.

#### 10c. Merged Cells + Formulas

Preserve complex Excel structures.

### Timeline

2-3 weeks

### Difficulty

Medium-high (Excel quirks are annoying, but solvable)

### Payoff

Very high (prevents "export looks wrong" complaints)

---

## Phase 11 — Cross-Questionnaire Intelligence

**Objective:** Help customers discover they're answering the same question multiple ways.

### What to Build

#### 11a. Question Similarity Matching

When uploading questionnaire #2, surface similar questions from previous questionnaires.

"Question 'Do you encrypt data at rest?' is 94% similar to SIG Lite Q7. Reuse that answer?"

#### 11b. Answer Consistency Alerts

Across all questionnaires, flag when same question is answered differently.

"You answered 'Do you have MFA?' as 'Yes' in SIG Lite, but 'Partial' in ISO 27001. Which is correct?"

This is a **compliance risk alert**.

#### 11c. Knowledge Graph Dashboard

Visual showing: policies → controls → questions → answers → questionnaires

See where knowledge is distributed, where gaps exist.

### Timeline

2-3 weeks

### Difficulty

Medium (embeddings + graph visualization)

### Payoff

High (dramatic UX improvement once customers have multiple questionnaires)

---

## Prioritization (Based on Customer Feedback)

**Phase 6:** Do this regardless. Customer validation is free information.

**Phase 7:** If 7+ customers say "answer reuse would save us time" or "we struggle with repetitive questions"

**Phase 8:** If 5+ customers mention "when we update a policy, we don't know which questionnaire answers are now outdated"

**Phase 9:** If 5+ customers say "we need approval workflows + audit trails for compliance"

**Phase 10:** If 5+ customers complain "the Excel export doesn't look right"

**Phase 11:** If customers are filling 3+ different questionnaires and mentioning "we're answering the same question differently"

**Don't build any phase 7-11 without customer validation first.**

---

## Post-Phase 11 Potential Directions

- **Vendor Risk Workflows:** Extend beyond questionnaires to vendor security reviews
- **Compliance Reporting:** Auto-generate compliance reports using your knowledge graph
- **Policy Linking:** Automated linking between policies, controls, and questionnaire answers
- **Integration:** Slack notifications, Teams, email digests
- **Analytics:** "You've saved X hours, spent Y dollars on LLM, had Z% answer reuse rate"
- **Multi-tenant:** Support multiple companies (with strict data isolation)
- **API:** Let customers query answers programmatically

---

## Using This Roadmap

### Phase 6 (Next 2-3 weeks)

1. Schedule customer calls using the script above
2. Specifically validate: **organizational memory, answer reuse, stale-answer problem**
3. Document feedback in `docs/customer-feedback.md`
4. **Decision:** Are organizational memory signals strong enough to commit to Phase 7?

### Phase 7-8 (If Phase 6 validates)

Commit to building answer library + stale-answer detection together.
These two phases form the **core moat**. Build them before broad GTM.

### Phase 9+ (Based on feedback)

Only build if customers validate the need.

---

## Key Metrics to Track (Across All Phases)

- **Time saved per questionnaire** (vs. manual)
- **Answer reuse rate** (% of answers reused from library)
- **Answer library growth** (answers accumulated per customer over time)
- **Stale-answer detection accuracy** (false positives/negatives)
- **Customer retention** (churn rate — should be very low once they have accumulated answers)
- **Switching cost validation** ("Would you switch if a competitor offered the same feature?" → should be "No, we've built too much knowledge")

---

## Red Flags (Stop and Pivot If True)

- 🚩 Phase 6: Customers don't care about answer reuse (they say "speed matters more")
- 🚩 Phase 7: Users don't actually reuse answers (library sits empty)
- 🚩 Phase 8: Stale-answer detection creates false positives (users ignore alerts)
- 🚩 Phase 9: Enterprise customers don't care about audit trails
- 🚩 Any phase: Customer LTV drops faster than CAC (you're not building defensibility)

If any red flag triggers, pause and reassess. Maybe the commodity version (speed + efficiency) is the better route.

---

## Success = Organizational Memory Moat

**You win when:**
- Users have accumulated 50+ answers in their library
- They're reusing 40%+ of answers from previous questionnaires
- They can't leave without losing institutional security knowledge
- They can't get the same value from Vanta

That's defensibility. That's a real business.
