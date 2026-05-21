"""Template service — extract Excel format metadata and manage questionnaire templates."""

from __future__ import annotations

import io
from typing import Any

from sqlalchemy.orm import Session

from app.models import QuestionnaireTemplate


def extract_format_config(xlsx_bytes: bytes) -> dict[str, Any]:
    """Extract format metadata from an XLSX file.

    Returns a dict with merged_cells, column_widths, and row_heights so the
    export can faithfully reproduce the original layout when writing answers.
    """
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), data_only=False)
    ws = wb.active

    merged = [str(r) for r in ws.merged_cells.ranges]

    col_widths: dict[str, float] = {}
    for col_letter, dim in ws.column_dimensions.items():
        if dim.width:
            col_widths[col_letter] = round(dim.width, 2)

    row_heights: dict[str, float] = {}
    for row_num, dim in ws.row_dimensions.items():
        if dim.height:
            row_heights[str(row_num)] = round(dim.height, 2)

    # Collect formula cells so export can avoid overwriting them
    formula_cells: list[str] = []
    for row in ws.iter_rows():
        for cell in row:
            if isinstance(cell.value, str) and cell.value.startswith("="):
                formula_cells.append(cell.coordinate)

    return {
        "merged_cells": merged,
        "column_widths": col_widths,
        "row_heights": row_heights,
        "formula_cells": formula_cells,
    }


def get_merged_top_left_cells(format_config: dict[str, Any]) -> set[str]:
    """Return the set of top-left cell coords for every merged range."""
    import openpyxl.utils

    top_left: set[str] = set()
    for range_str in format_config.get("merged_cells", []):
        # e.g. "A1:C3" → top-left is A1
        first_cell = range_str.split(":")[0]
        top_left.add(first_cell)
    return top_left


def is_cell_in_merge_interior(
    row: int, col: int, format_config: dict[str, Any]
) -> bool:
    """Return True if (row, col) is inside a merged range but not its top-left cell.

    We should NOT write answers into these cells — writing to any non-top-left
    cell of a merged range raises an openpyxl error.
    """
    import openpyxl
    from openpyxl.utils import get_column_letter

    for range_str in format_config.get("merged_cells", []):
        try:
            merged_range = openpyxl.worksheet.cell_range.CellRange(range_str)
        except Exception:
            continue
        if (row, col) in merged_range.cells:
            # It IS in this merged range — check if it's the top-left
            tl_row, tl_col = merged_range.min_row, merged_range.min_col
            if row != tl_row or col != tl_col:
                return True
    return False


def find_template_by_customer(
    customer_name: str | None, db: Session
) -> QuestionnaireTemplate | None:
    """Return the most-used template for this customer, or None."""
    if not customer_name:
        return None
    return (
        db.query(QuestionnaireTemplate)
        .filter(QuestionnaireTemplate.customer_name == customer_name)
        .order_by(QuestionnaireTemplate.times_used.desc(), QuestionnaireTemplate.created_at.desc())
        .first()
    )


def list_templates(db: Session) -> list[QuestionnaireTemplate]:
    return (
        db.query(QuestionnaireTemplate)
        .order_by(QuestionnaireTemplate.customer_name, QuestionnaireTemplate.name)
        .all()
    )


def save_template(
    name: str,
    customer_name: str | None,
    question_col: int,
    answer_col: int | None,
    xlsx_bytes: bytes,
    db: Session,
) -> QuestionnaireTemplate:
    """Create and persist a new template from an uploaded XLSX."""
    config = extract_format_config(xlsx_bytes)
    tmpl = QuestionnaireTemplate(
        name=name.strip(),
        customer_name=customer_name.strip() if customer_name else None,
        question_col=question_col,
        answer_col=answer_col,
        format_config=config,
    )
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)
    return tmpl
