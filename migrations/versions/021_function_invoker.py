"""Reduce los privilegios de las funciones helper de contexto de tenant

Revision ID: 021_function_invoker
Revises: 020_personalizacion
Create Date: 2026-10-20

set_current_municipio()/clear_current_municipio() nacieron SECURITY DEFINER
en la revision 003. Definer solo era necesario si set_config exigiera
privilegios especiales, pero las variables personalizadas de la clase
`app.` son seteables por cualquier rol, por lo que el modo DEFINER no aporta
nada y si expone: permite ejecutar código con los privilegios del rol de
migración (dueño de las tablas) desde el rol de aplicación.

Con SECURITY INVOKER la función pasa a ejecutarse con los privilegios del
llamante; el efecto (fijar app.current_municipio_id) queda inalterado porque
cualquier rol puede fijar esa variable directamente con set_config().
Aplicaciones de referencia (src/backend/core/database.py) nunca las usan:
fijan la variable con SQL directo, que es el camino documentado.

Se mantiene el search_path fijado a pg_catalog (revision 017) y el REVOKE a
PUBLIC para usarlas solo de forma explícita.
"""

from alembic import op

revision = '021_function_invoker'
down_revision = '020_personalizacion'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER FUNCTION set_current_municipio(UUID) SECURITY INVOKER")
    op.execute("ALTER FUNCTION clear_current_municipio() SECURITY INVOKER")


def downgrade() -> None:
    # Restaura el modo SECURITY DEFINER de la revision 003.
    op.execute("ALTER FUNCTION clear_current_municipio() SECURITY DEFINER")
    op.execute("ALTER FUNCTION set_current_municipio(UUID) SECURITY DEFINER")
