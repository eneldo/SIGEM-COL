"""Add avance revision columns

Revision ID: 010
Revises: 009
Create Date: 2026-09-23
"""

from alembic import op
import sqlalchemy as sa

revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('avances_producto', sa.Column('indicador', sa.String(300), nullable=True))
    op.add_column('avances_producto', sa.Column('periodo', sa.String(50), nullable=True))
    op.add_column('avances_producto', sa.Column('fecha_registro', sa.DateTime(timezone=True), nullable=True))
    op.add_column('avances_producto', sa.Column('estado_revision', sa.String(50), nullable=False, server_default='PENDIENTE'))
    op.add_column('avances_producto', sa.Column('evidencia_nombre', sa.String(255), nullable=True))
    op.add_column('avances_producto', sa.Column('evidencia_tipo', sa.String(50), nullable=True))
    op.create_index(op.f('ix_avances_producto_estado_revision'), 'avances_producto', ['estado_revision'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_avances_producto_estado_revision'), table_name='avances_producto')
    op.drop_column('avances_producto', 'evidencia_tipo')
    op.drop_column('avances_producto', 'evidencia_nombre')
    op.drop_column('avances_producto', 'estado_revision')
    op.drop_column('avances_producto', 'fecha_registro')
    op.drop_column('avances_producto', 'periodo')
    op.drop_column('avances_producto', 'indicador')
