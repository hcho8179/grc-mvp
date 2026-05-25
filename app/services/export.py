"""Excel export service — fills the original questionnaire XLSX with generated answers."""

import io
import zipfile

from sqlalchemy.orm import Session

from app.models import Question, Questionnaire


class ExportedWorkbook(bytes):
    """Workbook bytes that can also be unpacked as (bytes, extension)."""

    def __new__(cls, data: bytes, extension: str):
        obj = super().__new__(cls, data)
        obj.extension = extension
        return obj

    def __iter__(self):
        yield bytes(self)
        yield self.extension


def _has_vba(xlsx_bytes: bytes) -> bool:
    """Return True if the workbook contains a VBA project (xlsm file)."""
    try:
        with zipfile.ZipFile(io.BytesIO(xlsx_bytes)) as z:
            return "xl/vbaProject.bin" in z.namelist()
    except Exception:
        return False


def _parse_dv_list(formula1: str) -> list[str]:
    """Parse a data-validation list formula into allowed values.

    Handles inline lists like '"Yes,No,N/A"' or '"Yes","No","N/A"'.
    Returns empty list for range references (e.g. '$A$1:$A$5') which
    cannot be resolved without reading the sheet data.
    """
    val = formula1.strip()
    if not val or val.startswith("$") or val.startswith("="):
        return []
    val = val.strip('"')
    if '","' in val:
        return [v.strip().strip('"') for v in val.split('","')]
    return [v.strip() for v in val.split(",") if v.strip()]


def _cell_in_dv(dv, row: int, col: int) -> bool:
    """Return True if the cell (row, col) falls within a DataValidation's sqref."""
    from openpyxl.utils import get_column_letter
    from openpyxl.utils.cell import coordinate_from_string, column_index_from_string

    cell_ref = f"{get_column_letter(col)}{row}"
    try:
        for rng in str(dv.sqref).split():
            if ":" in rng:
                start, end = rng.split(":", 1)
                sc, sr = coordinate_from_string(start)
                ec, er = coordinate_from_string(end)
                if (column_index_from_string(sc) <= col <= column_index_from_string(ec)
                        and int(sr) <= row <= int(er)):
                    return True
            elif rng == cell_ref:
                return True
    except Exception:
        pass
    return False


def _match_dv_value(value: str, allowed: list[str]) -> str:
    """Return the best-matching allowed value, or the original value if no match."""
    for v in allowed:
        if v.lower() == value.lower():
            return v
    for v in allowed:
        if value.lower() in v.lower() or v.lower() in value.lower():
            return v
    return value


def export_questionnaire_to_xlsx(questionnaire_id: int, db: Session, white_label: bool = False) -> ExportedWorkbook:
    """Return (file_bytes, extension) for the filled workbook.

    Loads the raw_xlsx_blob saved at upload time, writes each question's
    final_answer into the answer column, and appends a footer row.
    Original formatting, merged cells, column widths, and row heights are
    preserved because we edit the original workbook in place.

    Writing rules:
    - Merged-cell interiors are skipped to avoid openpyxl errors.
    - Formula cells are never overwritten.
    - Cells with dropdown data-validation have their value matched to the
      nearest allowed option so the file passes Excel's own validation.
    - If the source file contains a VBA project the workbook is loaded with
      keep_vba=True and returned as .xlsm so macros are not silently stripped.
    """
    import openpyxl

    q = db.query(Questionnaire).filter(Questionnaire.id == questionnaire_id).first()
    if not q:
        raise ValueError("Questionnaire not found.")

    # Fetch file bytes — S3 key takes priority, fall back to legacy DB blob
    raw_xlsx_key = getattr(q, "raw_xlsx_key", None)
    if raw_xlsx_key:
        from app.services.storage import download
        xlsx_bytes = download(raw_xlsx_key)
    elif q.raw_xlsx_blob:
        xlsx_bytes = q.raw_xlsx_blob
    else:
        raise ValueError("Questionnaire has no stored file — cannot export.")

    questions = (
        db.query(Question)
        .filter(Question.questionnaire_id == questionnaire_id)
        .order_by(Question.row_index)
        .all()
    )

    has_vba = _has_vba(xlsx_bytes)
    wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), data_only=False, keep_vba=has_vba)
    ws = wb.active

    # Build a set of merged-range interior cells (non-top-left) to skip
    merge_interiors: set[tuple[int, int]] = set()
    for merged_range in ws.merged_cells.ranges:
        min_r, min_c = merged_range.min_row, merged_range.min_col
        for r, c in merged_range.cells:
            if (r, c) != (min_r, min_c):
                merge_interiors.add((r, c))

    # Determine columns to write into (1-based for openpyxl)
    if q.answer_col_index is not None:
        ans_col = q.answer_col_index + 1
    else:
        ans_col = (ws.max_column or 1) + 1

    # Secondary col: evidence/comments. When set, primary col gets short_answer (Yes/No),
    # secondary col gets the full answer.
    secondary_answer_col_index = getattr(q, "secondary_answer_col_index", None)
    ev_col = (secondary_answer_col_index + 1) if secondary_answer_col_index is not None else None

    def _safe_write(row: int, col: int, value: str) -> None:
        if (row, col) in merge_interiors:
            return
        cell = ws.cell(row=row, column=col)
        if isinstance(cell.value, str) and cell.value.startswith("="):
            return
        # Match value to dropdown list if data validation is present
        for dv in ws.data_validations.dataValidation:
            if dv.type == "list" and _cell_in_dv(dv, row, col):
                allowed = _parse_dv_list(dv.formula1 or "")
                if allowed:
                    value = _match_dv_value(value, allowed)
                break
        cell.value = value

    for question in questions:
        answer = question.final_answer
        if answer is None and not hasattr(question, "_sa_instance_state"):
            answer = question.draft_answer
        if not answer:
            continue  # only approved answers leave
        xlsx_row = question.row_index + 2

        if ev_col:
            # Two-column mode: Yes/No → primary col, full answer → evidence col
            _safe_write(xlsx_row, ans_col, getattr(question, "short_answer", None) or "N/A")
            _safe_write(xlsx_row, ev_col, answer)
        else:
            # Single-column mode: full answer → answer col
            _safe_write(xlsx_row, ans_col, answer)

    # Footer: two rows below the last data row
    if not white_label:
        footer_row = (q.question_count or 0) + 3
        ws.cell(row=footer_row, column=1, value="Generated with Greenlight")

    buf = io.BytesIO()
    wb.save(buf)
    ext = "xlsm" if has_vba else "xlsx"
    return ExportedWorkbook(buf.getvalue(), ext)
