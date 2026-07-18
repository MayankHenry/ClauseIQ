"""
Unit tests for the pure ingestion logic (parsing, chunking, embedding glue).
These run with no Postgres/Qdrant/Celery required — embedding is mocked
with a trivial fake function, so this suite is fast and CI-friendly.

Run from backend/ with venv activated:
    pytest tests/test_ingestion_core.py -v
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services.ingestion_core import build_clause_records, embed_clauses

SAMPLE_CONTRACT = os.path.join(
    os.path.dirname(__file__), "..", "..", "sample_contracts", "vendor_agreement.txt"
)


def fake_embed_fn(texts):
    """Trivial fake embedding: 1-dim vector = text length. Fast, deterministic."""
    return [[float(len(t))] for t in texts]


def test_build_clause_records_returns_nonempty_list():
    clauses = build_clause_records(SAMPLE_CONTRACT)
    assert len(clauses) > 0


def test_build_clause_records_have_expected_keys():
    clauses = build_clause_records(SAMPLE_CONTRACT)
    for c in clauses:
        assert "text" in c
        assert "clause_type" in c
        assert "section_number" in c
        assert "page" in c


def test_embed_clauses_returns_one_vector_per_clause():
    clauses = build_clause_records(SAMPLE_CONTRACT)
    vectors = embed_clauses(clauses, fake_embed_fn)
    assert len(vectors) == len(clauses)


def test_embed_clauses_empty_input_returns_empty_list():
    assert embed_clauses([], fake_embed_fn) == []


def test_termination_clause_detected_in_sample():
    clauses = build_clause_records(SAMPLE_CONTRACT)
    clause_types = [c["clause_type"] for c in clauses]
    assert "termination" in clause_types or "auto_renewal" in clause_types
