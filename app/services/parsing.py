"""File parsing service: PDF, DOCX, XLSX."""

import io
from pathlib import Path


def parse_pdf(file_bytes: bytes) -> str:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(io.BytesIO(file_bytes))
    except PdfReadError as exc:
        raise ValueError(f"Could not read PDF: {exc}") from exc
    except Exception as exc:
        raise ValueError(f"Could not read PDF: {exc}") from exc

    if reader.is_encrypted:
        raise ValueError("PDF is password-protected and cannot be read.")

    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)

    return "\n\n".join(parts)


def parse_docx(file_bytes: bytes) -> str:
    from docx import Document as DocxDocument

    try:
        doc = DocxDocument(io.BytesIO(file_bytes))
    except Exception as exc:
        raise ValueError(f"Could not read DOCX: {exc}") from exc

    return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())


def parse_xlsx_preview(file_bytes: bytes) -> dict:
    """Return column headers, sample rows, and total row count for the column-picker UI."""
    import openpyxl

    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True, read_only=True)
    except Exception as exc:
        raise ValueError(f"Could not read XLSX: {exc}") from exc

    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if not rows:
        return {"columns": [], "sample_rows": [], "total_rows": 0}

    columns = [
        str(cell) if cell is not None else f"Column {i + 1}"
        for i, cell in enumerate(rows[0])
    ]
    data_rows = rows[1:]
    sample = [
        [str(cell) if cell is not None else "" for cell in row]
        for row in data_rows[:5]
    ]
    return {"columns": columns, "sample_rows": sample, "total_rows": len(data_rows)}


def parse_xlsx_qa(file_bytes: bytes, question_col: int, answer_col: int) -> list[dict]:
    """Parse an XLSX file into Q&A pairs using the given 0-based column indices."""
    import openpyxl

    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True, read_only=True)
    except Exception as exc:
        raise ValueError(f"Could not read XLSX: {exc}") from exc

    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if not rows:
        return []

    required_cols = max(question_col, answer_col)
    pairs: list[dict] = []
    for row in rows[1:]:  # skip header
        if len(row) <= required_cols:
            continue
        question = str(row[question_col]).strip() if row[question_col] is not None else ""
        answer = str(row[answer_col]).strip() if row[answer_col] is not None else ""
        if question:
            pairs.append({"question": question, "answer": answer})

    return pairs


def parse_file(filename: str, file_bytes: bytes) -> str:
    """Dispatch to the appropriate text parser based on file extension."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return parse_pdf(file_bytes)
    if ext == ".docx":
        return parse_docx(file_bytes)
    if ext == ".xlsx":
        raise ValueError("XLSX files require column selection — use parse_xlsx_* functions directly.")
    raise ValueError(f"Unsupported file type: {ext!r}. Supported: .pdf, .docx, .xlsx")
