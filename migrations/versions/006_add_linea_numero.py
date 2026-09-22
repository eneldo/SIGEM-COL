"""Add numero column to lineas_estrategicas

Revision ID: 006
Revises: 005_seed_dependencias
Create Date: 2026-09-21
"""
from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005_seed_dependencias"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "lineas_estrategicas",
        sa.Column("numero", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("lineas_estrategicas", "numero")
