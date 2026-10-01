import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis import asyncio as redis_asyncio
from sqlalchemy import text
from starlette.middleware.base import RequestResponseEndpoint

from .api.v1.router import api_router
from .core.config import settings
from .core.database import AsyncSessionLocal, RLSMiddleware, engine
from .core.logging import setup_logging
from .core.metrics import MetricsMiddleware, render_metrics
from .core.middleware import AuditMiddleware, RateLimitMiddleware, RequestIDMiddleware

HEALTH_CHECK_TIMEOUT_SECONDS = 2.0

setup_logging(settings.LOG_LEVEL, settings.LOG_FORMAT)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings.validate_production()
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="API para SIGEM Colombia - Sistema de Información para el Seguimiento al Plan de Desarrollo Municipal",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(AuditMiddleware)
app.add_middleware(RLSMiddleware)  # Extracts municipio_id for Row-Level Security
if settings.METRICS_ENABLED:
    app.add_middleware(MetricsMiddleware)
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(
        RateLimitMiddleware,
        default_max_requests=settings.RATE_LIMIT_DEFAULT_REQUESTS,
        login_max_requests=settings.RATE_LIMIT_LOGIN_ATTEMPTS,
        window_seconds=settings.RATE_LIMIT_WINDOW,
    )
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )


@app.middleware("http")
async def security_headers(request: Request, call_next: RequestResponseEndpoint) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Router
app.include_router(api_router, prefix="/api/v1")


async def _check_database() -> str:
    try:
        async with asyncio.timeout(HEALTH_CHECK_TIMEOUT_SECONDS):
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "error"


async def _check_redis() -> str:
    try:
        async with asyncio.timeout(HEALTH_CHECK_TIMEOUT_SECONDS):
            client = redis_asyncio.from_url(
                settings.REDIS_URL,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
            try:
                await client.ping()
            finally:
                await client.aclose()
        return "ok"
    except Exception:
        return "error"


@app.get("/health")
async def health_check() -> JSONResponse:
    database_status = await _check_database()
    healthy = database_status == "ok"
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={
            "status": "healthy" if healthy else "degraded",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "checks": {"database": database_status},
        },
    )


@app.get("/health/live")
async def health_live() -> dict[str, str]:
    return {
        "status": "alive",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/health/ready")
async def health_ready() -> Response:
    from fastapi.responses import JSONResponse

    checks: dict[str, str] = {"database": "error", "redis": "error"}
    try:
        database_status, redis_status = await asyncio.gather(_check_database(), _check_redis())
        checks = {"database": database_status, "redis": redis_status}
    except Exception:
        pass

    ready = all(status == "ok" for status in checks.values())
    return JSONResponse(
        status_code=200 if ready else 503,
        content={
            "status": "ready" if ready else "not_ready",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "checks": checks,
        },
    )


@app.get("/metrics")
async def metrics_endpoint(request: Request) -> Response:
    if not settings.METRICS_ENABLED:
        raise HTTPException(status_code=404, detail="Recurso no encontrado")

    token = settings.METRICS_TOKEN
    if token:
        authorization = request.headers.get("Authorization", "")
        if authorization != f"Bearer {token}":
            raise HTTPException(
                status_code=401,
                detail="Token de métricas inválido o ausente",
            )

    content, media_type = render_metrics()
    return Response(content=content, media_type=media_type)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": f"Bienvenido a {settings.APP_NAME}",
        "docs": "/docs",
    }
