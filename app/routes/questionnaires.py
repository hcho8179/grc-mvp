"""Routes for questionnaire upload, listing, and detail view."""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Questionnaire, QuestionnaireStatus, Question, QuestionStatus
from app.services.parsing import (
    parse_xlsx_questionnaire_preview,
    parse_xlsx_questionnaire_full,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# In-memory temp store: temp_id → {"bytes": bytes, "filename": str}
_upload_tmp: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@router.get("", response_class=HTMLResponse)
async def questionnaire_list(request: Request, db: Session = Depends(get_db)):
    questionnaires = (
        db.query(Questionnaire).order_by(Questionnaire.created_at.desc()).all()
    )
    return templates.TemplateResponse(
        request,
        "questionnaires/list.html",
        {"questionnaires": questionnaires},
    )


# ---------------------------------------------------------------------------
# Upload — GET (form) and POST (save + preview)
# ---------------------------------------------------------------------------

@router.get("/upload", response_class=HTMLResponse)
async def upload_form(request: Request):
    return templates.TemplateResponse(
        request, "questionnaires/upload.html", {"error": None}
    )


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
            request,
            "questionnaires/upload.html",
            {"error": msg},
            status_code=400,
        )

    file_bytes = await file.read()
    filename = file.filename or "questionnaire.xlsx"

    if not file_bytes:
        return _error("Uploaded file is empty.")

    ext = Path(filename).suffix.lower()
    if ext != ".xlsx":
        return _error("Only XLSX files are supported for questionnaires.")

    if not name.strip():
        return _error("Questionnaire name is required.")

    try:
        parse_xlsx_questionnaire_preview(file_bytes)  # validate it's readable
    except ValueError as exc:
        return _error(str(exc))

    temp_id = str(uuid.uuid4())
    _upload_tmp[temp_id] = {
        "bytes": file_bytes,
        "filename": filename,
        "name": name.strip(),
        "customer_name": customer_name.strip() or None,
    }
    return RedirectResponse(
        url=f"/questionnaires/upload/{temp_id}/columns", status_code=303
    )


# ---------------------------------------------------------------------------
# Column picker — GET (preview) and POST (finalize)
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
            request,
            "questionnaires/upload.html",
            {"error": str(exc)},
            status_code=400,
        )

    return templates.TemplateResponse(
        request,
        "questionnaires/column_picker.html",
        {
            "temp_id": temp_id,
            "filename": meta["filename"],
            "name": meta["name"],
            "preview": preview,
        },
    )


@router.post("/upload/{temp_id}/columns")
async def finalize_upload(
    temp_id: str,
    request: Request,
    question_col: int = Form(...),
    answer_col: str = Form(""),  # "" means not selected
    db: Session = Depends(get_db),
):
    meta = _upload_tmp.get(temp_id)
    if not meta:
        return RedirectResponse(url="/questionnaires/upload", status_code=303)

    ans_col: int | None = int(answer_col) if answer_col.strip() else None

    try:
        parsed_questions = parse_xlsx_questionnaire_full(
            meta["bytes"], question_col, ans_col
        )
    except ValueError as exc:
        return templates.TemplateResponse(
            request,
            "questionnaires/upload.html",
            {"error": str(exc)},
            status_code=400,
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
    )
    db.add(questionnaire)
    db.flush()

    for pq in parsed_questions:
        db.add(Question(
            questionnaire_id=questionnaire.id,
            row_index=pq["row_index"],
            question_text=pq["question"],
            draft_answer=pq["existing_answer"],  # pre-filled if any
            status=QuestionStatus.pending,
        ))

    db.commit()

    del _upload_tmp[temp_id]

    return RedirectResponse(url=f"/questionnaires/{questionnaire.id}", status_code=303)


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
        request,
        "questionnaires/detail.html",
        {"questionnaire": q, "questions": questions},
    )


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

@router.post("/{questionnaire_id}/delete")
async def delete_questionnaire(
    questionnaire_id: int, db: Session = Depends(get_db)
):
    q = db.query(Questionnaire).filter(Questionnaire.id == questionnaire_id).first()
    if q:
        db.delete(q)
        db.commit()
    return RedirectResponse(url="/questionnaires", status_code=303)
