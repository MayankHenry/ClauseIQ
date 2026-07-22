"""
Search API — hybrid retrieval + reranking, with no LLM synthesis yet
(that's Day 8/9). Useful on its own for manually evaluating retrieval
quality before the synthesis layer is added on top.
"""

from typing import Optional, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.services.retrieval import hybrid_retrieve
from app.services.reranker import rerank

router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    query: str
    document_ids: Optional[List[str]] = None
    retrieve_k: int = 20
    final_k: int = 5


class SearchResultItem(BaseModel):
    clause_id: str
    document_id: str
    text: str
    clause_type: Optional[str]
    section_number: Optional[str]
    page: Optional[int]
    bm25_score: float
    vector_score: float
    combined_score: float
    rerank_score: float


@router.post("", response_model=List[SearchResultItem])
def search_clauses(request: SearchRequest, db: Session = Depends(get_db)):
    candidates = hybrid_retrieve(
        db,
        query=request.query,
        document_ids=request.document_ids,
        top_k=request.retrieve_k,
    )
    reranked = rerank(request.query, candidates, top_k=request.final_k)
    return reranked
