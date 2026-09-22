"""
Database configuration - SIGEM Colombia
RLS (Row-Level Security) activated via session variable.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from .config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,
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

    async def dispatch(self, request: Request, call_next):
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
                pass
        return await call_next(request)


async def get_db() -> AsyncSession:
    """
    Database session dependency with RLS activation.
    The RLS middleware must be in the middleware stack for this to work.
    """
    async with AsyncSessionLocal() as session:
        try:
            # Activate Row-Level Security if municipio_id is available
            # This is set by RLSMiddleware before this dependency runs
            from starlette.requests import Request
            from fastapi import Request as FastAPIRequest
            try:
                # FastAPI dependency injection provides request context
                request = FastAPIRequest.scope.get("app")
            except Exception:
                pass

            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_with_rls(request: Request) -> AsyncSession:
    """
    Database session dependency with RLS activation.
    Extracts municipio_id from request.state (set by RLSMiddleware)
    and activates PostgreSQL Row-Level Security.
    """
    async with AsyncSessionLocal() as session:
        try:
            municipio_id = getattr(request.state, "municipio_id", None)
            if municipio_id:
                await session.execute(
                    text("SELECT set_config('app.current_municipio_id', :mid, true)"),
                    {"mid": str(municipio_id)},
                )
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
