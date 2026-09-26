"""Add evidencias table

Revision ID: 015
Revises: 014
Create Date: 2026-09-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'evidencias',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('estado', sa.String(50), nullable=False, server_default='ACTIVO'),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('avance_id', UUID(as_uuid=True), sa.ForeignKey('avances_producto.id'), nullable=False, index=True),
        sa.Column('municipio_id', UUID(as_uuid=True), sa.ForeignKey('municipios.id'), nullable=False, index=True),
        sa.Column('nombre', sa.String(255), nullable=False),
        sa.Column('tipo', sa.String(50), nullable=False),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('descripcion', sa.Text, nullable=True),
        sa.Column('tamano_original', sa.Integer, nullable=True),
        sa.Column('tamano_almacenado', sa.Integer, nullable=True),
        sa.Column('optimizada', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('subida_por', UUID(as_uuid=True), sa.ForeignKey('usuarios.id'), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('evidencias')
