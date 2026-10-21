"""Otorga al rol de aplicación los privilegios mínimos sobre una base local.

Equivalente local de infra/postgres/init/01-app-role.sh (que solo aplica en el
primer arranque del contenedor de Docker): alinea el modelo de privilegios del
rol restringido cuando la base ya existe (entornos de desarrollo y pruebas en
el host, fuera de Docker).

Uso:
    SIGEM_APP_ROLE=sigem_app_test \
    ALEMBIC_DATABASE_URL='postgresql+asyncpg://sigem_test:***@127.0.0.1:5432/sigem_col_test' \
    python scripts/setup/grant_app_role_local.py

El rol de migración (usuario de la URL) ejecuta los grants; el rol de
aplicación debe existir previamente. Es idempotente: revoca los privilegios
acumulados y reotorga el conjunto mínimo, aplicando además los default
privileges para las tablas creadas por migraciones futuras.
"""

import asyncio
import os
import sys
from urllib.parse import unquote, urlparse


GRANT_SQL = [
    # Schema: la base es del rol de migración; PUBLIC no debe crear objetos.
    "REVOKE CREATE ON SCHEMA public FROM PUBLIC",
    "REVOKE CREATE ON SCHEMA public FROM {app_role}",
    # Base: solo conexión.
    "REVOKE ALL ON DATABASE {db_name} FROM {app_role}",
    "GRANT CONNECT ON DATABASE {db_name} TO {app_role}",
    # Schema: uso (resolución de nombres) sin creación.
    "GRANT USAGE ON SCHEMA public TO {app_role}",
    # Tablas y secuencias: DML mínimo, sin DDL.
    "REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM {app_role}",
    "REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM {app_role}",
    "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {app_role}",
    "GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO {app_role}",
    # Funciones: ejecución únicamente.
    "REVOKE ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public FROM {app_role}",
    "GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO {app_role}",
    # Futures: tablas, secuencias y funciones creadas por el rol de migración
    # heredan el mismo conjunto sin repetir el script tras cada migración.
    (
        "ALTER DEFAULT PRIVILEGES FOR ROLE {migration_role} IN SCHEMA public "
        "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {app_role}"
    ),
    (
        "ALTER DEFAULT PRIVILEGES FOR ROLE {migration_role} IN SCHEMA public "
        "GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO {app_role}"
    ),
    (
        "ALTER DEFAULT PRIVILEGES FOR ROLE {migration_role} IN SCHEMA public "
        "GRANT EXECUTE ON FUNCTIONS TO {app_role}"
    ),
]


def resolve_url() -> tuple[str, str]:
    """Retorna (url_tokens, nombre_base) desde el entorno; jamás imprime secretos."""
    url = os.environ.get("ALEMBIC_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit(
            "ERROR: define ALEMBIC_DATABASE_URL o DATABASE_URL en el entorno"
        )
    parsed = urlparse(url.replace("postgresql+asyncpg", "postgresql"))
    if not parsed.hostname or not parsed.path.lstrip("/"):
        raise SystemExit("ERROR: la URL de conexión no es reconocida")
    return parsed, parsed.path.lstrip("/")


async def main() -> None:
    parsed, db_name = resolve_url()
    app_role = os.environ.get("SIGEM_APP_ROLE", "sigem_app")
    migration_role = parsed.username or "postgres"

    import asyncpg

    conn = await asyncpg.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        user=unquote(parsed.username or "postgres"),
        password=unquote(parsed.password or ""),
        database=db_name,
    )
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_roles WHERE rolname = $1", app_role
        )
        if not exists:
            raise SystemExit(
                f"ERROR: el rol {app_role!r} no existe; créalo antes de otorgar privilegios"
            )
        ctx = {"app_role": app_role, "db_name": db_name, "migration_role": migration_role}
        for statement in GRANT_SQL:
            await conn.execute(statement.format(**ctx))
        print(f"Privilegios aplicados: rol={app_role} base={db_name}")
        granted = await conn.fetch(
            """
            SELECT privilege_type
            FROM information_schema.role_table_grants
            WHERE grantee = $1 AND table_schema = 'public'
            ORDER BY privilege_type
            """,
            app_role,
        )
        counts: dict[str, int] = {}
        for g in granted:
            counts[g["privilege_type"]] = counts.get(g["privilege_type"], 0) + 1
        print("Resumen de grants sobre tablas:", counts or "ninguno")
    finally:
        await conn.close()


if __name__ == "__main__":
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
