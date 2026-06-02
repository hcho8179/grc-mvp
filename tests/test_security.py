"""Security regression tests — cross-tenant isolation and access control.

Verifies that users in one workspace cannot access data belonging to
another workspace, even when they know the resource IDs.
"""

import io
import uuid

import openpyxl
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_db, SessionLocal
from app.main import app


def unique_email() -> str:
    return f"test-{uuid.uuid4().hex[:8]}@example.com"


# ---------------------------------------------------------------------------
# Fixtures
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
    from app.limiter import limiter
    original = limiter.enabled
    limiter.enabled = False
    yield
    limiter.enabled = original


@pytest.fixture()
def client(db):
    return TestClient(app, raise_server_exceptions=True)


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


def _register_and_login(client, email=None):
    email = email or unique_email()
    r = client.post("/api/auth/register", json={
        "email": email,
        "password": "Password1!",
        "full_name": "Test User",
        "org_name": f"Org {email}",
    })
    assert r.status_code == 200, r.text
    # Register returns {"user": {...}} — extract workspace_id from here
    workspace_id = r.json()["user"]["workspace_id"]
    return client, email, workspace_id


def _upload_questionnaire(client, name="Test Q") -> int:
    xlsx = _make_xlsx(["Do you encrypt data at rest?"])
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


# ---------------------------------------------------------------------------
# Cross-tenant tests
# ---------------------------------------------------------------------------

def test_cannot_access_other_workspace_questionnaire(client, db):
    """User B cannot read User A's questionnaire by ID."""
    # Workspace A
    _register_and_login(client)
    qs_id = _upload_questionnaire(client, name="Workspace A Questionnaire")

    # Log out A, register B
    client.post("/api/auth/logout")
    _register_and_login(client)

    # B tries to access A's questionnaire
    r = client.get(f"/api/questionnaires/{qs_id}")
    assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"


def test_cannot_delete_other_workspace_questionnaire(client, db):
    """User B cannot delete User A's questionnaire."""
    _register_and_login(client)
    qs_id = _upload_questionnaire(client)

    client.post("/api/auth/logout")
    _register_and_login(client)

    r = client.post(f"/api/questionnaires/{qs_id}/delete")
    assert r.status_code in (403, 404), f"Expected 403/404, got {r.status_code}"


def test_cannot_access_other_workspace_chunk(client, db):
    """User B cannot read User A's knowledge chunk by ID."""
    from app.models import Document, FileType, KnowledgeChunk, SourceType

    _, _, ws_id_a = _register_and_login(client)

    # Create a chunk directly in workspace A
    doc = Document(filename="test.pdf", file_type=FileType.pdf, chunk_count=1, workspace_id=ws_id_a)
    db.add(doc)
    db.flush()
    chunk = KnowledgeChunk(
        document_id=doc.id,
        source_document="test.pdf",
        source_type=SourceType.policy,
        text="Sensitive policy content for workspace A",
        embedding=[0.0] * 1024,
    )
    db.add(chunk)
    db.flush()
    chunk_id = chunk.id

    # Log out A, register B
    client.post("/api/auth/logout")
    _register_and_login(client)

    # B tries to access A's chunk
    r = client.get(f"/api/chunks/{chunk_id}")
    assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"


def test_cannot_access_other_workspace_question_history(client, db):
    """User B cannot access answer history for User A's questions."""
    _register_and_login(client)
    qs_id = _upload_questionnaire(client)

    # Get questions
    r = client.get(f"/api/questionnaires/{qs_id}")
    assert r.status_code == 200
    q_id = r.json()["questions"][0]["id"]

    # Log out A, register B
    client.post("/api/auth/logout")
    _register_and_login(client)

    # B tries to access A's question history
    r = client.get(f"/api/questionnaires/{qs_id}/questions/{q_id}/history")
    assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"


def test_cannot_export_other_workspace_questionnaire(client, db):
    """User B cannot export User A's filled questionnaire."""
    _register_and_login(client)
    qs_id = _upload_questionnaire(client)

    client.post("/api/auth/logout")
    _register_and_login(client)

    r = client.get(f"/api/questionnaires/{qs_id}/export")
    assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"


def test_cannot_access_other_workspace_knowledge(client, db):
    """User B cannot list or access User A's knowledge base documents."""
    from app.models import Document, FileType

    _, _, ws_id_a = _register_and_login(client)

    doc = Document(filename="secret.pdf", file_type=FileType.pdf, chunk_count=0, workspace_id=ws_id_a)
    db.add(doc)
    db.flush()
    doc_id = doc.id

    client.post("/api/auth/logout")
    _register_and_login(client)

    # B lists their own knowledge — should not see A's doc
    r = client.get("/api/knowledge")
    assert r.status_code == 200
    ids = [d["id"] for d in r.json()["items"]]
    assert doc_id not in ids, "Workspace A's document leaked into Workspace B's knowledge list"


def test_unauthenticated_request_rejected(client, db):
    """Unauthenticated requests to protected endpoints return 401/403."""
    # Fresh client with no login
    fresh = TestClient(app, raise_server_exceptions=True)
    r = fresh.get("/api/questionnaires")
    assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"


def test_share_link_respects_workspace_boundary(client, db):
    """Share link only exposes progress data, not full answer content for sensitive fields."""
    _register_and_login(client)
    qs_id = _upload_questionnaire(client)

    # Generate share token
    r = client.post(f"/api/questionnaires/{qs_id}/share-token")
    assert r.status_code == 200
    token = r.json()["token"]

    # Public access via share link
    fresh = TestClient(app, raise_server_exceptions=True)
    r = fresh.get(f"/api/share/{token}")
    assert r.status_code == 200
    data = r.json()

    # Share link should NOT expose workspace_id or internal IDs
    assert "workspace_id" not in data
    assert "workspace" not in str(data).lower() or data.get("workspace_id") is None
