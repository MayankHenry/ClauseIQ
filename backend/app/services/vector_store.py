"""
Thin wrapper around the Qdrant client for clause-vector storage.
Keeps all Qdrant-specific API calls in one place so the rest of the
ingestion pipeline doesn't need to know Qdrant's client internals.
"""

import uuid
from typing import List, Dict

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from app.core.config import settings

_client = None


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=settings.QDRANT_URL)
    return _client


def ensure_collection(vector_size: int) -> None:
    """Creates the clause collection if it doesn't already exist."""
    client = get_client()
    existing = [c.name for c in client.get_collections().collections]
    if settings.QDRANT_COLLECTION not in existing:
        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )


def upsert_clause_vectors(
    clause_ids: List[str],
    vectors: List[List[float]],
    payloads: List[Dict],
) -> List[str]:
    """
    Upserts one point per clause into Qdrant. `clause_ids` is only used to
    keep call sites self-documenting (Qdrant point IDs are generated fresh
    here as UUIDs, then returned so callers can persist the mapping in
    Postgres's clause_embeddings table).
    """
    assert (
        len(clause_ids) == len(vectors) == len(payloads)
    ), "clause_ids, vectors, and payloads must all be the same length"

    client = get_client()
    point_ids = [str(uuid.uuid4()) for _ in clause_ids]

    points = [
        PointStruct(id=point_ids[i], vector=vectors[i], payload=payloads[i])
        for i in range(len(clause_ids))
    ]
    client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)
    return point_ids
