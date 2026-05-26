"""JSON API router — consumed by the React frontend."""

import asyncio
import hashlib
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from fastapi import Response
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from collections import defaultdict

from app.auth import get_current_user
from app.db import get_db
from app.models import (
    AnswerVersion,
    ApprovedAnswer,
    AuditLog,
    ConfidenceLevel,
    Document,
    FileType,
    Invite,
    KnowledgeChunk,
    LLMCall,
    Notification,
    Workspace,
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
from app.services.answer_library import detect_category, classify_category, check_answer_conflict
from app.services.audit import log_event
from app.services.chunking import hierarchical_chunks
from app.services.embeddings import get_embedding_provider
from app.services.export import export_questionnaire_to_xlsx
from app.services.generation import generate_answer, extract_questions_from_text
from app.services.parsing import (
    parse_file,
    parse_docx,
    parse_pdf,
    parse_xlsx_questionnaire_full,
    parse_xlsx_questionnaire_preview,
)
from app.services.retrieval import retrieve_relevant_chunks, record_positive_feedback, record_negative_feedback
from app.services.sanitize import sanitize_text
from app.services.templates import find_template_by_customer, list_templates
from fastapi import HTTPException as _HTTPException

router = APIRouter(prefix="/api", tags=["api-json"])

_react_upload_tmp: dict[str, dict] = {}


# ── role guard ────────────────────────────────────────────────────────────────

def _require_role(user: User, *roles: str) -> None:
    if user.role not in roles:
        raise _HTTPException(status_code=403, detail="You don't have permission to do this")


# ── helpers ──────────────────────────────────────────────────────────────────

def _confidence_reason(q: Question) -> str | None:
    if q.confidence != ConfidenceLevel.low or q.status.value != "generated":
        return None
    if not (q.cited_chunk_ids or []):
        return (
            "No documents in your knowledge base matched this question. "
            "Visit KB Health to identify topic gaps, or write this answer manually."
        )
    return (
        "The closest matching documents were a weak match — this question may reference "
        "topics not well covered in your current policies. Review carefully before approving."
    )


def _q_json(q: Question, chunk_scores: dict | None = None) -> dict:
    scores = chunk_scores or {}
    cited = [{"id": cid, "score": scores.get(cid)} for cid in (q.cited_chunk_ids or [])]
    return {
        "id": q.id,
        "row_index": q.row_index,
        "question_text": q.question_text,
        "draft_answer": q.draft_answer or "",
        "short_answer": q.short_answer or "",
        "final_answer": q.final_answer or "",
        "status": q.status.value,
        "confidence": q.confidence.value if q.confidence else None,
        "confidence_reason": _confidence_reason(q),
        "cited_chunk_ids": q.cited_chunk_ids or [],
        "cited_chunks": cited,
        "reasoning": q.reasoning or "",
        "no_kb_context": q.status.value == "generated" and not (q.draft_answer or "").strip() and not (q.cited_chunk_ids or []),
        "conflict_warning": q.conflict_warning or None,
        "flag_note": q.flag_note or None,
    }


def _record_version(db: Session, q: Question, user: User, action: str) -> None:
    db.add(AnswerVersion(
        question_id=q.id,
        workspace_id=user.workspace_id,
        user_id=user.id,
        user_email=user.email,
        user_name=user.full_name or "",
        action=action,
        draft_answer=q.draft_answer,
        short_answer=q.short_answer,
    ))


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
        "share_token": q.share_token or None,
    }


def _get_approved_doc(db: Session, workspace_id: int):
    doc = db.query(Document).filter(
        Document.filename == "Approved Answers",
        Document.workspace_id == workspace_id,
    ).first()
    if not doc:
        doc = Document(filename="Approved Answers", file_type=FileType.xlsx, chunk_count=0, workspace_id=workspace_id)
        db.add(doc)
        db.flush()
    return doc


# ── dashboard ────────────────────────────────────────────────────────────────

@router.get("/dashboard")
def api_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace_id = current_user.workspace_id
    total_questionnaires = db.query(Questionnaire).filter(Questionnaire.workspace_id == workspace_id, Questionnaire.deleted_at == None).count()
    answered_statuses = [QuestionStatus.generated, QuestionStatus.approved]
    total_answered = (
        db.query(Question)
        .join(Questionnaire, Questionnaire.id == Question.questionnaire_id)
        .filter(Questionnaire.workspace_id == workspace_id, Question.status.in_(answered_statuses))
        .count()
    )
    total_approved = (
        db.query(Question)
        .join(Questionnaire, Questionnaire.id == Question.questionnaire_id)
        .filter(Questionnaire.workspace_id == workspace_id, Question.status == QuestionStatus.approved)
        .count()
    )

    high = db.query(Question).join(Questionnaire).filter(Questionnaire.workspace_id == workspace_id, Question.confidence == ConfidenceLevel.high).count()
    med  = db.query(Question).join(Questionnaire).filter(Questionnaire.workspace_id == workspace_id, Question.confidence == ConfidenceLevel.medium).count()
    low  = db.query(Question).join(Questionnaire).filter(Questionnaire.workspace_id == workspace_id, Question.confidence == ConfidenceLevel.low).count()
    conf_total = high + med + low
    avg_conf_pct = round(((high * 3 + med * 2 + low) / (conf_total * 3)) * 100) if conf_total else 0
    hours_saved = round(total_answered * 8 / 60, 1)
    total_cost = round(
        db.query(func.sum(LLMCall.cost_estimate)).filter(LLMCall.workspace_id == workspace_id).scalar() or 0.0, 4
    )

    recent = (
        db.query(Questionnaire)
        .filter(Questionnaire.workspace_id == workspace_id, Questionnaire.deleted_at == None)
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
    ext = Path(filename).suffix.lower()
    if not file_bytes:
        return JSONResponse({"error": "Uploaded file is empty."}, status_code=400)
    if len(file_bytes) > 20 * 1024 * 1024:
        return JSONResponse({"error": "File too large — maximum size is 20 MB."}, status_code=400)
    if ext not in (".xlsx", ".docx", ".pdf"):
        return JSONResponse({"error": "Only XLSX, DOCX, and PDF files are supported."}, status_code=400)
    if not name.strip():
        return JSONResponse({"error": "Questionnaire name is required."}, status_code=400)

    temp_id = str(uuid.uuid4())

    if ext == ".xlsx":
        try:
            preview = parse_xlsx_questionnaire_preview(file_bytes)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        _react_upload_tmp[temp_id] = {
            "bytes": file_bytes,
            "filename": filename,
            "name": name.strip(),
            "customer_name": customer_name.strip() or None,
            "workspace_id": current_user.workspace_id,
            "file_type": "xlsx",
        }
        suggested = find_template_by_customer(customer_name.strip() or None, db)
        return {
            "temp_id": temp_id,
            "filename": filename,
            "file_type": "xlsx",
            "preview": preview,
            "suggested_template": {"question_col": suggested.question_col, "answer_col": suggested.answer_col} if suggested else None,
        }

    # DOCX / PDF — extract text then use LLM to identify questions
    try:
        if ext == ".docx":
            text = parse_docx(file_bytes)
        else:
            text = parse_pdf(file_bytes)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    if not text.strip():
        return JSONResponse({"error": "Could not extract any text from this file."}, status_code=400)

    try:
        questions = await extract_questions_from_text(text)
    except Exception as exc:
        return JSONResponse({"error": f"Question extraction failed: {exc}"}, status_code=500)

    if not questions:
        return JSONResponse({"error": "No questions found in this document. Make sure it is a questionnaire."}, status_code=400)

    _react_upload_tmp[temp_id] = {
        "bytes": file_bytes,
        "filename": filename,
        "name": name.strip(),
        "customer_name": customer_name.strip() or None,
        "workspace_id": current_user.workspace_id,
        "file_type": ext.lstrip("."),
        "pre_extracted_questions": questions,
    }
    return {
        "temp_id": temp_id,
        "filename": filename,
        "file_type": ext.lstrip("."),
        "questions": questions,
        "question_count": len(questions),
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
    if meta.get("workspace_id") != current_user.workspace_id:
        return JSONResponse({"error": "Unauthorized."}, status_code=403)

    if meta.get("file_type") in ("docx", "pdf"):
        # Questions already extracted by LLM in the preview step
        raw_questions = meta.get("pre_extracted_questions", [])
        if not raw_questions:
            return JSONResponse({"error": "No questions found. Please upload again."}, status_code=400)
        parsed_questions = [{"row_index": i, "question": q, "existing_answer": None} for i, q in enumerate(raw_questions)]
        ans_col = ev_col = None
    else:
        ans_col = int(answer_col) if answer_col.strip() else None
        ev_col = int(evidence_col) if evidence_col.strip() else None
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
        xlsx_key = f"questionnaires/{current_user.workspace_id}/{uuid.uuid4().hex}.xlsx"
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
        workspace_id=current_user.workspace_id,
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
    log_event(db, workspace_id=current_user.workspace_id, user_id=current_user.id, user_email=current_user.email,
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
        Document.workspace_id == current_user.workspace_id,
    ).first()
    if existing:
        return JSONResponse({"error": f"Already uploaded as '{existing.filename}'."}, status_code=409)

    # Filename collision: same name, different content — likely an updated version
    same_name = db.query(Document).filter(
        Document.filename == filename,
        Document.workspace_id == current_user.workspace_id,
        Document.deleted_at == None,
        Document.is_starter == False,
    ).first()
    if same_name:
        return JSONResponse({
            "error": f"A document named '{filename}' already exists in your knowledge base.",
            "suggest_replace": True,
            "existing_id": same_name.id,
            "existing_filename": same_name.filename,
        }, status_code=409)
    try:
        text_content = parse_file(filename, file_bytes)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    if not text_content.strip():
        return JSONResponse({"error": "No text could be extracted. File may be scanned or encrypted."}, status_code=400)
    text_content = sanitize_text(text_content, source_label=filename)
    h_chunks = hierarchical_chunks(text_content)
    if not h_chunks:
        return JSONResponse({"error": "File contains no meaningful text."}, status_code=400)

    leaf_count = sum(1 for hc in h_chunks if hc.is_leaf)
    doc = Document(
        filename=filename,
        file_type=FileType(ext),
        chunk_count=leaf_count,
        content_hash=content_hash,
        workspace_id=current_user.workspace_id,
    )
    db.add(doc)
    db.flush()

    idx_to_obj: dict[int, KnowledgeChunk] = {}
    for idx, hc in enumerate(h_chunks):
        parent_db_id = (
            idx_to_obj[hc.parent_index].id
            if hc.parent_index is not None and hc.parent_index in idx_to_obj
            else None
        )
        chunk_obj = KnowledgeChunk(
            document_id=doc.id,
            source_document=filename,
            source_type=SourceType.policy,
            text=hc.text,
            is_leaf=hc.is_leaf,
            parent_chunk_id=parent_db_id,
        )
        db.add(chunk_obj)
        db.flush()
        idx_to_obj[idx] = chunk_obj

    context_prefix = f"Document: {filename}\n"
    leaves = [(idx, hc) for idx, hc in enumerate(h_chunks) if hc.is_leaf]
    if leaves:
        prefixed = [context_prefix + hc.text for _, hc in leaves]
        provider = get_embedding_provider()
        embeddings = await provider.embed(prefixed)
        for (idx, _), embedding in zip(leaves, embeddings):
            idx_to_obj[idx].embedding = embedding

    log_event(db, workspace_id=current_user.workspace_id, user_id=current_user.id, user_email=current_user.email,
              action="document.uploaded", resource_type="document", resource_id=doc.id,
              detail={"filename": filename, "chunk_count": leaf_count})
    db.commit()
    return {"id": doc.id, "filename": doc.filename, "file_type": doc.file_type.value, "chunk_count": doc.chunk_count}


@router.post("/knowledge/{doc_id}/replace")
async def api_knowledge_replace(
    doc_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Replace an existing document's content in-place.

    Drops all old chunks (and their feedback signals via CASCADE), re-parses
    and re-embeds the new file, and updates content_updated_at so the
    staleness indicator resets immediately.
    """
    from datetime import datetime, timezone
    _require_role(current_user, "owner", "admin")

    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.workspace_id == current_user.workspace_id,
        Document.deleted_at == None,
    ).first()
    if not doc:
        return JSONResponse({"error": "Document not found."}, status_code=404)

    file_bytes = await file.read()
    filename   = file.filename or doc.filename
    ext        = Path(filename).suffix.lower().lstrip(".")

    if not file_bytes:
        return JSONResponse({"error": "Uploaded file is empty."}, status_code=400)
    if len(file_bytes) > 20 * 1024 * 1024:
        return JSONResponse({"error": "File too large — maximum size is 20 MB."}, status_code=400)
    if ext not in {"pdf", "docx"}:
        return JSONResponse({"error": "Only PDF or DOCX files can be replaced."}, status_code=400)

    content_hash = hashlib.sha256(file_bytes).hexdigest()
    duplicate = db.query(Document).filter(
        Document.content_hash == content_hash,
        Document.id != doc_id,
        Document.workspace_id == current_user.workspace_id,
        Document.deleted_at == None,
    ).first()
    if duplicate:
        return JSONResponse({"error": f"This file is identical to '{duplicate.filename}'."}, status_code=409)

    try:
        text_content = parse_file(filename, file_bytes)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    if not text_content.strip():
        return JSONResponse({"error": "No text could be extracted. File may be scanned or encrypted."}, status_code=400)

    text_content = sanitize_text(text_content, source_label=filename)
    h_chunks = hierarchical_chunks(text_content)
    if not h_chunks:
        return JSONResponse({"error": "File contains no meaningful text."}, status_code=400)

    # Mark approved answers that cited chunks from this document as stale
    old_chunk_ids = [
        r[0] for r in db.query(KnowledgeChunk.id)
        .filter(KnowledgeChunk.document_id == doc_id).all()
    ]
    if old_chunk_ids:
        stale_answers = db.query(ApprovedAnswer).filter(
            ApprovedAnswer.workspace_id == current_user.workspace_id,
            ApprovedAnswer.status == "active",
        ).all()
        for a in stale_answers:
            if a.cited_chunk_ids and any(cid in old_chunk_ids for cid in a.cited_chunk_ids):
                a.is_stale = True

    # Drop old chunks (CASCADE removes ChunkFeedback automatically)
    db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == doc_id).delete(synchronize_session=False)

    leaf_count             = sum(1 for hc in h_chunks if hc.is_leaf)
    doc.filename           = filename
    doc.file_type          = FileType(ext)
    doc.chunk_count        = leaf_count
    doc.content_hash       = content_hash
    doc.content_updated_at = datetime.now(timezone.utc)
    db.flush()

    idx_to_obj: dict[int, KnowledgeChunk] = {}
    for idx, hc in enumerate(h_chunks):
        parent_db_id = (
            idx_to_obj[hc.parent_index].id
            if hc.parent_index is not None and hc.parent_index in idx_to_obj
            else None
        )
        chunk_obj = KnowledgeChunk(
            document_id=doc.id,
            source_document=filename,
            source_type=SourceType.policy,
            text=hc.text,
            is_leaf=hc.is_leaf,
            parent_chunk_id=parent_db_id,
        )
        db.add(chunk_obj)
        db.flush()
        idx_to_obj[idx] = chunk_obj

    context_prefix = f"Document: {filename}\n"
    leaves = [(idx, hc) for idx, hc in enumerate(h_chunks) if hc.is_leaf]
    if leaves:
        prefixed   = [context_prefix + hc.text for _, hc in leaves]
        provider   = get_embedding_provider()
        embeddings = await provider.embed(prefixed)
        for (idx, _), embedding in zip(leaves, embeddings):
            idx_to_obj[idx].embedding = embedding

    log_event(db, workspace_id=current_user.workspace_id, user_id=current_user.id, user_email=current_user.email,
              action="document.replaced", resource_type="document", resource_id=doc_id,
              detail={"filename": filename, "chunk_count": leaf_count})
    db.commit()
    return {"id": doc.id, "filename": doc.filename, "file_type": doc.file_type.value, "chunk_count": doc.chunk_count}


# ── questionnaires ────────────────────────────────────────────────────────────

@router.get("/questionnaires/clients")
def api_list_clients(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return distinct non-null customer names used in this workspace, for autocomplete."""
    rows = (
        db.query(Questionnaire.customer_name)
        .filter(
            Questionnaire.workspace_id == current_user.workspace_id,
            Questionnaire.customer_name != None,
            Questionnaire.customer_name != "",
            Questionnaire.deleted_at == None,
        )
        .distinct()
        .order_by(Questionnaire.customer_name)
        .all()
    )
    return [r.customer_name for r in rows]


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
        Questionnaire.workspace_id == current_user.workspace_id,
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
        Questionnaire.workspace_id == current_user.workspace_id,
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

    return {
        "questionnaire": _qs_json(qs),
        "questions": [
            _q_json(q, scores_by_question.get(q.id))
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
        Questionnaire.workspace_id == current_user.workspace_id,
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
    conflict_count = 0
    for q in pending:
        try:
            chunks = await retrieve_relevant_chunks(q.question_text, db, workspace_id=current_user.workspace_id, customer_name=qs.customer_name)
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
            log_event(db, workspace_id=current_user.workspace_id, user_id=current_user.id, user_email=current_user.email,
                      action="answer.generated", resource_type="question", resource_id=q.id,
                      detail={"questionnaire_id": questionnaire_id, "confidence": result.confidence})
            db.commit()
            updated += 1
        except Exception as exc:
            db.rollback()
            print(f"[generate] Failed on question {q.id}: {exc}")
            await asyncio.sleep(6)
            continue

        # Conflict check runs in its own transaction after the answer is safely committed
        try:
            warning = await check_answer_conflict(
                q.question_text, result.short_answer or "", db, current_user.workspace_id
            )
            if warning:
                q.conflict_warning = warning
                conflict_count += 1
                db.commit()
        except Exception:
            db.rollback()
        await asyncio.sleep(6)  # 6s gap = ~10 req/min, within free tier limit

    if qs.status == QuestionnaireStatus.draft:
        qs.status = QuestionnaireStatus.in_progress

    # In-app notification for the user who triggered generation
    db.add(Notification(
        workspace_id=current_user.workspace_id,
        user_id=current_user.id,
        type="generation_complete",
        title=f"Drafts ready — {qs.name}",
        body=f"{updated} answer{'s' if updated != 1 else ''} drafted."
             + (f" {conflict_count} conflict{'s' if conflict_count != 1 else ''} flagged." if conflict_count else ""),
        resource_type="questionnaire",
        resource_id=questionnaire_id,
    ))
    db.commit()

    # Email notification (best-effort)
    try:
        from app.services.email import send_generation_complete
        from app.config import get_settings
        settings = get_settings()
        url = f"{settings.app_url}/questionnaires/{questionnaire_id}"
        send_generation_complete(
            to_email=current_user.email,
            user_name=current_user.full_name or "",
            questionnaire_name=qs.name,
            total=updated,
            conflicts=conflict_count,
            questionnaire_url=url,
        )
    except Exception:
        pass

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
        Questionnaire.workspace_id == current_user.workspace_id,
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

    chunks = await retrieve_relevant_chunks(q.question_text, db, workspace_id=current_user.workspace_id, customer_name=qs.customer_name)
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
    # Negative feedback: reviewer asked for a regen — previous chunks were insufficient
    record_negative_feedback(q.cited_chunk_ids or [], current_user.workspace_id, db)
    log_event(db, workspace_id=current_user.workspace_id, user_id=current_user.id, user_email=current_user.email,
              action="answer.generated", resource_type="question", resource_id=q.id,
              detail={"questionnaire_id": questionnaire_id, "confidence": result.confidence, "regen": True})
    db.commit()
    return _q_json(q, chunk_scores=score_map)


@router.post("/questionnaires/{questionnaire_id}/questions/{question_id}/approve")
async def api_approve_question(
    questionnaire_id: int,
    question_id: int,
    make_generic: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    qs = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id,
        Questionnaire.workspace_id == current_user.workspace_id,
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
    q.conflict_warning = None
    _record_version(db, q, current_user, "approved")

    if q.final_answer and q.question_text:
        doc = _get_approved_doc(db, current_user.workspace_id)
        chunk_text_val = f"Q: {q.question_text}\nA: {q.final_answer}"
        chunk = KnowledgeChunk(
            document_id=doc.id,
            source_document="Approved Answers",
            source_section=f"Row {q.row_index}",
            source_type=SourceType.approved_answer,
            text=chunk_text_val,
            customer_name=None if make_generic else qs.customer_name,
        )
        db.add(chunk)
        db.flush()
        # Embed with context prefix for better retrieval
        try:
            from app.services.embeddings import get_embedding_provider as _get_emb
            _emb_provider = _get_emb()
            _ctx = f"Document: Approved Answers\n{chunk_text_val}"
            _embs = await _emb_provider.embed([_ctx])
            chunk.embedding = _embs[0]
        except Exception:
            pass
        doc.chunk_count = (doc.chunk_count or 0) + 1

        # Positive feedback: cited chunks that led to an approved answer were useful
        record_positive_feedback(q.cited_chunk_ids or [], current_user.workspace_id, db)

        # Save to answer library so future questionnaires can match against it
        try:
            from app.services.embeddings import get_embedding_provider
            provider = get_embedding_provider()
            embs = await provider.embed([q.question_text], input_type="query")
            conf_map = {"high": 0.9, "medium": 0.6, "low": 0.3}
            conf_score = conf_map.get(q.confidence.value if q.confidence else "low", 0.3)
            existing = db.query(ApprovedAnswer).filter(
                ApprovedAnswer.source_question_id == q.id
            ).first()
            _client_tag = None if make_generic else qs.customer_name
            if existing:
                existing.answer_text = q.final_answer
                existing.short_answer = q.short_answer
                existing.cited_chunk_ids = q.cited_chunk_ids
                existing.confidence_score = conf_score
                existing.embedding = embs[0]
                existing.status = "active"
                existing.customer_name = _client_tag
            else:
                db.add(ApprovedAnswer(
                    question_text=q.question_text,
                    answer_text=q.final_answer,
                    short_answer=q.short_answer,
                    answer_category=detect_category(q.question_text),
                    cited_chunk_ids=q.cited_chunk_ids,
                    confidence_score=conf_score,
                    embedding=embs[0],
                    source_question_id=q.id,
                    workspace_id=current_user.workspace_id,
                    customer_name=_client_tag,
                ))
        except Exception:
            pass  # library write failure must not break approval

    remaining = db.query(Question).filter(
        Question.questionnaire_id == questionnaire_id,
        Question.status.notin_([QuestionStatus.approved, QuestionStatus.rejected])
    ).count()
    if remaining == 0:
        qs.status = QuestionnaireStatus.complete

    log_event(db, workspace_id=current_user.workspace_id, user_id=current_user.id, user_email=current_user.email,
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
        Questionnaire.workspace_id == current_user.workspace_id,
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
    # If previously approved, remove the knowledge chunk and archive the answer library entry
    if q.status == QuestionStatus.approved and q.final_answer:
        approved_doc = db.query(Document).filter(
            Document.filename == "Approved Answers",
            Document.workspace_id == current_user.workspace_id,
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

        stale_aa = db.query(ApprovedAnswer).filter(
            ApprovedAnswer.source_question_id == q.id,
        ).first()
        if stale_aa:
            stale_aa.status = "archived"

    q.status = QuestionStatus.rejected
    q.final_answer = None
    _record_version(db, q, current_user, "rejected")
    # Negative feedback: cited chunks that led to a rejected answer were unhelpful
    record_negative_feedback(q.cited_chunk_ids or [], current_user.workspace_id, db)
    log_event(db, workspace_id=current_user.workspace_id, user_id=current_user.id, user_email=current_user.email,
              action="question.rejected", resource_type="question", resource_id=q.id,
              detail={"questionnaire_id": questionnaire_id})
    db.commit()
    return _q_json(q)


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
        Questionnaire.workspace_id == current_user.workspace_id,
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
    if draft_answer != (q.draft_answer or ""):
        q.draft_answer = draft_answer
        _record_version(db, q, current_user, "edited")
    log_event(db, workspace_id=current_user.workspace_id, user_id=current_user.id, user_email=current_user.email,
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
        Questionnaire.workspace_id == current_user.workspace_id,
        Questionnaire.deleted_at == None,
    ).first()
    if not qs:
        return JSONResponse({"error": "Not found"}, status_code=404)
    workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
    white_label = bool(workspace and workspace.white_label_export)
    file_bytes, file_ext = export_questionnaire_to_xlsx(questionnaire_id, db, white_label=white_label)
    log_event(db, workspace_id=current_user.workspace_id, user_id=current_user.id, user_email=current_user.email,
              action="questionnaire.exported", resource_type="questionnaire", resource_id=questionnaire_id,
              detail={"name": qs.name})
    db.commit()
    from datetime import date
    safe_name = qs.name.replace(" ", "_").replace("/", "-")
    today = date.today().strftime("%Y-%m-%d")
    filename = f"{safe_name}_filled_{today}.{file_ext}"
    media_type = (
        "application/vnd.ms-excel.sheet.macroEnabled.12"
        if file_ext == "xlsm"
        else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    return StreamingResponse(
        iter([file_bytes]),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


class ReassignBody(BaseModel):
    customer_name: str


@router.patch("/questionnaires/{questionnaire_id}/reassign")
def api_reassign_questionnaire(
    questionnaire_id: int,
    body: ReassignBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_role(current_user, "owner", "admin")
    qs = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id,
        Questionnaire.workspace_id == current_user.workspace_id,
        Questionnaire.deleted_at == None,
    ).first()
    if not qs:
        return JSONResponse({"error": "Not found"}, status_code=404)

    old_name = qs.customer_name
    new_name = body.customer_name.strip() or None

    if old_name == new_name:
        return _qs_json(qs)

    qs.customer_name = new_name

    # Re-tag approved answers that were tagged to the old client (not generic ones)
    question_ids = [q.id for q in db.query(Question.id).filter(
        Question.questionnaire_id == questionnaire_id
    ).all()]

    if question_ids:
        affected_answers = db.query(ApprovedAnswer).filter(
            ApprovedAnswer.source_question_id.in_(question_ids),
            ApprovedAnswer.customer_name == old_name,
        ).all()

        for answer in affected_answers:
            answer.customer_name = new_name
            # Re-tag the corresponding KnowledgeChunk via row_index
            if answer.source_question_id:
                row_idx = db.query(Question.row_index).filter(
                    Question.id == answer.source_question_id
                ).scalar()
                if row_idx is not None:
                    db.query(KnowledgeChunk).filter(
                        KnowledgeChunk.source_type == SourceType.approved_answer,
                        KnowledgeChunk.source_section == f"Row {row_idx}",
                        KnowledgeChunk.customer_name == old_name,
                    ).update({"customer_name": new_name}, synchronize_session=False)

    log_audit(db, current_user, "reassign_questionnaire", "questionnaire", questionnaire_id,
              {"old_customer_name": old_name, "new_customer_name": new_name})
    db.commit()
    return _qs_json(qs)


@router.post("/questionnaires/{questionnaire_id}/delete")
def api_delete_questionnaire(
    questionnaire_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_role(current_user, "owner", "admin")
    qs = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id,
        Questionnaire.workspace_id == current_user.workspace_id,
        Questionnaire.deleted_at == None,
    ).first()
    if not qs:
        return JSONResponse({"error": "Not found"}, status_code=404)
    from datetime import datetime, timezone
    qs.deleted_at = datetime.now(timezone.utc)
    log_event(db, workspace_id=current_user.workspace_id, user_id=current_user.id, user_email=current_user.email,
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
        .filter(Questionnaire.workspace_id == current_user.workspace_id, Questionnaire.deleted_at != None)
        .order_by(Questionnaire.deleted_at.desc())
        .all()
    )
    documents = (
        db.query(Document)
        .filter(Document.workspace_id == current_user.workspace_id, Document.deleted_at != None)
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
        Questionnaire.workspace_id == current_user.workspace_id,
        Questionnaire.deleted_at != None,
    ).first()
    if not qs:
        return JSONResponse({"error": "Not found in trash"}, status_code=404)

    qs.deleted_at = None
    log_event(db, workspace_id=current_user.workspace_id, user_id=current_user.id, user_email=current_user.email,
              action="questionnaire.restored", resource_type="questionnaire", resource_id=questionnaire_id,
              detail={"name": qs.name})
    db.commit()

    # Notify the workspace owner so they can investigate if this was unexpected
    from app.services.jobs import enqueue
    workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
    owner = db.query(User).filter(User.workspace_id == current_user.workspace_id, User.role == "owner").first()
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
        Document.workspace_id == current_user.workspace_id,
        Document.deleted_at != None,
    ).first()
    if not doc:
        return JSONResponse({"error": "Not found in trash"}, status_code=404)

    doc.deleted_at = None
    log_event(db, workspace_id=current_user.workspace_id, user_id=current_user.id, user_email=current_user.email,
              action="document.restored", resource_type="document", resource_id=doc_id,
              detail={"filename": doc.filename})
    db.commit()

    from app.services.jobs import enqueue
    owner = db.query(User).filter(User.workspace_id == current_user.workspace_id, User.role == "owner").first()
    if owner and owner.email != current_user.email:
        enqueue("send_restore_notification", {
            "owner_email": owner.email,
            "owner_name": owner.full_name or "",
            "item_type": "Document",
            "item_name": doc.filename,
            "restored_by_email": current_user.email,
        })
    return {"status": "restored"}


@router.post("/questionnaires/{questionnaire_id}/purge")
def api_purge_questionnaire(
    questionnaire_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_role(current_user, "owner")
    qs = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id,
        Questionnaire.workspace_id == current_user.workspace_id,
        Questionnaire.deleted_at != None,
    ).first()
    if not qs:
        return JSONResponse({"error": "Not found in trash"}, status_code=404)
    name = qs.name
    question_ids = [q.id for q in db.query(Question.id).filter(Question.questionnaire_id == questionnaire_id).all()]
    if question_ids:
        db.query(ApprovedAnswer).filter(ApprovedAnswer.source_question_id.in_(question_ids)).update(
            {ApprovedAnswer.source_question_id: None}, synchronize_session=False
        )
        db.execute(question_citations.delete().where(question_citations.c.question_id.in_(question_ids)))
        db.query(QuestionComment).filter(QuestionComment.question_id.in_(question_ids)).delete(synchronize_session=False)
        db.query(LLMCall).filter(LLMCall.question_id.in_(question_ids)).delete(synchronize_session=False)
        db.query(Question).filter(Question.questionnaire_id == questionnaire_id).delete(synchronize_session=False)
    db.delete(qs)
    log_event(db, workspace_id=current_user.workspace_id, user_id=current_user.id, user_email=current_user.email,
              action="questionnaire.purged", resource_type="questionnaire", resource_id=questionnaire_id,
              detail={"name": name})
    db.commit()
    return {"status": "purged"}


@router.post("/knowledge/{doc_id}/purge")
def api_purge_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_role(current_user, "owner")
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.workspace_id == current_user.workspace_id,
        Document.deleted_at != None,
    ).first()
    if not doc:
        return JSONResponse({"error": "Not found in trash"}, status_code=404)
    filename = doc.filename
    db.delete(doc)
    log_event(db, workspace_id=current_user.workspace_id, user_id=current_user.id, user_email=current_user.email,
              action="document.purged", resource_type="document", resource_id=doc_id,
              detail={"filename": filename})
    db.commit()
    return {"status": "purged"}


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
        "document_uploaded_at": chunk.document.created_at.isoformat() if chunk.document else None,
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
        Document.workspace_id == current_user.workspace_id,
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
            "content_updated_at": d.content_updated_at.isoformat() if d.content_updated_at else d.created_at.isoformat(),
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
        Document.workspace_id == current_user.workspace_id,
    ).first()
    if not doc:
        return JSONResponse({"error": "Not found"}, status_code=404)
    from datetime import datetime, timezone

    # Mark approved answers that cited chunks from this document as stale
    chunk_ids = [
        r[0] for r in db.query(KnowledgeChunk.id)
        .filter(KnowledgeChunk.document_id == doc_id).all()
    ]
    if chunk_ids:
        stale_answers = db.query(ApprovedAnswer).filter(
            ApprovedAnswer.workspace_id == current_user.workspace_id,
            ApprovedAnswer.status == "active",
        ).all()
        for a in stale_answers:
            if a.cited_chunk_ids and any(cid in chunk_ids for cid in a.cited_chunk_ids):
                a.is_stale = True

    doc.deleted_at = datetime.now(timezone.utc)
    log_event(db, workspace_id=current_user.workspace_id, user_id=current_user.id, user_email=current_user.email,
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
        ApprovedAnswer.workspace_id == current_user.workspace_id,
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
            ApprovedAnswer.workspace_id == current_user.workspace_id,
            ApprovedAnswer.answer_category != None,
            ApprovedAnswer.status == "active",
        )
        .group_by(ApprovedAnswer.answer_category)
        .all()
    )

    # Bulk-load source questionnaire info via source_question_id
    question_ids = [a.source_question_id for a in answers if a.source_question_id]
    qs_by_question: dict[int, Questionnaire] = {}
    if question_ids:
        rows = (
            db.query(Question.id, Questionnaire.id, Questionnaire.name, Questionnaire.customer_name)
            .join(Questionnaire, Question.questionnaire_id == Questionnaire.id)
            .filter(Question.id.in_(question_ids))
            .all()
        )
        for q_id, qs_id, qs_name, qs_customer in rows:
            qs_by_question[q_id] = {"id": qs_id, "name": qs_name, "customer_name": qs_customer}

    def _answer_json(a: ApprovedAnswer) -> dict:
        src = qs_by_question.get(a.source_question_id) if a.source_question_id else None
        return {
            "id": a.id,
            "question_text": a.question_text,
            "answer_text": a.answer_text,
            "answer_category": a.answer_category,
            "times_reused": a.times_reused,
            "created_at": a.created_at.isoformat(),
            "source_questionnaire_id": src["id"] if src else None,
            "source_questionnaire_name": src["name"] if src else None,
            "source_customer_name": src["customer_name"] if src else None,
            "is_stale": bool(a.is_stale),
            "customer_name": a.customer_name,
        }

    return {
        "answers": [_answer_json(a) for a in answers],
        "categories": [{"name": c, "count": n} for c, n in cats],
        "total": db.query(ApprovedAnswer).filter(ApprovedAnswer.workspace_id == current_user.workspace_id, ApprovedAnswer.status == "active").count(),
        "total_reuses": db.query(func.sum(ApprovedAnswer.times_reused)).filter(
            ApprovedAnswer.workspace_id == current_user.workspace_id, ApprovedAnswer.status == "active").scalar() or 0,
    }


@router.post("/answers/library/{answer_id}/mark-fresh")
def api_mark_answer_fresh(
    answer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    answer = db.query(ApprovedAnswer).filter(
        ApprovedAnswer.id == answer_id,
        ApprovedAnswer.workspace_id == current_user.workspace_id,
    ).first()
    if not answer:
        return JSONResponse({"error": "Not found"}, status_code=404)
    answer.is_stale = False
    db.commit()
    return {"status": "ok"}


@router.post("/answers/library/{answer_id}/make-generic")
def api_make_answer_generic(
    answer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    answer = db.query(ApprovedAnswer).filter(
        ApprovedAnswer.id == answer_id,
        ApprovedAnswer.workspace_id == current_user.workspace_id,
    ).first()
    if not answer:
        return JSONResponse({"error": "Not found"}, status_code=404)
    answer.customer_name = None
    # Also clear customer_name on the corresponding KnowledgeChunk
    if answer.source_question_id:
        db.query(KnowledgeChunk).filter(
            KnowledgeChunk.source_type == SourceType.approved_answer,
            KnowledgeChunk.source_section == f"Row {db.query(Question.row_index).filter(Question.id == answer.source_question_id).scalar()}",
            KnowledgeChunk.customer_name != None,
        ).update({"customer_name": None}, synchronize_session=False)
    db.commit()
    return {"status": "ok"}


@router.post("/answers/library/{answer_id}/archive")
def api_archive_answer(
    answer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    answer = db.query(ApprovedAnswer).filter(
        ApprovedAnswer.id == answer_id,
        ApprovedAnswer.workspace_id == current_user.workspace_id,
    ).first()
    if not answer:
        return JSONResponse({"error": "Not found"}, status_code=404)
    answer.status = "archived"

    # Also remove the corresponding knowledge chunk so it no longer pollutes RAG
    if answer.source_question_id is not None:
        approved_doc = db.query(Document).filter(
            Document.filename == "Approved Answers",
            Document.workspace_id == current_user.workspace_id,
        ).first()
        if approved_doc:
            source_q = db.query(Question).filter(Question.id == answer.source_question_id).first()
            if source_q:
                stale = db.query(KnowledgeChunk).filter(
                    KnowledgeChunk.document_id == approved_doc.id,
                    KnowledgeChunk.source_type == SourceType.approved_answer,
                    KnowledgeChunk.source_section == f"Row {source_q.row_index}",
                ).all()
                for chunk in stale:
                    db.delete(chunk)
                approved_doc.chunk_count = max(0, (approved_doc.chunk_count or 0) - len(stale))

    log_event(db, workspace_id=current_user.workspace_id, user_id=current_user.id, user_email=current_user.email,
              action="answer.archived", resource_type="approved_answer", resource_id=answer_id,
              detail={"question_text": answer.question_text[:120]})
    db.commit()
    return {"status": "ok"}


# ── templates ─────────────────────────────────────────────────────────────────

@router.get("/templates")
def api_list_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ts = db.query(QuestionnaireTemplate).filter(
        QuestionnaireTemplate.workspace_id == current_user.workspace_id
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
        QuestionnaireTemplate.workspace_id == current_user.workspace_id,
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
    workspace_id = current_user.workspace_id

    def month_filter(q):
        return q.filter(
            LLMCall.workspace_id == workspace_id,
            func.extract("year", LLMCall.created_at) == now.year,
            func.extract("month", LLMCall.created_at) == now.month,
        )

    month_calls  = month_filter(db.query(LLMCall)).count()
    month_input  = month_filter(db.query(func.sum(LLMCall.input_tokens))).scalar() or 0
    month_output = month_filter(db.query(func.sum(LLMCall.output_tokens))).scalar() or 0
    month_cost   = round(month_filter(db.query(func.sum(LLMCall.cost_estimate))).scalar() or 0.0, 6)

    total_calls  = db.query(LLMCall).filter(LLMCall.workspace_id == workspace_id).count()
    total_input  = db.query(func.sum(LLMCall.input_tokens)).filter(LLMCall.workspace_id == workspace_id).scalar() or 0
    total_output = db.query(func.sum(LLMCall.output_tokens)).filter(LLMCall.workspace_id == workspace_id).scalar() or 0
    total_cost   = round(db.query(func.sum(LLMCall.cost_estimate)).filter(LLMCall.workspace_id == workspace_id).scalar() or 0.0, 6)

    per_q_rows = (
        db.query(
            Questionnaire.name,
            func.count(LLMCall.id).label("calls"),
            func.sum(LLMCall.input_tokens).label("input_tokens"),
            func.sum(LLMCall.output_tokens).label("output_tokens"),
            func.sum(LLMCall.cost_estimate).label("cost"),
        )
        .join(LLMCall, LLMCall.questionnaire_id == Questionnaire.id)
        .filter(Questionnaire.workspace_id == workspace_id)
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


# ── flag + note ───────────────────────────────────────────────────────────────

class FlagRequest(BaseModel):
    note: str | None  # None or empty string = clear flag


@router.patch("/questionnaires/{questionnaire_id}/questions/{question_id}/flag")
def api_flag_question(
    questionnaire_id: int,
    question_id: int,
    req: FlagRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    qs = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id,
        Questionnaire.workspace_id == current_user.workspace_id,
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

    q.flag_note = req.note.strip() if req.note and req.note.strip() else None
    db.commit()
    return _q_json(q)


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
        Questionnaire.workspace_id == current_user.workspace_id,
        Questionnaire.deleted_at == None,
    ).first()
    if not qs:
        return JSONResponse({"error": "Not found"}, status_code=404)
    comments = (
        db.query(QuestionComment)
        .filter(QuestionComment.question_id == question_id,
                QuestionComment.workspace_id == current_user.workspace_id)
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
        Questionnaire.workspace_id == current_user.workspace_id,
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
        workspace_id=current_user.workspace_id,
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
        QuestionComment.workspace_id == current_user.workspace_id,
    ).first()
    if not comment:
        return JSONResponse({"error": "Not found"}, status_code=404)
    # Author can delete their own; owner/admin can delete any
    if comment.user_id != current_user.id and current_user.role not in ("owner", "admin"):
        return JSONResponse({"error": "You can only delete your own comments"}, status_code=403)
    db.delete(comment)
    db.commit()
    return {"status": "deleted"}


# ── KB health / answer confidence analytics ───────────────────────────────────

@router.get("/kb-health")
def api_kb_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services.answer_library import detect_category

    workspace_id = current_user.workspace_id

    # Load all generated/approved/rejected questions for this org
    questions = (
        db.query(Question)
        .join(Questionnaire, Questionnaire.id == Question.questionnaire_id)
        .filter(
            Questionnaire.workspace_id == workspace_id,
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


# ── RAG evaluation ────────────────────────────────────────────────────────────

@router.get("/admin/rag-eval")
async def api_rag_eval(
    top_k: int = 8,
    sample_size: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_role(current_user, "owner", "admin")
    from app.services.evaluation import evaluate_retrieval
    report = await evaluate_retrieval(
        workspace_id=current_user.workspace_id,
        db=db,
        top_k=top_k,
        sample_size=sample_size,
    )
    return {
        "questions_evaluated": report.questions_evaluated,
        "coverage":            report.coverage,
        "hit_rate_at_k":       report.hit_rate_at_k,
        "precision_at_1":      report.precision_at_1,
        "mrr":                 report.mrr,
        "avg_top1_similarity": report.avg_top1_similarity,
        "top_k":               report.top_k,
        "warnings":            report.warnings,
        "interpretation": {
            "hit_rate_at_k":   f"% of questions where ≥1 correct chunk in top {top_k}",
            "precision_at_1":  "% of questions where top-1 result is correct",
            "mrr":             "Mean Reciprocal Rank (1.0 = perfect, 0.0 = never in top-k)",
            "avg_similarity":  "Average vector similarity of top-1 result (higher = better)",
        },
    }


# ── audit log ─────────────────────────────────────────────────────────────────

@router.get("/audit")
def api_audit_log(
    action: Optional[str] = "",
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(AuditLog).filter(AuditLog.workspace_id == current_user.workspace_id)
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


# ── Notifications ─────────────────────────────────────────────────────────────

def _notif_json(n: Notification) -> dict:
    return {
        "id": n.id,
        "type": n.type,
        "title": n.title,
        "body": n.body or "",
        "read": n.read,
        "resource_type": n.resource_type,
        "resource_id": n.resource_id,
        "created_at": n.created_at.isoformat(),
    }


@router.get("/notifications")
def api_list_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notifs = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(30)
        .all()
    )
    unread = sum(1 for n in notifs if not n.read)
    return {"notifications": [_notif_json(n) for n in notifs], "unread": unread}


@router.post("/notifications/{notification_id}/read")
def api_mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    n = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    ).first()
    if n:
        n.read = True
        db.commit()
    return {"status": "ok"}


@router.post("/notifications/read-all")
def api_mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.read == False,
    ).update({"read": True}, synchronize_session=False)
    db.commit()
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Share progress link
# ---------------------------------------------------------------------------

@router.post("/questionnaires/{questionnaire_id}/share-token")
def api_get_share_token(
    questionnaire_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    qs = db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id,
        Questionnaire.workspace_id == current_user.workspace_id,
        Questionnaire.deleted_at == None,
    ).first()
    if not qs:
        return JSONResponse({"error": "Not found"}, status_code=404)
    if not qs.share_token:
        import secrets
        qs.share_token = secrets.token_urlsafe(32)
        db.commit()
    return {"token": qs.share_token}


@router.get("/share/{token}")
def api_public_share(token: str, db: Session = Depends(get_db)):
    qs = db.query(Questionnaire).filter(
        Questionnaire.share_token == token,
        Questionnaire.deleted_at == None,
    ).first()
    if not qs:
        return JSONResponse({"error": "Not found"}, status_code=404)
    questions = (
        db.query(Question)
        .filter(Question.questionnaire_id == qs.id)
        .order_by(Question.row_index)
        .all()
    )
    total    = len(questions)
    approved = sum(1 for q in questions if q.status == QuestionStatus.approved)
    rejected = sum(1 for q in questions if q.status == QuestionStatus.rejected)
    pending  = sum(1 for q in questions if q.status in (QuestionStatus.pending, QuestionStatus.generated))
    pct      = round((approved / total) * 100) if total else 0
    return {
        "name": qs.name,
        "customer_name": qs.customer_name or "",
        "created_at": qs.created_at.isoformat(),
        "total": total,
        "approved": approved,
        "rejected": rejected,
        "pending": pending,
        "pct": pct,
        "questions": [
            {
                "id": q.id,
                "index": i + 1,
                "question_text": q.question_text,
                "answer": q.final_answer or q.draft_answer or "",
                "short_answer": q.short_answer or "",
                "status": q.status.value,
                "confidence": q.confidence.value if q.confidence else "",
            }
            for i, q in enumerate(questions)
        ],
    }


# ---------------------------------------------------------------------------
# Answer version history
# ---------------------------------------------------------------------------

@router.get("/questionnaires/{questionnaire_id}/questions/{question_id}/history")
def api_question_history(
    questionnaire_id: int,
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Question).filter(
        Question.id == question_id,
        Question.questionnaire_id == questionnaire_id,
    ).first()
    if not q:
        return JSONResponse({"error": "Not found"}, status_code=404)
    versions = (
        db.query(AnswerVersion)
        .filter(AnswerVersion.question_id == question_id)
        .order_by(AnswerVersion.created_at.desc())
        .limit(20)
        .all()
    )
    return {"versions": [
        {
            "id": v.id,
            "action": v.action,
            "user_email": v.user_email or "",
            "user_name": v.user_name or "",
            "draft_answer": v.draft_answer or "",
            "short_answer": v.short_answer or "",
            "created_at": v.created_at.isoformat(),
        }
        for v in versions
    ]}


# ---------------------------------------------------------------------------
# Workspace settings
# ---------------------------------------------------------------------------

@router.get("/workspace/settings")
def api_get_workspace_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
    if not workspace:
        return {"white_label_export": False}
    return {"white_label_export": bool(workspace.white_label_export)}


class WorkspaceSettingsBody(BaseModel):
    white_label_export: bool | None = None


@router.patch("/workspace/settings")
def api_update_workspace_settings(
    body: WorkspaceSettingsBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "owner":
        return JSONResponse({"error": "Only the workspace owner can change workspace settings."}, status_code=403)
    workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
    if not workspace:
        return JSONResponse({"error": "Not found"}, status_code=404)
    if body.white_label_export is not None:
        workspace.white_label_export = body.white_label_export
    db.commit()
    return {"white_label_export": workspace.white_label_export}


