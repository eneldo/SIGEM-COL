"""Add sector column to programas

Revision ID: 007
Revises: 006
Create Date: 2026-09-21
"""
from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "programas",
        sa.Column("sector", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("programas", "sector")
