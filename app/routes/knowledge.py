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
from app.services.chunking import hierarchical_chunks
from app.services.embeddings import get_embedding_provider
from app.services.parsing import parse_file, parse_xlsx_preview, parse_xlsx_qa
from app.services.sanitize import sanitize_text

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# In-memory store for XLSX temp files (temp_id → metadata dict).
_xlsx_tmp: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@router.get("", response_class=HTMLResponse)
async def knowledge_list(request: Request, db: Session = Depends(get_db)):
    documents = db.query(Document).filter(Document.deleted_at == None).order_by(Document.created_at.desc()).all()
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
    if len(file_bytes) > 20 * 1024 * 1024:
        return _error("File too large — maximum size is 20 MB.")
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

    # PDF / DOCX → parse → sanitize → chunk → embed → persist
    try:
        text = parse_file(filename, file_bytes)
    except ValueError as exc:
        return _error(str(exc))

    if not text.strip():
        return _error(
            "No text could be extracted. The file may be scanned, image-only, or encrypted."
        )

    text = sanitize_text(text, source_label=filename)
    h_chunks = hierarchical_chunks(text)
    if not h_chunks:
        return _error("File appears to contain no meaningful text after parsing.")

    leaf_count = sum(1 for hc in h_chunks if hc.is_leaf)
    doc = Document(
        filename=filename,
        file_type=FileType(ext),
        chunk_count=leaf_count,
        content_hash=content_hash,
    )
    db.add(doc)
    db.flush()

    # First pass: store all chunks, track index → db id for parent linking
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

    # Second pass: embed leaf chunks only, with contextual prefix
    context_prefix = f"Document: {filename}\n"
    leaves = [(idx, hc) for idx, hc in enumerate(h_chunks) if hc.is_leaf]
    if leaves:
        prefixed = [context_prefix + hc.text for _, hc in leaves]
        provider = get_embedding_provider()
        embeddings = await provider.embed(prefixed)
        for (idx, _), emb in zip(leaves, embeddings):
            idx_to_obj[idx].embedding = emb

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
# Replace — re-parse and re-embed an existing document without changing its ID
# ---------------------------------------------------------------------------

@router.post("/{document_id}/replace")
async def replace_document(
    document_id: int,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a new version of an existing document.

    Drops all existing chunks (including their feedback signals), then runs
    the full parse → sanitize → hierarchical_chunk → embed pipeline on the
    new file.  The Document row keeps its original id so downstream references
    (audit log, etc.) remain valid.  XLSX column-picker documents are not
    replaceable via this endpoint — delete and re-upload instead.
    """
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.deleted_at == None,
    ).first()
    if not doc:
        return RedirectResponse(url="/knowledge", status_code=303)

    def _error(msg: str):
        return templates.TemplateResponse(
            request,
            "knowledge/upload.html",
            {"error": msg},
            status_code=400,
        )

    file_bytes = await file.read()
    filename   = file.filename or doc.filename
    ext        = Path(filename).suffix.lower().lstrip(".")

    if not file_bytes:
        return _error("Uploaded file is empty.")
    if len(file_bytes) > 20 * 1024 * 1024:
        return _error("File too large — maximum size is 20 MB.")
    if ext not in {"pdf", "docx"}:
        return _error("Only PDF or DOCX files can be replaced here. For XLSX, delete and re-upload.")

    content_hash = hashlib.sha256(file_bytes).hexdigest()

    # Reject if this exact content already lives on a *different* document
    duplicate = db.query(Document).filter(
        Document.content_hash == content_hash,
        Document.id != document_id,
        Document.deleted_at == None,
    ).first()
    if duplicate:
        return _error(f"This file is identical to '{duplicate.filename}' already in the knowledge base.")

    try:
        text = parse_file(filename, file_bytes)
    except ValueError as exc:
        return _error(str(exc))

    if not text.strip():
        return _error("No text could be extracted. The file may be scanned, image-only, or encrypted.")

    text     = sanitize_text(text, source_label=filename)
    h_chunks = hierarchical_chunks(text)
    if not h_chunks:
        return _error("File appears to contain no meaningful text after parsing.")

    # Drop all old chunks — CASCADE removes ChunkFeedback rows automatically
    db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == document_id).delete(synchronize_session=False)

    # Update the document record in place
    leaf_count        = sum(1 for hc in h_chunks if hc.is_leaf)
    doc.filename      = filename
    doc.file_type     = FileType(ext)
    doc.chunk_count   = leaf_count
    doc.content_hash  = content_hash
    db.flush()

    # First pass: store all chunks, wire parent links
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

    # Second pass: embed leaf chunks with contextual prefix
    context_prefix = f"Document: {filename}\n"
    leaves = [(idx, hc) for idx, hc in enumerate(h_chunks) if hc.is_leaf]
    if leaves:
        prefixed  = [context_prefix + hc.text for _, hc in leaves]
        provider  = get_embedding_provider()
        embeddings = await provider.embed(prefixed)
        for (idx, _), emb in zip(leaves, embeddings):
            idx_to_obj[idx].embedding = emb

    db.commit()
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
