"""Add avances_producto.observaciones_revision

Revision ID: 014
Revises: 013
Create Date: 2026-09-23
"""

from alembic import op
import sqlalchemy as sa

revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('avances_producto', sa.Column('observaciones_revision', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('avances_producto', 'observaciones_revision')
