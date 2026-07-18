"""
Embedding service — wraps a sentence-transformers model (bge-small by
default; swappable to bge-large or any other model via EMBEDDING_MODEL_NAME
in config, with zero code changes elsewhere).

The model is loaded lazily on first use, not at import time, so importing
this module doesn't trigger a slow model download/load in contexts that
don't need it (e.g. running the chunker tests alone).
"""

from typing import List

from app.core.config import settings

_model = None
_embedding_dim = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embeds a list of texts and returns a list of float vectors.
    Uses cosine-normalized embeddings (recommended for bge models) so
    Qdrant's COSINE distance metric behaves correctly.
    """
    if not texts:
        return []
    model = _get_model()
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return vectors.tolist()


def get_embedding_dim() -> int:
    """
    Returns the output dimension of the current embedding model, detected
    at runtime by embedding a throwaway string once and caching the result.
    This means swapping EMBEDDING_MODEL_NAME (e.g. bge-small's 384 dims vs
    bge-large's 1024 dims) never requires a manual constant update anywhere
    else in the codebase.
    """
    global _embedding_dim
    if _embedding_dim is None:
        vectors = embed_texts(["dimension probe"])
        _embedding_dim = len(vectors[0])
    return _embedding_dim
