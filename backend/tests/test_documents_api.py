"""
Tests for the document upload + status API.

Runs against an in-memory SQLite DB (via FastAPI dependency override) and
mocks out the Celery ingest_document.delay() call, so this suite needs no
real Postgres, Qdrant, or Redis running — fast and CI-friendly.

Run from backend/ with venv activated:
    pytest tests/test_documents_api.py -v
"""

import os
import sys
import io

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import get_db
from app.models.db import Base
import app.api.documents as documents_module


@pytest.fixture()
def client(monkeypatch, tmp_path):
    # Fresh in-memory SQLite DB per test
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Don't actually hit Celery/Redis during tests
    monkeypatch.setattr(documents_module.ingest_document, "delay", lambda document_id: None)

    # Write uploaded files to a throwaway temp dir instead of the real storage dir
    monkeypatch.setattr(documents_module.settings, "STORAGE_DIR", str(tmp_path))

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_rejects_bad_extension(client):
    response = client.post(
        "/documents/upload",
        files={"file": ("contract.exe", io.BytesIO(b"not a real contract"), "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_rejects_empty_file(client):
    response = client.post(
        "/documents/upload",
        files={"file": ("contract.txt", io.BytesIO(b""), "text/plain")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_upload_success_creates_document(client):
    response = client.post(
        "/documents/upload",
        files={"file": ("nda.txt", io.BytesIO(b"This is a test NDA contract."), "text/plain")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "nda.txt"
    assert body["status"] == "uploaded"
    assert "document_id" in body


def test_status_returns_404_for_unknown_document(client):
    response = client.get("/documents/does-not-exist/status")
    assert response.status_code == 404


def test_status_returns_uploaded_status_after_upload(client):
    upload_response = client.post(
        "/documents/upload",
        files={"file": ("nda.txt", io.BytesIO(b"Some contract text."), "text/plain")},
    )
    document_id = upload_response.json()["document_id"]

    status_response = client.get(f"/documents/{document_id}/status")
    assert status_response.status_code == 200
    body = status_response.json()
    assert body["status"] == "uploaded"
    assert body["clause_count"] is None  # not "ready" yet, so no clause count


def test_list_documents_includes_uploaded_document(client):
    client.post(
        "/documents/upload",
        files={"file": ("nda.txt", io.BytesIO(b"Some contract text."), "text/plain")},
    )
    response = client.get("/documents")
    assert response.status_code == 200
    filenames = [d["filename"] for d in response.json()]
    assert "nda.txt" in filenames
