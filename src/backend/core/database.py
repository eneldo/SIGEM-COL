"""
Database configuration - SIGEM Colombia
RLS (Row-Level Security) activated via session variable.
"""

import logging
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,
    query_cache_size=0,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


class RLSMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts municipio_id from the JWT token
    and stores it in request.state for RLS activation.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request.state.municipio_id = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                from ..core.security import decode_token

                token = auth_header.split(" ")[1]
                payload = decode_token(token)
                if payload and payload.get("type") == "access":
                    request.state.municipio_id = payload.get("municipio_id")
            except Exception:
                logger.warning("rls_token_decode_failed")
        return await call_next(request)


TENANT_CONTEXT_SQL = "SELECT set_config('app.current_municipio_id', :value, false)"
RESET_TENANT_SQL = "RESET app.current_municipio_id"


async def set_tenant_context(session: AsyncSession, municipio_id: uuid.UUID | None) -> None:
    """
    Set (or clear) the PostgreSQL RLS tenant context for this session.

    Uses session-level set_config (is_local=false) so the context survives the
    commits performed mid-request by services. Combined with get_db's dedicated
    per-request connection, the GUC can never leak to or from another request.
    """
    if municipio_id:
        await session.execute(text(TENANT_CONTEXT_SQL), {"value": str(municipio_id)})
    else:
        # Fallo cerrado: sin contexto significa cero filas visibles, y además
        # la conexión queda limpia (ver pool hygiene en get_db).
        await session.execute(text(RESET_TENANT_SQL))


async def assert_restricted_db_role() -> None:
    """
    Verifica al arranque que la conexión usa un rol que NO puede bypasear RLS.

    Un rol SUPERUSER ignora R incluso con FORCE ROW LEVEL SECURITY; un rol con
    BYPASSRLS igual. En producción es condición de arranque; en desarrollo se
    emite un log CRITICAL porque .env apunta habitualmente al rol de migración.
    """
    async with engine.connect() as connection:
        row = (
            await connection.execute(
                text(
                    "SELECT current_user AS role, "
                    "COALESCE((SELECT rolsuper FROM pg_roles WHERE rolname = current_user), "
                    "false) AS rolsuper, "
                    "COALESCE((SELECT rolbypassrls FROM pg_roles WHERE rolname = current_user), "
                    "false) AS bypassrls"
                )
            )
        ).one()

    if row.rolsuper or row.bypassrls:
        message = (
            f"El rol de base de datos '{row.role}' bypasea RLS "
            "(superusuario o BYPASSRLS); el aislamiento multi-municipio no es efectivo. "
            "DATABASE_URL debe usar el rol restringido 'sigem_app'."
        )
        if settings.is_production:
            raise RuntimeError(message)
        logger.critical("db_role_bypasses_rls %s", message)


async def release_tenant_context(connection: AsyncConnection) -> None:
    """
    Higiene de pool: limpia el contexto tenant ANTES de devolver la conexión.

    set_config(is_local=false) sobrevive al commit del request y al RESET del
    pool de SQLAlchemy (ROLLBACK no deshace GUCs consolidados), por lo que una
    conexión devuelta quedaría 'marcada' con el tenant del último request.
    Cualquier consumidor futuro del pool que no fije contexto al inicio heredaría
    ese tenant. El RESET garantiza que la conexión regresa neutra.
    """
    try:
        await connection.execute(text(RESET_TENANT_SQL))
    except Exception:
        # Defensa: la higiene jamás debe romper la liberación de la conexión;
        # el próximo get_db re-fija el contexto en todo caso.
        logger.warning("tenant_context_reset_failed", exc_info=True)


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    """
    Database session dependency with RLS activation.

    RLSMiddleware extracts municipio_id from the JWT into request.state;
    this dependency applies it to the session before any query runs.
    Sessions without a token are explicitly scoped to no tenant (RESET),
    which makes every RLS-protected query fail closed.

    The session is bound to a connection held for the whole request: services
    that commit mid-request keep the same physical connection, so the tenant
    GUC (set once below) stays valid for every later statement of the request.
    Before the connection returns to the pool, release_tenant_context clears
    the GUC so nothing is inherited by a future checkout.
    """
    async with engine.connect() as connection:
        session = AsyncSession(bind=connection, expire_on_commit=False)
        try:
            await set_tenant_context(session, getattr(request.state, "municipio_id", None))
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
            await release_tenant_context(connection)


# Alias intencional (mismo objeto de función, no una copia): ambas dependencias
# aplican el mismo contexto tenant y FastAPI comparte la sesión cacheada cuando
# un endpoint declara las dos, evitando una segunda conexión física por request.
get_db_with_rls = get_db
