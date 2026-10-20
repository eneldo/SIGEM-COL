"""Pruebas de aislamiento multi-municipio ejecutadas con el rol de aplicación.

El rol de migración es superusuario y por diseño ignora RLS (BYPASSRLS). Para que
estas pruebas signifiquen algo deben ejecutarse con un rol restringido equivalente
al de producción (`sigem_app`): sin SUPERUSER, sin BYPASSRLS y sin CREATE sobre el
esquema. El módulo crea ese rol, replica los permisos de
`infra/postgres/init/01-app-role.sh` y lo elimina al terminar.

El fixture crea su propio municipio, plan y línea estratégica temporales, y los
limpia al terminar, de modo que las pruebas no dependan de datos sembrados.

Las conexiones trabajan en AUTOCOMMIT: una sentencia rechazada por RLS no deja la
transacción abortada y, por tanto, no envenena el pool para el resto de la sesión.
"""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine

from src.backend.core.config import settings
from src.backend.core.database import TENANT_CONTEXT_SQL, engine

APP_ROLE = "sigem_rls_test_app"
APP_PASSWORD = "sigem-rls-test-password"
LINEAS_VISIBLES = "SELECT count(*) FROM lineas_estrategicas WHERE deleted_at IS NULL"

PRIVILEGES = (
    "REVOKE CREATE ON SCHEMA public FROM PUBLIC",
    f"REVOKE CREATE ON SCHEMA public FROM {APP_ROLE}",
    f"REVOKE ALL ON DATABASE {{db}} FROM {APP_ROLE}",
    f"GRANT CONNECT ON DATABASE {{db}} TO {APP_ROLE}",
    f"GRANT USAGE ON SCHEMA public TO {APP_ROLE}",
    f"REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM {APP_ROLE}",
    f"REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM {APP_ROLE}",
    f"REVOKE ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public FROM {APP_ROLE}",
    f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {APP_ROLE}",
    f"GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO {APP_ROLE}",
    f"GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO {APP_ROLE}",
)


async def _app_database_url() -> str:
    return settings.DATABASE_URL.replace(
        f"//{settings.DATABASE_URL.split('//')[1].split('@')[0]}@",
        f"//{APP_ROLE}:{APP_PASSWORD}@",
    )


async def _drop_test_role(connection) -> None:
    existe = (
        await connection.execute(
            text("SELECT 1 FROM pg_roles WHERE rolname = :rol"), {"rol": APP_ROLE}
        )
    ).first()
    if not existe:
        return
    await connection.execute(text(f"DROP OWNED BY {APP_ROLE} CASCADE"))
    await connection.execute(text(f'DROP ROLE "{APP_ROLE}"'))


@pytest.fixture(scope="module")
async def app_role():
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        pytest.skip("PostgreSQL no está disponible para las pruebas de RLS")

    database = engine.url.database
    async with engine.begin() as connection:
        await _drop_test_role(connection)
        await connection.execute(
            text(
                f'CREATE ROLE "{APP_ROLE}" LOGIN NOSUPERUSER NOCREATEDB '
                "NOCREATEROLE NOREPLICATION NOBYPASSRLS"
            )
        )
        await connection.execute(
            text(f"ALTER ROLE \"{APP_ROLE}\" PASSWORD '{APP_PASSWORD}'")
        )
        for statement in PRIVILEGES:
            await connection.execute(text(statement.format(db=database)))

    try:
        yield APP_ROLE
    finally:
        async with engine.begin() as connection:
            await _drop_test_role(connection)
        await engine.dispose()


MINIMUM_REVISION = "017_enforce_rls"


async def _schema_supports_rls(connection) -> bool:
    try:
        actual = (
            await connection.execute(text("SELECT version_num FROM alembic_version"))
        ).scalar_one()
    except Exception:
        pytest.skip(
            "La base de datos no tiene control de migraciones (alembic_version)"
        )
    if actual != "020_personalizacion":
        pytest.skip(
            f"La base de datos está en la revisión {actual}; "
            f"las pruebas de RLS requieren el esquema en head (RLS forzado desde {MINIMUM_REVISION})"
        )
    return True


@pytest.fixture
async def conexion(app_role):
    url = await _app_database_url()
    app_engine = create_async_engine(url)
    connection = await app_engine.connect()
    await connection.execution_options(isolation_level="AUTOCOMMIT")

    bypassrls = (
        await connection.execute(
            text("SELECT rolbypassrls FROM pg_roles WHERE rolname = current_user")
        )
    ).scalar_one()
    if bypassrls:
        await connection.close()
        await app_engine.dispose()
        pytest.skip("El rol de prueba tiene BYPASSRLS: la validación no sería válida")

    await _schema_supports_rls(connection)

    try:
        yield connection
    finally:
        await connection.close()
        await app_engine.dispose()


async def _set_tenant(connection, municipio_id: str) -> None:
    await connection.execute(text(TENANT_CONTEXT_SQL), {"value": municipio_id})


async def _scalar(connection, statement: str, params: dict | None = None) -> int:
    result = await connection.execute(text(statement), params or {})
    return int(result.scalar_one())


@pytest.fixture
async def tenant_principal(conexion) -> str:
    row = (
        await conexion.execute(
            text("SELECT id::text FROM municipios WHERE codigo = '00000' LIMIT 1")
        )
    ).first()
    if row is None:
        pytest.skip("El municipio 00000 no existe en la base de datos de pruebas")
    return row[0]


@pytest.fixture
async def tenant_ajeno(conexion) -> str:
    municipio_id = str(uuid.uuid4())
    plan_id = str(uuid.uuid4())
    linea_id = str(uuid.uuid4())

    await conexion.execute(
        text(
            "INSERT INTO municipios (id, codigo, nombre, estado) "
            "VALUES (CAST(:id AS uuid), :codigo, :nombre, 'ACTIVO')"
        ),
        {
            "id": municipio_id,
            "codigo": f"T{uuid.uuid4().hex[:8].upper()}",
            "nombre": "Municipio temporal de pruebas RLS",
        },
    )
    await _set_tenant(conexion, municipio_id)
    await conexion.execute(
        text(
            "INSERT INTO planes_desarrollo (id, municipio_id, codigo, nombre, estado) "
            "VALUES (CAST(:id AS uuid), CAST(:municipio AS uuid), :codigo, :nombre, 'ACTIVO')"
        ),
        {
            "id": plan_id,
            "municipio": municipio_id,
            "codigo": "PLAN-RLS",
            "nombre": "Plan temporal de pruebas RLS",
        },
    )
    await conexion.execute(
        text(
            "INSERT INTO lineas_estrategicas "
            "(id, municipio_id, plan_desarrollo_id, codigo, nombre, estado) "
            "VALUES (CAST(:id AS uuid), CAST(:municipio AS uuid), CAST(:plan AS uuid), "
            ":codigo, :nombre, 'ACTIVO')"
        ),
        {
            "id": linea_id,
            "municipio": municipio_id,
            "plan": plan_id,
            "codigo": f"RLS-{uuid.uuid4().hex[:8].upper()}",
            "nombre": "Linea temporal de pruebas RLS",
        },
    )

    try:
        yield {"municipio_id": municipio_id, "plan_id": plan_id}
    finally:
        await _set_tenant(conexion, municipio_id)
        await conexion.execute(
            text(
                "DELETE FROM lineas_estrategicas WHERE municipio_id = CAST(:m AS uuid)"
            ),
            {"m": municipio_id},
        )
        await conexion.execute(
            text("DELETE FROM planes_desarrollo WHERE municipio_id = CAST(:m AS uuid)"),
            {"m": municipio_id},
        )
        await _set_tenant(conexion, "")
        await conexion.execute(
            text("DELETE FROM municipios WHERE id = CAST(:m AS uuid)"),
            {"m": municipio_id},
        )


@pytest.mark.asyncio
async def test_cada_tenant_solo_ve_sus_propias_lineas(
    conexion, tenant_principal, tenant_ajeno
):
    await _set_tenant(conexion, tenant_ajeno["municipio_id"])
    assert await _scalar(conexion, LINEAS_VISIBLES) == 1

    await _set_tenant(conexion, tenant_principal)
    lineas_del_otro = await _scalar(
        conexion,
        f"{LINEAS_VISIBLES} AND municipio_id = CAST(:municipio AS uuid)",
        {"municipio": tenant_ajeno["municipio_id"]},
    )

    assert lineas_del_otro == 0


@pytest.mark.asyncio
async def test_sin_contexto_de_tenant_no_se_ven_filas(conexion, tenant_ajeno):
    await _set_tenant(conexion, "")

    assert await _scalar(conexion, LINEAS_VISIBLES) == 0


@pytest.mark.asyncio
async def test_no_se_puede_escribir_una_fila_de_otro_municipio(
    conexion, tenant_principal, tenant_ajeno
):
    await _set_tenant(conexion, tenant_principal)

    with pytest.raises(DBAPIError):
        await conexion.execute(
            text(
                "INSERT INTO lineas_estrategicas "
                "(id, municipio_id, plan_desarrollo_id, codigo, nombre, estado) "
                "VALUES (CAST(:id AS uuid), CAST(:municipio AS uuid), CAST(:plan AS uuid), "
                ":codigo, :nombre, 'ACTIVO')"
            ),
            {
                "id": str(uuid.uuid4()),
                "municipio": tenant_ajeno["municipio_id"],
                "plan": tenant_ajeno["plan_id"],
                "codigo": f"RLS-{uuid.uuid4().hex[:8].upper()}",
                "nombre": "Linea escrita hacia otro municipio",
            },
        )


@pytest.mark.asyncio
async def test_no_se_puede_actualizar_ni_borrar_una_fila_ajena(conexion, tenant_ajeno):
    await _set_tenant(conexion, tenant_ajeno["municipio_id"])
    fila = (
        await conexion.execute(
            text("SELECT id FROM lineas_estrategicas WHERE deleted_at IS NULL LIMIT 1")
        )
    ).first()

    await _set_tenant(conexion, "")
    actualizadas = await conexion.execute(
        text(
            "UPDATE lineas_estrategicas SET nombre = 'intento' WHERE id = CAST(:id AS uuid)"
        ),
        {"id": fila[0]},
    )
    borradas = await conexion.execute(
        text("DELETE FROM lineas_estrategicas WHERE id = CAST(:id AS uuid)"),
        {"id": fila[0]},
    )

    assert actualizadas.rowcount == 0
    assert borradas.rowcount == 0


@pytest.mark.asyncio
async def test_el_rol_de_aplicacion_no_puede_crear_tablas(conexion, tenant_ajeno):
    with pytest.raises(DBAPIError):
        await conexion.execute(text("CREATE TABLE prueba_rls (id uuid)"))
