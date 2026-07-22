"""
Unit tests for the reranker's merge/sort logic, using a fake predict_fn
so no cross-encoder model needs to load — fast and CI-friendly.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services.reranker import rerank


def fake_predict_fn(pairs):
    """Fake relevance score: longer passage text = higher score. Deterministic."""
    return [float(len(passage)) for _, passage in pairs]


def make_candidate(text, clause_id="id"):
    return {"clause_id": clause_id, "text": text}


def test_rerank_empty_candidates_returns_empty():
    assert rerank("query", [], predict_fn=fake_predict_fn) == []


def test_rerank_sorts_by_score_descending():
    candidates = [
        make_candidate("short", "a"),
        make_candidate("a much longer passage of text here", "b"),
        make_candidate("medium length text", "c"),
    ]
    result = rerank("query", candidates, top_k=3, predict_fn=fake_predict_fn)
    assert [c["clause_id"] for c in result] == ["b", "c", "a"]


def test_rerank_respects_top_k():
    candidates = [make_candidate(f"text {i}" * i, str(i)) for i in range(1, 6)]
    result = rerank("query", candidates, top_k=2, predict_fn=fake_predict_fn)
    assert len(result) == 2


def test_rerank_adds_rerank_score_field():
    candidates = [make_candidate("some text", "a")]
    result = rerank("query", candidates, predict_fn=fake_predict_fn)
    assert "rerank_score" in result[0]
