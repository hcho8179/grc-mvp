"""Excel export service — fills the original questionnaire XLSX with generated answers."""

import io

from sqlalchemy.orm import Session

from app.models import Question, Questionnaire


def export_questionnaire_to_xlsx(questionnaire_id: int, db: Session) -> bytes:
    """Return a filled XLSX as bytes.

    Loads the raw_xlsx_blob saved at upload time, writes each question's
    final_answer (or draft_answer fallback) into the answer column, and
    appends a footer row.  Original formatting, merged cells, column widths,
    and row heights are preserved because we edit the original workbook in place.

    Writing rules:
    - Merged-cell interiors (non-top-left cells) are skipped to avoid openpyxl errors.
    - Formula cells are never overwritten.
    """
    import openpyxl

    q = db.query(Questionnaire).filter(Questionnaire.id == questionnaire_id).first()
    if not q:
        raise ValueError("Questionnaire not found.")

    # Fetch file bytes — S3 key takes priority, fall back to legacy DB blob
    if q.raw_xlsx_key:
        from app.services.storage import download
        xlsx_bytes = download(q.raw_xlsx_key)
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

    # Load with data_only=False so formulas are preserved as formula strings
    wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), data_only=False)
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
    ev_col = (q.secondary_answer_col_index + 1) if q.secondary_answer_col_index is not None else None

    def _safe_write(row: int, col: int, value: str) -> None:
        if (row, col) in merge_interiors:
            return
        cell = ws.cell(row=row, column=col)
        if isinstance(cell.value, str) and cell.value.startswith("="):
            return
        cell.value = value

    for question in questions:
        if not question.final_answer:
            continue  # only approved answers leave
        xlsx_row = question.row_index + 2

        if ev_col:
            # Two-column mode: Yes/No → primary col, full answer → evidence col
            _safe_write(xlsx_row, ans_col, question.short_answer or "N/A")
            _safe_write(xlsx_row, ev_col, question.final_answer)
        else:
            # Single-column mode: full answer → answer col
            _safe_write(xlsx_row, ans_col, question.final_answer)

    # Footer: two rows below the last data row
    footer_row = (q.question_count or 0) + 3
    ws.cell(row=footer_row, column=1, value="Generated with Sentinel GRC")

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
