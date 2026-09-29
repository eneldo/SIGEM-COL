"""Enforce Row-Level Security on every multi-municipality table

Revision ID: 017_enforce_rls
Revises: 016_seed_avances_evidencias
Create Date: 2026-09-28

Enables and FORCEs RLS (so the table owner cannot bypass it), recreates
tenant policies with a fail-closed, missing-safe context lookup, adds the
tables created after revision 003 (avances_producto, evidencias) and
hardens the helper functions created in revision 003.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '017_enforce_rls'
down_revision = '016_seed_avances_evidencias'
branch_labels = None
depends_on = None

# Tables WITH municipio_id (multi-municipio isolation).
# 'municipios' is excluded - it IS the reference table, not filtered by municipio_id.
tables_with_municipio_id = [
    'planes_desarrollo',
    'vigencias',
    'dependencias',
    'usuarios',
    'gestores_lideres',
    'lineas_estrategicas',
    'programas',
    'productos',
    'sesiones',
    'intentos_login',
    'mfa_factors',
    'auditoria_eventos',
    'usuario_roles',
    'usuario_dependencias',
    # Tables created after revision 003:
    'avances_producto',
    'evidencias',
]

# Fail-closed expression: NULL context (no token / unscoped session) yields NULL,
# so no row is visible and no row can be written. current_setting(..., true)
# never raises when the GUC has not been set in this session.
TENANT_EXPR = (
    "municipio_id = NULLIF(current_setting('app.current_municipio_id', true), '')::uuid"
)


def upgrade() -> None:
    for table in tables_with_municipio_id:
        policy_name = f"municipio_isolation_{table}"
        op.execute(f"DROP POLICY IF EXISTS {policy_name} ON {table}")
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        # FORCE: the table owner (typically the application/migration role)
        # is subject to the policies as any other role.
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        op.execute(
            f"CREATE POLICY {policy_name} ON {table} "
            f"FOR ALL USING ({TENANT_EXPR}) WITH CHECK ({TENANT_EXPR});"
        )

    # Harden the helper functions from revision 003: only the technical role
    # may execute them and their search_path is pinned to pg_catalog.
    op.execute(
        "ALTER FUNCTION set_current_municipio(UUID) SET search_path = pg_catalog"
    )
    op.execute(
        "ALTER FUNCTION clear_current_municipio() SET search_path = pg_catalog"
    )
    op.execute("REVOKE ALL ON FUNCTION set_current_municipio(UUID) FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION clear_current_municipio() FROM PUBLIC")


def downgrade() -> None:
    # Restore the revision 003 state: original policy expression, no FORCE,
    # no RLS at all on tables created after revision 003.
    original_tables = [
        table for table in tables_with_municipio_id
        if table not in ('avances_producto', 'evidencias')
    ]

    for table in original_tables:
        policy_name = f"municipio_isolation_{table}"
        op.execute(f"DROP POLICY IF EXISTS {policy_name} ON {table}")
        op.execute(
            f"CREATE POLICY {policy_name} ON {table} "
            f"USING (municipio_id = current_setting('app.current_municipio_id')::uuid);"
        )
        # Revision 003 had ENABLE without FORCE.
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")

    for table in ('avances_producto', 'evidencias'):
        op.execute(f"DROP POLICY IF EXISTS municipio_isolation_{table} ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")

    op.execute("GRANT EXECUTE ON FUNCTION set_current_municipio(UUID) TO PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION clear_current_municipio() TO PUBLIC")
