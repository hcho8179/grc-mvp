"""Excel export service — fills the original questionnaire XLSX with generated answers."""

import io

from sqlalchemy.orm import Session

from app.models import Question, Questionnaire


def export_questionnaire_to_xlsx(questionnaire_id: int, db: Session) -> bytes:
    """Return a filled XLSX as bytes.

    Loads the raw_xlsx_blob saved at upload time, writes each question's
    final_answer (or draft_answer fallback) into the answer column, and
    appends a footer row.  Original formatting is preserved by openpyxl.
    """
    import openpyxl

    q = db.query(Questionnaire).filter(Questionnaire.id == questionnaire_id).first()
    if not q or not q.raw_xlsx_blob:
        raise ValueError("Questionnaire not found or has no stored XLSX blob.")

    questions = (
        db.query(Question)
        .filter(Question.questionnaire_id == questionnaire_id)
        .order_by(Question.row_index)
        .all()
    )

    wb = openpyxl.load_workbook(io.BytesIO(q.raw_xlsx_blob))
    ws = wb.active

    # Determine which column to write into (1-based for openpyxl)
    if q.answer_col_index is not None:
        ans_col = q.answer_col_index + 1
    else:
        # Append after the last used column
        ans_col = (ws.max_column or 1) + 1

    for question in questions:
        answer = question.final_answer or question.draft_answer or ""
        # row_index is 0-based data row; row 1 is the header, data starts at row 2
        xlsx_row = question.row_index + 2
        ws.cell(row=xlsx_row, column=ans_col, value=answer)

    # Footer: two rows below the last data row
    footer_row = (q.question_count or 0) + 3
    ws.cell(row=footer_row, column=1, value="Generated with Sentinel (AI-powered GRC)")

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
