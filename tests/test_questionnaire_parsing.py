"""Tests for questionnaire-specific parsing functions."""

import io

import openpyxl
import pytest

from app.services.parsing import (
    parse_xlsx_questionnaire_full,
    parse_xlsx_questionnaire_preview,
)


def _make_xlsx(rows: list[list]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# parse_xlsx_questionnaire_preview
# ---------------------------------------------------------------------------

class TestPreview:
    def test_returns_columns_and_rows(self):
        data = [
            ["ID", "Question", "Answer"],
            ["1", "Do you use MFA?", ""],
            ["2", "Describe your patch policy.", ""],
        ]
        result = parse_xlsx_questionnaire_preview(_make_xlsx(data))
        assert result["columns"] == ["ID", "Question", "Answer"]
        assert result["total_rows"] == 2
        assert len(result["sample_rows"]) == 2

    def test_includes_sheet_name(self):
        result = parse_xlsx_questionnaire_preview(_make_xlsx([["Q"]]))
        assert "sheet_name" in result
        assert isinstance(result["sheet_name"], str)

    def test_sample_capped_at_five(self):
        data = [["Q", "A"]] + [[f"Q{i}", ""] for i in range(10)]
        result = parse_xlsx_questionnaire_preview(_make_xlsx(data))
        assert len(result["sample_rows"]) == 5
        assert result["total_rows"] == 10

    def test_empty_sheet(self):
        result = parse_xlsx_questionnaire_preview(_make_xlsx([]))
        assert result["columns"] == []
        assert result["total_rows"] == 0

    def test_corrupted_bytes_raises(self):
        with pytest.raises(ValueError, match="Could not read XLSX"):
            parse_xlsx_questionnaire_preview(b"not xlsx")


# ---------------------------------------------------------------------------
# parse_xlsx_questionnaire_full
# ---------------------------------------------------------------------------

class TestFull:
    def test_basic_extraction(self):
        data = [
            ["Question", "Answer"],
            ["Do you use MFA?", ""],
            ["Describe your patch policy.", "We patch monthly."],
        ]
        result = parse_xlsx_questionnaire_full(_make_xlsx(data), question_col=0)
        assert len(result) == 2
        assert result[0]["question"] == "Do you use MFA?"
        assert result[0]["row_index"] == 0
        assert result[1]["question"] == "Describe your patch policy."
        assert result[1]["row_index"] == 1

    def test_skips_empty_question_rows(self):
        data = [
            ["Q", "A"],
            ["Real question?", ""],
            ["", "Orphan answer"],
            [None, "Also orphan"],
            ["   ", "Whitespace question"],
        ]
        result = parse_xlsx_questionnaire_full(_make_xlsx(data), question_col=0)
        assert len(result) == 1
        assert result[0]["question"] == "Real question?"

    def test_row_index_is_zero_based_data_rows(self):
        data = [["Q"]] + [[f"Question {i}"] for i in range(5)]
        result = parse_xlsx_questionnaire_full(_make_xlsx(data), question_col=0)
        assert [r["row_index"] for r in result] == [0, 1, 2, 3, 4]

    def test_existing_answer_extracted_when_col_given(self):
        data = [
            ["Q", "Existing Answer"],
            ["Do you encrypt at rest?", "Yes, AES-256."],
            ["Do you have MFA?", ""],
        ]
        result = parse_xlsx_questionnaire_full(_make_xlsx(data), question_col=0, answer_col=1)
        assert result[0]["existing_answer"] == "Yes, AES-256."
        assert result[1]["existing_answer"] is None  # empty → None

    def test_existing_answer_none_when_no_col(self):
        data = [["Q", "A"], ["Question?", "Ignored answer"]]
        result = parse_xlsx_questionnaire_full(_make_xlsx(data), question_col=0)
        assert result[0]["existing_answer"] is None

    def test_empty_sheet_returns_empty_list(self):
        assert parse_xlsx_questionnaire_full(_make_xlsx([]), question_col=0) == []

    def test_non_default_question_column(self):
        data = [
            ["ID", "Category", "Question Text", "Notes"],
            ["1", "Access Control", "Do you use RBAC?", ""],
            ["2", "Encryption", "Is data encrypted in transit?", ""],
        ]
        result = parse_xlsx_questionnaire_full(_make_xlsx(data), question_col=2)
        assert result[0]["question"] == "Do you use RBAC?"
        assert result[1]["question"] == "Is data encrypted in transit?"

    def test_corrupted_bytes_raises(self):
        with pytest.raises(ValueError, match="Could not read XLSX"):
            parse_xlsx_questionnaire_full(b"garbage", question_col=0)

    def test_row_index_preserves_order_through_skipped_rows(self):
        data = [
            ["Q"],
            ["First question"],
            [""],            # skipped
            ["Third question"],
        ]
        result = parse_xlsx_questionnaire_full(_make_xlsx(data), question_col=0)
        assert len(result) == 2
        assert result[0]["row_index"] == 0
        assert result[1]["row_index"] == 2  # skipped row still counts in index
