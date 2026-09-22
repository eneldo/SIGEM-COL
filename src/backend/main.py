from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.middleware import RequestIDMiddleware, AuditMiddleware, RateLimitMiddleware
from .core.database import RLSMiddleware
from .api.v1.router import api_router

app = FastAPI(
    title=settings.APP_NAME,
    description="API para SIGEM Colombia - Sistema de Información para el Seguimiento al Plan de Desarrollo Municipal",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(AuditMiddleware)
app.add_middleware(RLSMiddleware)  # Extracts municipio_id for Row-Level Security
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=settings.RATE_LIMIT_LOGIN_ATTEMPTS * 10,
        window_seconds=settings.RATE_LIMIT_LOGIN_WINDOW_MINUTES * 60,
    )
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
)


@app.middleware("http")
async def security_headers(request, call_next):
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


@app.get("/health")
async def health_check():
    from sqlalchemy import text
    from .core.database import AsyncSessionLocal

    db_ok = False
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        pass

    status_code = 200 if db_ok else 503
    return {
        "status": "healthy" if db_ok else "degraded",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "checks": {"database": "ok" if db_ok else "error"},
    }


@app.get("/")
async def root():
    return {
        "message": f"Bienvenido a {settings.APP_NAME}",
        "docs": "/docs",
    }
