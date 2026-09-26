"""Add productos.asignado_at

Revision ID: 013
Revises: 012
Create Date: 2026-09-23
"""

from alembic import op
import sqlalchemy as sa

revision = '013'
down_revision = '012_seed_catalogo_productos_programas'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('productos', sa.Column('asignado_at', sa.DateTime(timezone=True), nullable=True))
    op.execute("""
        UPDATE productos
        SET asignado_at = updated_at
        WHERE gestor_lider_id IS NOT NULL AND asignado_at IS NULL
    """)


def downgrade() -> None:
    op.drop_column('productos', 'asignado_at')
