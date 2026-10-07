"""
Database configuration - SIGEM Colombia
RLS (Row-Level Security) activated via session variable.
"""

import logging
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
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


async def set_tenant_context(session: AsyncSession, municipio_id: uuid.UUID | None) -> None:
    """
    Set (or clear) the PostgreSQL RLS tenant context for this session.

    Uses session-level set_config (is_local=false) so the context survives the
    commits performed mid-request by services. Combined with get_db's dedicated
    per-request connection, the GUC can never leak to or from another request.
    """
    value = str(municipio_id) if municipio_id else ""
    await session.execute(text(TENANT_CONTEXT_SQL), {"value": value})


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    """
    Database session dependency with RLS activation.

    RLSMiddleware extracts municipio_id from the JWT into request.state;
    this dependency applies it to the session before any query runs.
    Sessions without a token are explicitly scoped to the empty tenant,
    which makes every RLS-protected query fail closed.

    The session is bound to a connection held for the whole request: services
    that commit mid-request keep the same physical connection, so the tenant
    GUC (set once below) stays valid for every later statement of the request.
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


async def get_db_with_rls(request: Request) -> AsyncIterator[AsyncSession]:
    """
    Backward-compatible alias of get_db: both dependencies apply the same
    tenant context, so endpoints can no longer obtain an unscoped session.
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
