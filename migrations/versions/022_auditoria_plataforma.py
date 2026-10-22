"""Tabla de auditoría de plataforma (eventos sin municipio)

Revision ID: 022_auditoria_plataforma
Revises: 021_function_invoker
Create Date: 2026-10-21

`auditoria_eventos.municipio_id` es nullable pero su política RLS es
fail-closed (`municipio_id = NULLIF(...)::uuid`), de modo que un evento global
(municipio NULL) no podía escribirse ni leerse con el rol de aplicación. Esta
tabla toma ese sector: no es multi-municipio y no tiene RLS, y el rol de
aplicación solo recibe INSERT (append-only); UPDATE/DELETE quedan para el rol
de migración. La escritura es idempotente: si `sigem_app` aún no existe en la
base destino, los grants se omiten y `scripts/setup/grant_app_role_local.py`
los aplicará al crear el rol (los default privileges ya cubren INSERT).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '022_auditoria_plataforma'
down_revision = '021_function_invoker'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'auditoria_plataforma',
        sa.Column('id', postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('usuario_id', postgresql.UUID(), nullable=True),
        sa.Column('actor_id', postgresql.UUID(), nullable=True),
        sa.Column('evento_tipo', sa.String(length=100), nullable=False),
        sa.Column('recurso_tipo', sa.String(length=100), nullable=True),
        sa.Column('recurso_id', postgresql.UUID(), nullable=True),
        sa.Column('resultado', sa.String(length=50), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column(
            'fecha_evento', sa.DateTime(timezone=True), server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name='fk_auditoria_plataforma_usuario'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_auditoria_plataforma_usuario_id', 'auditoria_plataforma', ['usuario_id'])
    op.create_index('ix_auditoria_plataforma_evento_tipo', 'auditoria_plataforma', ['evento_tipo'])
    op.create_index('ix_auditoria_plataforma_fecha_evento', 'auditoria_plataforma', ['fecha_evento'])

    # Append-only para el rol de aplicación: solo INSERT; UPDATE y DELETE
    # quedan para el rol de migración. Idempotente si el rol no existe.
    op.execute(
        "DO $$ BEGIN "
        "IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sigem_app') THEN "
        "REVOKE ALL PRIVILEGES ON TABLE auditoria_plataforma FROM sigem_app; "
        "GRANT INSERT ON TABLE auditoria_plataforma TO sigem_app; "
        "END IF; END $$;"
    )


def downgrade() -> None:
    op.drop_index('ix_auditoria_plataforma_fecha_evento', table_name='auditoria_plataforma')
    op.drop_index('ix_auditoria_plataforma_evento_tipo', table_name='auditoria_plataforma')
    op.drop_index('ix_auditoria_plataforma_usuario_id', table_name='auditoria_plataforma')
    op.drop_table('auditoria_plataforma')
