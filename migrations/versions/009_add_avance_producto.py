"""Add avance_producto table

Revision ID: 009
Revises: 008
Create Date: 2026-09-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop table if it exists from a partial run
    op.execute("DROP TABLE IF EXISTS avances_producto CASCADE")
    
    op.create_table(
        'avances_producto',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('municipio_id', UUID(as_uuid=True), sa.ForeignKey('municipios.id'), nullable=False, index=True),
        sa.Column('producto_id', UUID(as_uuid=True), sa.ForeignKey('productos.id'), nullable=False, index=True),
        sa.Column('gestor_lider_id', UUID(as_uuid=True), sa.ForeignKey('gestores_lideres.id'), nullable=False, index=True),
        sa.Column('avance_porcentaje', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('avance_valor', sa.Integer, nullable=True),
        sa.Column('observaciones', sa.Text, nullable=True),
        sa.Column('evidencia_url', sa.String(500), nullable=True),
        sa.Column('estado', sa.String(50), nullable=False, server_default='REGISTRADO'),
        sa.Column('registrado_por', UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('avances_producto')
