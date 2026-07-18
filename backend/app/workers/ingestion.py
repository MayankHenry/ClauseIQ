"""
Document ingestion pipeline, wired up as a Celery task.

Flow: parse -> chunk -> persist clause rows to Postgres -> embed ->
      upsert vectors to Qdrant -> persist clause_embeddings rows ->
      mark document "ready" (or "failed" if anything raises).

Can be called two ways:
  - ingest_document.delay(document_id)   -> async, via Celery worker + Redis
  - ingest_document(document_id)         -> sync, direct call (used by
                                             scripts/seed_and_ingest.py for
                                             local testing without a worker)
"""

from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.db import Document, Clause, ClauseEmbedding
from app.services.ingestion_core import build_clause_records
from app.services.embeddings import embed_texts, get_embedding_dim
from app.services.vector_store import ensure_collection, upsert_clause_vectors
from app.core.config import settings


@celery_app.task(name="ingest_document")
def ingest_document(document_id: str) -> dict:
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")

        document.status = "parsing"
        db.commit()

        # 1. Parse + chunk
        clause_dicts = build_clause_records(document.storage_path)

        if not clause_dicts:
            document.status = "failed"
            db.commit()
            return {"document_id": document_id, "status": "failed", "reason": "no clauses extracted"}

        # 2. Persist clause rows first, so we have real clause_ids to use
        #    as Qdrant payload references (needed for click-to-highlight later)
        clause_rows = []
        for c in clause_dicts:
            clause = Clause(
                document_id=document.id,
                text=c["text"],
                clause_type=c["clause_type"],
                section_number=c["section_number"],
                page=c["page"],
                bbox=None,  # populated once PDF bbox-mapping is added (later day)
            )
            db.add(clause)
            clause_rows.append(clause)
        db.flush()  # assigns IDs without committing yet, so we can roll back on failure

        # 3. Embed
        texts = [c["text"] for c in clause_dicts]
        vectors = embed_texts(texts)

        # 4. Upsert to Qdrant
        ensure_collection(vector_size=get_embedding_dim())
        payloads = [
            {
                "clause_id": clause_rows[i].id,
                "document_id": document.id,
                "org_id": document.org_id,
                "clause_type": clause_rows[i].clause_type,
                "section_number": clause_rows[i].section_number,
                "page": clause_rows[i].page,
            }
            for i in range(len(clause_rows))
        ]
        clause_ids = [c.id for c in clause_rows]
        point_ids = upsert_clause_vectors(clause_ids, vectors, payloads)

        # 5. Persist clause_embeddings linking clause -> qdrant point
        for i, clause in enumerate(clause_rows):
            db.add(ClauseEmbedding(
                clause_id=clause.id,
                qdrant_point_id=point_ids[i],
                model_name=settings.EMBEDDING_MODEL_NAME,
            ))

        document.status = "ready"
        db.commit()

        return {"document_id": document_id, "status": "ready", "clause_count": len(clause_rows)}

    except Exception:
        db.rollback()
        failed_doc = db.query(Document).filter(Document.id == document_id).first()
        if failed_doc:
            failed_doc.status = "failed"
            db.commit()
        raise
    finally:
        db.close()
