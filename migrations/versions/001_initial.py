"""001_initial

Revision ID: 001_initial
Revises:
Create Date: 2026-09-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============================================================
    # Tables created in dependency order
    # ============================================================

    # ----------------------------------------------------------------
    # 1. municipios
    # ----------------------------------------------------------------
    op.create_table(
        'municipios',
        sa.Column('id', postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('codigo', sa.String(length=10), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('departamento', sa.String(length=255), nullable=True),
        sa.Column('region', sa.String(length=255), nullable=True),
        sa.Column('poblacion', sa.Integer(), nullable=True),
        sa.Column('alcalde', sa.String(length=255), nullable=True),
        sa.Column('email_institucional', sa.String(length=255), nullable=True),
        sa.Column('telefono', sa.String(length=50), nullable=True),
        sa.Column('direccion', sa.String(length=500), nullable=True),
        sa.Column('activo', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('estado', sa.String(length=50), server_default='ACTIVO', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codigo', name='uq_municipios_codigo'),
    )

    # ----------------------------------------------------------------
    # 2. planes_desarrollo
    # ----------------------------------------------------------------
    op.create_table(
        'planes_desarrollo',
        sa.Column('id', postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('municipio_id', postgresql.UUID(), nullable=False),
        sa.Column('codigo', sa.String(length=50), nullable=False),
        sa.Column('nombre', sa.String(length=500), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('fecha_inicio', sa.Date(), nullable=True),
        sa.Column('fecha_fin', sa.Date(), nullable=True),
        sa.Column('vigencias', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('estado', sa.String(length=50), server_default='ACTIVO', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['municipio_id'], ['municipios.id'], name='fk_planes_desarrollo_municipio'),
    )
    op.create_index('ix_planes_desarrollo_municipio_id', 'planes_desarrollo', ['municipio_id'])

    # ----------------------------------------------------------------
    # 3. vigencias
    # ----------------------------------------------------------------
    op.create_table(
        'vigencias',
        sa.Column('id', postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('municipio_id', postgresql.UUID(), nullable=False),
        sa.Column('plan_desarrollo_id', postgresql.UUID(), nullable=False),
        sa.Column('codigo', sa.String(length=50), nullable=False),
        sa.Column('anio', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('estado', sa.String(length=50), server_default='ACTIVO', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['municipio_id'], ['municipios.id'], name='fk_vigencias_municipio'),
        sa.ForeignKeyConstraint(['plan_desarrollo_id'], ['planes_desarrollo.id'], name='fk_vigencias_plan_desarrollo'),
    )
    op.create_index('ix_vigencias_municipio_id', 'vigencias', ['municipio_id'])
    op.create_index('ix_vigencias_plan_desarrollo_id', 'vigencias', ['plan_desarrollo_id'])

    # ----------------------------------------------------------------
    # 4. dependencias  (self-referencing FK)
    # ----------------------------------------------------------------
    op.create_table(
        'dependencias',
        sa.Column('id', postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('municipio_id', postgresql.UUID(), nullable=False),
        sa.Column('codigo', sa.String(length=50), nullable=False),
        sa.Column('nombre', sa.String(length=500), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('dependencia_padre_id', postgresql.UUID(), nullable=True),
        sa.Column('nivel', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('estado', sa.String(length=50), server_default='ACTIVO', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['municipio_id'], ['municipios.id'], name='fk_dependencias_municipio'),
        sa.ForeignKeyConstraint(['dependencia_padre_id'], ['dependencias.id'], name='fk_dependencias_padre'),
    )
    op.create_index('ix_dependencias_municipio_id', 'dependencias', ['municipio_id'])
    op.create_index('ix_dependencias_dependencia_padre_id', 'dependencias', ['dependencia_padre_id'])

    # ----------------------------------------------------------------
    # 5. roles
    # ----------------------------------------------------------------
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('codigo', sa.String(length=100), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('nivel', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('estado', sa.String(length=50), server_default='ACTIVO', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codigo', name='uq_roles_codigo'),
    )

    # ----------------------------------------------------------------
    # 6. permisos
    # ----------------------------------------------------------------
    op.create_table(
        'permisos',
        sa.Column('id', postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('codigo', sa.String(length=150), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('modulo', sa.String(length=100), nullable=True),
        sa.Column('accion', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('estado', sa.String(length=50), server_default='ACTIVO', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codigo', name='uq_permisos_codigo'),
    )
    op.create_index('ix_permisos_modulo', 'permisos', ['modulo'])
    op.create_index('ix_permisos_accion', 'permisos', ['accion'])

    # ----------------------------------------------------------------
    # 7. usuarios
    # ----------------------------------------------------------------
    op.create_table(
        'usuarios',
        sa.Column('id', postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('municipio_id', postgresql.UUID(), nullable=False),
        sa.Column('codigo', sa.String(length=50), nullable=False),
        sa.Column('username', sa.String(length=150), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('nombre_completo', sa.String(length=500), nullable=False),
        sa.Column('telefono', sa.String(length=50), nullable=True),
        sa.Column('cargo', sa.String(length=255), nullable=True),
        sa.Column('password_hash', sa.String(length=500), nullable=False),
        sa.Column('must_change_password', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('activo', sa.Integer(), server_default='1', nullable=False),
        sa.Column('ultimo_acceso', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ip_ultimo_acceso', sa.String(length=45), nullable=True),
        sa.Column('user_agent_ultimo_acceso', sa.Text(), nullable=True),
        sa.Column('intentos_fallidos', sa.Integer(), server_default='0', nullable=False),
        sa.Column('ultimo_intento_fallido', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ultimo_cambio_password', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fecha_bloqueo', sa.DateTime(timezone=True), nullable=True),
        sa.Column('motivo_bloqueo', sa.Text(), nullable=True),
        sa.Column('mfa_activo', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('mfa_secret', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('estado', sa.String(length=50), server_default='ACTIVO', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codigo', name='uq_usuarios_codigo'),
        sa.UniqueConstraint('municipio_id', 'username', name='uq_usuarios_municipio_username'),
        sa.ForeignKeyConstraint(['municipio_id'], ['municipios.id'], name='fk_usuarios_municipio'),
    )
    op.create_index('ix_usuarios_municipio_id', 'usuarios', ['municipio_id'])
    op.create_index('ix_usuarios_username', 'usuarios', ['username'])
    op.create_index('ix_usuarios_email', 'usuarios', ['email'])
    op.create_index('ix_usuarios_activo', 'usuarios', ['activo'])

    # ----------------------------------------------------------------
    # 8. usuario_roles
    # ----------------------------------------------------------------
    op.create_table(
        'usuario_roles',
        sa.Column('id', postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('usuario_id', postgresql.UUID(), nullable=False),
        sa.Column('rol_id', postgresql.UUID(), nullable=False),
        sa.Column('municipio_id', postgresql.UUID(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name='fk_usuario_roles_usuario'),
        sa.ForeignKeyConstraint(['rol_id'], ['roles.id'], name='fk_usuario_roles_rol'),
        sa.ForeignKeyConstraint(['municipio_id'], ['municipios.id'], name='fk_usuario_roles_municipio'),
    )
    op.create_index('ix_usuario_roles_usuario_id', 'usuario_roles', ['usuario_id'])
    op.create_index('ix_usuario_roles_rol_id', 'usuario_roles', ['rol_id'])
    op.create_index('ix_usuario_roles_municipio_id', 'usuario_roles', ['municipio_id'])

    # ----------------------------------------------------------------
    # 9. rol_permisos
    # ----------------------------------------------------------------
    op.create_table(
        'rol_permisos',
        sa.Column('id', postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('rol_id', postgresql.UUID(), nullable=False),
        sa.Column('permiso_id', postgresql.UUID(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['rol_id'], ['roles.id'], name='fk_rol_permisos_rol'),
        sa.ForeignKeyConstraint(['permiso_id'], ['permisos.id'], name='fk_rol_permisos_permiso'),
    )
    op.create_index('ix_rol_permisos_rol_id', 'rol_permisos', ['rol_id'])
    op.create_index('ix_rol_permisos_permiso_id', 'rol_permisos', ['permiso_id'])

    # ----------------------------------------------------------------
    # 10. usuario_dependencias
    # ----------------------------------------------------------------
    op.create_table(
        'usuario_dependencias',
        sa.Column('id', postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('usuario_id', postgresql.UUID(), nullable=False),
        sa.Column('dependencia_id', postgresql.UUID(), nullable=False),
        sa.Column('municipio_id', postgresql.UUID(), nullable=False),
        sa.Column('es_principal', sa.Boolean(), server_default='false', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name='fk_usuario_dependencias_usuario'),
        sa.ForeignKeyConstraint(['dependencia_id'], ['dependencias.id'], name='fk_usuario_dependencias_dependencia'),
        sa.ForeignKeyConstraint(['municipio_id'], ['municipios.id'], name='fk_usuario_dependencias_municipio'),
    )
    op.create_index('ix_usuario_dependencias_usuario_id', 'usuario_dependencias', ['usuario_id'])
    op.create_index('ix_usuario_dependencias_dependencia_id', 'usuario_dependencias', ['dependencia_id'])
    op.create_index('ix_usuario_dependencias_municipio_id', 'usuario_dependencias', ['municipio_id'])

    # ----------------------------------------------------------------
    # 11. sesiones
    # ----------------------------------------------------------------
    op.create_table(
        'sesiones',
        sa.Column('id', postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('usuario_id', postgresql.UUID(), nullable=False),
        sa.Column('municipio_id', postgresql.UUID(), nullable=False),
        sa.Column('token_jti', sa.String(length=36), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('activa', sa.Integer(), server_default='1', nullable=False),
        sa.Column('fecha_creacion', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('ultima_actividad', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fecha_expiracion', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_jti', name='uq_sesiones_token_jti'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name='fk_sesiones_usuario'),
        sa.ForeignKeyConstraint(['municipio_id'], ['municipios.id'], name='fk_sesiones_municipio'),
    )
    op.create_index('ix_sesiones_usuario_id', 'sesiones', ['usuario_id'])
    op.create_index('ix_sesiones_municipio_id', 'sesiones', ['municipio_id'])
    op.create_index('ix_sesiones_token_jti', 'sesiones', ['token_jti'])
    op.create_index('ix_sesiones_activa', 'sesiones', ['activa'])

    # ----------------------------------------------------------------
    # 12. intentos_login
    # ----------------------------------------------------------------
    op.create_table(
        'intentos_login',
        sa.Column('id', postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('usuario_id', postgresql.UUID(), nullable=True),
        sa.Column('username_intentado', sa.String(length=150), nullable=True),
        sa.Column('municipio_id', postgresql.UUID(), nullable=True),
        sa.Column('exitoso', sa.Boolean(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('fecha_intento', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('razon_fallo', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name='fk_intentos_login_usuario'),
        sa.ForeignKeyConstraint(['municipio_id'], ['municipios.id'], name='fk_intentos_login_municipio'),
    )
    op.create_index('ix_intentos_login_usuario_id', 'intentos_login', ['usuario_id'])
    op.create_index('ix_intentos_login_municipio_id', 'intentos_login', ['municipio_id'])
    op.create_index('ix_intentos_login_exitoso', 'intentos_login', ['exitoso'])
    op.create_index('ix_intentos_login_fecha_intento', 'intentos_login', ['fecha_intento'])

    # ----------------------------------------------------------------
    # 13. mfa_factors
    # ----------------------------------------------------------------
    op.create_table(
        'mfa_factors',
        sa.Column('id', postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('usuario_id', postgresql.UUID(), nullable=False),
        sa.Column('municipio_id', postgresql.UUID(), nullable=False),
        sa.Column('tipo', sa.String(length=50), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=True),
        sa.Column('secret_encrypted', sa.Text(), nullable=True),
        sa.Column('public_key', sa.Text(), nullable=True),
        sa.Column('activo', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('fecha_creacion', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('ultimo_uso', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revocado', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('fecha_revocacion', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name='fk_mfa_factors_usuario'),
        sa.ForeignKeyConstraint(['municipio_id'], ['municipios.id'], name='fk_mfa_factors_municipio'),
    )
    op.create_index('ix_mfa_factors_usuario_id', 'mfa_factors', ['usuario_id'])
    op.create_index('ix_mfa_factors_municipio_id', 'mfa_factors', ['municipio_id'])
    op.create_index('ix_mfa_factors_activo', 'mfa_factors', ['activo'])

    # ----------------------------------------------------------------
    # 14. auditoria_eventos
    # ----------------------------------------------------------------
    op.create_table(
        'auditoria_eventos',
        sa.Column('id', postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('municipio_id', postgresql.UUID(), nullable=True),
        sa.Column('usuario_id', postgresql.UUID(), nullable=True),
        sa.Column('actor_id', postgresql.UUID(), nullable=True),
        sa.Column('evento_tipo', sa.String(length=100), nullable=False),
        sa.Column('recurso_tipo', sa.String(length=100), nullable=True),
        sa.Column('recurso_id', postgresql.UUID(), nullable=True),
        sa.Column('resultado', sa.String(length=50), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('fecha_evento', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['municipio_id'], ['municipios.id'], name='fk_auditoria_eventos_municipio'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name='fk_auditoria_eventos_usuario'),
    )
    op.create_index('ix_auditoria_eventos_municipio_id', 'auditoria_eventos', ['municipio_id'])
    op.create_index('ix_auditoria_eventos_usuario_id', 'auditoria_eventos', ['usuario_id'])
    op.create_index('ix_auditoria_eventos_evento_tipo', 'auditoria_eventos', ['evento_tipo'])
    op.create_index('ix_auditoria_eventos_fecha_evento', 'auditoria_eventos', ['fecha_evento'])

    # ----------------------------------------------------------------
    # 15. gestores_lideres
    # ----------------------------------------------------------------
    op.create_table(
        'gestores_lideres',
        sa.Column('id', postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('municipio_id', postgresql.UUID(), nullable=False),
        sa.Column('usuario_id', postgresql.UUID(), nullable=False),
        sa.Column('codigo', sa.String(length=50), nullable=False),
        sa.Column('nombre_completo', sa.String(length=500), nullable=False),
        sa.Column('cargo', sa.String(length=255), nullable=True),
        sa.Column('dependencia_principal_id', postgresql.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('estado', sa.String(length=50), server_default='ACTIVO', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('usuario_id', name='uq_gestores_lideres_usuario'),
        sa.UniqueConstraint('codigo', name='uq_gestores_lideres_codigo'),
        sa.ForeignKeyConstraint(['municipio_id'], ['municipios.id'], name='fk_gestores_lideres_municipio'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], name='fk_gestores_lideres_usuario'),
        sa.ForeignKeyConstraint(['dependencia_principal_id'], ['dependencias.id'], name='fk_gestores_lideres_dependencia'),
    )
    op.create_index('ix_gestores_lideres_municipio_id', 'gestores_lideres', ['municipio_id'])
    op.create_index('ix_gestores_lideres_usuario_id', 'gestores_lideres', ['usuario_id'])
    op.create_index('ix_gestores_lideres_dependencia_principal_id', 'gestores_lideres', ['dependencia_principal_id'])

    # ----------------------------------------------------------------
    # 16. lineas_estrategicas
    # ----------------------------------------------------------------
    op.create_table(
        'lineas_estrategicas',
        sa.Column('id', postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('municipio_id', postgresql.UUID(), nullable=False),
        sa.Column('plan_desarrollo_id', postgresql.UUID(), nullable=False),
        sa.Column('codigo', sa.String(length=50), nullable=False),
        sa.Column('nombre', sa.String(length=500), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('orden', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('estado', sa.String(length=50), server_default='ACTIVO', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['municipio_id'], ['municipios.id'], name='fk_lineas_estrategicas_municipio'),
        sa.ForeignKeyConstraint(['plan_desarrollo_id'], ['planes_desarrollo.id'], name='fk_lineas_estrategicas_plan'),
    )
    op.create_index('ix_lineas_estrategicas_municipio_id', 'lineas_estrategicas', ['municipio_id'])
    op.create_index('ix_lineas_estrategicas_plan_desarrollo_id', 'lineas_estrategicas', ['plan_desarrollo_id'])

    # ----------------------------------------------------------------
    # 17. programas
    # ----------------------------------------------------------------
    op.create_table(
        'programas',
        sa.Column('id', postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('municipio_id', postgresql.UUID(), nullable=False),
        sa.Column('linea_estrategica_id', postgresql.UUID(), nullable=False),
        sa.Column('codigo', sa.String(length=50), nullable=False),
        sa.Column('nombre', sa.String(length=500), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('estado', sa.String(length=50), server_default='ACTIVO', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['municipio_id'], ['municipios.id'], name='fk_programas_municipio'),
        sa.ForeignKeyConstraint(['linea_estrategica_id'], ['lineas_estrategicas.id'], name='fk_programas_linea_estrategica'),
    )
    op.create_index('ix_programas_municipio_id', 'programas', ['municipio_id'])
    op.create_index('ix_programas_linea_estrategica_id', 'programas', ['linea_estrategica_id'])

    # ----------------------------------------------------------------
    # 18. productos
    # ----------------------------------------------------------------
    op.create_table(
        'productos',
        sa.Column('id', postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('municipio_id', postgresql.UUID(), nullable=False),
        sa.Column('programa_id', postgresql.UUID(), nullable=False),
        sa.Column('codigo', sa.String(length=50), nullable=False),
        sa.Column('nombre', sa.String(length=500), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('unidad_medida', sa.String(length=100), nullable=True),
        sa.Column('dependencia_responsable_id', postgresql.UUID(), nullable=True),
        sa.Column('gestor_lider_id', postgresql.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('estado', sa.String(length=50), server_default='ACTIVO', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['municipio_id'], ['municipios.id'], name='fk_productos_municipio'),
        sa.ForeignKeyConstraint(['programa_id'], ['programas.id'], name='fk_productos_programa'),
        sa.ForeignKeyConstraint(['dependencia_responsable_id'], ['dependencias.id'], name='fk_productos_dependencia'),
        sa.ForeignKeyConstraint(['gestor_lider_id'], ['gestores_lideres.id'], name='fk_productos_gestor'),
    )
    op.create_index('ix_productos_municipio_id', 'productos', ['municipio_id'])
    op.create_index('ix_productos_programa_id', 'productos', ['programa_id'])
    op.create_index('ix_productos_dependencia_responsable_id', 'productos', ['dependencia_responsable_id'])
    op.create_index('ix_productos_gestor_lider_id', 'productos', ['gestor_lider_id'])


def downgrade() -> None:
    # Drop tables in reverse dependency order

    op.drop_table('productos')
    op.drop_table('programas')
    op.drop_table('lineas_estrategicas')
    op.drop_table('gestores_lideres')
    op.drop_table('auditoria_eventos')
    op.drop_table('mfa_factors')
    op.drop_table('intentos_login')
    op.drop_table('sesiones')
    op.drop_table('usuario_dependencias')
    op.drop_table('rol_permisos')
    op.drop_table('usuario_roles')
    op.drop_table('usuarios')
    op.drop_table('permisos')
    op.drop_table('roles')
    op.drop_table('dependencias')
    op.drop_table('vigencias')
    op.drop_table('planes_desarrollo')
    op.drop_table('municipios')
