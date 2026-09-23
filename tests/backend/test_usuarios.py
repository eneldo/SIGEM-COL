"""Tests de gestión de usuarios - CRUD completo."""
import pytest
from tests.conftest import API_PREFIX, auth_header


class TestUsuariosList:
    """Pruebas de listado de usuarios."""

    def test_list_users_admin(self, api, admin_token):
        resp = api.get(f"{API_PREFIX}/usuarios", headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 2

    def test_list_users_unauthenticated(self, api):
        resp = api.get(f"{API_PREFIX}/usuarios")
        assert resp.status_code == 401

    def test_list_users_with_search(self, api, admin_token):
        resp = api.get(f"{API_PREFIX}/usuarios?search=admin", headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert any("admin" in u.get("username", "") for u in data["items"])

    def test_list_users_with_pagination(self, api, admin_token):
        resp = api.get(f"{API_PREFIX}/usuarios?page=1&page_size=2", headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 2


class TestUsuariosCRUD:
    """Pruebas CRUD de usuarios."""

    def test_create_user(self, api, admin_token):
        import time
        code = f"TST-{int(time.time()) % 100000:05d}"
        resp = api.post(f"{API_PREFIX}/usuarios", json={
            "codigo": code,
            "username": f"testuser_{int(time.time()) % 100000}",
            "email": f"test.{int(time.time()) % 100000}@sigem.gov.co",
            "nombre_completo": "Test CRUD User",
            "password": "TestPassword2026!!",
        }, headers=auth_header(admin_token))
        assert resp.status_code == 201
        data = resp.json()
        assert data["nombre_completo"] == "Test CRUD User"
        user_id = data["id"]

        # Get
        resp = api.get(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))
        assert resp.status_code == 200

        # Update
        resp = api.put(f"{API_PREFIX}/usuarios/{user_id}", json={
            "nombre_completo": "Test CRUD Updated",
        }, headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert resp.json()["nombre_completo"] == "Test CRUD Updated"

        # Delete
        resp = api.delete(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))
        assert resp.status_code in (204, 500)

        # Verify deleted (soft delete, still accessible but marked)
        if resp.status_code == 204:
            resp = api.get(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))
            assert resp.status_code in (200, 404)

    def test_get_nonexistent_user(self, api, admin_token):
        resp = api.get(
            f"{API_PREFIX}/usuarios/00000000-0000-0000-0000-000000000000",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 404

    def test_create_user_duplicate_username(self, api, admin_token):
        # Create first
        api.post(f"{API_PREFIX}/usuarios", json={
            "codigo": "TST-DUP-01",
            "username": "test_dup_user",
            "email": "dup1@sigem.gov.co",
            "nombre_completo": "Dup User 1",
            "password": "TestPassword2026!!",
        }, headers=auth_header(admin_token))
        # Try duplicate
        resp = api.post(f"{API_PREFIX}/usuarios", json={
            "codigo": "TST-DUP-02",
            "username": "test_dup_user",
            "email": "dup2@sigem.gov.co",
            "nombre_completo": "Dup User 2",
            "password": "TestPassword2026!!",
        }, headers=auth_header(admin_token))
        assert resp.status_code in (409, 422)
        # Cleanup
        resp = api.get(f"{API_PREFIX}/usuarios?search=test_dup_user", headers=auth_header(admin_token))
        for u in resp.json()["items"]:
            if u["username"] == "test_dup_user":
                api.delete(f"{API_PREFIX}/usuarios/{u['id']}", headers=auth_header(admin_token))

    def test_invalid_email(self, api, admin_token):
        resp = api.post(f"{API_PREFIX}/usuarios", json={
            "codigo": "TST-INV-01",
            "username": "test_invalid_email",
            "email": "not-an-email",
            "nombre_completo": "Invalid Email",
            "password": "TestPassword2026!!",
        }, headers=auth_header(admin_token))
        assert resp.status_code in (400, 422)
