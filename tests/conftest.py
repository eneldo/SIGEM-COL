"""Shared test fixtures for SIGEM Colombia tests.

The suite runs in-process by default: `fastapi.testclient.TestClient` wraps the
ASGI app so no running server is required. Set `SIGEM_API_URL` to run the same
tests against a live server (e.g. http://localhost:8001).

Environment variables must be configured before importing `src.backend`, because
settings, the DB engine and the rate limiter are all built at import time.
"""

import asyncio
import os
import tempfile
import uuid

# tests/manual/ contiene scripts funcionales con código a nivel de módulo
# que se conectan a backend Docker; no deben coleccionarse por pytest.
collect_ignore = ["manual"]

_TEST_ENV_DEFAULTS = {
    "ENVIRONMENT": "development",
    "APP_ENV": "development",
    "DEBUG": "false",
    "SECRET_KEY": "sigem-test-secret-key-0123456789abcdef0123456789",
    "JWT_SECRET_KEY": "sigem-test-jwt-secret-key-0123456789abcdef01234",
    "DATABASE_URL": "postgresql+asyncpg://sigem:sigem_password@localhost:5433/sigem_db",
    "REDIS_URL": "redis://localhost:6379/0",
    "RATE_LIMIT_LOGIN_ATTEMPTS": "10000000",
    "RATE_LIMIT_DEFAULT_REQUESTS": "10000000",
    "STORAGE_PATH": os.path.join(tempfile.gettempdir(), "sigem_test_evidencias"),
}

for _key, _value in _TEST_ENV_DEFAULTS.items():
    os.environ.setdefault(_key, _value)

import httpx  # noqa: E402
import pyotp  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from src.backend.main import app  # noqa: E402

LIVE_URL = os.getenv("SIGEM_API_URL")
BASE_URL = LIVE_URL or "http://testserver"
API_PREFIX = f"{BASE_URL}/api/v1"

ADMIN_PASSWORD = "SigemAdmin2026!"


def _totp(secret: str) -> str:
    return pyotp.TOTP(secret).now()


def unique_username(prefix: str = "test") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def auth_header(token: str) -> dict:
    """Return Authorization header dict."""
    return {"Authorization": f"Bearer {token}"}


def create_temp_user(api, admin_token, *, rol_id=None, username=None, password=None):
    """Create an isolated temporary user (soft-deleted afterwards)."""
    username = username or unique_username()
    password = password or "TempMfaPassword2026!!"
    payload = {
        "codigo": uuid.uuid4().hex[:10].upper(),
        "username": username,
        "email": f"{username}@example.com",
        "nombre_completo": "Test MFA Usuario",
        "password": password,
    }
    if rol_id:
        payload["rol_id"] = rol_id
    resp = api.post(f"{API_PREFIX}/usuarios", json=payload, headers=auth_header(admin_token))
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["id"], username, password


def login_as(api, username, password):
    return api.post(
        f"{API_PREFIX}/auth/login",
        json={
            "username": username,
            "password": password,
            "municipio_codigo": "00000",
        },
    )


def _reset_admin_mfa() -> bool:
    """Clear a leftover admin MFA state left behind by a crashed run.

    The suite enables/disables admin MFA only through fixtures; if a previous
    run died mid-way the admin account can be left with MFA active and no known
    secret, which would block every subsequent run. Restore the documented dev
    state (MFA off) directly in the database.
    """
    from src.backend.core.config import settings

    try:
        import asyncpg
        from sqlalchemy import make_url

        url = make_url(settings.DATABASE_URL)

        async def _reset() -> None:
            conn = await asyncpg.connect(
                host=url.host or "localhost",
                port=url.port or 5432,
                user=url.username or "sigem",
                password=url.password or "",
                database=url.database or "sigem_db",
            )
            try:
                await conn.execute(
                    "UPDATE usuarios SET mfa_activo=false, mfa_secret=NULL "
                    "WHERE username='admin' AND municipio_id = "
                    "(SELECT id FROM municipios WHERE codigo='00000')"
                )
            finally:
                await conn.close()

        asyncio.run(_reset())
        return True
    except Exception:
        return False


def _quiet_sql_logs():
    """SQLAlchemy's startup SQL is noise in test output.

    `setup_logging()` forces the sqlalchemy loggers to INFO during app
    lifespan, which makes the engine emit every statement; keep them quiet
    for the whole session.
    """
    import logging

    for name in (
        "sqlalchemy.engine",
        "sqlalchemy.engine.Engine",
        "sqlalchemy.pool",
        "sqlalchemy.dialects",
        "sqlalchemy.orm",
    ):
        logging.getLogger(name).setLevel(logging.WARNING)


@pytest.fixture(scope="session")
def api():
    """HTTP client: in-process ASGI by default, live server if SIGEM_API_URL is set."""
    if LIVE_URL:
        with httpx.Client(base_url=LIVE_URL, timeout=30.0) as client:
            yield client
    else:
        with TestClient(app) as client:
            _quiet_sql_logs()
            yield client


@pytest.fixture(scope="session")
def admin_token(api):
    """Login as admin and return the access token."""
    resp = api.post(
        "/api/v1/auth/login",
        json={
            "username": "admin",
            "password": ADMIN_PASSWORD,
            "municipio_codigo": "00000",
        },
    )
    if resp.status_code == 200 and resp.json().get("mfa_required"):
        if not _reset_admin_mfa():
            pytest.fail(
                "Admin has MFA enabled but no secret is known to this test run and "
                "the database could not be reached to reset it. "
                "Reset it with: UPDATE usuarios SET mfa_activo=false, mfa_secret=NULL "
                "WHERE username='admin';"
            )
        resp = api.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": ADMIN_PASSWORD,
                "municipio_codigo": "00000",
            },
        )
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"
    data = resp.json()
    assert not data.get("mfa_required"), "Admin MFA state could not be reset"
    return data["access_token"]


def _first_item(resp, label):
    assert resp.status_code == 200, f"{label}: {resp.text}"
    body = resp.json()
    items = body.get("items") if isinstance(body, dict) else body
    assert items, f"{label}: no hay datos sembrados en el municipio"
    return items[0]


@pytest.fixture(scope="session")
def gestor_credentials(api, admin_token):
    """Provision an isolated plain-GESTOR account with one assigned product.

    The seeded gestor accounts are soft-deleted or have roles that would break
    the RBAC assertions, so the suite creates its own gestor líder (rol GESTOR,
    no GESTOR_LIDER) plus a product assigned to it, and cleans both up at the
    end of the session.
    """
    roles = api.get(f"{API_PREFIX}/catalogos/roles", headers=auth_header(admin_token))
    assert roles.status_code == 200, roles.text
    rol_id = next((r["id"] for r in roles.json() if r["codigo"] == "GESTOR"), None)
    assert rol_id, "El rol GESTOR debe existir en el catálogo de roles"

    deps = api.get(f"{API_PREFIX}/catalogos/dependencias", headers=auth_header(admin_token))
    dependencia_id = _first_item(deps, "catalogos/dependencias")["id"]

    username = unique_username("tges")
    password = "GestorTestPassword2026!!"
    created = api.post(
        f"{API_PREFIX}/gestores",
        json={
            "nombre_completo": "Gestor De Pruebas SIGEM",
            "email": f"{username}@example.com",
            "cargo": "Gestor de pruebas",
            "rol_id": rol_id,
            "dependencia_principal_id": dependencia_id,
            "username": username,
            "password": password,
        },
        headers=auth_header(admin_token),
    )
    assert created.status_code == 201, created.text
    gestor_id = created.json()["id"]

    programas = api.get(
        f"{API_PREFIX}/programas?estado=ACTIVO&page_size=100",
        headers=auth_header(admin_token),
    )
    programa_id = _first_item(programas, "programas")["id"]

    producto = api.post(
        f"{API_PREFIX}/productos",
        json={
            "codigo": f"PT-{uuid.uuid4().hex[:10].upper()}",
            "nombre": "Producto de pruebas automatizadas",
            "indicador": "Porcentaje de avance de pruebas",
            "meta_cuatrienio": 10000,
            "unidad_medida": "Unidades",
            "programa_id": programa_id,
            "gestor_lider_id": gestor_id,
        },
        headers=auth_header(admin_token),
    )
    assert producto.status_code == 201, producto.text
    producto_id = producto.json()["id"]

    yield {
        "username": username,
        "password": password,
        "gestor_id": gestor_id,
        "producto_id": producto_id,
    }

    for url in (
        f"{API_PREFIX}/productos/{producto_id}",
        f"{API_PREFIX}/gestores/{gestor_id}",
    ):
        try:
            api.delete(url, headers=auth_header(admin_token))
        except Exception:
            pass


@pytest.fixture(scope="session")
def gestor_token(api, gestor_credentials):
    """Login as the provisioned gestor and return the access token."""
    resp = api.post(
        f"{API_PREFIX}/auth/login",
        json={
            "username": gestor_credentials["username"],
            "password": gestor_credentials["password"],
        },
    )
    assert resp.status_code == 200, f"Gestor login failed: {resp.text}"
    return resp.json()["access_token"]
