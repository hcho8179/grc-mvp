"""Invite link API — create, list, validate."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import get_db, SessionLocal
from app.main import app


def unique_email() -> str:
    return f"test-{uuid.uuid4().hex[:8]}@example.com"


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


def _register_owner(client):
    email = unique_email()
    r = client.post("/api/auth/register", json={
        "email": email,
        "password": "Password1!",
        "full_name": "Owner",
        "workspace_name": "Invite Test Co",
    })
    assert r.status_code == 200, r.text
    assert r.json()["user"]["role"] == "owner"
    return r


class TestInvites:
    def test_create_list_and_validate(self, client):
        _register_owner(client)
        created = client.post("/api/auth/invites", json={})
        assert created.status_code == 200, created.text
        data = created.json()
        assert "url" in data
        assert "/invite/" in data["url"]
        token = data["url"].rstrip("/").split("/invite/")[-1]
        assert len(token) >= 32

        listed = client.get("/api/auth/invites")
        assert listed.status_code == 200
        assert any(i["status"] == "active" for i in listed.json())

        valid = client.get(f"/api/auth/invites/validate/{token}")
        assert valid.status_code == 200
        assert valid.json()["workspace_name"] == "Invite Test Co"
