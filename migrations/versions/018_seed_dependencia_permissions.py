"""Seed dependencia module permissions

Revision ID: 018_seed_dependencia_permissions
Revises: 017_enforce_rls
Create Date: 2026-09-28

The dependencias CRUD endpoints now enforce require_permission. This adds the
permission codes they check so administrators can also grant them to other
roles from the roles UI (admins themselves always pass via the RBAC bypass).

Read access (GET) stays authentication-only on purpose: dependency names are
not sensitive and are already exposed by the catalogos endpoints.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '018_seed_dependencia_permissions'
down_revision = '017_enforce_rls'
branch_labels = None
depends_on = None

permisos = [
    ('DEPENDENCIA_CREAR', 'Permiso para crear dependencias', 'dependencia', 'crear'),
    ('DEPENDENCIA_EDITAR', 'Permiso para editar dependencias', 'dependencia', 'editar'),
    ('DEPENDENCIA_ELIMINAR', 'Permiso para eliminar dependencias', 'dependencia', 'eliminar'),
]


def upgrade() -> None:
    for codigo, nombre, modulo, accion in permisos:
        op.execute(
            sa.text(
                "INSERT INTO permisos (id, codigo, nombre, descripcion, modulo, accion, "
                "created_at, updated_at, version, estado) "
                "SELECT gen_random_uuid(), :codigo, :nombre, :nombre, :modulo, :accion, "
                "now(), now(), 1, 'ACTIVO' "
                "WHERE NOT EXISTS (SELECT 1 FROM permisos WHERE codigo = :codigo)"
            ).bindparams(codigo=codigo, nombre=nombre, modulo=modulo, accion=accion)
        )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM permisos WHERE codigo IN "
                "('DEPENDENCIA_CREAR', 'DEPENDENCIA_EDITAR', 'DEPENDENCIA_ELIMINAR')")
    )
