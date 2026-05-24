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


def parse_xlsx_questionnaire_preview(file_bytes: bytes) -> dict:
    """Return column headers, sample rows, total row count, and sheet name for the questionnaire column-picker."""
    import openpyxl

    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    except Exception as exc:
        raise ValueError(f"Could not read XLSX: {exc}") from exc

    ws = wb.active
    sheet_name = ws.title

    hidden_rows = {r for r, rd in ws.row_dimensions.items() if rd.hidden}

    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if not rows:
        return {"columns": [], "sample_rows": [], "total_rows": 0, "sheet_name": sheet_name}

    columns = [
        str(cell) if cell is not None else f"Column {i + 1}"
        for i, cell in enumerate(rows[0])
    ]
    data_rows = [
        row for i, row in enumerate(rows[1:], start=2)
        if i not in hidden_rows
    ]
    sample = [
        [str(cell) if cell is not None else "" for cell in row]
        for row in data_rows[:5]
    ]
    return {
        "columns": columns,
        "sample_rows": sample,
        "total_rows": len(data_rows),
        "sheet_name": sheet_name,
    }


def parse_xlsx_questionnaire_full(
    file_bytes: bytes,
    question_col: int,
    answer_col: int | None = None,
) -> list[dict]:
    """Parse a blank questionnaire XLSX into structured question rows.

    Returns list of {"row_index": int, "question": str, "existing_answer": str | None}.
    row_index is 0-based relative to the first data row (after header).
    Rows where the question cell is empty, whitespace, or hidden are skipped.
    """
    import openpyxl

    try:
        # Must load without read_only to access row_dimensions (hidden row detection)
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    except Exception as exc:
        raise ValueError(f"Could not read XLSX: {exc}") from exc

    ws = wb.active

    # Build set of hidden row numbers (1-based)
    hidden_rows = {
        r for r, rd in ws.row_dimensions.items()
        if rd.hidden
    }

    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if not rows:
        return []

    results: list[dict] = []
    for idx, row in enumerate(rows[1:]):  # skip header; idx = 0-based data row index
        xlsx_row = idx + 2  # 1-based row number in the sheet (header is row 1)
        if xlsx_row in hidden_rows:
            continue
        if len(row) <= question_col:
            continue
        question = str(row[question_col]).strip() if row[question_col] is not None else ""
        if not question:
            continue
        existing_answer: str | None = None
        if answer_col is not None and len(row) > answer_col:
            val = row[answer_col]
            existing_answer = str(val).strip() if val is not None else None
            if not existing_answer:
                existing_answer = None
        results.append({"row_index": idx, "question": question, "existing_answer": existing_answer})

    return results


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
