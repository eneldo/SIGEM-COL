"""Tests de autenticación - Login, tokens, cambio de contraseña."""
from tests.conftest import API_PREFIX, auth_header


class TestLogin:
    """Pruebas de login y autenticación."""

    def test_login_admin_ok(self, api):
        resp = api.post(f"{API_PREFIX}/auth/login", json={
            "username": "admin",
            "password": "SigemAdmin2026!",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["expires_in"] > 0
        assert "user" in data
        assert data["user"]["username"] == "admin"
        assert "SUPERADMIN_PLATAFORMA" in data["user"]["roles"]

    def test_login_gestor_ok(self, api):
        resp = api.post(f"{API_PREFIX}/auth/login", json={
            "username": "enemova",
            "password": "EneldoGestor2026!",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["username"] == "enemova"
        assert "GESTOR" in data["user"]["roles"]

    def test_login_wrong_password(self, api):
        resp = api.post(f"{API_PREFIX}/auth/login", json={
            "username": "admin",
            "password": "wrong_password_12345",
        })
        assert resp.status_code == 401
        assert "Credenciales" in resp.json()["detail"]

    def test_login_nonexistent_user(self, api):
        resp = api.post(f"{API_PREFIX}/auth/login", json={
            "username": "usuario_falso_xyz",
            "password": "whatever_password_12345",
        })
        assert resp.status_code == 401

    def test_login_empty_body(self, api):
        resp = api.post(f"{API_PREFIX}/auth/login", json={})
        assert resp.status_code == 422

    def test_login_missing_password(self, api):
        resp = api.post(f"{API_PREFIX}/auth/login", json={"username": "admin"})
        assert resp.status_code == 422


class TestTokenValidation:
    """Pruebas de validación de tokens JWT."""

    def test_me_with_valid_token(self, api, admin_token):
        resp = api.get(f"{API_PREFIX}/auth/me", headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "admin"
        assert "id" in data
        assert "email" in data

    def test_me_without_token(self, api):
        resp = api.get(f"{API_PREFIX}/auth/me")
        assert resp.status_code == 401
        assert "Token" in resp.json()["detail"]

    def test_me_with_invalid_token(self, api):
        resp = api.get(f"{API_PREFIX}/auth/me", headers=auth_header("invalid.jwt.token"))
        assert resp.status_code == 401

    def test_me_with_malformed_header(self, api):
        resp = api.get(f"{API_PREFIX}/auth/me", headers={"Authorization": "NotBearer xxx"})
        assert resp.status_code == 401

    def test_me_with_empty_token_value(self, api):
        resp = api.get(f"{API_PREFIX}/auth/me", headers={"Authorization": "Bearer xyz"})
        assert resp.status_code == 401


class TestLogout:
    """Pruebas de cierre de sesión."""

    def test_logout_ok(self, api, admin_token):
        resp = api.post(f"{API_PREFIX}/auth/logout", headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert "Sesión cerrada" in resp.json()["message"]


class TestPasswordChange:
    """Pruebas de cambio de contraseña."""

    def test_change_password_ok(self, api, admin_token):
        orig, alt = "SigemAdmin2026!", "NewSigemAdmin2026!!"

        def _try_change(current, new):
            return api.post(f"{API_PREFIX}/auth/change-password", json={
                "current_password": current,
                "new_password": new,
                "confirm_password": new,
            }, headers=auth_header(admin_token))

        changed = False
        try:
            resp = _try_change(orig, alt)
            assert resp.status_code == 200, resp.text
            changed = True
            assert "exitosamente" in resp.json()["message"]
        finally:
            if changed:
                back = _try_change(alt, orig)
                assert back.status_code == 200, back.text

    def test_change_password_mismatch(self, api, admin_token):
        resp = api.post(f"{API_PREFIX}/auth/change-password", json={
            "current_password": "SigemAdmin2026!",
            "new_password": "NewPassword2026!!",
            "confirm_password": "DifferentPassword2026!!",
        }, headers=auth_header(admin_token))
        assert resp.status_code == 400
        assert "coinciden" in resp.json()["detail"]

    def test_change_password_wrong_current(self, api, admin_token):
        resp = api.post(f"{API_PREFIX}/auth/change-password", json={
            "current_password": "wrong_current_password",
            "new_password": "NewSigemAdmin2026!!",
            "confirm_password": "NewSigemAdmin2026!!",
        }, headers=auth_header(admin_token))
        assert resp.status_code == 400
        assert "incorrecta" in resp.json()["detail"]

    def test_change_password_without_auth(self, api):
        resp = api.post(f"{API_PREFIX}/auth/change-password", json={
            "current_password": "SigemAdmin2026!",
            "new_password": "NewSigemAdmin2026!!",
            "confirm_password": "NewSigemAdmin2026!!",
        })
        assert resp.status_code == 401
