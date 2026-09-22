"""Add indicador fields to productos

Revision ID: 008
Revises: 007
Create Date: 2026-09-21
"""
from alembic import op
import sqlalchemy as sa

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('productos', sa.Column('codigo_indicador', sa.String(30), nullable=True))
    op.add_column('productos', sa.Column('indicador', sa.String(300), nullable=True))
    op.add_column('productos', sa.Column('meta_redactada', sa.Text(), nullable=True))
    op.add_column('productos', sa.Column('linea_base', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('productos', sa.Column('meta_cuatrienio', sa.Integer(), nullable=True, server_default='0'))


def downgrade() -> None:
    op.drop_column('productos', 'meta_cuatrienio')
    op.drop_column('productos', 'linea_base')
    op.drop_column('productos', 'meta_redactada')
    op.drop_column('productos', 'indicador')
    op.drop_column('productos', 'codigo_indicador')
