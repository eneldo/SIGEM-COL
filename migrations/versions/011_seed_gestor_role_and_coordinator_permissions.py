"""011_seed_gestor_role_and_coordinator_permissions

Crea el rol GESTOR y otorga permisos de gestión de equipo al rol GESTOR_LIDER
(coordinador) y permisos básicos de operación al rol GESTOR.

Revision ID: 011_seed_gestor_role_and_coordinator_permissions
Revises: 010_add_avance_revision_columns
Create Date: 2026-09-23 00:00:00.000000

"""
from typing import Sequence, Union
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa


revision: str = '011_seed_gestor_role_and_coordinator_permissions'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


COORDINATOR_PERMISSIONS = [
    'GESTOR_CREAR',
    'GESTOR_VER',
    'GESTOR_EDITAR',
    'GESTOR_ELIMINAR',
    'GESTOR_PERMISOS',
    'GESTOR_ACTIVAR',
    'GESTOR_DESACTIVAR',
    'GESTOR_BLOQUEAR',
    'GESTOR_DESBLOQUEAR',
    'PRODUCTO_VER',
    'PRODUCTO_EDITAR',
    'DASHBOARD_GESTOR_VER',
]

GESTOR_PERMISSIONS = [
    'DASHBOARD_GESTOR_VER',
    'PRODUCTO_VER',
]


def upgrade() -> None:
    now = datetime.now(timezone.utc).isoformat()

    op.execute(
        sa.text(
            """
            INSERT INTO roles (id, codigo, nombre, descripcion, nivel, created_at, updated_at, version, estado)
            SELECT gen_random_uuid(), 'GESTOR', 'Gestor',
                   'Gestor operativo del equipo de coordinación', 4, :now, :now, 1, 'ACTIVO'
            WHERE NOT EXISTS (SELECT 1 FROM roles WHERE codigo = 'GESTOR' AND deleted_at IS NULL)
            """
        ).bindparams(now=now)
    )

    for role_code, permisos in (
        ('GESTOR_LIDER', COORDINATOR_PERMISSIONS),
        ('GESTOR', GESTOR_PERMISSIONS),
    ):
        for permiso_codigo in permisos:
            op.execute(
                sa.text(
                    """
                    INSERT INTO rol_permisos (id, rol_id, permiso_id)
                    SELECT gen_random_uuid(), r.id, p.id
                    FROM roles r
                    JOIN permisos p ON p.codigo = :permiso_codigo
                    WHERE r.codigo = :role_code
                      AND r.deleted_at IS NULL
                      AND p.deleted_at IS NULL
                      AND NOT EXISTS (
                        SELECT 1 FROM rol_permisos rp
                        WHERE rp.rol_id = r.id AND rp.permiso_id = p.id
                      )
                    """
                ).bindparams(role_code=role_code, permiso_codigo=permiso_codigo)
            )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM rol_permisos rp
            USING roles r, permisos p
            WHERE rp.rol_id = r.id
              AND rp.permiso_id = p.id
              AND r.codigo IN ('GESTOR_LIDER', 'GESTOR')
              AND p.codigo IN (
                'GESTOR_CREAR','GESTOR_VER','GESTOR_EDITAR','GESTOR_ELIMINAR',
                'GESTOR_PERMISOS','GESTOR_ACTIVAR','GESTOR_DESACTIVAR',
                'GESTOR_BLOQUEAR','GESTOR_DESBLOQUEAR',
                'PRODUCTO_VER','PRODUCTO_EDITAR','DASHBOARD_GESTOR_VER'
              )
            """
        )
    )
    op.execute(sa.text("DELETE FROM roles WHERE codigo = 'GESTOR'"))
