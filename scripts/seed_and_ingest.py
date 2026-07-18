"""
Day 3 test script — creates a test Org + Document row pointing at a sample
contract, then runs the full ingestion pipeline SYNCHRONOUSLY (calling the
task function directly, bypassing Celery/Redis) so you can verify the whole
parse -> chunk -> embed -> store flow end-to-end without needing a worker
running yet.

Requires: Postgres, Qdrant running (docker compose up -d) and the schema
migrated (alembic upgrade head). The embedding model downloads (~130MB for
bge-small) on first run — this is normal and only happens once.

Usage (from repo root, backend venv activated):
    python scripts/seed_and_ingest.py sample_contracts/vendor_agreement.txt
"""

import sys
import os
import shutil

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.db.session import SessionLocal
from app.models.db import Org, Document
from app.workers.ingestion import ingest_document

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "storage")


def main(sample_path: str):
    os.makedirs(STORAGE_DIR, exist_ok=True)
    filename = os.path.basename(sample_path)
    dest_path = os.path.join(STORAGE_DIR, filename)
    shutil.copyfile(sample_path, dest_path)

    db = SessionLocal()
    try:
        org = db.query(Org).first()
        if not org:
            org = Org(name="Test Org")
            db.add(org)
            db.commit()
            db.refresh(org)

        document = Document(
            org_id=org.id,
            filename=filename,
            contract_type="vendor_agreement",
            status="uploaded",
            storage_path=dest_path,
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        document_id = document.id
        print(f"Created document {document_id} ({filename}). Running ingestion...")
    finally:
        db.close()

    result = ingest_document(document_id)
    print("Ingestion result:", result)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/seed_and_ingest.py <path_to_sample_contract>")
        sys.exit(1)
    main(sys.argv[1])
