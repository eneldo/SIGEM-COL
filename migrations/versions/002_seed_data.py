"""002_seed_data

Revision ID: 002_seed_data
Revises: 001_initial
Create Date: 2026-09-20 00:00:00.000000

"""
from typing import Sequence, Union
from datetime import datetime
import uuid

from alembic import op
import sqlalchemy as sa


revision: str = '002_seed_data'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    now = datetime.utcnow()

    # Pre-generate UUIDs
    role_ids = {name: str(uuid.uuid4()) for name in [
        'SUPERADMIN_PLATAFORMA', 'ADMINISTRADOR_MUNICIPAL',
        'GESTOR_LIDER', 'AUDITOR', 'CONSULTA'
    ]}
    municipio_id = str(uuid.uuid4())
    plan_id = str(uuid.uuid4())

    # ============================================================
    # 1. Roles
    # ============================================================
    for code, name, desc, level in [
        ('SUPERADMIN_PLATAFORMA', 'Superadministrador Plataforma', 'Superadministrador con acceso total a la plataforma', 1),
        ('ADMINISTRADOR_MUNICIPAL', 'Administrador Municipal', 'Administrador con acceso de gestión a nivel municipal', 2),
        ('GESTOR_LIDER', 'Gestor Líder', 'Gestor líder encargado de la coordinación de productos', 3),
        ('AUDITOR', 'Auditor', 'Auditor con acceso de solo lectura y auditoría', 4),
        ('CONSULTA', 'Consulta', 'Usuario con acceso de solo consulta', 5),
    ]:
        op.execute(
            sa.text(
                f"INSERT INTO roles (id, codigo, nombre, descripcion, nivel, created_at, updated_at, version, estado) "
                f"VALUES ('{role_ids[code]}', '{code}', '{name}', '{desc}', {level}, '{now}', '{now}', 1, 'ACTIVO')"
            )
        )

    # ============================================================
    # 2. Permisos
    # ============================================================
    permisos = []

    # gestor module
    for accion in ['crear', 'ver', 'editar', 'eliminar', 'permisos', 'activar', 'desactivar', 'bloquear', 'desbloquear']:
        permisos.append((f'GESTOR_{accion.upper()}', f'Permiso para {accion} de gestores', 'gestor', accion))

    # linea_estrategica module
    for accion in ['crear', 'ver', 'editar', 'eliminar']:
        permisos.append((f'LINEA_ESTRATEGICA_{accion.upper()}', f'Permiso para {accion} de líneas estratégicas', 'linea_estrategica', accion))

    # programa module
    for accion in ['crear', 'ver', 'editar', 'eliminar']:
        permisos.append((f'PROGRAMA_{accion.upper()}', f'Permiso para {accion} de programas', 'programa', accion))

    # producto module
    for accion in ['crear', 'ver', 'editar', 'eliminar']:
        permisos.append((f'PRODUCTO_{accion.upper()}', f'Permiso para {accion} de productos', 'producto', accion))

    # security module
    for accion in ['usuarios_ver', 'usuarios_crear', 'usuarios_editar', 'usuarios_eliminar',
                    'roles_ver', 'roles_crear', 'roles_editar', 'roles_eliminar', 'permisos_ver']:
        permisos.append((f'SECURITY_{accion.upper()}', f'Permiso para {accion}', 'security', accion))

    # audit module
    for accion in ['eventos_ver', 'evidencias_ver']:
        permisos.append((f'AUDIT_{accion.upper()}', f'Permiso para {accion}', 'audit', accion))

    # dashboard module
    for accion in ['admin_ver', 'gestor_ver']:
        permisos.append((f'DASHBOARD_{accion.upper()}', f'Permiso para {accion}', 'dashboard', accion))

    for codigo, desc, modulo, accion in permisos:
        pid = str(uuid.uuid4())
        op.execute(
            sa.text(
                f"INSERT INTO permisos (id, codigo, nombre, descripcion, modulo, accion, created_at, updated_at, version, estado) "
                f"VALUES ('{pid}', '{codigo}', '{desc}', '{desc}', '{modulo}', '{accion}', '{now}', '{now}', 1, 'ACTIVO')"
            )
        )

    # ============================================================
    # 3. Municipio Default
    # ============================================================
    op.execute(
        sa.text(
            f"INSERT INTO municipios (id, codigo, nombre, departamento, created_at, updated_at, version, estado, activo) "
            f"VALUES ('{municipio_id}', '00000', 'Municipio Default', 'Cundinamarca', '{now}', '{now}', 1, 'ACTIVO', 1)"
        )
    )

    # ============================================================
    # 4. Plan de Desarrollo Default
    # ============================================================
    op.execute(
        sa.text(
            f"INSERT INTO planes_desarrollo (id, municipio_id, codigo, nombre, descripcion, fecha_inicio, fecha_fin, vigencias, created_at, updated_at, version, estado) "
            f"VALUES ('{plan_id}', '{municipio_id}', 'PD-001', 'Plan de Desarrollo 2024-2027', 'Plan de Desarrollo Municipal para el periodo 2024-2027', '2024-01-01', '2027-12-31', 4, '{now}', '{now}', 1, 'ACTIVO')"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM planes_desarrollo WHERE codigo = 'PD-001'"))
    op.execute(sa.text("DELETE FROM municipios WHERE codigo = '00000'"))
    op.execute(sa.text("DELETE FROM permisos WHERE modulo IN ('gestor', 'linea_estrategica', 'programa', 'producto', 'security', 'audit', 'dashboard')"))
    op.execute(sa.text("DELETE FROM roles WHERE codigo IN ('SUPERADMIN_PLATAFORMA', 'ADMINISTRADOR_MUNICIPAL', 'GESTOR_LIDER', 'AUDITOR', 'CONSULTA')"))
