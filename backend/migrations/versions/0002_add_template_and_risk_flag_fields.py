"""add is_template flag and risk flag detail columns

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-27

"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("is_template", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column("risk_flags", sa.Column("clause_type", sa.String(), nullable=True))
    op.add_column("risk_flags", sa.Column("flag_type", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("risk_flags", "flag_type")
    op.drop_column("risk_flags", "clause_type")
    op.drop_column("documents", "is_template")
