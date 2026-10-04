"""Add personalizaciones table (branding por municipio)

Revision ID: 020_personalizacion
Revises: 019_decimal_progress_values
Create Date: 2026-10-04

Una fila de configuracion visual por municipio: colores primario/secundario,
nombre del sistema y logotipo embebido (data URL). La tabla multi-municipio
recibe RLS fail-closed igual que el resto (revisiones 003/017), y se siembra
el permiso CONFIGURACION_EDITAR que exige el endpoint PUT.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '020_personalizacion'
down_revision = '019_decimal_progress_values'
branch_labels = None
depends_on = None

TENANT_EXPR = (
    "municipio_id = NULLIF(current_setting('app.current_municipio_id', true), '')::uuid"
)


def upgrade() -> None:
    op.create_table(
        'personalizaciones',
        sa.Column('id', postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('municipio_id', postgresql.UUID(), sa.ForeignKey('municipios.id'), nullable=False),
        sa.Column('color_primario', sa.String(length=7), server_default='#0F3D3B', nullable=False),
        sa.Column('color_secundario', sa.String(length=7), server_default='#B9852F', nullable=False),
        sa.Column('nombre_sistema', sa.String(length=120), server_default='SIGEM Colombia', nullable=False),
        sa.Column('logo_data_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('estado', sa.String(length=50), server_default='ACTIVO', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(), nullable=True),
        sa.UniqueConstraint('municipio_id', name='uq_personalizaciones_municipio'),
    )
    op.create_index('ix_personalizaciones_municipio_id', 'personalizaciones', ['municipio_id'])

    op.execute("ALTER TABLE personalizaciones ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE personalizaciones FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY municipio_isolation_personalizaciones ON personalizaciones "
        f"FOR ALL USING ({TENANT_EXPR}) WITH CHECK ({TENANT_EXPR})"
    )

    op.execute(
        sa.text(
            "INSERT INTO permisos (id, codigo, nombre, descripcion, modulo, accion, "
            "created_at, updated_at, version, estado) "
            "SELECT gen_random_uuid(), :codigo, :nombre, :nombre, :modulo, :accion, "
            "now(), now(), 1, 'ACTIVO' "
            "WHERE NOT EXISTS (SELECT 1 FROM permisos WHERE codigo = :codigo)"
        ).bindparams(
            codigo='CONFIGURACION_EDITAR',
            nombre='Permiso para editar la configuracion del sistema',
            modulo='configuracion',
            accion='editar',
        )
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS municipio_isolation_personalizaciones ON personalizaciones")
    op.drop_index('ix_personalizaciones_municipio_id', table_name='personalizaciones')
    op.drop_table('personalizaciones')
    op.execute("DELETE FROM permisos WHERE codigo = 'CONFIGURACION_EDITAR'")
