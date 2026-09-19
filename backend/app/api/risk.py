"""
Risk-diffing API:
  POST /documents/{id}/set-template  -> mark a ready document as the
                                         standard template for its contract_type
  POST /documents/{id}/risk-diff     -> compare a document against its
                                         contract_type's template, persist
                                         + return risk flags
  GET  /documents/{id}/risk-flags    -> fetch previously computed flags
                                         without recomputing (feeds Day 13's
                                         frontend risk-diff dashboard)
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.models.db import Document, Clause, RiskFlag
from app.services.risk_diff import diff_clauses
from app.api.auth import require_auth

router = APIRouter(prefix="/documents", tags=["risk"])


class RiskFlagResponse(BaseModel):
    clause_id: Optional[str] = None
    clause_type: Optional[str] = None
    flag_type: Optional[str] = None
    severity: float
    description: str


class SetTemplateResponse(BaseModel):
    document_id: str
    contract_type: str
    is_template: bool


@router.post("/{document_id}/set-template", response_model=SetTemplateResponse, dependencies=[Depends(require_auth)])
def set_as_template(document_id: str, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if not document.contract_type:
        raise HTTPException(
            status_code=400,
            detail="Document has no contract_type set -- cannot be used as a template.",
        )
    if document.status != "ready":
        raise HTTPException(status_code=400, detail="Document must be fully ingested (status=ready) first.")

    # Only one template per contract_type -- unset any previous one
    db.query(Document).filter(
        Document.contract_type == document.contract_type,
        Document.is_template.is_(True),
    ).update({"is_template": False})

    document.is_template = True
    db.commit()
    db.refresh(document)

    return SetTemplateResponse(
        document_id=document.id,
        contract_type=document.contract_type,
        is_template=document.is_template,
    )


@router.post("/{document_id}/risk-diff", response_model=List[RiskFlagResponse], dependencies=[Depends(require_auth)])
def run_risk_diff(document_id: str, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.status != "ready":
        raise HTTPException(status_code=400, detail="Document must be fully ingested (status=ready) first.")
    if not document.contract_type:
        raise HTTPException(status_code=400, detail="Document has no contract_type set.")

    template = (
        db.query(Document)
        .filter(
            Document.contract_type == document.contract_type,
            Document.is_template.is_(True),
            Document.id != document.id,
        )
        .first()
    )
    if not template:
        raise HTTPException(
            status_code=400,
            detail=(
                f"No standard template found for contract_type '{document.contract_type}'. "
                f"Upload one and mark it via POST /documents/{{id}}/set-template first."
            ),
        )

    template_clauses = [
        {"clause_id": c.id, "clause_type": c.clause_type, "text": c.text}
        for c in db.query(Clause).filter(Clause.document_id == template.id).all()
    ]
    new_clauses = [
        {"clause_id": c.id, "clause_type": c.clause_type, "text": c.text}
        for c in db.query(Clause).filter(Clause.document_id == document.id).all()
    ]

    flags = diff_clauses(template_clauses, new_clauses)

    # Clear previous flags for this document before storing the fresh run
    db.query(RiskFlag).filter(RiskFlag.document_id == document.id).delete()

    for flag in flags:
        db.add(RiskFlag(
            document_id=document.id,
            clause_id=flag["clause_id"],
            clause_type=flag["clause_type"],
            flag_type=flag["flag_type"],
            description=flag["description"],
            severity=flag["severity"],
        ))
    db.commit()

    return [RiskFlagResponse(**f) for f in flags]


@router.get("/{document_id}/risk-flags", response_model=List[RiskFlagResponse])
def get_risk_flags(document_id: str, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    flags = db.query(RiskFlag).filter(RiskFlag.document_id == document_id).all()
    return [
        RiskFlagResponse(
            clause_id=f.clause_id,
            clause_type=f.clause_type,
            flag_type=f.flag_type,
            severity=f.severity,
            description=f.description,
        )
        for f in flags
    ]
