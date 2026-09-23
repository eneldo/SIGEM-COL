"""Shared test fixtures for SIGEM Colombia tests."""
import os
import httpx
import pytest

BASE_URL = os.getenv("SIGEM_API_URL", "http://localhost:8001")
API_PREFIX = f"{BASE_URL}/api/v1"


@pytest.fixture(scope="session")
def api():
    """HTTPX async client targeting the live Docker backend."""
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture(scope="session")
def admin_token(api):
    """Login as admin and return the access token."""
    resp = api.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "SigemAdmin2026!",
    })
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"
    data = resp.json()
    return data["access_token"]


@pytest.fixture(scope="session")
def gestor_token(api):
    """Login as gestor líder and return the access token."""
    resp = api.post("/api/v1/auth/login", json={
        "username": "candresmejia",
        "password": "@aTrfh0xcHYKng*QOkyDshUr",
    })
    assert resp.status_code == 200, f"Gestor login failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def superadmin_token(api):
    """Login as superadmin and return the access token."""
    resp = api.post("/api/v1/auth/login", json={
        "username": "superadmin",
        "password": "SuperAdmin2026!",
    })
    assert resp.status_code == 200, f"SuperAdmin login failed: {resp.text}"
    return resp.json()["access_token"]


def auth_header(token: str) -> dict:
    """Return Authorization header dict."""
    return {"Authorization": f"Bearer {token}"}
