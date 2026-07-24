from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, Float, JSON
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


def gen_uuid():
    return str(uuid.uuid4())


class Org(Base):
    __tablename__ = "orgs"
    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True, default=gen_uuid)
    org_id = Column(String, ForeignKey("orgs.id"), nullable=False)
    filename = Column(String, nullable=False)
    contract_type = Column(String)  # e.g. "NDA", "vendor_agreement"
    status = Column(
        String, default="uploaded"
    )  # uploaded -> parsing -> ready -> failed
    storage_path = Column(String)
    created_at = Column(DateTime, server_default=func.now())


class Clause(Base):
    __tablename__ = "clauses"
    id = Column(String, primary_key=True, default=gen_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    text = Column(Text, nullable=False)
    clause_type = Column(String)  # e.g. "termination", "auto_renewal"
    section_number = Column(String)
    page = Column(Integer)
    bbox = Column(JSON)  # for highlight-on-click


class ClauseEmbedding(Base):
    __tablename__ = "clause_embeddings"
    id = Column(String, primary_key=True, default=gen_uuid)
    clause_id = Column(String, ForeignKey("clauses.id"), nullable=False)
    qdrant_point_id = Column(String, nullable=False)
    model_name = Column(String, default="bge-large")


class Query(Base):
    __tablename__ = "queries"
    id = Column(String, primary_key=True, default=gen_uuid)
    org_id = Column(String, ForeignKey("orgs.id"))
    question = Column(Text, nullable=False)
    answer = Column(Text)
    retrieved_chunk_ids = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())


class RiskFlag(Base):
    __tablename__ = "risk_flags"
    id = Column(String, primary_key=True, default=gen_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    clause_id = Column(String, ForeignKey("clauses.id"))
    description = Column(Text)
    severity = Column(Float)  # 0-1 score
    created_at = Column(DateTime, server_default=func.now())
