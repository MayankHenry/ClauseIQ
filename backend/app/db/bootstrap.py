"""
Small helper for getting a default Org row before real multi-tenant auth
lands (Day 11). Creates one "Default Org" if none exists yet, and reuses
it thereafter — used by both the upload API and local test scripts so
behavior stays consistent in the meantime.
"""

from sqlalchemy.orm import Session

from app.models.db import Org


def get_or_create_default_org(db: Session) -> Org:
    org = db.query(Org).first()
    if org:
        return org
    org = Org(name="Default Org")
    db.add(org)
    db.commit()
    db.refresh(org)
    return org
