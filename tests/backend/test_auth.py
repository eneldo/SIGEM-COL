"""Tests de autenticación - Login, tokens, cambio de contraseña."""

import uuid

from tests.conftest import API_PREFIX, auth_header, create_temp_user, login_as


class TestLogin:
    """Pruebas de login y autenticación."""

    def test_login_admin_ok(self, api):
        resp = api.post(
            f"{API_PREFIX}/auth/login",
            json={
                "username": "admin",
                "password": "SigemAdmin2026!",
                "municipio_codigo": "00000",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["expires_in"] > 0
        assert "user" in data
        assert data["user"]["username"] == "admin"
        assert "SUPERADMIN_PLATAFORMA" in data["user"]["roles"]

    def test_login_gestor_ok(self, api, gestor_credentials):
        resp = api.post(
            f"{API_PREFIX}/auth/login",
            json={
                "username": gestor_credentials["username"],
                "password": gestor_credentials["password"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["username"] == gestor_credentials["username"]
        assert "GESTOR" in data["user"]["roles"]

    def test_login_wrong_password(self, api):
        resp = api.post(
            f"{API_PREFIX}/auth/login",
            json={
                "username": "admin",
                "password": "wrong_password_12345",
                "municipio_codigo": "00000",
            },
        )
        assert resp.status_code == 401
        assert "Credenciales" in resp.json()["detail"]

    def test_login_nonexistent_user(self, api):
        resp = api.post(
            f"{API_PREFIX}/auth/login",
            json={
                "username": "usuario_falso_xyz",
                "password": "whatever_password_12345",
                "municipio_codigo": "00000",
            },
        )
        assert resp.status_code == 401

    def test_login_without_municipio_uses_default(self, api):
        resp = api.post(
            f"{API_PREFIX}/auth/login",
            json={
                "username": "admin",
                "password": "SigemAdmin2026!",
            },
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["access_token"]

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
        resp = api.get(
            f"{API_PREFIX}/auth/me", headers=auth_header("invalid.jwt.token")
        )
        assert resp.status_code == 401

    def test_me_with_malformed_header(self, api):
        resp = api.get(
            f"{API_PREFIX}/auth/me", headers={"Authorization": "NotBearer xxx"}
        )
        assert resp.status_code == 401

    def test_me_with_empty_token_value(self, api):
        resp = api.get(f"{API_PREFIX}/auth/me", headers={"Authorization": "Bearer xyz"})
        assert resp.status_code == 401


class TestLogout:
    """Pruebas de cierre de sesión."""

    def test_logout_ok(self, api, admin_token):
        # Logout revoca todas las sesiones del usuario: se usa un usuario
        # temporal para no invalidar el token compartido del fixture admin.
        user_id, username, password = create_temp_user(api, admin_token)
        try:
            login = login_as(api, username, password)
            assert login.status_code == 200, login.text
            token = login.json()["access_token"]

            resp = api.post(f"{API_PREFIX}/auth/logout", headers=auth_header(token))
            assert resp.status_code == 200
            assert "Sesión cerrada" in resp.json()["message"]
        finally:
            api.delete(
                f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token)
            )


class TestPasswordChange:
    """Pruebas de cambio de contraseña."""

    def test_change_password_ok(self, api, admin_token):
        orig, alt = "SigemAdmin2026!", "NewSigemAdmin2026!!"

        def _try_change(current, new):
            return api.post(
                f"{API_PREFIX}/auth/change-password",
                json={
                    "current_password": current,
                    "new_password": new,
                    "confirm_password": new,
                },
                headers=auth_header(admin_token),
            )

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
        resp = api.post(
            f"{API_PREFIX}/auth/change-password",
            json={
                "current_password": "SigemAdmin2026!",
                "new_password": "NewPassword2026!!",
                "confirm_password": "DifferentPassword2026!!",
            },
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 400
        assert "coinciden" in resp.json()["detail"]

    def test_change_password_wrong_current(self, api, admin_token):
        resp = api.post(
            f"{API_PREFIX}/auth/change-password",
            json={
                "current_password": "wrong_current_password",
                "new_password": "NewSigemAdmin2026!!",
                "confirm_password": "NewSigemAdmin2026!!",
            },
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 400
        assert "incorrecta" in resp.json()["detail"]

    def test_change_password_without_auth(self, api):
        resp = api.post(
            f"{API_PREFIX}/auth/change-password",
            json={
                "current_password": "SigemAdmin2026!",
                "new_password": "NewSigemAdmin2026!!",
                "confirm_password": "NewSigemAdmin2026!!",
            },
        )
        assert resp.status_code == 401


class TestMustChangePasswordEnforcement:
    """Server-side enforcement del cambio obligatorio de contraseña."""

    def test_flag_blocks_endpoints_until_password_changed(self, api, admin_token):
        suffix = uuid.uuid4().hex[:8]
        username = f"test_pw_{suffix}"
        codigo = f"TST-PW-{suffix[:6].upper()}"
        initial_pw = "TempPassword2026!!"
        new_pw = "ChangedPassword2026!!"
        user_id = None

        try:
            resp = api.post(
                f"{API_PREFIX}/usuarios",
                json={
                    "codigo": codigo,
                    "username": username,
                    "email": f"{username}@example.com",
                    "nombre_completo": "Test PW Enforce",
                    "password": initial_pw,
                },
                headers=auth_header(admin_token),
            )
            assert resp.status_code in (200, 201), resp.text
            user_id = resp.json()["id"]

            login = api.post(
                f"{API_PREFIX}/auth/login",
                json={
                    "username": username,
                    "password": initial_pw,
                    "municipio_codigo": "00000",
                },
            )
            assert login.status_code == 200, login.text
            assert login.json()["must_change_password"] is True
            token = login.json()["access_token"]
            headers = auth_header(token)

            # /auth/me is in the allowlist: the app needs it to boot.
            me = api.get(f"{API_PREFIX}/auth/me", headers=headers)
            assert me.status_code == 200, me.text

            # Any other protected endpoint is rejected while the flag is set.
            blocked = api.get(f"{API_PREFIX}/catalogos/roles", headers=headers)
            assert blocked.status_code == 403, blocked.text
            assert blocked.json()["detail"] == "PASSWORD_CHANGE_REQUIRED"

            # The change-password flow itself must be reachable.
            cp = api.post(
                f"{API_PREFIX}/auth/change-password",
                json={
                    "current_password": initial_pw,
                    "new_password": new_pw,
                    "confirm_password": new_pw,
                },
                headers=headers,
            )
            assert cp.status_code == 200, cp.text

            # Flag cleared: protected endpoints are now reachable.
            after = api.get(f"{API_PREFIX}/catalogos/roles", headers=headers)
            assert after.status_code == 200, after.text
        finally:
            if user_id:
                api.delete(
                    f"{API_PREFIX}/usuarios/{user_id}",
                    headers=auth_header(admin_token),
                )
