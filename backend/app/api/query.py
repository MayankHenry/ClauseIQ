"""
POST /query — the main question-answering endpoint. Wires together
hybrid retrieval, reranking, and citation-grounded synthesis, and logs
every query + retrieved chunk IDs + answer to the `queries` table for
future retrieval-quality evaluation.
"""

from typing import Optional, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.db.bootstrap import get_or_create_default_org
from app.models.db import Query as QueryModel
from app.services.retrieval import hybrid_retrieve
from app.services.reranker import rerank
from app.services.synthesis import synthesize_answer

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    question: str
    document_ids: Optional[List[str]] = None
    retrieve_k: int = 20
    final_k: int = 5


class CitedClause(BaseModel):
    clause_id: str
    document_id: str
    section_number: Optional[str] = None
    clause_type: Optional[str] = None
    page: Optional[int] = None
    text: str


class QueryResponse(BaseModel):
    query_id: str
    answer: str
    grounded: bool
    cited_clauses: List[CitedClause]


@router.post("", response_model=QueryResponse)
def ask_question(request: QueryRequest, db: Session = Depends(get_db)):
    org = get_or_create_default_org(db)

    candidates = hybrid_retrieve(
        db,
        query=request.question,
        document_ids=request.document_ids,
        top_k=request.retrieve_k,
    )
    reranked = rerank(request.question, candidates, top_k=request.final_k)

    result = synthesize_answer(request.question, reranked)

    cited_ids = set(result["cited_clause_ids"])
    cited_clauses = [
        CitedClause(
            clause_id=c["clause_id"],
            document_id=c["document_id"],
            section_number=c.get("section_number"),
            clause_type=c.get("clause_type"),
            page=c.get("page"),
            text=c["text"],
        )
        for c in reranked
        if c["clause_id"] in cited_ids
    ]

    # Log every query + what was retrieved + the final answer, so retrieval
    # quality can be reviewed/eval'd later without re-running the pipeline
    query_row = QueryModel(
        org_id=org.id,
        question=request.question,
        answer=result["answer"],
        retrieved_chunk_ids=[c["clause_id"] for c in reranked],
    )
    db.add(query_row)
    db.commit()
    db.refresh(query_row)

    return QueryResponse(
        query_id=query_row.id,
        answer=result["answer"],
        grounded=result["grounded"],
        cited_clauses=cited_clauses,
    )
