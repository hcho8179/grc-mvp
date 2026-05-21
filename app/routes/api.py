"""JSON API router — consumed by the React frontend."""

import asyncio
import hashlib
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from collections import defaultdict

from app.auth import get_current_user
from app.db import get_db
from app.models import (
    ApprovedAnswer,
    AuditLog,
    ConfidenceLevel,
    Document,
    FileType,
    KnowledgeChunk,
    LLMCall,
    Question,
    QuestionComment,
    QuestionnaireStatus,
    QuestionnaireTemplate,
    Questionnaire,
    QuestionStatus,
    SourceType,
    User,
    question_citations,
)
from app.services.answer_library import detect_category, classify_category
from app.services.audit import log_event
from app.services.email import send_question_assigned
from app.services.chunking import chunk_text
from app.services.embeddings import get_embedding_provider
from app.services.export import export_questionnaire_to_xlsx
from app.services.generation import generate_answer
from app.services.parsing import (
    parse_file,
    parse_xlsx_questionnaire_full,
    parse_xlsx_questionnaire_preview,
)
from app.services.retrieval import retrieve_relevant_chunks
from app.services.templates import find_template_by_customer, list_templates
from fastapi import HTTPException as _HTTPException

router = APIRouter(prefix="/api", tags=["api-json"])

_react_upload_tmp: dict[str, dict] = {}


# ── role guard ────────────────────────────────────────────────────────────────

def _require_role(user: User, *roles: str) -> None:
    if user.role not in roles:
        raise _HTTPException(status_code=403, detail="You don't have permission to do this")


# ── helpers ──────────────────────────────────────────────────────────────────

def _q_json(q: Question, assignee: User | None = None, chunk_scores: dict | None = None, starter_chunk_ids: set | None = None) -> dict:
    scores = chunk_scores or {}
    cited = [{"id": cid, "score": scores.get(cid)} for cid in (q.cited_chunk_ids or [])]
    has_starter = bool(
        starter_chunk_ids and any(cid in starter_chunk_ids for cid in (q.cited_chunk_ids or []))
    )
    return {
        "id": q.id,
        "row_index": q.row_index,
        "question_text": q.question_text,
        "draft_answer": q.draft_answer or "",
        "short_answer": q.short_answer or "",
        "final_answer": q.final_answer or "",
        "status": q.status.value,
        "confidence": q.confidence.value if q.confidence else None,
        "cited_chunk_ids": q.cited_chunk_ids or [],
        "cited_chunks": cited,   # [{id, score}] — score is cosine similarity 0–1
        "reasoning": q.reasoning or "",
        "has_starter_sources": has_starter,
        "assigned_to_id": q.assigned_to_id,
        "assigned_to_email": assignee.email if assignee else None,
        "assigned_to_name": assignee.full_name if assignee else None,
    }


def _save_citation_scores(db: Session, question_id: int, chunks: list, cited_ids: list[int]) -> dict[int, float]:
    """Write retrieval scores to question_citations and return {chunk_id: score} map."""
    score_map = {r.chunk.id: r.similarity for r in chunks}
    # Clear old citations for this question then re-insert with fresh scores
    db.execute(question_citations.delete().where(question_citations.c.question_id == question_id))
    for cid in cited_ids:
        if cid in score_map:
            db.execute(question_citations.insert().values(
                question_id=question_id,
                chunk_id=cid,
                retrieval_score=score_map[cid],
            ))
    return score_map


def _comment_json(c: QuestionComment) -> dict:
    return {
        "id": c.id,
        "user_id": c.user_id,
        "user_email": c.user_email or "",
        "user_name": c.user_name or "",
        "body": c.body,
        "created_at": c.created_at.isoformat(),
    }


def _qs_json(q: Questionnaire) -> dict:
    return {
        "id": q.id,
        "name": q.name,
        "customer_name": q.customer_name or "",
        "source_filename": q.source_filename or "",
        "status": q.status.value,
        "question_count": q.question_count,
        "created_at": q.created_at.isoformat(),
    }


def _get_approved_doc(db: Session, org_id: int):
    doc = db.query(Document).filter(
        Document.filename == "Approved Answers",
        Document.org_id == org_id,
    ).first()
    if not doc:
        doc = Document(filename="Approved Answers", file_type=FileType.xlsx, chunk_count=0, org_id=org_id)
        db.add(doc)
        db.flush()
    return doc


# ── dashboard ────────────────────────────────────────────────────────────────

@router.get("/dashboard")
def api_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org_id = current_user.org_id
    total_questionnaires = db.query(Questionnaire).filter(Questionnaire.org_id == org_id, Questionnaire.deleted_at == None).count()
    answered_statuses = [QuestionStatus.generated, QuestionStatus.approved]
    total_answered = (
        db.query(Question)
        .join(Questionnaire, Questionnaire.id == Question.questionnaire_id)
        .filter(Questionnaire.org_id == org_id, Question.status.in_(answered_statuses))
        .count()
    )
    total_approved = (
        db.query(Question)
        .join(Questionnaire, Questionnaire.id == Question.questionnaire_id)
        .filter(Questionnaire.org_id == org_id, Question.status == QuestionStatus.approved)
        .count()
    )

    high = db.query(Question).join(Questionnaire).filter(Questionnaire.org_id == org_id, Question.confidence == ConfidenceLevel.high).count()
    med  = db.query(Question).join(Questionnaire).filter(Questionnaire.org_id == org_id, Question.confidence == ConfidenceLevel.medium).count()
    low  = db.query(Question).join(Questionnaire).filter(Questionnaire.org_id == org_id, Question.confidence == ConfidenceLevel.low).count()
    conf_total = high + med + low
    avg_conf_pct = round(((high * 3 + med * 2 + low) / (conf_total * 3)) * 100) if conf_total else 0
    hours_saved = round(total_answered * 8 / 60, 1)
    total_cost = round(
        db.query(func.sum(LLMCall.cost_estimate)).filter(LLMCall.org_id == org_id).scalar() or 0.0, 4
    )

    recent = (
        db.query(Questionnaire)
        .filter(Questionnaire.org_id == org_id, Questionnaire.deleted_at == None)
        .order_by(Questionnaire.created_at.desc())
        .limit(5)
        .all()
    )
    return {
        "total_questionnaires": total_questionnaires,
        "total_answered": total_answered,
        "total_approved": total_approved,
        "avg_conf_pct": avg_conf_pct,
        "hours_saved": hours_saved,
        "total_cost": total_cost,
        "recent": [_qs_json(q) for q in recent],
    }


# ── questionnaire upload (React multi-step wizard) ────────────────────────────

@router.post("/questionnaires/upload/preview")
async def api_questionnaire_upload_preview(
    file: UploadFile = File(...),
    name: str = Form(...),
    customer_name: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    file_bytes = await file.read()
    filename = file.filename or "questionnaire.xlsx"
    if not file_bytes:
        return JSONResponse({"error": "Uploaded file is empty."}, status_code=400)
    if len(file_bytes) > 20 * 1024 * 1024:
        return JSONResponse({"error": "File too large — maximum size is 20 MB."}, status_code=400)
    if Path(filename).suffix.lower() != ".xlsx":
        return JSONResponse({"error": "Only XLSX files are supported for questionnaires."}, status_code=400)
    if not name.strip():
        return JSONResponse({"error": "Questionnaire name is required."}, status_code=400)
    try:
        preview = parse_xlsx_questionnaire_preview(file_bytes)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    temp_id = str(uuid.uuid4())
    _react_upload_tmp[temp_id] = {
        "bytes": file_bytes,
        "filename": filename,
        "name": name.strip(),
        "customer_name": customer_name.strip() or None,
        "org_id": current_user.org_id,
    }
    suggested = find_template_by_customer(customer_name.strip() or None, db)
    return {
        "temp_id": temp_id,
        "filename": filename,
        "preview": preview,
        "suggested_template": {"question_col": suggested.question_col, "answer_col": suggested.answer_col} if suggested else None,
    }


@router.post("/questionnaires/upload/{temp_id}/finalize")
def api_questionnaire_upload_finalize(
    temp_id: str,
    question_col: int = Form(...),
    answer_col: str = Form(""),
    evidence_col: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    meta = _react_upload_tmp.get(temp_id)
    if not meta:
        return JSONResponse({"error": "Upload session expired. Please upload again."}, status_code=400)
    if meta.get("org_id") != current_user.org_id:
        return JSONResponse({"error": "Unauthorized."}, status_code=403)
    ans_col: int | None = int(answer_col) if answer_col.strip() else None
    ev_col: int | None = int(evidence_col) if evidence_col.strip() else None
    try:
        parsed_questions = parse_xlsx_questionnaire_full(meta["bytes"], question_col, ans_col)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    if not parsed_questions:
        return JSONResponse({"error": "No questions found in the selected column."}, status_code=400)

    from app.services import storage as file_storage
    import uuid
    file_bytes = meta["bytes"]
    xlsx_key: str | None = None
    store_blob: bytes | None = file_bytes  # fallback for local dev without S3

    if file_storage.is_configured():
        xlsx_key = f"questionnaires/{current_user.org_id}/{uuid.uuid4().hex}.xlsx"
        file_storage.upload(xlsx_key, file_bytes,
                            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        store_blob = None  # don't double-store in DB

    questionnaire = Questionnaire(
        name=meta["name"],
        customer_name=meta["customer_name"],
        source_filename=meta["filename"],
        status=QuestionnaireStatus.draft,
        question_count=len(parsed_questions),
        raw_xlsx_blob=store_blob,
        raw_xlsx_key=xlsx_key,
        answer_col_index=ans_col,
        secondary_answer_col_index=ev_col,
        question_col_index=question_col,
        org_id=current_user.org_id,
    )
    db.add(questionnaire)
    db.flush()
    for pq in parsed_questions:
        db.add(Question(
            questionnaire_id=questionnaire.id,
            row_index=pq["row_index"],
            question_text=pq["question"],
            draft_answer=pq["existing_answer"],
            status=QuestionStatus.pending,
        ))
    log_event(db, org_id=current_user.org_id, user_id=current_user.id, user_email=current_user.email,
              action="questionnaire.uploaded", resource_type="questionnaire", resource_id=questionnaire.id,
              detail={"name": questionnaire.name, "question_count": len(parsed_questions)})
    db.commit()
    del _react_upload_tmp[temp_id]
    return {"id": questionnaire.id, "name": questionnaire.name, "question_count": len(parsed_questions)}


# ── knowledge upload ──────────────────────────────────────────────────────────

@router.post("/knowledge/upload")
async def api_knowledge_upload(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    file_bytes = await file.read()
    filename = file.filename or "document"
    ext = Path(filename).suffix.lower().lstrip(".")
    if not file_bytes:
        return JSONResponse({"error": "Uploaded file is empty."}, status_code=400)
    if len(file_bytes) > 20 * 1024 * 1024:
        return JSONResponse({"error": "File too large — maximum size is 20 MB."}, status_code=400)
    if ext not in {"pdf", "docx"}:
        return JSONResponse({"error": f"Unsupported type '.{ext}'. Upload PDF or DOCX."}, status_code=400)
    content_hash = hashlib.sha256(file_bytes).hexdigest()
    existing = db.query(Document).filter(
        Document.content_hash == content_hash,
        Document.org_id == current_user.org_id,
    ).first()
    if existing:
        return JSONResponse({"error": f"Already uploaded as '{existing.filename}'."}, status_code=409)
    try:
        text_content = parse_file(filename, file_bytes)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    if not text_content.strip():
        return JSONResponse({"error": "No text could be extracted. File may be scanned or encrypted."}, status_code=400)
    chunks = chunk_text(text_content)
    if not chunks:
        return JSONResponse({"error": "File contains no meaningful text."}, status_code=400)

    provider = get_embedding_provider()
    embeddings = await provider.embed(chunks)

    doc = Document(
        filename=filename,
        file_type=FileType(ext),
        chunk_count=len(chunks),
        content_hash=content_hash,
        org_id=current_user.org_id,
    )
    db.add(doc)
    db.flush()
    for chunk_val, embedding in zip(chunks, embeddings):
        db.add(KnowledgeChunk(
            document_id=doc.id,
            source_document=filename,
            source_type=SourceType.policy,
            text=chunk_val,
            embedding=embedding,
        ))
    log_event(db, org_id=current_user.org_id, user_id=current_user.id, user_email=current_user.email,
              action="document.uploaded", resource_type="document", resource_id=doc.id,
              detail={"filename": filename, "chunk_count": len(chunks)})
    db.commit()
    return {"id": doc.id, "filename": doc.filename, "file_type": doc.file_type.value, "chunk_count": doc.chunk_count}


# ── questionnaires ────────────────────────────────────────────────────────────

@router.get("/questionnaires")
def api_list_questionnaires(
    page: int = 1,
    per_page: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    per_page = min(per_page, 100)
    offset = (page - 1) * per_page
    base = db.query(Questionnaire).filter(
        Questionnaire.org_id == current_user.org_id,
        Questionnaire.deleted_at == None,
    )
    total = base.count()
    qs = base.order_by(Questionnaire.created_at.desc()).offset(offset).limit(per_page).all()
    return {
        "items": [_qs_json(q) for q in qs],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max(1, -(-total // per_page)),  # ceiling division
    }


@router.get("/questionnaires/{questionnaire_id}")
def api_get_questionnaire(
    questionnaire_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    qs = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id,
        Questionnaire.org_id == current_user.org_id,
        Questionnaire.deleted_at == None,
    ).first()
    if not qs:
        return JSONResponse({"error": "Not found"}, status_code=404)
    questions = (
        db.query(Question)
        .filter(Question.questionnaire_id == questionnaire_id)
        .order_by(Question.row_index)
        .all()
    )
    # Batch-load assignees to avoid N+1
    assignee_ids = {q.assigned_to_id for q in questions if q.assigned_to_id}
    assignees = {u.id: u for u in db.query(User).filter(User.id.in_(assignee_ids)).all()} if assignee_ids else {}

    # Batch-load retrieval scores from question_citations junction table
    question_ids = [q.id for q in questions]
    scores_by_question: dict[int, dict[int, float]] = defaultdict(dict)
    if question_ids:
        rows = db.execute(
            select(
                question_citations.c.question_id,
                question_citations.c.chunk_id,
                question_citations.c.retrieval_score,
            ).where(question_citations.c.question_id.in_(question_ids))
        ).fetchall()
        for row in rows:
            scores_by_question[row.question_id][row.chunk_id] = row.retrieval_score

    # Find which cited chunks come from starter documents (one batch query)
    all_cited_ids = {cid for q in questions for cid in (q.cited_chunk_ids or [])}
    starter_chunk_ids: set[int] = set()
    if all_cited_ids:
        starter_rows = db.execute(
            select(KnowledgeChunk.id)
            .join(Document, KnowledgeChunk.document_id == Document.id)
            .where(KnowledgeChunk.id.in_(all_cited_ids), Document.is_starter == True)
        ).fetchall()
        starter_chunk_ids = {row.id for row in starter_rows}

    return {
        "questionnaire": _qs_json(qs),
        "questions": [
            _q_json(q, assignees.get(q.assigned_to_id), scores_by_question.get(q.id), starter_chunk_ids)
            for q in questions
        ],
    }


@router.post("/questionnaires/{questionnaire_id}/generate")
async def api_generate(
    questionnaire_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    qs = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id,
        Questionnaire.org_id == current_user.org_id,
        Questionnaire.deleted_at == None,
    ).first()
    if not qs:
        return JSONResponse({"error": "Not found"}, status_code=404)

    pending = (
        db.query(Question)
        .filter(Question.questionnaire_id == questionnaire_id, Question.status == QuestionStatus.pending)
        .order_by(Question.row_index)
        .all()
    )
    updated = 0
    for q in pending:
        chunks = await retrieve_relevant_chunks(q.question_text, db, org_id=current_user.org_id)
        if not chunks:
            continue
        result = await generate_answer(q.question_text, chunks)
        q.draft_answer = result.answer
        q.short_answer = result.short_answer
        q.confidence = ConfidenceLevel(result.confidence)
        q.cited_chunk_ids = result.cited_chunk_ids
        q.reasoning = result.reasoning
        q.status = QuestionStatus.generated
        if not q.category:
            q.category = await classify_category(q.question_text)
        _save_citation_scores(db, q.id, chunks, result.cited_chunk_ids)
        log_event(db, org_id=current_user.org_id, user_id=current_user.id, user_email=current_user.email,
                  action="answer.generated", resource_type="question", resource_id=q.id,
                  detail={"questionnaire_id": questionnaire_id, "confidence": result.confidence})
        db.commit()  # save each answer as it completes
        updated += 1
        await asyncio.sleep(6)  # 6s gap = ~10 req/min, within free tier limit

    if qs.status == QuestionnaireStatus.draft:
        qs.status = QuestionnaireStatus.in_progress
    db.commit()
    return {"updated": updated, "status": "ok"}


@router.post("/questionnaires/{questionnaire_id}/questions/{question_id}/regenerate")
async def api_regenerate_question(
    questionnaire_id: int,
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    qs = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id,
        Questionnaire.org_id == current_user.org_id,
        Questionnaire.deleted_at == None,
    ).first()
    if not qs:
        return JSONResponse({"error": "Not found"}, status_code=404)
    q = db.query(Question).filter(
        Question.id == question_id,
        Question.questionnaire_id == questionnaire_id,
    ).first()
    if not q:
        return JSONResponse({"error": "Not found"}, status_code=404)

    chunks = await retrieve_relevant_chunks(q.question_text, db, org_id=current_user.org_id)
    if not chunks:
        return JSONResponse({"error": "No relevant chunks found to generate an answer."}, status_code=400)

    result = await generate_answer(q.question_text, chunks)
    q.draft_answer = result.answer
    q.short_answer = result.short_answer
    q.confidence = ConfidenceLevel(result.confidence)
    q.cited_chunk_ids = result.cited_chunk_ids
    q.reasoning = result.reasoning
    q.status = QuestionStatus.generated
    q.final_answer = None
    if not q.category:
        q.category = await classify_category(q.question_text)

    score_map = _save_citation_scores(db, q.id, chunks, result.cited_chunk_ids)
    log_event(db, org_id=current_user.org_id, user_id=current_user.id, user_email=current_user.email,
              action="answer.generated", resource_type="question", resource_id=q.id,
              detail={"questionnaire_id": questionnaire_id, "confidence": result.confidence, "regen": True})
    db.commit()
    return _q_json(q, chunk_scores=score_map)


@router.post("/questionnaires/{questionnaire_id}/questions/{question_id}/approve")
def api_approve_question(
    questionnaire_id: int,
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    qs = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id,
        Questionnaire.org_id == current_user.org_id,
        Questionnaire.deleted_at == None,
    ).first()
    if not qs:
        return JSONResponse({"error": "Not found"}, status_code=404)
    q = db.query(Question).filter(
        Question.id == question_id,
        Question.questionnaire_id == questionnaire_id,
    ).first()
    if not q:
        return JSONResponse({"error": "Not found"}, status_code=404)

    q.final_answer = q.draft_answer
    q.status = QuestionStatus.approved

    if q.final_answer and q.question_text:
        doc = _get_approved_doc(db, current_user.org_id)
        chunk = KnowledgeChunk(
            document_id=doc.id,
            source_document="Approved Answers",
            source_section=f"Row {q.row_index}",
            source_type=SourceType.approved_answer,
            text=f"Q: {q.question_text}\nA: {q.final_answer}",
        )
        db.add(chunk)
        doc.chunk_count = (doc.chunk_count or 0) + 1

    remaining = db.query(Question).filter(
        Question.questionnaire_id == questionnaire_id,
        Question.status.notin_([QuestionStatus.approved, QuestionStatus.rejected])
    ).count()
    if remaining == 0:
        qs.status = QuestionnaireStatus.complete

    log_event(db, org_id=current_user.org_id, user_id=current_user.id, user_email=current_user.email,
              action="question.approved", resource_type="question", resource_id=q.id,
              detail={"questionnaire_id": questionnaire_id})
    db.commit()
    return _q_json(q)


@router.post("/questionnaires/{questionnaire_id}/questions/{question_id}/reject")
def api_reject_question(
    questionnaire_id: int,
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    qs = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id,
        Questionnaire.org_id == current_user.org_id,
        Questionnaire.deleted_at == None,
    ).first()
    if not qs:
        return JSONResponse({"error": "Not found"}, status_code=404)
    q = db.query(Question).filter(
        Question.id == question_id,
        Question.questionnaire_id == questionnaire_id,
    ).first()
    if not q:
        return JSONResponse({"error": "Not found"}, status_code=404)
    # If previously approved, remove the knowledge chunk so bad answers don't pollute future RAG
    if q.status == QuestionStatus.approved and q.final_answer:
        approved_doc = db.query(Document).filter(
            Document.filename == "Approved Answers",
            Document.org_id == current_user.org_id,
        ).first()
        if approved_doc:
            stale = db.query(KnowledgeChunk).filter(
                KnowledgeChunk.document_id == approved_doc.id,
                KnowledgeChunk.source_type == SourceType.approved_answer,
                KnowledgeChunk.source_section == f"Row {q.row_index}",
            ).all()
            for chunk in stale:
                db.delete(chunk)
            approved_doc.chunk_count = max(0, (approved_doc.chunk_count or 0) - len(stale))

    q.status = QuestionStatus.rejected
    q.final_answer = None
    log_event(db, org_id=current_user.org_id, user_id=current_user.id, user_email=current_user.email,
              action="question.rejected", resource_type="question", resource_id=q.id,
              detail={"questionnaire_id": questionnaire_id})
    db.commit()
    return _q_json(q)


@router.post("/questionnaires/{questionnaire_id}/bulk-approve-high")
def api_bulk_approve_high(
    questionnaire_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    qs = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id,
        Questionnaire.org_id == current_user.org_id,
        Questionnaire.deleted_at == None,
    ).first()
    if not qs:
        return JSONResponse({"error": "Not found"}, status_code=404)
    questions = db.query(Question).filter(
        Question.questionnaire_id == questionnaire_id,
        Question.status == QuestionStatus.generated,
        Question.confidence == ConfidenceLevel.high,
    ).all()
    count = 0
    for q in questions:
        q.final_answer = q.draft_answer
        q.status = QuestionStatus.approved
        if q.final_answer and q.question_text:
            doc = _get_approved_doc(db, current_user.org_id)
            db.add(KnowledgeChunk(
                document_id=doc.id,
                source_document="Approved Answers",
                source_section=f"Row {q.row_index}",
                source_type=SourceType.approved_answer,
                text=f"Q: {q.question_text}\nA: {q.final_answer}",
            ))
            doc.chunk_count = (doc.chunk_count or 0) + 1
        count += 1
    remaining = db.query(Question).filter(
        Question.questionnaire_id == questionnaire_id,
        Question.status.notin_([QuestionStatus.approved, QuestionStatus.rejected])
    ).count()
    if remaining == 0:
        qs.status = QuestionnaireStatus.complete
    log_event(db, org_id=current_user.org_id, user_id=current_user.id, user_email=current_user.email,
              action="question.bulk_approved", resource_type="questionnaire", resource_id=questionnaire_id,
              detail={"count": count})
    db.commit()
    return {"approved": count}


@router.patch("/questionnaires/{questionnaire_id}/questions/{question_id}")
def api_update_question(
    questionnaire_id: int,
    question_id: int,
    draft_answer: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    qs = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id,
        Questionnaire.org_id == current_user.org_id,
        Questionnaire.deleted_at == None,
    ).first()
    if not qs:
        return JSONResponse({"error": "Not found"}, status_code=404)
    q = db.query(Question).filter(
        Question.id == question_id,
        Question.questionnaire_id == questionnaire_id,
    ).first()
    if not q:
        return JSONResponse({"error": "Not found"}, status_code=404)
    q.draft_answer = draft_answer
    log_event(db, org_id=current_user.org_id, user_id=current_user.id, user_email=current_user.email,
              action="question.edited", resource_type="question", resource_id=q.id,
              detail={"questionnaire_id": questionnaire_id})
    db.commit()
    return _q_json(q)


@router.get("/questionnaires/{questionnaire_id}/export")
def api_export_questionnaire(
    questionnaire_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    qs = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id,
        Questionnaire.org_id == current_user.org_id,
        Questionnaire.deleted_at == None,
    ).first()
    if not qs:
        return JSONResponse({"error": "Not found"}, status_code=404)
    xlsx_bytes = export_questionnaire_to_xlsx(questionnaire_id, db)
    log_event(db, org_id=current_user.org_id, user_id=current_user.id, user_email=current_user.email,
              action="questionnaire.exported", resource_type="questionnaire", resource_id=questionnaire_id,
              detail={"name": qs.name})
    db.commit()
    from datetime import date
    safe_name = qs.name.replace(" ", "_").replace("/", "-")
    today = date.today().strftime("%Y-%m-%d")
    filename = f"{safe_name}_filled_{today}.xlsx"
    return StreamingResponse(
        iter([xlsx_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/questionnaires/{questionnaire_id}/delete")
def api_delete_questionnaire(
    questionnaire_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_role(current_user, "owner", "admin")
    qs = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id,
        Questionnaire.org_id == current_user.org_id,
        Questionnaire.deleted_at == None,
    ).first()
    if not qs:
        return JSONResponse({"error": "Not found"}, status_code=404)
    from datetime import datetime, timezone
    qs.deleted_at = datetime.now(timezone.utc)
    log_event(db, org_id=current_user.org_id, user_id=current_user.id, user_email=current_user.email,
              action="questionnaire.deleted", resource_type="questionnaire", resource_id=questionnaire_id,
              detail={"name": qs.name})
    db.commit()
    return {"status": "deleted"}


# ── trash & restore ──────────────────────────────────────────────────────────

@router.get("/trash")
def api_trash(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_role(current_user, "owner", "admin")
    questionnaires = (
        db.query(Questionnaire)
        .filter(Questionnaire.org_id == current_user.org_id, Questionnaire.deleted_at != None)
        .order_by(Questionnaire.deleted_at.desc())
        .all()
    )
    documents = (
        db.query(Document)
        .filter(Document.org_id == current_user.org_id, Document.deleted_at != None)
        .order_by(Document.deleted_at.desc())
        .all()
    )
    return {
        "questionnaires": [
            {"id": q.id, "name": q.name, "deleted_at": q.deleted_at.isoformat(), "question_count": q.question_count}
            for q in questionnaires
        ],
        "documents": [
            {"id": d.id, "filename": d.filename, "deleted_at": d.deleted_at.isoformat(), "chunk_count": d.chunk_count}
            for d in documents
        ],
    }


@router.post("/questionnaires/{questionnaire_id}/restore")
def api_restore_questionnaire(
    questionnaire_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_role(current_user, "owner", "admin")
    qs = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id,
        Questionnaire.org_id == current_user.org_id,
        Questionnaire.deleted_at != None,
    ).first()
    if not qs:
        return JSONResponse({"error": "Not found in trash"}, status_code=404)

    qs.deleted_at = None
    log_event(db, org_id=current_user.org_id, user_id=current_user.id, user_email=current_user.email,
              action="questionnaire.restored", resource_type="questionnaire", resource_id=questionnaire_id,
              detail={"name": qs.name})
    db.commit()

    # Notify the org owner so they can investigate if this was unexpected
    from app.services.jobs import enqueue
    from app.models import Organization
    org = db.query(Organization).filter(Organization.id == current_user.org_id).first()
    owner = db.query(User).filter(User.org_id == current_user.org_id, User.role == "owner").first()
    if owner and owner.email != current_user.email:
        enqueue("send_restore_notification", {
            "owner_email": owner.email,
            "owner_name": owner.full_name or "",
            "item_type": "Questionnaire",
            "item_name": qs.name,
            "restored_by_email": current_user.email,
        })
    return {"status": "restored"}


@router.post("/knowledge/{doc_id}/restore")
def api_restore_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_role(current_user, "owner", "admin")
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.org_id == current_user.org_id,
        Document.deleted_at != None,
    ).first()
    if not doc:
        return JSONResponse({"error": "Not found in trash"}, status_code=404)

    doc.deleted_at = None
    log_event(db, org_id=current_user.org_id, user_id=current_user.id, user_email=current_user.email,
              action="document.restored", resource_type="document", resource_id=doc_id,
              detail={"filename": doc.filename})
    db.commit()

    from app.services.jobs import enqueue
    owner = db.query(User).filter(User.org_id == current_user.org_id, User.role == "owner").first()
    if owner and owner.email != current_user.email:
        enqueue("send_restore_notification", {
            "owner_email": owner.email,
            "owner_name": owner.full_name or "",
            "item_type": "Document",
            "item_name": doc.filename,
            "restored_by_email": current_user.email,
        })
    return {"status": "restored"}


# ── chunks (for source references) ───────────────────────────────────────────

@router.get("/chunks/{chunk_id}")
def api_get_chunk(
    chunk_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chunk = db.query(KnowledgeChunk).filter(KnowledgeChunk.id == chunk_id).first()
    if not chunk:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return {
        "id": chunk.id,
        "text": chunk.text,
        "source_document": chunk.source_document,
        "source_section": chunk.source_section,
        "source_type": chunk.source_type.value,
    }


# ── knowledge base ────────────────────────────────────────────────────────────

@router.get("/knowledge")
def api_list_knowledge(
    page: int = 1,
    per_page: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    per_page = min(per_page, 100)
    offset = (page - 1) * per_page
    base = db.query(Document).filter(
        Document.org_id == current_user.org_id,
        Document.deleted_at == None,
    )
    total = base.count()
    docs = base.order_by(Document.created_at.desc()).offset(offset).limit(per_page).all()
    items = [
        {
            "id": d.id,
            "filename": d.filename,
            "file_type": d.file_type.value,
            "chunk_count": d.chunk_count,
            "created_at": d.created_at.isoformat(),
            "is_starter": d.is_starter,
        }
        for d in docs
    ]
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max(1, -(-total // per_page)),
    }


@router.post("/knowledge/{doc_id}/delete")
def api_delete_knowledge(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_role(current_user, "owner", "admin")
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.org_id == current_user.org_id,
    ).first()
    if not doc:
        return JSONResponse({"error": "Not found"}, status_code=404)
    from datetime import datetime, timezone
    doc.deleted_at = datetime.now(timezone.utc)
    log_event(db, org_id=current_user.org_id, user_id=current_user.id, user_email=current_user.email,
              action="document.deleted", resource_type="document", resource_id=doc_id,
              detail={"filename": doc.filename})
    db.commit()
    return {"status": "deleted"}


# ── answer library ────────────────────────────────────────────────────────────

@router.get("/answers/library")
def api_answer_library(
    q: Optional[str] = "",
    category: Optional[str] = "",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(ApprovedAnswer).filter(
        ApprovedAnswer.org_id == current_user.org_id,
        ApprovedAnswer.status == "active",
    )
    if q:
        like = f"%{q}%"
        query = query.filter(
            (ApprovedAnswer.question_text.ilike(like)) |
            (ApprovedAnswer.answer_text.ilike(like))
        )
    if category:
        query = query.filter(ApprovedAnswer.answer_category == category)
    answers = query.order_by(ApprovedAnswer.times_reused.desc()).all()

    cats = (
        db.query(ApprovedAnswer.answer_category, func.count(ApprovedAnswer.id))
        .filter(
            ApprovedAnswer.org_id == current_user.org_id,
            ApprovedAnswer.answer_category != None,
            ApprovedAnswer.status == "active",
        )
        .group_by(ApprovedAnswer.answer_category)
        .all()
    )

    return {
        "answers": [
            {
                "id": a.id,
                "question_text": a.question_text,
                "answer_text": a.answer_text,
                "answer_category": a.answer_category,
                "times_reused": a.times_reused,
                "created_at": a.created_at.isoformat(),
            }
            for a in answers
        ],
        "categories": [{"name": c, "count": n} for c, n in cats],
        "total": db.query(ApprovedAnswer).filter(ApprovedAnswer.org_id == current_user.org_id, ApprovedAnswer.status == "active").count(),
        "total_reuses": db.query(func.sum(ApprovedAnswer.times_reused)).filter(
            ApprovedAnswer.org_id == current_user.org_id, ApprovedAnswer.status == "active").scalar() or 0,
    }


# ── templates ─────────────────────────────────────────────────────────────────

@router.get("/templates")
def api_list_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ts = db.query(QuestionnaireTemplate).filter(
        QuestionnaireTemplate.org_id == current_user.org_id
    ).order_by(QuestionnaireTemplate.times_used.desc()).all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "customer_name": t.customer_name,
            "question_col": t.question_col,
            "answer_col": t.answer_col,
            "times_used": t.times_used,
            "merged_ranges": len(t.format_config.get("merged_cells", [])) if t.format_config else 0,
            "created_at": t.created_at.isoformat(),
        }
        for t in ts
    ]


@router.post("/templates/{template_id}/delete")
def api_delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_role(current_user, "owner", "admin")
    t = db.query(QuestionnaireTemplate).filter(
        QuestionnaireTemplate.id == template_id,
        QuestionnaireTemplate.org_id == current_user.org_id,
    ).first()
    if not t:
        return JSONResponse({"error": "Not found"}, status_code=404)
    db.delete(t)
    db.commit()
    return {"status": "deleted"}


# ── AI usage ──────────────────────────────────────────────────────────────────

@router.get("/usage")
def api_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    org_id = current_user.org_id

    def month_filter(q):
        return q.filter(
            LLMCall.org_id == org_id,
            func.extract("year", LLMCall.created_at) == now.year,
            func.extract("month", LLMCall.created_at) == now.month,
        )

    month_calls  = month_filter(db.query(LLMCall)).count()
    month_input  = month_filter(db.query(func.sum(LLMCall.input_tokens))).scalar() or 0
    month_output = month_filter(db.query(func.sum(LLMCall.output_tokens))).scalar() or 0
    month_cost   = round(month_filter(db.query(func.sum(LLMCall.cost_estimate))).scalar() or 0.0, 6)

    total_calls  = db.query(LLMCall).filter(LLMCall.org_id == org_id).count()
    total_input  = db.query(func.sum(LLMCall.input_tokens)).filter(LLMCall.org_id == org_id).scalar() or 0
    total_output = db.query(func.sum(LLMCall.output_tokens)).filter(LLMCall.org_id == org_id).scalar() or 0
    total_cost   = round(db.query(func.sum(LLMCall.cost_estimate)).filter(LLMCall.org_id == org_id).scalar() or 0.0, 6)

    per_q_rows = (
        db.query(
            Questionnaire.name,
            func.count(LLMCall.id).label("calls"),
            func.sum(LLMCall.input_tokens).label("input_tokens"),
            func.sum(LLMCall.output_tokens).label("output_tokens"),
            func.sum(LLMCall.cost_estimate).label("cost"),
        )
        .join(LLMCall, LLMCall.questionnaire_id == Questionnaire.id)
        .filter(Questionnaire.org_id == org_id)
        .group_by(Questionnaire.id, Questionnaire.name)
        .all()
    )

    return {
        "month_label": now.strftime("%B %Y"),
        "month_calls": month_calls,
        "month_input": month_input,
        "month_output": month_output,
        "month_cost": month_cost,
        "total_calls": total_calls,
        "total_input": total_input,
        "total_output": total_output,
        "total_cost": total_cost,
        "per_questionnaire": [
            {"name": r.name, "calls": r.calls,
             "input_tokens": r.input_tokens or 0,
             "output_tokens": r.output_tokens or 0,
             "cost": round(r.cost or 0, 6)}
            for r in per_q_rows
        ],
    }


# ── assignment ────────────────────────────────────────────────────────────────

class AssignRequest(BaseModel):
    user_id: int | None  # None = unassign


@router.post("/questionnaires/{questionnaire_id}/questions/{question_id}/assign")
def api_assign_question(
    questionnaire_id: int,
    question_id: int,
    req: AssignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_role(current_user, "owner", "admin")
    qs = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id,
        Questionnaire.org_id == current_user.org_id,
        Questionnaire.deleted_at == None,
    ).first()
    if not qs:
        return JSONResponse({"error": "Not found"}, status_code=404)
    q = db.query(Question).filter(
        Question.id == question_id,
        Question.questionnaire_id == questionnaire_id,
    ).first()
    if not q:
        return JSONResponse({"error": "Not found"}, status_code=404)

    assignee = None
    if req.user_id:
        assignee = db.query(User).filter(
            User.id == req.user_id,
            User.org_id == current_user.org_id,
            User.is_active == True,
        ).first()
        if not assignee:
            return JSONResponse({"error": "User not found"}, status_code=404)

    q.assigned_to_id = req.user_id
    log_event(db, org_id=current_user.org_id, user_id=current_user.id, user_email=current_user.email,
              action="question.assigned", resource_type="question", resource_id=q.id,
              detail={"questionnaire_id": questionnaire_id,
                      "assigned_to": assignee.email if assignee else None})
    db.commit()

    # Fire-and-forget email — don't fail the request if email fails
    if assignee and assignee.id != current_user.id:
        from app.config import get_settings
        url = f"{get_settings().app_url}/questionnaires/{questionnaire_id}"
        try:
            send_question_assigned(
                to_email=assignee.email,
                assignee_name=assignee.full_name or "",
                assignor_name=current_user.full_name or current_user.email,
                questionnaire_name=qs.name,
                question_text=q.question_text,
                questionnaire_url=url,
            )
        except Exception as e:
            print(f"[email] Failed to send assignment notification: {e}")

    return _q_json(q, assignee)


# ── comments ──────────────────────────────────────────────────────────────────

class CommentRequest(BaseModel):
    body: str


@router.get("/questionnaires/{questionnaire_id}/questions/{question_id}/comments")
def api_list_comments(
    questionnaire_id: int,
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    qs = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id,
        Questionnaire.org_id == current_user.org_id,
        Questionnaire.deleted_at == None,
    ).first()
    if not qs:
        return JSONResponse({"error": "Not found"}, status_code=404)
    comments = (
        db.query(QuestionComment)
        .filter(QuestionComment.question_id == question_id,
                QuestionComment.org_id == current_user.org_id)
        .order_by(QuestionComment.created_at.asc())
        .all()
    )
    return [_comment_json(c) for c in comments]


@router.post("/questionnaires/{questionnaire_id}/questions/{question_id}/comments")
def api_post_comment(
    questionnaire_id: int,
    question_id: int,
    req: CommentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not req.body.strip():
        return JSONResponse({"error": "Comment cannot be empty"}, status_code=400)
    qs = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id,
        Questionnaire.org_id == current_user.org_id,
        Questionnaire.deleted_at == None,
    ).first()
    if not qs:
        return JSONResponse({"error": "Not found"}, status_code=404)
    q = db.query(Question).filter(
        Question.id == question_id,
        Question.questionnaire_id == questionnaire_id,
    ).first()
    if not q:
        return JSONResponse({"error": "Not found"}, status_code=404)

    comment = QuestionComment(
        question_id=question_id,
        questionnaire_id=questionnaire_id,
        org_id=current_user.org_id,
        user_id=current_user.id,
        user_email=current_user.email,
        user_name=current_user.full_name or current_user.email,
        body=req.body.strip(),
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return _comment_json(comment)


@router.delete("/questionnaires/{questionnaire_id}/questions/{question_id}/comments/{comment_id}")
def api_delete_comment(
    questionnaire_id: int,
    question_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment = db.query(QuestionComment).filter(
        QuestionComment.id == comment_id,
        QuestionComment.org_id == current_user.org_id,
    ).first()
    if not comment:
        return JSONResponse({"error": "Not found"}, status_code=404)
    # Author can delete their own; owner/admin can delete any
    if comment.user_id != current_user.id and current_user.role not in ("owner", "admin"):
        return JSONResponse({"error": "You can only delete your own comments"}, status_code=403)
    db.delete(comment)
    db.commit()
    return {"status": "deleted"}


# ── my assignments ─────────────────────────────────────────────────────────────

@router.get("/assignments")
def api_my_assignments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    questions = (
        db.query(Question)
        .join(Questionnaire, Questionnaire.id == Question.questionnaire_id)
        .filter(
            Question.assigned_to_id == current_user.id,
            Questionnaire.org_id == current_user.org_id,
            Questionnaire.deleted_at == None,
        )
        .order_by(Question.created_at.desc())
        .all()
    )
    qs_ids = {q.questionnaire_id for q in questions}
    qs_map = {qs.id: qs for qs in db.query(Questionnaire).filter(Questionnaire.id.in_(qs_ids)).all()} if qs_ids else {}

    return [
        {
            **_q_json(q, current_user),
            "questionnaire_id": q.questionnaire_id,
            "questionnaire_name": qs_map[q.questionnaire_id].name if q.questionnaire_id in qs_map else "",
            "customer_name": qs_map[q.questionnaire_id].customer_name if q.questionnaire_id in qs_map else "",
        }
        for q in questions
    ]


# ── KB health / answer confidence analytics ───────────────────────────────────

@router.get("/kb-health")
def api_kb_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services.answer_library import detect_category

    org_id = current_user.org_id

    # Load all generated/approved/rejected questions for this org
    questions = (
        db.query(Question)
        .join(Questionnaire, Questionnaire.id == Question.questionnaire_id)
        .filter(
            Questionnaire.org_id == org_id,
            Question.status.in_([QuestionStatus.generated, QuestionStatus.approved, QuestionStatus.rejected]),
        )
        .all()
    )

    if not questions:
        return {"categories": [], "overall_health": None, "total_questions": 0}

    # Batch-load retrieval scores
    q_ids = [q.id for q in questions]
    score_rows = db.execute(
        select(
            question_citations.c.question_id,
            question_citations.c.chunk_id,
            question_citations.c.retrieval_score,
        ).where(question_citations.c.question_id.in_(q_ids))
    ).fetchall()

    # Best score per question (take the highest scoring source chunk)
    best_score: dict[int, float] = {}
    for row in score_rows:
        if row.retrieval_score is not None:
            cur = best_score.get(row.question_id, 0.0)
            best_score[row.question_id] = max(cur, row.retrieval_score)

    # Group by category
    from collections import defaultdict
    buckets: dict[str, dict] = defaultdict(lambda: {
        "total": 0, "approved": 0, "rejected": 0,
        "low_conf": 0, "no_source": 0, "scores": [],
    })

    for q in questions:
        # Use cached embedding-based category; fall back to keywords for old questions
        cat = q.category or detect_category(q.question_text)
        b = buckets[cat]
        b["total"] += 1
        if q.status == QuestionStatus.approved:
            b["approved"] += 1
        elif q.status == QuestionStatus.rejected:
            b["rejected"] += 1
        if q.confidence and q.confidence.value == "low":
            b["low_conf"] += 1
        score = best_score.get(q.id)
        if score is None:
            b["no_source"] += 1
        else:
            b["scores"].append(score)

    # Build category rows
    _DOC_HINTS = {
        "Data Encryption":     "encryption policy or key management procedure",
        "Access Control":      "access control policy or IAM documentation",
        "Audit & Logging":     "audit logging policy or SIEM documentation",
        "Incident Response":   "incident response plan or playbook",
        "Backup & Recovery":   "backup and disaster recovery policy",
        "Vulnerability Mgmt":  "vulnerability management or patch management policy",
        "Data Privacy":        "privacy policy or GDPR/CCPA documentation",
        "Vendor Risk":         "vendor risk management or third-party policy",
        "Business Continuity": "business continuity plan (BCP)",
        "Physical Security":   "physical security or data centre policy",
        "Network Security":    "network security policy or architecture documentation",
        "General":             "general security policy or documentation",
    }

    rows = []
    for cat, b in buckets.items():
        scores = b["scores"]
        avg_score = round(sum(scores) / len(scores), 3) if scores else None
        strong = sum(1 for s in scores if s >= 0.85)
        coverage_pct = round((strong / b["total"]) * 100) if b["total"] else 0
        rejection_rate = round((b["rejected"] / b["total"]) * 100) if b["total"] else 0

        # Health: blend of avg_score (60%) and approval/rejection signal (40%)
        if avg_score is not None:
            approval_signal = (b["approved"] / b["total"]) if b["total"] else 0
            rejection_signal = 1 - (b["rejected"] / b["total"]) if b["total"] else 1
            health = round(((avg_score * 0.6) + (approval_signal * 0.2) + (rejection_signal * 0.2)) * 100)
        else:
            health = 0

        rows.append({
            "category": cat,
            "total": b["total"],
            "approved": b["approved"],
            "rejected": b["rejected"],
            "low_conf": b["low_conf"],
            "no_source": b["no_source"],
            "avg_score": avg_score,
            "coverage_pct": coverage_pct,
            "rejection_rate": rejection_rate,
            "health": health,
            "upload_hint": _DOC_HINTS.get(cat, "relevant policy documentation"),
        })

    # Sort worst → best so actionable gaps appear first
    rows.sort(key=lambda r: r["health"])

    # Overall health = weighted average by question count
    total_q = sum(r["total"] for r in rows)
    overall = round(sum(r["health"] * r["total"] for r in rows) / total_q) if total_q else None

    return {
        "categories": rows,
        "overall_health": overall,
        "total_questions": total_q,
    }


# ── audit log ─────────────────────────────────────────────────────────────────

@router.get("/audit")
def api_audit_log(
    action: Optional[str] = "",
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(AuditLog).filter(AuditLog.org_id == current_user.org_id)
    if action:
        query = query.filter(AuditLog.action == action)
    events = query.order_by(AuditLog.created_at.desc()).limit(min(limit, 500)).all()
    return [
        {
            "id": e.id,
            "created_at": e.created_at.isoformat(),
            "user_email": e.user_email or "",
            "action": e.action,
            "resource_type": e.resource_type or "",
            "resource_id": e.resource_id,
            "detail": e.detail or {},
        }
        for e in events
    ]
