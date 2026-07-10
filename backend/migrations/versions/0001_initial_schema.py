"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-10

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "orgs",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("org_id", sa.String, sa.ForeignKey("orgs.id"), nullable=False),
        sa.Column("filename", sa.String, nullable=False),
        sa.Column("contract_type", sa.String),
        sa.Column("status", sa.String, server_default="uploaded"),
        sa.Column("storage_path", sa.String),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "clauses",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("document_id", sa.String, sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("clause_type", sa.String),
        sa.Column("section_number", sa.String),
        sa.Column("page", sa.Integer),
        sa.Column("bbox", sa.JSON),
    )

    op.create_table(
        "clause_embeddings",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("clause_id", sa.String, sa.ForeignKey("clauses.id"), nullable=False),
        sa.Column("qdrant_point_id", sa.String, nullable=False),
        sa.Column("model_name", sa.String, server_default="bge-large"),
    )

    op.create_table(
        "queries",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("org_id", sa.String, sa.ForeignKey("orgs.id")),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("answer", sa.Text),
        sa.Column("retrieved_chunk_ids", sa.JSON),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "risk_flags",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("document_id", sa.String, sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("clause_id", sa.String, sa.ForeignKey("clauses.id")),
        sa.Column("description", sa.Text),
        sa.Column("severity", sa.Float),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("risk_flags")
    op.drop_table("queries")
    op.drop_table("clause_embeddings")
    op.drop_table("clauses")
    op.drop_table("documents")
    op.drop_table("orgs")
