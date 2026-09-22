"""RLS policies for SIGEM Colombia

Revision ID: 003_rls_policies
Revises: 002_seed_data
Create Date: 2026-09-20
"""

from alembic import op
import sqlalchemy as sa

revision = '003_rls_policies'
down_revision = '002_seed_data'
branch_labels = None
depends_on = None

# Tables WITH municipio_id (multi-municipio isolation)
# Note: 'municipios' is excluded - it IS the reference table, not filtered by municipio_id
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
]

# Tables WITHOUT municipio_id (global tables - skip RLS)
tables_without_municipio_id = [
    'rol_permisos',
    'permisos',
    'roles',
]


def upgrade() -> None:
    # Create helper functions for setting/clearing municipality context
    op.execute("""
        CREATE OR REPLACE FUNCTION set_current_municipio(p_municipio_id UUID)
        RETURNS VOID AS $$
        BEGIN
          PERFORM set_config('app.current_municipio_id', p_municipio_id::TEXT, true);
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION clear_current_municipio()
        RETURNS VOID AS $$
        BEGIN
          PERFORM set_config('app.current_municipio_id', '', true);
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Enable RLS and create policies on all multi-municipio tables
    for table in tables_with_municipio_id:
        policy_name = f"municipio_isolation_{table}"
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(
            f"CREATE POLICY {policy_name} ON {table} "
            f"USING (municipio_id = current_setting('app.current_municipio_id')::uuid);"
        )


def downgrade() -> None:
    # Drop all policies on multi-municipio tables
    for table in tables_with_municipio_id:
        policy_name = f"municipio_isolation_{table}"
        op.execute(f"DROP POLICY IF EXISTS {policy_name} ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    # Drop helper functions
    op.execute("DROP FUNCTION IF EXISTS clear_current_municipio();")
    op.execute("DROP FUNCTION IF EXISTS set_current_municipio(UUID);")
