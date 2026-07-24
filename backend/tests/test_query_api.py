"""
Tests for the /query endpoint. Mocks hybrid_retrieve, rerank, and
synthesize_answer so this runs with no Postgres/Qdrant/Anthropic API
key needed — fast and CI-friendly. Uses in-memory SQLite, same pattern
as test_documents_api.py.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.models.db import Base
import app.api.query as query_module

FAKE_CANDIDATES = [
    {
        "clause_id": "c1",
        "document_id": "d1",
        "text": "Termination clause text.",
        "clause_type": "termination",
        "section_number": "3",
        "page": None,
    }
]


@pytest.fixture()
def client(monkeypatch):
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

    # Build a minimal app with just the query router mounted, so this test
    # doesn't need documents.py/search.py (and their Celery/Qdrant imports)
    # to be present -- keeps this suite focused on /query behavior only.
    app = FastAPI()
    app.include_router(query_module.router)
    app.dependency_overrides[get_db] = override_get_db

    monkeypatch.setattr(
        query_module, "hybrid_retrieve",
        lambda db, query, document_ids=None, top_k=20: FAKE_CANDIDATES,
    )
    monkeypatch.setattr(
        query_module, "rerank",
        lambda query, candidates, top_k=5: FAKE_CANDIDATES,
    )
    monkeypatch.setattr(
        query_module, "synthesize_answer",
        lambda question, candidates, call_llm_fn=None: {
            "answer": "You can terminate for material breach [clause:c1].",
            "grounded": True,
            "cited_clause_ids": ["c1"],
            "valid_clause_ids": ["c1"],
        },
    )

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_query_returns_grounded_answer(client):
    response = client.post("/query", json={"question": "When can we terminate?"})
    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is True
    assert body["cited_clauses"][0]["clause_id"] == "c1"


def test_query_response_includes_query_id(client):
    response = client.post("/query", json={"question": "When can we terminate?"})
    assert response.json()["query_id"] is not None


def test_query_only_includes_actually_cited_clauses(client, monkeypatch):
    # Two candidates retrieved, but only one gets cited -> only one should
    # appear in cited_clauses, even though both were passed to the LLM
    two_candidates = FAKE_CANDIDATES + [
        {
            "clause_id": "c2",
            "document_id": "d1",
            "text": "Unrelated clause.",
            "clause_type": "general",
            "section_number": "9",
            "page": None,
        }
    ]
    monkeypatch.setattr(query_module, "rerank", lambda query, candidates, top_k=5: two_candidates)

    response = client.post("/query", json={"question": "When can we terminate?"})
    cited_ids = [c["clause_id"] for c in response.json()["cited_clauses"]]
    assert cited_ids == ["c1"]
