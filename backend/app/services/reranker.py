"""
Cross-encoder reranker: re-scores the top hybrid-retrieval candidates
using a cross-encoder model, which attends to the query and passage
jointly (unlike embedding cosine similarity, which encodes them
separately) — this is what typically gives the biggest precision boost
over "vanilla" retrieval.

`predict_fn` is injectable so the merge/sort logic can be unit-tested
without loading the actual model.
"""

from typing import List, Dict, Optional, Callable

_reranker_model = None

PredictFn = Callable[[List[List[str]]], List[float]]


def _get_reranker():
    global _reranker_model
    if _reranker_model is None:
        from sentence_transformers import CrossEncoder
        _reranker_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _reranker_model


def _default_predict_fn(pairs: List[List[str]]) -> List[float]:
    model = _get_reranker()
    return list(model.predict(pairs))


def rerank(
    query: str,
    candidates: List[Dict],
    top_k: int = 5,
    predict_fn: Optional[PredictFn] = None,
) -> List[Dict]:
    """
    candidates: output of retrieval.hybrid_retrieve() — list of dicts
    with a "text" key. Returns the top_k candidates re-sorted by
    cross-encoder relevance score (added as "rerank_score" on each dict).
    """
    if not candidates:
        return []

    predict = predict_fn or _default_predict_fn
    pairs = [[query, c["text"]] for c in candidates]
    scores = predict(pairs)

    for c, score in zip(candidates, scores):
        c["rerank_score"] = float(score)

    reranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
    return reranked[:top_k]
