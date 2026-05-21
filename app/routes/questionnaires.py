"""Routes for questionnaire upload, listing, detail, generation, and review."""

import asyncio
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from fastapi.responses import Response

from app.config import get_settings
from app.db import SessionLocal, get_db
from app.models import (
    ApprovedAnswer,
    ConfidenceLevel,
    Document,
    FileType,
    KnowledgeChunk,
    LLMCall,
    Questionnaire,
    QuestionnaireStatus,
    QuestionnaireTemplate,
    Question,
    QuestionStatus,
    SourceType,
)
from app.services.answer_library import detect_category, find_similar_answers
from app.services.embeddings import get_embedding_provider
from app.services.export import export_questionnaire_to_xlsx
from app.services.generation import estimate_cost, generate_answer, get_llm_provider
from app.services.parsing import (
    parse_xlsx_questionnaire_full,
    parse_xlsx_questionnaire_preview,
)
from app.services.retrieval import retrieve_relevant_chunks
from app.services.templates import (
    find_template_by_customer,
    list_templates,
    save_template,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

_upload_tmp: dict[str, dict] = {}

_APPROVED_DOC_NAME = "Approved Answers"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_or_create_approved_doc(db: Session) -> Document:
    doc = db.query(Document).filter(Document.filename == _APPROVED_DOC_NAME).first()
    if not doc:
        doc = Document(
            filename=_APPROVED_DOC_NAME,
            file_type=FileType.xlsx,
            chunk_count=0,
        )
        db.add(doc)
        db.flush()
    return doc


def _render_row(request: Request, question: Question, questionnaire_id: int) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "questionnaires/_row.html",
        {"q": question, "questionnaire_id": questionnaire_id},
    )


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@router.get("", response_class=HTMLResponse)
async def questionnaire_list(request: Request, db: Session = Depends(get_db)):
    questionnaires = db.query(Questionnaire).filter(Questionnaire.deleted_at == None).order_by(Questionnaire.created_at.desc()).all()
    return templates.TemplateResponse(
        request, "questionnaires/list.html", {"questionnaires": questionnaires}
    )


# ---------------------------------------------------------------------------
# Upload — GET form / POST save+preview
# ---------------------------------------------------------------------------

@router.get("/upload", response_class=HTMLResponse)
async def upload_form(request: Request):
    return templates.TemplateResponse(request, "questionnaires/upload.html", {"error": None})


@router.post("/upload")
async def upload_questionnaire(
    request: Request,
    file: UploadFile = File(...),
    name: str = Form(...),
    customer_name: str = Form(""),
    db: Session = Depends(get_db),
):
    def _error(msg: str):
        return templates.TemplateResponse(
            request, "questionnaires/upload.html", {"error": msg}, status_code=400
        )

    file_bytes = await file.read()
    filename = file.filename or "questionnaire.xlsx"

    if not file_bytes:
        return _error("Uploaded file is empty.")
    if len(file_bytes) > 20 * 1024 * 1024:
        return _error("File too large — maximum size is 20 MB.")
    if Path(filename).suffix.lower() != ".xlsx":
        return _error("Only XLSX files are supported for questionnaires.")
    if not name.strip():
        return _error("Questionnaire name is required.")

    try:
        parse_xlsx_questionnaire_preview(file_bytes)
    except ValueError as exc:
        return _error(str(exc))

    temp_id = str(uuid.uuid4())
    _upload_tmp[temp_id] = {
        "bytes": file_bytes,
        "filename": filename,
        "name": name.strip(),
        "customer_name": customer_name.strip() or None,
    }
    return RedirectResponse(url=f"/questionnaires/upload/{temp_id}/columns", status_code=303)


# ---------------------------------------------------------------------------
# Column picker
# ---------------------------------------------------------------------------

@router.get("/upload/{temp_id}/columns", response_class=HTMLResponse)
async def column_picker(temp_id: str, request: Request):
    meta = _upload_tmp.get(temp_id)
    if not meta:
        return RedirectResponse(url="/questionnaires/upload", status_code=303)

    try:
        preview = parse_xlsx_questionnaire_preview(meta["bytes"])
    except ValueError as exc:
        return templates.TemplateResponse(
            request, "questionnaires/upload.html", {"error": str(exc)}, status_code=400
        )

    db: Session = SessionLocal()
    suggested_template = None
    try:
        suggested_template = find_template_by_customer(meta.get("customer_name"), db)
    finally:
        db.close()

    return templates.TemplateResponse(
        request,
        "questionnaires/column_picker.html",
        {
            "temp_id": temp_id,
            "filename": meta["filename"],
            "name": meta["name"],
            "preview": preview,
            "suggested_template": suggested_template,
        },
    )


@router.post("/upload/{temp_id}/columns")
async def finalize_upload(
    temp_id: str,
    request: Request,
    question_col: int = Form(...),
    answer_col: str = Form(""),
    db: Session = Depends(get_db),
):
    meta = _upload_tmp.get(temp_id)
    if not meta:
        return RedirectResponse(url="/questionnaires/upload", status_code=303)

    ans_col: int | None = int(answer_col) if answer_col.strip() else None

    try:
        parsed_questions = parse_xlsx_questionnaire_full(meta["bytes"], question_col, ans_col)
    except ValueError as exc:
        return templates.TemplateResponse(
            request, "questionnaires/upload.html", {"error": str(exc)}, status_code=400
        )

    if not parsed_questions:
        return templates.TemplateResponse(
            request,
            "questionnaires/upload.html",
            {"error": "No questions found in the selected column. Check your column choice."},
            status_code=400,
        )

    questionnaire = Questionnaire(
        name=meta["name"],
        customer_name=meta["customer_name"],
        source_filename=meta["filename"],
        status=QuestionnaireStatus.draft,
        question_count=len(parsed_questions),
        raw_xlsx_blob=meta["bytes"],
        answer_col_index=ans_col,
        question_col_index=question_col,
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

    db.commit()
    del _upload_tmp[temp_id]
    return RedirectResponse(url=f"/questionnaires/{questionnaire.id}", status_code=303)


# ---------------------------------------------------------------------------
# Templates list page  (must be declared before /{questionnaire_id} to avoid
# Starlette matching "templates" as an integer questionnaire_id)
# ---------------------------------------------------------------------------

@router.get("/templates", response_class=HTMLResponse)
async def templates_list(request: Request, db: Session = Depends(get_db)):
    all_templates = list_templates(db)
    return templates.TemplateResponse(
        request,
        "questionnaires/templates.html",
        {"templates": all_templates},
    )


@router.post("/templates/{template_id}/delete")
async def delete_template(template_id: int, db: Session = Depends(get_db)):
    tmpl = db.query(QuestionnaireTemplate).filter(QuestionnaireTemplate.id == template_id).first()
    if tmpl:
        db.delete(tmpl)
        db.commit()
    return RedirectResponse(url="/questionnaires/templates", status_code=303)


# ---------------------------------------------------------------------------
# Detail
# ---------------------------------------------------------------------------

@router.get("/{questionnaire_id}", response_class=HTMLResponse)
async def questionnaire_detail(
    questionnaire_id: int, request: Request, db: Session = Depends(get_db)
):
    q = db.query(Questionnaire).filter(Questionnaire.id == questionnaire_id).first()
    if not q:
        return RedirectResponse(url="/questionnaires", status_code=303)

    questions = (
        db.query(Question)
        .filter(Question.questionnaire_id == questionnaire_id)
        .order_by(Question.row_index)
        .all()
    )
    return templates.TemplateResponse(
        request, "questionnaires/detail.html",
        {"questionnaire": q, "questions": questions, "questionnaire_id": questionnaire_id},
    )


# ---------------------------------------------------------------------------
# Generate all pending questions  (batched asyncio.gather, max 5 concurrent)
# ---------------------------------------------------------------------------

async def _generate_one_question(question_id: int, questionnaire_id: int) -> bool:
    """Process a single question in its own DB session. Returns True on success."""
    db = SessionLocal()
    result = None
    success = False
    try:
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            return False

        retrieved = await retrieve_relevant_chunks(question.question_text, db)
        result = await generate_answer(question.question_text, retrieved)

        question.draft_answer = result.answer
        question.reasoning = result.reasoning
        question.cited_chunk_ids = result.cited_chunk_ids
        question.confidence = (
            None if result.insufficient_context
            else ConfidenceLevel(result.confidence)
        )
        question.status = QuestionStatus.generated
        db.commit()
        success = True
    except Exception:
        db.rollback()
    finally:
        # Log cost in a separate block — failures here must not affect status commit
        if result is not None:
            try:
                model = (
                    get_settings().gemini_model
                    if get_settings().llm_provider == "gemini"
                    else get_settings().claude_model
                )
                db.add(LLMCall(
                    model=model,
                    input_tokens=result.input_tokens,
                    output_tokens=result.output_tokens,
                    cost_estimate=estimate_cost(model, result.input_tokens, result.output_tokens),
                    questionnaire_id=questionnaire_id,
                    question_id=question_id,
                ))
                db.commit()
            except Exception:
                db.rollback()
        db.close()
    return success


@router.post("/{questionnaire_id}/generate")
async def generate_all(questionnaire_id: int, db: Session = Depends(get_db)):
    q = db.query(Questionnaire).filter(Questionnaire.id == questionnaire_id).first()
    if not q:
        return RedirectResponse(url="/questionnaires", status_code=303)

    pending_ids = [
        row.id for row in db.query(Question.id)
        .filter(
            Question.questionnaire_id == questionnaire_id,
            Question.status == QuestionStatus.pending,
        )
        .order_by(Question.row_index)
        .all()
    ]

    q.status = QuestionnaireStatus.in_progress
    db.commit()

    # Process in batches of 5 with a semaphore; sleep 1 s between calls
    semaphore = asyncio.Semaphore(5)
    results: list[bool] = []

    async def _with_semaphore(qid: int) -> None:
        async with semaphore:
            ok = await _generate_one_question(qid, questionnaire_id)
            results.append(ok)
            await asyncio.sleep(1)

    await asyncio.gather(*[_with_semaphore(qid) for qid in pending_ids])

    failed = results.count(False)
    if failed == len(results) and results:
        # All failed — revert questionnaire status so user isn't stuck on in_progress
        db.refresh(q)
        q.status = QuestionnaireStatus.draft
        db.commit()

    return RedirectResponse(url=f"/questionnaires/{questionnaire_id}", status_code=303)


# ---------------------------------------------------------------------------
# Regenerate a single question (HTMX — returns updated row HTML)
# ---------------------------------------------------------------------------

@router.post("/{questionnaire_id}/questions/{question_id}/regenerate")
async def regenerate_question(
    questionnaire_id: int,
    question_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        return HTMLResponse("", status_code=404)

    try:
        retrieved = await retrieve_relevant_chunks(question.question_text, db)
        result = await generate_answer(question.question_text, retrieved)

        question.draft_answer = result.answer
        question.reasoning = result.reasoning
        question.cited_chunk_ids = result.cited_chunk_ids
        question.confidence = (
            None if result.insufficient_context
            else ConfidenceLevel(result.confidence)
        )
        question.status = QuestionStatus.generated
        db.commit()
    except Exception:
        # Rollback so the in-memory object re-syncs with DB on next attribute access
        db.rollback()

    return _render_row(request, question, questionnaire_id)


# ---------------------------------------------------------------------------
# Update draft answer inline (HTMX PATCH — returns updated row HTML)
# ---------------------------------------------------------------------------

@router.patch("/{questionnaire_id}/questions/{question_id}", response_class=HTMLResponse)
async def update_draft(
    questionnaire_id: int,
    question_id: int,
    request: Request,
    draft_answer: str = Form(""),
    db: Session = Depends(get_db),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        return HTMLResponse("", status_code=404)

    question.draft_answer = draft_answer.strip() or None
    db.commit()
    return _render_row(request, question, questionnaire_id)


# ---------------------------------------------------------------------------
# Approve (HTMX — returns updated row HTML + self-learning)
# ---------------------------------------------------------------------------

@router.post("/{questionnaire_id}/questions/{question_id}/approve")
async def approve_question(
    questionnaire_id: int,
    question_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        return HTMLResponse("", status_code=404)

    question.final_answer = question.draft_answer
    question.status = QuestionStatus.approved
    db.commit()

    # Self-learning: embed and save to both RAG knowledge base and answer library
    if question.final_answer:
        try:
            doc = _get_or_create_approved_doc(db)
            chunk_text = f"Q: {question.question_text}\nA: {question.final_answer}"
            provider = get_embedding_provider()

            # Embed in parallel: Q+A for RAG retrieval, question-only for answer reuse
            qa_embs, q_embs = await asyncio.gather(
                provider.embed([chunk_text]),
                provider.embed([question.question_text]),
            )

            db.add(KnowledgeChunk(
                document_id=doc.id,
                source_document=_APPROVED_DOC_NAME,
                source_type=SourceType.approved_answer,
                text=chunk_text,
                embedding=qa_embs[0],
            ))
            doc.chunk_count += 1

            # Upsert into answer library
            conf_map = {"high": 1.0, "medium": 0.67, "low": 0.33}
            conf_score = conf_map.get(question.confidence.value, 0.5) if question.confidence else None

            existing = (
                db.query(ApprovedAnswer)
                .filter(ApprovedAnswer.question_text == question.question_text)
                .first()
            )
            if existing:
                existing.answer_text = question.final_answer
                existing.cited_chunk_ids = question.cited_chunk_ids
                existing.confidence_score = conf_score
                existing.embedding = q_embs[0]
                existing.status = "active"
                existing.source_question_id = question.id
            else:
                db.add(ApprovedAnswer(
                    question_text=question.question_text,
                    answer_text=question.final_answer,
                    answer_category=detect_category(question.question_text),
                    cited_chunk_ids=question.cited_chunk_ids,
                    confidence_score=conf_score,
                    embedding=q_embs[0],
                    source_question_id=question.id,
                ))

            db.commit()
        except Exception:
            pass  # KB/library write failure must not break the approval

    return _render_row(request, question, questionnaire_id)


# ---------------------------------------------------------------------------
# Reject (HTMX — returns updated row HTML)
# ---------------------------------------------------------------------------

@router.post("/{questionnaire_id}/questions/{question_id}/reject")
async def reject_question(
    questionnaire_id: int,
    question_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        return HTMLResponse("", status_code=404)

    question.status = QuestionStatus.rejected
    db.commit()
    return _render_row(request, question, questionnaire_id)


# ---------------------------------------------------------------------------
# Chunk source expand (HTMX GET — returns chunk text snippet)
# ---------------------------------------------------------------------------

@router.get(
    "/{questionnaire_id}/questions/{question_id}/chunks/{chunk_id}",
    response_class=HTMLResponse,
)
async def get_chunk_text(
    questionnaire_id: int,
    question_id: int,
    chunk_id: int,
    db: Session = Depends(get_db),
):
    chunk = db.query(KnowledgeChunk).filter(KnowledgeChunk.id == chunk_id).first()
    if not chunk:
        return HTMLResponse("<p class='text-xs text-red-500'>Chunk not found.</p>")
    safe = chunk.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return HTMLResponse(
        f'<p class="text-xs text-gray-600 whitespace-pre-wrap leading-relaxed">{safe}</p>'
        f'<p class="text-xs text-gray-400 mt-1">Source: {chunk.source_document}</p>'
    )


# ---------------------------------------------------------------------------
# Export to XLSX
# ---------------------------------------------------------------------------

@router.get("/{questionnaire_id}/export")
async def export_questionnaire(questionnaire_id: int, db: Session = Depends(get_db)):
    q = db.query(Questionnaire).filter(Questionnaire.id == questionnaire_id).first()
    if not q:
        return RedirectResponse(url="/questionnaires", status_code=303)

    try:
        xlsx_bytes = export_questionnaire_to_xlsx(questionnaire_id, db)
    except ValueError as exc:
        return HTMLResponse(f"<p>Export failed: {exc}</p>", status_code=400)

    from datetime import date
    safe_name = q.name.replace(" ", "_").replace("/", "-")
    today = date.today().strftime("%Y-%m-%d")
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}_filled_{today}.xlsx"'},
    )


# ---------------------------------------------------------------------------
# Delete questionnaire
# ---------------------------------------------------------------------------

@router.post("/{questionnaire_id}/delete")
async def delete_questionnaire(questionnaire_id: int, db: Session = Depends(get_db)):
    q = db.query(Questionnaire).filter(Questionnaire.id == questionnaire_id).first()
    if q:
        db.delete(q)
        db.commit()
    return RedirectResponse(url="/questionnaires", status_code=303)


# ---------------------------------------------------------------------------
# Save as template (HTMX POST — returns confirmation fragment)
# ---------------------------------------------------------------------------

@router.post("/{questionnaire_id}/save-template", response_class=HTMLResponse)
async def save_as_template(
    questionnaire_id: int,
    request: Request,
    template_name: str = Form(...),
    db: Session = Depends(get_db),
):
    q = db.query(Questionnaire).filter(Questionnaire.id == questionnaire_id).first()
    if not q or not q.raw_xlsx_blob:
        return HTMLResponse(
            '<p class="text-xs text-red-500">Questionnaire not found.</p>', status_code=404
        )

    tmpl = save_template(
        name=template_name,
        customer_name=q.customer_name,
        question_col=q.question_col_index or 0,
        answer_col=q.answer_col_index,
        xlsx_bytes=q.raw_xlsx_blob,
        db=db,
    )
    q.template_id = tmpl.id
    db.commit()

    return HTMLResponse(
        f'<span class="text-xs text-emerald-600 font-medium">'
        f'Template &ldquo;{tmpl.name}&rdquo; saved.</span>'
    )


