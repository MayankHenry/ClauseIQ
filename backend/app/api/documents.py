"""
Document upload + status API.

POST /documents/upload       -> accepts a PDF/DOCX/TXT file, saves it to disk,
                                 creates a Document row (status="uploaded"),
                                 and enqueues the ingestion pipeline as an
                                 async Celery task.
GET  /documents/{id}/status  -> returns current status, and clause count once ready.
GET  /documents              -> lists all documents (feeds the frontend doc list).
GET  /documents/{id}/file    -> serves the original uploaded file bytes, so the
                                 frontend can render it (e.g. PDF.js for PDFs).
"""

import os
import uuid
from typing import Optional, List

from fastapi import APIRouter, BackgroundTasks, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.db.bootstrap import get_or_create_default_org
from app.models.db import Document, Clause
from app.core.config import settings
from app.workers.ingestion import ingest_document
from app.api.auth import require_auth

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25MB

MEDIA_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
}


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str


class DocumentStatusResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    contract_type: Optional[str] = None
    clause_count: Optional[int] = None


class DocumentListItem(BaseModel):
    document_id: str
    filename: str
    status: str
    contract_type: Optional[str] = None


@router.post("/upload", response_model=DocumentUploadResponse, dependencies=[Depends(require_auth)])
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    contract_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    ext = file.filename.lower().rsplit(".", 1)[-1] if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '.{ext}'. Allowed: {allowed}",
        )

    os.makedirs(settings.STORAGE_DIR, exist_ok=True)

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size is {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB.",
        )
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    stored_filename = f"{uuid.uuid4()}_{file.filename}"
    dest_path = os.path.join(settings.STORAGE_DIR, stored_filename)
    with open(dest_path, "wb") as f:
        f.write(contents)

    org = get_or_create_default_org(db)

    document = Document(
        org_id=org.id,
        filename=file.filename,
        contract_type=contract_type,
        status="uploaded",
        storage_path=dest_path,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    if settings.INGESTION_MODE == "celery":
        ingest_document.delay(document.id)
    else:
        background_tasks.add_task(ingest_document, document.id)

    return DocumentUploadResponse(
        document_id=document.id,
        filename=document.filename,
        status=document.status,
    )


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def get_document_status(document_id: str, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    clause_count = None
    if document.status == "ready":
        clause_count = db.query(Clause).filter(Clause.document_id == document.id).count()

    return DocumentStatusResponse(
        document_id=document.id,
        filename=document.filename,
        status=document.status,
        contract_type=document.contract_type,
        clause_count=clause_count,
    )


@router.get("", response_model=List[DocumentListItem])
def list_documents(db: Session = Depends(get_db)):
    documents = db.query(Document).order_by(Document.created_at.desc()).all()
    return [
        DocumentListItem(
            document_id=d.id,
            filename=d.filename,
            status=d.status,
            contract_type=d.contract_type,
        )
        for d in documents
    ]


@router.get("/{document_id}/file")
def get_document_file(document_id: str, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if not document.storage_path or not os.path.exists(document.storage_path):
        raise HTTPException(status_code=404, detail="Original file no longer available on disk")

    ext = document.filename.lower().rsplit(".", 1)[-1] if "." in document.filename else ""
    media_type = MEDIA_TYPES.get(ext, "application/octet-stream")

    return FileResponse(document.storage_path, media_type=media_type, filename=document.filename)
