"""Shared test fixtures for SIGEM Colombia tests."""
import os
import uuid

import httpx
import pyotp
import pytest

# tests/manual/ contiene scripts funcionales con código a nivel de módulo
# que se conectan a backend Docker; no deben coleccionarse por pytest.
collect_ignore = ["manual"]

BASE_URL = os.getenv("SIGEM_API_URL", "http://localhost:8001")
API_PREFIX = f"{BASE_URL}/api/v1"

ADMIN_PASSWORD = "SigemAdmin2026!"

# Admin MFA state (the server enforces MFA for admins, so the session-scoped
# fixture provisions it once and revokes it in its finalizer).
_admin_mfa = {"secret": None}


def _totp(secret: str) -> str:
    return pyotp.TOTP(secret).now()


def unique_username(prefix: str = "test") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


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
    return api.post(f"{API_PREFIX}/auth/login", json={
        "username": username,
        "password": password,
        "municipio_codigo": "00000",
    })


@pytest.fixture(scope="session")
def api():
    """HTTPX async client targeting the live Docker backend."""
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture(scope="session")
def admin_token(api):
    """Login as admin, provisioning MFA when needed (enforced for admins)."""
    resp = api.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": ADMIN_PASSWORD,
        "municipio_codigo": "00000",
    })
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"
    data = resp.json()

    if data.get("mfa_required"):
        if not _admin_mfa["secret"]:
            pytest.fail(
                "Admin has MFA enabled but no secret is known to this test run. "
                "Reset it with: UPDATE usuarios SET mfa_activo=false, mfa_secret=NULL "
                "WHERE username='admin';"
            )
        login = api.post("/api/v1/auth/mfa/login", json={
            "mfa_token": data["mfa_token"],
            "code": _totp(_admin_mfa["secret"]),
        })
        assert login.status_code == 200, f"MFA login failed: {login.text}"
        token = login.json()["access_token"]
    else:
        token = data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        setup = api.post("/api/v1/auth/mfa/setup", headers=headers)
        assert setup.status_code == 200, f"MFA setup failed: {setup.text}"
        _admin_mfa["secret"] = setup.json()["secret"]

        verify = api.post("/api/v1/auth/mfa/verify", json={
            "code": _totp(_admin_mfa["secret"]),
        }, headers=headers)
        assert verify.status_code == 200, f"MFA verify failed: {verify.text}"

    yield token

    # Restore: the admin must not keep MFA between sessions so manual dev
    # logins keep working without an authenticator app.
    if _admin_mfa["secret"]:
        api.post("/api/v1/auth/mfa/disable", json={
            "password": ADMIN_PASSWORD,
            "code": _totp(_admin_mfa["secret"]),
        }, headers={"Authorization": f"Bearer {token}"})
        _admin_mfa["secret"] = None


@pytest.fixture(scope="session")
def gestor_token(api):
    """Login as gestor líder and return the access token."""
    resp = api.post("/api/v1/auth/login", json={
        "username": "enemova",
        "password": "EneldoGestor2026!",
        "municipio_codigo": "00000",
    })
    assert resp.status_code == 200, f"Gestor login failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def superadmin_token(api):
    """Login as superadmin and return the access token."""
    resp = api.post("/api/v1/auth/login", json={
        "username": "superadmin",
        "password": "SuperAdmin2026!",
        "municipio_codigo": "00000",
    })
    assert resp.status_code == 200, f"SuperAdmin login failed: {resp.text}"
    return resp.json()["access_token"]


def auth_header(token: str) -> dict:
    """Return Authorization header dict."""
    return {"Authorization": f"Bearer {token}"}
