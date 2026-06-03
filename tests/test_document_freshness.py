"""Document freshness helpers and stale-answer marking."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.db import get_db, SessionLocal
from app.main import app
from app.models import ApprovedAnswer, Document, FileType, KnowledgeChunk, SourceType, Workspace
from app.services.document_freshness import (
    REVIEW_URGENT_DAYS,
    REVIEW_WARN_DAYS,
    mark_answers_stale_for_chunk_ids,
    review_level,
    review_meta,
)
from fastapi.testclient import TestClient
import uuid


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


def test_review_levels():
    now = datetime.now(timezone.utc)
    recent = now - timedelta(days=30)
    warn = now - timedelta(days=REVIEW_WARN_DAYS)
    urgent = now - timedelta(days=REVIEW_URGENT_DAYS)
    assert review_level(recent, recent) is None
    assert review_level(warn, warn) == "warn"
    assert review_level(urgent, urgent) == "urgent"
    meta = review_meta(urgent, urgent, now=now)
    assert meta and meta["level"] == "urgent"


def test_mark_answers_stale_for_chunk_ids(db: Session):
    ws = Workspace(name="Freshness WS", slug=f"fw-{uuid.uuid4().hex[:8]}", workspace_type="company")
    db.add(ws)
    db.flush()
    doc = Document(filename="policy.pdf", file_type=FileType.pdf, chunk_count=1, workspace_id=ws.id)
    db.add(doc)
    db.flush()
    chunk = KnowledgeChunk(
        document_id=doc.id,
        source_document="policy.pdf",
        source_type=SourceType.policy,
        text="Encryption at rest.",
        is_leaf=True,
    )
    db.add(chunk)
    db.flush()
    answer = ApprovedAnswer(
        workspace_id=ws.id,
        question_text="Encrypt data?",
        answer_text="Yes, AES-256.",
        cited_chunk_ids=[chunk.id],
        status="active",
        is_stale=False,
    )
    db.add(answer)
    db.flush()

    n = mark_answers_stale_for_chunk_ids(db, ws.id, [chunk.id])
    assert n == 1
    db.refresh(answer)
    assert answer.is_stale is True

    # Idempotent — already stale
    n2 = mark_answers_stale_for_chunk_ids(db, ws.id, [chunk.id])
    assert n2 == 0


@pytest.fixture(autouse=True)
def disable_rate_limits():
    from app.limiter import limiter
    original = limiter.enabled
    limiter.enabled = False
    yield
    limiter.enabled = original


def test_freshness_summary_endpoint(db: Session):
    client = TestClient(app, raise_server_exceptions=True)
    email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/auth/register", json={
        "email": email,
        "password": "Password1!",
        "full_name": "Test",
        "workspace_name": "Fresh Co",
    })
    assert r.status_code == 200
    summary = client.get("/api/knowledge/freshness-summary")
    assert summary.status_code == 200
    body = summary.json()
    assert "stale_answer_count" in body
    assert "documents_needing_review" in body
