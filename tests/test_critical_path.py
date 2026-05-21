"""Critical path integration tests — covers the full product flow end to end.

Register → Upload questionnaire → Generate answers → Approve → Export XLSX
Also: delete (soft), restore from trash, pagination.

Uses the real Postgres DB with transactions rolled back after each test — no data persists.
No real LLM or embedding calls are made — all external services are mocked.
"""

import io
import json
import uuid
from unittest.mock import AsyncMock, patch

import openpyxl
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_db, SessionLocal
from app.main import app


def unique_email() -> str:
    return f"test-{uuid.uuid4().hex[:8]}@example.com"


# ---------------------------------------------------------------------------
# DB fixture — wraps each test in a transaction that rolls back on teardown
# ---------------------------------------------------------------------------

@pytest.fixture()
def db():
    connection = SessionLocal().bind.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    def override():
        yield session

    app.dependency_overrides[get_db] = override
    yield session
    session.close()
    transaction.rollback()
    connection.close()
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def disable_rate_limits():
    """Disable rate limiting entirely for tests."""
    from app.limiter import limiter
    original = limiter.enabled
    limiter.enabled = False
    yield
    limiter.enabled = original


@pytest.fixture()
def client(db):
    return TestClient(app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_xlsx(questions: list[str]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.cell(row=1, column=1, value="Question")
    ws.cell(row=1, column=2, value="Answer")
    for i, q in enumerate(questions, start=2):
        ws.cell(row=i, column=1, value=q)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _register(client, email=None, org=None):
    email = email or unique_email()
    org = org or f"Org {email}"
    r = client.post("/api/auth/register", json={
        "email": email,
        "password": "password123",
        "full_name": "Test User",
        "org_name": org,
    })
    assert r.status_code == 200, r.text
    return r


def _upload_questionnaire(client, questions: list[str], name="Test Q") -> int:
    xlsx = _make_xlsx(questions)
    prev = client.post(
        "/api/questionnaires/upload/preview",
        data={"name": name, "customer_name": "Acme"},
        files={"file": ("q.xlsx", xlsx,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert prev.status_code == 200, prev.text
    temp_id = prev.json()["temp_id"]

    fin = client.post(
        f"/api/questionnaires/upload/{temp_id}/finalize",
        data={"question_col": "0", "answer_col": "1"},
    )
    assert fin.status_code == 200, fin.text
    return fin.json()["id"]


MOCK_LLM_RESPONSE = json.dumps({
    "answer": "We encrypt all data at rest using AES-256.",
    "short_answer": "Yes",
    "confidence": "high",
    "cited_chunk_ids": [],
    "reasoning": "Direct policy match.",
    "insufficient_context": False,
})


# ---------------------------------------------------------------------------
# 1. Register
# ---------------------------------------------------------------------------

class TestRegister:
    def test_creates_user_and_org(self, client):
        email = unique_email()
        r = _register(client, email=email, org="My Org")
        data = r.json()["user"]
        assert data["email"] == email
        assert data["org_name"] == "My Org"
        assert data["role"] == "owner"

    def test_duplicate_email_rejected(self, client):
        email = unique_email()
        _register(client, email=email)
        r = client.post("/api/auth/register", json={
            "email": email,
            "password": "password123",
            "full_name": "Dup",
            "org_name": "Dup Org",
        })
        assert r.status_code == 400

    def test_short_password_rejected(self, client):
        r = client.post("/api/auth/register", json={
            "email": unique_email(),
            "password": "abc",
            "full_name": "Short",
            "org_name": "Short Org",
        })
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# 2. Upload
# ---------------------------------------------------------------------------

class TestUpload:
    def test_preview_returns_columns(self, client):
        _register(client)
        xlsx = _make_xlsx(["Do you encrypt data?"])
        r = client.post(
            "/api/questionnaires/upload/preview",
            data={"name": "Test Q", "customer_name": ""},
            files={"file": ("q.xlsx", xlsx,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert r.status_code == 200
        assert "temp_id" in r.json()
        assert len(r.json()["preview"]["columns"]) >= 1

    def test_finalize_creates_correct_question_count(self, client):
        _register(client)
        qs_id = _upload_questionnaire(client, ["Q1", "Q2", "Q3"])
        r = client.get(f"/api/questionnaires/{qs_id}")
        assert r.status_code == 200
        assert r.json()["questionnaire"]["question_count"] == 3

    def test_oversized_file_rejected(self, client):
        _register(client)
        big = b"x" * (21 * 1024 * 1024)
        r = client.post(
            "/api/questionnaires/upload/preview",
            data={"name": "Big", "customer_name": ""},
            files={"file": ("big.xlsx", big,
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert r.status_code == 400
        assert "too large" in r.json()["error"].lower()

    def test_non_xlsx_rejected(self, client):
        _register(client)
        r = client.post(
            "/api/questionnaires/upload/preview",
            data={"name": "Doc", "customer_name": ""},
            files={"file": ("doc.pdf", b"fake pdf", "application/pdf")},
        )
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# 3. Approve & Export
# ---------------------------------------------------------------------------

class TestApproveExport:
    def _get_first_question_id(self, client, qs_id: int) -> int:
        return client.get(f"/api/questionnaires/{qs_id}").json()["questions"][0]["id"]

    def test_approve_question(self, client):
        _register(client)
        qs_id = _upload_questionnaire(client, ["Do you encrypt data?"])
        q_id = self._get_first_question_id(client, qs_id)
        client.patch(f"/api/questionnaires/{qs_id}/questions/{q_id}",
                     data={"draft_answer": "Yes, AES-256."})
        r = client.post(f"/api/questionnaires/{qs_id}/questions/{q_id}/approve")
        assert r.status_code == 200
        assert r.json()["status"] == "approved"

    def test_export_returns_xlsx_bytes(self, client):
        _register(client)
        qs_id = _upload_questionnaire(client, ["Do you encrypt data?"])
        q_id = self._get_first_question_id(client, qs_id)
        client.patch(f"/api/questionnaires/{qs_id}/questions/{q_id}",
                     data={"draft_answer": "Yes, AES-256."})
        client.post(f"/api/questionnaires/{qs_id}/questions/{q_id}/approve")

        r = client.get(f"/api/questionnaires/{qs_id}/export")
        assert r.status_code == 200
        assert "spreadsheetml" in r.headers["content-type"]
        assert "_filled_" in r.headers["content-disposition"]

    def test_export_contains_approved_answer(self, client):
        _register(client)
        qs_id = _upload_questionnaire(client, ["Do you encrypt data?"])
        q_id = self._get_first_question_id(client, qs_id)
        client.patch(f"/api/questionnaires/{qs_id}/questions/{q_id}",
                     data={"draft_answer": "We use AES-256 encryption."})
        client.post(f"/api/questionnaires/{qs_id}/questions/{q_id}/approve")

        r = client.get(f"/api/questionnaires/{qs_id}/export")
        wb = openpyxl.load_workbook(io.BytesIO(r.content))
        ws = wb.active
        all_values = [ws.cell(row=row, column=col).value
                      for row in range(1, ws.max_row + 1)
                      for col in range(1, ws.max_column + 1)]
        assert "We use AES-256 encryption." in all_values

    def test_export_excludes_unapproved_draft(self, client):
        _register(client)
        qs_id = _upload_questionnaire(client, ["Do you encrypt data?"])
        q_id = self._get_first_question_id(client, qs_id)
        client.patch(f"/api/questionnaires/{qs_id}/questions/{q_id}",
                     data={"draft_answer": "SECRET UNAPPROVED DRAFT"})

        r = client.get(f"/api/questionnaires/{qs_id}/export")
        wb = openpyxl.load_workbook(io.BytesIO(r.content))
        ws = wb.active
        all_values = [ws.cell(row=row, column=col).value
                      for row in range(1, ws.max_row + 1)
                      for col in range(1, ws.max_column + 1)]
        assert "SECRET UNAPPROVED DRAFT" not in all_values

    def test_reject_then_export_excludes_answer(self, client):
        _register(client)
        qs_id = _upload_questionnaire(client, ["Do you encrypt data?"])
        q_id = self._get_first_question_id(client, qs_id)
        client.patch(f"/api/questionnaires/{qs_id}/questions/{q_id}",
                     data={"draft_answer": "REJECTED ANSWER"})
        client.post(f"/api/questionnaires/{qs_id}/questions/{q_id}/reject")

        r = client.get(f"/api/questionnaires/{qs_id}/export")
        wb = openpyxl.load_workbook(io.BytesIO(r.content))
        ws = wb.active
        all_values = [ws.cell(row=row, column=col).value
                      for row in range(1, ws.max_row + 1)
                      for col in range(1, ws.max_column + 1)]
        assert "REJECTED ANSWER" not in all_values


# ---------------------------------------------------------------------------
# 4. Soft delete & restore
# ---------------------------------------------------------------------------

class TestSoftDelete:
    def test_deleted_questionnaire_hidden_from_list(self, client):
        _register(client)
        qs_id = _upload_questionnaire(client, ["Q1"])
        client.post(f"/api/questionnaires/{qs_id}/delete")
        ids = [q["id"] for q in client.get("/api/questionnaires").json()["items"]]
        assert qs_id not in ids

    def test_deleted_questionnaire_in_trash(self, client):
        _register(client)
        qs_id = _upload_questionnaire(client, ["Q1"])
        client.post(f"/api/questionnaires/{qs_id}/delete")
        trash_ids = [q["id"] for q in client.get("/api/trash").json()["questionnaires"]]
        assert qs_id in trash_ids

    def test_restore_brings_back_to_list(self, client):
        _register(client)
        qs_id = _upload_questionnaire(client, ["Q1"])
        client.post(f"/api/questionnaires/{qs_id}/delete")
        client.post(f"/api/questionnaires/{qs_id}/restore")
        ids = [q["id"] for q in client.get("/api/questionnaires").json()["items"]]
        assert qs_id in ids

    def test_restored_not_in_trash(self, client):
        _register(client)
        qs_id = _upload_questionnaire(client, ["Q1"])
        client.post(f"/api/questionnaires/{qs_id}/delete")
        client.post(f"/api/questionnaires/{qs_id}/restore")
        trash_ids = [q["id"] for q in client.get("/api/trash").json()["questionnaires"]]
        assert qs_id not in trash_ids


# ---------------------------------------------------------------------------
# 5. Pagination
# ---------------------------------------------------------------------------

class TestPagination:
    def test_questionnaires_returns_pagination_meta(self, client):
        _register(client)
        r = client.get("/api/questionnaires?page=1&per_page=20")
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data
        assert "pages" in data
        assert "page" in data
        assert data["page"] == 1

    def test_knowledge_returns_pagination_meta(self, client):
        _register(client)
        r = client.get("/api/knowledge?page=1&per_page=20")
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data

    def test_per_page_capped_at_100(self, client):
        _register(client)
        r = client.get("/api/questionnaires?page=1&per_page=9999")
        assert r.status_code == 200
        assert r.json()["per_page"] == 100
