"""
Unit tests for retrieval scoring/merging logic. These test the pure
functions only (tokenize, normalize, combine_hybrid_scores) — no
Postgres/Qdrant required, so this suite is fast and CI-friendly.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services.retrieval import tokenize, normalize, combine_hybrid_scores


def test_tokenize_lowercases_and_splits():
    assert tokenize("Termination Clause") == ["termination", "clause"]


def test_normalize_scales_to_zero_one():
    result = normalize([10.0, 20.0, 30.0])
    assert result[0] == 0.0
    assert result[-1] == 1.0
    assert 0.0 < result[1] < 1.0


def test_normalize_handles_identical_scores():
    # all-equal input shouldn't divide by zero
    assert normalize([5.0, 5.0, 5.0]) == [0.0, 0.0, 0.0]


def test_normalize_empty_list():
    assert normalize([]) == []


def test_combine_hybrid_scores_weighted_sum():
    bm25 = [1.0, 0.0]
    vector = [0.0, 1.0]
    combined = combine_hybrid_scores(bm25, vector, bm25_weight=0.5, vector_weight=0.5)
    assert combined == [0.5, 0.5]


def test_combine_hybrid_scores_respects_weights():
    bm25 = [1.0]
    vector = [0.0]
    # weighting entirely toward BM25 should return the BM25 score untouched
    combined = combine_hybrid_scores(bm25, vector, bm25_weight=1.0, vector_weight=0.0)
    assert combined == [1.0]


def test_combine_hybrid_scores_mismatched_lengths_raises():
    try:
        combine_hybrid_scores([1.0, 2.0], [1.0])
        assert False, "expected an assertion error for mismatched lengths"
    except AssertionError:
        pass
