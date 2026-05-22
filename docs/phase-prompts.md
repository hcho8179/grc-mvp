PHASE 3: Questionnaire Upload and Parsing

PROJECT CONTEXT (read app/ before starting):
Phases 1-2 complete: scaffold + knowledge base ingestion working. Users 
can upload PDFs/DOCX/XLSX containing policies and past answered 
questionnaires; these are parsed, chunked, embedded via Voyage 
(voyage-3, 1024 dims), and stored in pgvector. Document and KnowledgeChunk 
models exist with cascade FK.

This phase is DIFFERENT from Phase 2:
- Phase 2 ingested the company's OWN policies/past answers (knowledge base)
- Phase 3 receives a NEW blank questionnaire from a customer that needs 
  filling in
- Same XLSX file format, but different intent and different storage

PHASE 3 GOAL:
User uploads a new blank security questionnaire (typically an XLSX with 
100-500 questions sent by an enterprise customer). System parses it into 
structured Question records linked to a Questionnaire record, ready for 
AI answer generation in Phase 4. NO AI answers yet — just parse and store.

THEN BUILD IN THIS ORDER — STOP AFTER EACH STEP:

STEP 3a: Models + migration
- Questionnaire model: id, name, customer_name, source_filename, 
  uploaded_at, status (enum: draft, in_progress, complete), 
  question_count, raw_xlsx_blob (LargeBinary, the original file for 
  preserving format on export later)
- Question model: id, questionnaire_id (FK CASCADE), question_text, 
  draft_answer (text, nullable), final_answer (text, nullable), 
  status (enum: pending, generated, approved, rejected), 
  row_index (int, for export ordering), confidence (enum: high, medium, 
  low, nullable), cited_chunk_ids (JSON array of int, nullable), 
  reasoning (text, nullable)
- Both inherit from Base in app/models.py
- alembic revision --autogenerate -m "add questionnaire and question models"
- Show migration BEFORE applying. Apply, verify with \dt.

STEP 3b: Questionnaire XLSX parser (extend app/services/parsing.py) + tests
- parse_xlsx_questionnaire_preview(file_bytes) -> 
  {"columns": [...], "sample_rows": [first 5 rows as dicts], 
   "total_rows": int, "sheet_name": str}
- parse_xlsx_questionnaire_full(file_bytes, question_col, answer_col=None) 
  -> list[{"row_index": int, "question": str, "existing_answer": str|None}]
- Assume first sheet, row 1 is header
- Skip rows where question column is empty/whitespace
- Tests with fake XLSX created inline

STEP 3c: Upload route (app/routes/questionnaires.py) + register in main.py
- GET /questionnaires — list page (table: name, customer, status, 
  question_count, uploaded_at, actions)
- GET /questionnaires/upload — form: file upload, questionnaire name, 
  customer name
- POST /questionnaires/upload — saves file as blob in temp store 
  (in-memory dict by uuid for now), parses preview, redirects to picker
- GET /questionnaires/upload/{temp_id}/columns — shows preview rows 
  and column dropdowns
- POST /questionnaires/upload/{temp_id}/columns — user picks question 
  column (required) and existing-answer column (optional). Creates 
  Questionnaire + N Question rows. Status = draft. Saves raw_xlsx_blob 
  for later export.

STEP 3d: Detail view route + template
- GET /questionnaires/{id} — read-only table of all questions 
  (Question | Status | Answer Preview). NO generation buttons yet 
  (that's Phase 4). Add a placeholder "Generate Answers" button that's 
  disabled with tooltip "Coming in Phase 4".
- POST /questionnaires/{id}/delete — cascade delete

STEP 3e: Templates
- questionnaires/list.html — table with status badges (color-coded)
- questionnaires/upload.html — form
- questionnaires/column_picker.html — preview table + dropdowns
- questionnaires/detail.html — question list with empty answer placeholders

STEP 3f: End-to-end test
- Download SIG Lite from sharedassessments.org (or I'll provide a 
  test XLSX with ~20 questions)
- Upload via /questionnaires/upload
- Pick the question column from dropdown
- Verify Questionnaire row exists with correct counts
- Verify N Question rows exist with row_index preserving order
- Verify raw_xlsx_blob is non-null

NON-GOALS:
- Do NOT generate any AI answers yet (Phase 4)
- Do NOT handle merged cells, multi-sheet workbooks, conditional 
  formatting, or other exotic Excel features — first sheet, simple table
- Do NOT auto-detect which column is the question — user always picks

Confirm you've read the relevant files,
then start with Step 3a.

PHASE 4: AI Answer Generation — The Core Magic

PROJECT CONTEXT (read app/ before starting):
Phases 1-3 complete. Knowledge base ingestion works (Document + 
KnowledgeChunk with embeddings). Questionnaire upload works 
(Questionnaire + Question records). LLM provider abstraction exists 
in app/services/generation.py supporting Anthropic + Gemini; currently 
using Gemini 2.5 Flash. Embedding provider abstraction in 
app/services/embeddings.py using Voyage (voyage-3, 1024 dims).

PHASE 4 GOAL:
For each parsed question in a questionnaire, retrieve top-K relevant 
chunks from the knowledge base via pgvector cosine similarity, send 
to the LLM with a strict structured-output prompt, parse the JSON 
response, store draft_answer + confidence + cited_chunk_ids. Build 
a review interface where the user can edit, approve, or reject each 
answer. Approved edited answers feed back into the knowledge base 
(self-learning loop).

This is the heart of the product.


THEN BUILD IN THIS ORDER — STOP AFTER EACH STEP:

STEP 4a: Retrieval service (app/services/retrieval.py) + tests
- retrieve_relevant_chunks(question_text: str, top_k: int = 5, 
  similarity_threshold: float = 0.6) -> list[RetrievalResult]
- RetrievalResult dataclass: chunk (KnowledgeChunk), similarity (float)
- Embed the question using EmbeddingProvider
- Query pgvector with cosine distance:
  SELECT *, 1 - (embedding <=> :query_embedding) AS similarity
  FROM knowledge_chunks
  ORDER BY embedding <=> :query_embedding
  LIMIT :top_k
- Use raw SQL via session.execute() — SQLAlchemy ORM is awkward with 
  vector ops
- Filter out chunks below similarity_threshold (track these for 
  low-confidence flagging)
- Test on existing chunks (I'll have some in DB by now): manually 
  embed "do you encrypt data at rest" and verify it retrieves the 
  most semantically similar chunks

STEP 4b: Generation service refactor (app/services/generation.py) 
         + structured output prompt + test
- generate_answer(question_text, retrieved_chunks) -> AnswerResult
- AnswerResult dataclass: answer (str), confidence (Literal["high", 
  "medium", "low"]), cited_chunk_ids (list[int]), reasoning (str), 
  insufficient_context (bool)
- System prompt (use exactly this — we'll iterate later):

  """You are a security compliance expert helping a SaaS company answer 
  a security questionnaire from their enterprise customer.

  You will be given:
  - A question being asked
  - Relevant excerpts from the company's existing policies and previous 
    questionnaire answers (each labeled with chunk_id)

  Your job:
  1. Write a clear, professional answer based ONLY on the provided context.
  2. Match the formal tone and terminology of the source material.
  3. If the context is insufficient, set insufficient_context to true 
     and leave answer empty.
  4. Do NOT invent facts, certifications, or capabilities not in sources.
  5. Keep answers concise (2-4 sentences typical, longer only if needed).
  6. Cite the chunk_ids you actually used.

  Confidence levels:
  - high: multiple strong source chunks directly answer the question
  - medium: sources partially cover the question or require some inference
  - low: weak retrieval, answer likely needs human review

  Respond with ONLY valid JSON in this exact format (no markdown fences):
  {
    "answer": "your answer text or empty string",
    "confidence": "high" | "medium" | "low",
    "cited_chunk_ids": [1, 5, 12],
    "reasoning": "brief explanation of confidence",
    "insufficient_context": false
  }"""

- User message format:
  Question: <question_text>
  
  Available sources:
  [chunk_id 1, similarity 0.87]: <chunk content>
  [chunk_id 5, similarity 0.81]: <chunk content>
  ...

- Parse the JSON response. Strip markdown fences if model adds them 
  despite instructions. On parse failure, retry once with a stricter 
  message; on second failure, return AnswerResult with 
  insufficient_context=True
- If retrieval returned no chunks above threshold, skip LLM call 
  entirely and return insufficient_context=True
- Test with mocked LLM provider returning hardcoded JSON

STEP 4c: Generation orchestration route (extend app/routes/questionnaires.py 
         or new app/routes/answers.py)
- POST /questionnaires/{id}/generate — iterates all pending questions, 
  generates answers, updates rows. Use HTMX or simple page reload to 
  show progress. NOT background jobs — synchronous is fine.
- POST /questionnaires/{id}/questions/{qid}/regenerate — regenerate 
  one question
- asyncio.sleep(1) between LLM calls for free tier rate limits
- Wrap each question generation in try/except — one failure shouldn't 
  kill the batch

STEP 4d: Review interface (UPDATE questionnaires/detail.html)
- Table: Question | Draft Answer | Confidence Badge | Sources | Status 
  | Actions
- Confidence badge colors: high=green, medium=yellow, low=red
- Inline edit on draft_answer via HTMX PATCH to 
  /questionnaires/{id}/questions/{qid}
- "Approve" button → status=approved, copies (possibly edited) 
  draft_answer to final_answer
- "Reject" button → status=rejected
- Sources column shows chunk_ids as clickable badges that expand 
  to show cited source text (HTMX get on click)
- Regenerate button per row

STEP 4e: Self-learning loop
- On approve: create a new KnowledgeChunk from the approved Q+A pair 
  ("Q: <question>\nA: <final_answer>"). Embed it. Save it.
- Link it to a special Document called "Approved Answers" (create 
  this Document once on first approval, reuse for subsequent approvals)
- Future retrievals will find these approved answers and reuse them

STEP 4f: Full end-to-end demo
- I'll have ~10 policy chunks in knowledge base and ~20-question 
  test questionnaire
- Run POST /questionnaires/{id}/generate
- Review the answers — check accuracy, citations, confidence calibration
- Edit one, approve it, regenerate another to verify the loop works
- Verify approved answers now exist as KnowledgeChunks

NON-GOALS:
- Background job queues — synchronous is fine even at 5 min for 100 
  questions (slowness is a Phase 5 concern)
- Auth, multi-user
- Streaming token-by-token responses (just return when complete)
- Cost tracking dashboard (Phase 5)

COST AWARENESS:
Gemini 2.5 Flash free tier has rate limits ~15 RPM. asyncio.sleep(1) 
between calls keeps us safe. For a 100-question questionnaire that's 
~100 seconds minimum, which is fine.

Confirm you've read the relevant files,
then start with Step 4a.

PHASE 5: Export, Polish, and Demo-Readiness

PROJECT CONTEXT (read app/ before starting):
Phases 1-4 complete. Full RAG pipeline works: upload knowledge → upload 
questionnaire → generate AI answers with citations → review and approve 
→ approved answers feed back into knowledge base.

PHASE 5 GOAL:
Make the product demo-able. Generated answers can be exported to Excel 
in the original format. UI looks intentional, not like a school project. 
End-to-end flow is smooth. There's a dashboard showing the value the 
product delivers.

THEN BUILD IN THIS ORDER — STOP AFTER EACH STEP:

STEP 5a: Excel export service (app/services/export.py) + route
- export_questionnaire_to_xlsx(questionnaire_id) -> bytes
- Load the original raw_xlsx_blob (saved in Phase 3) with openpyxl
- For each Question, write final_answer (fallback draft_answer if 
  not approved) into the correct cell using row_index and the 
  answer column (need to also save which column index user chose 
  for answers — update Questionnaire model with answer_col_index 
  and add a migration)
- Preserve all original formatting (openpyxl maintains styles when 
  modifying cells)
- Add small footer cell: "Generated with [tool name]" in row N+2 
  of column A
- GET /questionnaires/{id}/export — returns the XLSX as download 
  with Content-Disposition: attachment; filename="<name>_filled.xlsx"

STEP 5b: Dashboard / home page (app/routes/dashboard.py)
- GET / — landing page with:
  - Stats cards: total questionnaires, total questions answered, 
    avg confidence, hours saved (estimate: 8 min/question × answered)
  - Recent questionnaires (last 5) with status
  - Quick action buttons: Upload Policy | New Questionnaire
- Use Tailwind cards, clean spacing, real numbers from DB

STEP 5c: UI polish pass — go through every page and fix:
- Consistent Tailwind styling (one color palette: indigo/slate base)
- Loading states: HTMX spinners during generation, page-level for 
  uploads
- Empty states: "No questionnaires yet — upload one to get started" 
  with CTA button
- Error states: friendly error messages on failed parse/embed/generate
- Navbar in base.html: logo placeholder (just text \"Greenlight\" or 
  whatever — pick something), main sections, current page highlighted
- Favicon (use an emoji-as-favicon trick: data URL SVG)
- Decent at 1280×800; mobile responsiveness NOT required

STEP 5d: Demo data seed script (scripts/seed_demo.py)
- Drops all data (with confirmation prompt)
- Creates "Acme Corp" demo policies as Documents:
  - Information Security Policy (3-4 pages of plausible policy text)
  - Data Protection Policy (2-3 pages)
  - Incident Response Plan (2 pages)
  - 30 sample past Q&A pairs (from common SIG questions, written 
    in Acme's voice)
- Embeds and stores everything
- Creates a sample new questionnaire ("MegaBank Vendor Assessment") 
  with 20 representative questions, ready to generate answers for
- Make: python scripts/seed_demo.py runnable from project root

STEP 5e: Cost & performance tracking
- Add LLMCall model: id, model, input_tokens, output_tokens, 
  cost_estimate, created_at, questionnaire_id (nullable FK), 
  question_id (nullable FK)
- Wrap LLM calls to log to this table
- Add admin route GET /admin/usage showing total cost this month, 
  cost per questionnaire
- If a 100-question questionnaire takes more than 3 min, refactor 
  generation to use asyncio.gather in batches of 5 (still respecting 
  rate limits with semaphore)

STEP 5f: Demo run-through documentation (docs/demo.md)
- Write the 5-minute demo script
- Steps to reset and reload demo data
- Common questions during demo and good answers
- Talking points: time saved, retention story, integration roadmap

NON-GOALS:
- User accounts, billing, Stripe — still MVP
- Marketing website
- Email notifications
- Multi-tenancy
- Mobile responsive (desktop demo only)

Confirm you've read the relevant files,
then start with Step 5a.