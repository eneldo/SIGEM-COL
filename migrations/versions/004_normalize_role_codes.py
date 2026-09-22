"""Normalize seeded role codes.

Revision ID: 004_normalize_role_codes
Revises: 003_rls_policies
"""

from alembic import op


revision = "004_normalize_role_codes"
down_revision = "003_rls_policies"
branch_labels = None
depends_on = None


ROLE_CODES = {
    "Superadministrador Plataforma": "SUPERADMIN_PLATAFORMA",
    "Administrador Municipal": "ADMINISTRADOR_MUNICIPAL",
    "Gestor Líder": "GESTOR_LIDER",
    "Auditor": "AUDITOR",
    "Consulta": "CONSULTA",
}


def upgrade() -> None:
    for old_code, new_code in ROLE_CODES.items():
        op.execute(
            f"UPDATE roles SET codigo = '{new_code}' WHERE codigo = '{old_code}'"
        )


def downgrade() -> None:
    for old_code, new_code in ROLE_CODES.items():
        op.execute(
            f"UPDATE roles SET codigo = '{old_code}' WHERE codigo = '{new_code}'"
        )
