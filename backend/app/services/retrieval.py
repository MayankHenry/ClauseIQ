"""
Hybrid retrieval: combines BM25 (lexical) and vector (semantic) search
over clauses, normalizes both score sets to [0,1], and merges them into
a single ranked list.

Pure scoring/merging logic (tokenize, normalize, combine_hybrid_scores)
is separated from the DB/Qdrant-touching orchestration function
(hybrid_retrieve) so it can be unit-tested without any external services
running — same pattern as ingestion_core.py.
"""

from typing import List, Dict, Optional

from sqlalchemy.orm import Session

from app.models.db import Clause
from app.services.embeddings import embed_texts
from app.services.vector_store import get_client
from app.core.config import settings


# ---- Pure, unit-testable logic ----

def tokenize(text: str) -> List[str]:
    return text.lower().split()


def normalize(scores: List[float]) -> List[float]:
    """Min-max normalizes a list of scores to [0, 1]."""
    if not scores:
        return []
    lo, hi = min(scores), max(scores)
    if hi - lo < 1e-9:
        return [0.0 for _ in scores]
    return [(s - lo) / (hi - lo) for s in scores]


def combine_hybrid_scores(
    bm25_scores: List[float],
    vector_scores: List[float],
    bm25_weight: float = 0.5,
    vector_weight: float = 0.5,
) -> List[float]:
    """Combines two already-normalized score lists via weighted sum."""
    assert len(bm25_scores) == len(vector_scores), "score lists must be same length"
    return [
        bm25_weight * b + vector_weight * v
        for b, v in zip(bm25_scores, vector_scores)
    ]


# ---- Orchestration (touches Postgres + Qdrant) ----

def hybrid_retrieve(
    db: Session,
    query: str,
    document_ids: Optional[List[str]] = None,
    top_k: int = 10,
    bm25_weight: float = 0.5,
    vector_weight: float = 0.5,
) -> List[Dict]:
    """
    Retrieves the top_k clauses most relevant to `query`, combining BM25
    lexical scores with vector similarity scores. If document_ids is
    given, restricts the search to those documents.

    Note: BM25 index is rebuilt fresh per query over the candidate clause
    set. Fine at MVP scale (hundreds-thousands of clauses); a persistent
    inverted index would be the next optimization at larger scale.
    """
    from rank_bm25 import BM25Okapi

    q = db.query(Clause)
    if document_ids:
        q = q.filter(Clause.document_id.in_(document_ids))
    clauses = q.all()

    if not clauses:
        return []

    # --- BM25 (lexical) ---
    corpus = [tokenize(c.text) for c in clauses]
    bm25 = BM25Okapi(corpus)
    bm25_raw = list(bm25.get_scores(tokenize(query)))
    bm25_scores = normalize(bm25_raw)

    # --- Vector (semantic) ---
    query_vector = embed_texts([query])[0]
    client = get_client()

    search_filter = None
    if document_ids:
        from qdrant_client.models import Filter, FieldCondition, MatchAny
        search_filter = Filter(
            must=[FieldCondition(key="document_id", match=MatchAny(any=document_ids))]
        )

    response = client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=query_vector,
        limit=max(top_k * 5, 50),  # over-fetch so results merge well with BM25 candidates
        query_filter=search_filter,
    )
    vector_hits = response.points
    vector_score_by_clause_id = {hit.payload["clause_id"]: hit.score for hit in vector_hits}
    vector_raw = [vector_score_by_clause_id.get(c.id, 0.0) for c in clauses]
    vector_scores = normalize(vector_raw)

    # --- Combine + rank ---
    combined_scores = combine_hybrid_scores(bm25_scores, vector_scores, bm25_weight, vector_weight)

    results = [
        {
            "clause_id": clauses[i].id,
            "document_id": clauses[i].document_id,
            "text": clauses[i].text,
            "clause_type": clauses[i].clause_type,
            "section_number": clauses[i].section_number,
            "page": clauses[i].page,
            "bm25_score": bm25_scores[i],
            "vector_score": vector_scores[i],
            "combined_score": combined_scores[i],
        }
        for i in range(len(clauses))
    ]
    results.sort(key=lambda x: x["combined_score"], reverse=True)
    return results[:top_k]
