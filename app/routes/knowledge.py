"""Routes for knowledge base management."""

import hashlib
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Document, FileType, KnowledgeChunk, SourceType
from app.services.chunking import chunk_text
from app.services.embeddings import get_embedding_provider
from app.services.parsing import parse_file, parse_xlsx_preview, parse_xlsx_qa

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# In-memory store for XLSX temp files (temp_id → metadata dict).
_xlsx_tmp: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@router.get("", response_class=HTMLResponse)
async def knowledge_list(request: Request, db: Session = Depends(get_db)):
    documents = db.query(Document).order_by(Document.created_at.desc()).all()
    return templates.TemplateResponse(
        request,
        "knowledge/list.html",
        {"documents": documents},
    )


# ---------------------------------------------------------------------------
# Upload — GET (form) and POST (process)
# ---------------------------------------------------------------------------

@router.get("/upload", response_class=HTMLResponse)
async def upload_form(request: Request):
    return templates.TemplateResponse(request, "knowledge/upload.html", {"error": None})


@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    file_bytes = await file.read()
    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower().lstrip(".")

    def _error(msg: str, status: int = 400):
        return templates.TemplateResponse(
            request,
            "knowledge/upload.html",
            {"error": msg},
            status_code=status,
        )

    if not file_bytes:
        return _error("Uploaded file is empty.")

    if ext not in {"pdf", "docx", "xlsx"}:
        return _error(f"Unsupported file type '.{ext}'. Please upload PDF, DOCX, or XLSX.")

    content_hash = hashlib.sha256(file_bytes).hexdigest()
    existing = db.query(Document).filter(Document.content_hash == content_hash).first()
    if existing:
        return _error(
            f"Duplicate: this file was already uploaded as '{existing.filename}'.",
            status=409,
        )

    # XLSX → save to /tmp and redirect to column picker
    if ext == "xlsx":
        temp_id = str(uuid.uuid4())
        tmp_path = f"/tmp/grc_{temp_id}.xlsx"
        with open(tmp_path, "wb") as fh:
            fh.write(file_bytes)
        _xlsx_tmp[temp_id] = {
            "path": tmp_path,
            "filename": filename,
            "content_hash": content_hash,
        }
        return RedirectResponse(url=f"/knowledge/upload/xlsx/{temp_id}", status_code=303)

    # PDF / DOCX → parse → chunk → embed → persist
    try:
        text = parse_file(filename, file_bytes)
    except ValueError as exc:
        return _error(str(exc))

    if not text.strip():
        return _error(
            "No text could be extracted. The file may be scanned, image-only, or encrypted."
        )

    chunks = chunk_text(text)
    if not chunks:
        return _error("File appears to contain no meaningful text after parsing.")

    provider = get_embedding_provider()
    embeddings = await provider.embed(chunks)

    doc = Document(
        filename=filename,
        file_type=FileType(ext),
        chunk_count=len(chunks),
        content_hash=content_hash,
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

    db.commit()
    return RedirectResponse(url="/knowledge", status_code=303)


# ---------------------------------------------------------------------------
# XLSX column picker — GET (preview) and POST (finalize)
# ---------------------------------------------------------------------------

@router.get("/upload/xlsx/{temp_id}", response_class=HTMLResponse)
async def xlsx_picker(temp_id: str, request: Request):
    meta = _xlsx_tmp.get(temp_id)
    if not meta:
        return RedirectResponse(url="/knowledge/upload", status_code=303)

    with open(meta["path"], "rb") as fh:
        file_bytes = fh.read()

    try:
        preview = parse_xlsx_preview(file_bytes)
    except ValueError as exc:
        return templates.TemplateResponse(
            request,
            "knowledge/upload.html",
            {"error": str(exc)},
            status_code=400,
        )

    return templates.TemplateResponse(
        request,
        "knowledge/xlsx_picker.html",
        {
            "temp_id": temp_id,
            "filename": meta["filename"],
            "preview": preview,
        },
    )


@router.post("/upload/xlsx/{temp_id}")
async def finalize_xlsx(
    temp_id: str,
    request: Request,
    question_col: int = Form(...),
    answer_col: int = Form(...),
    db: Session = Depends(get_db),
):
    meta = _xlsx_tmp.get(temp_id)
    if not meta:
        return RedirectResponse(url="/knowledge/upload", status_code=303)

    with open(meta["path"], "rb") as fh:
        file_bytes = fh.read()

    try:
        qa_pairs = parse_xlsx_qa(file_bytes, question_col, answer_col)
    except ValueError as exc:
        return templates.TemplateResponse(
            request,
            "knowledge/upload.html",
            {"error": str(exc)},
            status_code=400,
        )

    if not qa_pairs:
        return templates.TemplateResponse(
            request,
            "knowledge/upload.html",
            {"error": "No Q&A pairs found with the selected columns."},
            status_code=400,
        )

    chunks = [f"Q: {p['question']}\nA: {p['answer']}" for p in qa_pairs]

    provider = get_embedding_provider()
    embeddings = await provider.embed(chunks)

    doc = Document(
        filename=meta["filename"],
        file_type=FileType.xlsx,
        chunk_count=len(chunks),
        content_hash=meta["content_hash"],
    )
    db.add(doc)
    db.flush()

    for chunk_val, embedding in zip(chunks, embeddings):
        db.add(KnowledgeChunk(
            document_id=doc.id,
            source_document=meta["filename"],
            source_type=SourceType.past_answer,
            text=chunk_val,
            embedding=embedding,
        ))

    db.commit()

    try:
        os.unlink(meta["path"])
    except OSError:
        pass
    del _xlsx_tmp[temp_id]

    return RedirectResponse(url="/knowledge", status_code=303)


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

@router.post("/{document_id}/delete")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if doc:
        db.delete(doc)
        db.commit()
    return RedirectResponse(url="/knowledge", status_code=303)
