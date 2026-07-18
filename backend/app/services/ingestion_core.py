"""
Pure ingestion logic — parsing, chunking, and embedding glue code that
doesn't touch Postgres, Qdrant, or Celery directly. Kept separate from
workers/ingestion.py so it can be unit-tested with fake embedding
functions and no external services running (see backend/tests/).
"""

from typing import Callable, List, Dict

from app.services.parsers import parse_document
from app.services.chunker import chunk_document

EmbedFn = Callable[[List[str]], List[List[float]]]


def build_clause_records(file_path: str) -> List[Dict]:
    """Parses and chunks a document into clause dicts (no embedding yet)."""
    pages = parse_document(file_path)
    clauses = chunk_document(pages)
    return clauses


def embed_clauses(clauses: List[Dict], embed_fn: EmbedFn) -> List[List[float]]:
    """Embeds the text of each clause using the given embedding function."""
    if not clauses:
        return []
    texts = [c["text"] for c in clauses]
    return embed_fn(texts)
