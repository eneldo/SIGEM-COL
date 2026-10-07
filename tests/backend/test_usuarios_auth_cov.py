"""Tests de integración para Usuarios y Auth - cobertura extendida."""

import uuid

import pytest

from tests.conftest import (
    API_PREFIX,
    auth_header,
    create_temp_user,
    login_as,
    unique_username,
)


class TestUsuariosCRUD:
    """CRUD completo de usuarios."""

    def _admin_login(self, api):
        resp = api.post(
            f"{API_PREFIX}/auth/login",
            json={
                "username": "admin",
                "password": "SigemAdmin2026!",
                "municipio_codigo": "00000",
            },
        )
        assert resp.status_code == 200, resp.text
        return resp.json()["access_token"]

    def test_crear_usuario_basico(self, api):
        admin_token = self._admin_login(api)
        username = unique_username("create")
        resp = api.post(
            f"{API_PREFIX}/usuarios",
            json={
                "codigo": uuid.uuid4().hex[:10].upper(),
                "username": username,
                "email": f"{username}@example.com",
                "nombre_completo": "Usuario de Prueba",
                "password": "TestPassword2026!!",
            },
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 201, resp.text
        user_id = resp.json()["id"]
        assert resp.json()["must_change_password"] is True
        assert resp.json()["activo"] == 1

        api.delete(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))

    def test_crear_usuario_con_rol_y_dependencia(self, api):
        admin_token = self._admin_login(api)
        roles = api.get(f"{API_PREFIX}/catalogos/roles", headers=auth_header(admin_token)).json()
        rol_id = next((r["id"] for r in roles if r["codigo"] == "GESTOR"), None)
        deps = api.get(
            f"{API_PREFIX}/catalogos/dependencias", headers=auth_header(admin_token)
        ).json()
        dep_id = deps[0]["id"] if deps else None

        username = unique_username("create")
        payload = {
            "codigo": uuid.uuid4().hex[:10].upper(),
            "username": username,
            "email": f"{username}@example.com",
            "nombre_completo": "Usuario con Rol",
            "password": "TestPassword2026!!",
        }
        if rol_id:
            payload["rol_id"] = rol_id
        if dep_id:
            payload["dependencia_id"] = dep_id

        resp = api.post(f"{API_PREFIX}/usuarios", json=payload, headers=auth_header(admin_token))
        assert resp.status_code == 201, resp.text
        user_id = resp.json()["id"]

        api.delete(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))

    def test_crear_usuario_codigo_duplicado(self, api):
        admin_token = self._admin_login(api)
        codigo = uuid.uuid4().hex[:10].upper()
        username1 = unique_username("dup1")
        username2 = unique_username("dup2")
        payload1 = {
            "codigo": codigo,
            "username": username1,
            "email": f"{username1}@example.com",
            "nombre_completo": "Usuario 1",
            "password": "TestPassword2026!!",
        }
        payload2 = {
            "codigo": codigo,
            "username": username2,
            "email": f"{username2}@example.com",
            "nombre_completo": "Usuario 2",
            "password": "TestPassword2026!!",
        }
        r1 = api.post(f"{API_PREFIX}/usuarios", json=payload1, headers=auth_header(admin_token))
        assert r1.status_code == 201, r1.text
        user_id = r1.json()["id"]
        try:
            r2 = api.post(
                f"{API_PREFIX}/usuarios",
                json=payload2,
                headers=auth_header(admin_token),
            )
            assert r2.status_code == 422, r2.text
            assert "código" in r2.json()["detail"]
        finally:
            api.delete(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))

    def test_crear_usuario_username_duplicado(self, api):
        admin_token = self._admin_login(api)
        username = unique_username("dupuser")
        payload1 = {
            "codigo": uuid.uuid4().hex[:10].upper(),
            "username": username,
            "email": f"{username}1@example.com",
            "nombre_completo": "Usuario 1",
            "password": "TestPassword2026!!",
        }
        payload2 = {
            "codigo": uuid.uuid4().hex[:10].upper(),
            "username": username,
            "email": f"{username}2@example.com",
            "nombre_completo": "Usuario 2",
            "password": "TestPassword2026!!",
        }
        r1 = api.post(f"{API_PREFIX}/usuarios", json=payload1, headers=auth_header(admin_token))
        assert r1.status_code == 201, r1.text
        user_id = r1.json()["id"]
        try:
            r2 = api.post(
                f"{API_PREFIX}/usuarios",
                json=payload2,
                headers=auth_header(admin_token),
            )
            assert r2.status_code == 422, r2.text
            assert "username" in r2.json()["detail"]
        finally:
            api.delete(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))

    def test_crear_usuario_campos_obligatorios(self, api):
        admin_token = self._admin_login(api)
        resp = api.post(
            f"{API_PREFIX}/usuarios",
            json={"username": "incompleto"},
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 422, resp.text

    def test_listar_usuarios_sin_filtros(self, api, admin_token):
        resp = api.get(f"{API_PREFIX}/usuarios", headers=auth_header(admin_token))
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    def test_listar_usuarios_con_search(self, api, admin_token):
        resp = api.get(
            f"{API_PREFIX}/usuarios",
            params={"search": "admin"},
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200, resp.text

    def test_listar_usuarios_filtro_estado_activo(self, api, admin_token):
        resp = api.get(
            f"{API_PREFIX}/usuarios",
            params={"estado": "ACTIVO"},
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200, resp.text

    def test_listar_usuarios_filtro_estado_inactivo(self, api, admin_token):
        resp = api.get(
            f"{API_PREFIX}/usuarios",
            params={"estado": "INACTIVO"},
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200, resp.text

    def test_listar_usuarios_paginacion(self, api, admin_token):
        resp = api.get(
            f"{API_PREFIX}/usuarios",
            params={"page": 1, "page_size": 5},
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 5

    def test_obtener_usuario_existente(self, api, admin_token):
        user_id, _, _ = create_temp_user(api, admin_token)
        try:
            resp = api.get(
                f"{API_PREFIX}/usuarios/{user_id}",
                headers=auth_header(admin_token),
            )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["id"] == user_id
            assert "roles" in data
            assert "mfa_activo" in data
            assert "ultimo_acceso" in data
        finally:
            api.delete(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))

    def test_obtener_usuario_inexistente(self, api, admin_token):
        fake_id = str(uuid.uuid4())
        resp = api.get(
            f"{API_PREFIX}/usuarios/{fake_id}",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 404, resp.text

    def test_obtener_usuario_uuid_invalido(self, api, admin_token):
        resp = api.get(
            f"{API_PREFIX}/usuarios/no-es-uuid",
            headers=auth_header(admin_token),
        )
        assert resp.status_code in (400, 422, 500), resp.text

    def test_actualizar_usuario_campos_basicos(self, api, admin_token):
        user_id, _, _ = create_temp_user(api, admin_token)
        try:
            resp = api.put(
                f"{API_PREFIX}/usuarios/{user_id}",
                json={
                    "nombre_completo": "Nombre Actualizado",
                    "email": f"updated_{unique_username()}@example.com",
                    "telefono": "3001234567",
                    "cargo": "Nuevo Cargo",
                },
                headers=auth_header(admin_token),
            )
            assert resp.status_code == 200, resp.text
            assert resp.json()["nombre_completo"] == "Nombre Actualizado"
            assert resp.json()["telefono"] == "3001234567"
            assert resp.json()["cargo"] == "Nuevo Cargo"
        finally:
            api.delete(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))

    def test_actualizar_usuario_estado_activo_inactivo(self, api, admin_token):
        user_id, _, _ = create_temp_user(api, admin_token)
        try:
            resp = api.put(
                f"{API_PREFIX}/usuarios/{user_id}",
                json={"activo": 0},
                headers=auth_header(admin_token),
            )
            assert resp.status_code == 200, resp.text
            assert resp.json()["activo"] == 0

            resp = api.put(
                f"{API_PREFIX}/usuarios/{user_id}",
                json={"activo": 1},
                headers=auth_header(admin_token),
            )
            assert resp.status_code == 200, resp.text
            assert resp.json()["activo"] == 1
        finally:
            api.delete(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))

    def test_actualizar_usuario_must_change_password(self, api, admin_token):
        user_id, _, _ = create_temp_user(api, admin_token)
        try:
            resp = api.put(
                f"{API_PREFIX}/usuarios/{user_id}",
                json={"must_change_password": False},
                headers=auth_header(admin_token),
            )
            assert resp.status_code == 200, resp.text
            assert resp.json()["must_change_password"] is False

            resp = api.put(
                f"{API_PREFIX}/usuarios/{user_id}",
                json={"must_change_password": True},
                headers=auth_header(admin_token),
            )
            assert resp.status_code == 200, resp.text
            assert resp.json()["must_change_password"] is True
        finally:
            api.delete(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))

    def test_actualizar_usuario_rol(self, api, admin_token):
        user_id, _, _ = create_temp_user(api, admin_token)
        try:
            roles = api.get(
                f"{API_PREFIX}/catalogos/roles", headers=auth_header(admin_token)
            ).json()
            rol_id = next((r["id"] for r in roles if r["codigo"] == "GESTOR"), None)
            if not rol_id:
                pytest.skip("Rol GESTOR no existe")

            resp = api.put(
                f"{API_PREFIX}/usuarios/{user_id}",
                json={"rol_id": rol_id},
                headers=auth_header(admin_token),
            )
            assert resp.status_code == 200, resp.text
            roles_resp = [r["codigo"] for r in resp.json()["roles"]]
            assert "GESTOR" in roles_resp
        finally:
            api.delete(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))

    def test_actualizar_usuario_inexistente(self, api, admin_token):
        fake_id = str(uuid.uuid4())
        resp = api.put(
            f"{API_PREFIX}/usuarios/{fake_id}",
            json={"nombre_completo": "Nuevo"},
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 404, resp.text

    def test_eliminar_usuario(self, api, admin_token):
        user_id, _, _ = create_temp_user(api, admin_token)
        resp = api.delete(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))
        assert resp.status_code == 204, resp.text

        verify = api.get(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))
        assert verify.status_code == 404

    def test_eliminar_usuario_inexistente(self, api, admin_token):
        fake_id = str(uuid.uuid4())
        resp = api.delete(f"{API_PREFIX}/usuarios/{fake_id}", headers=auth_header(admin_token))
        assert resp.status_code == 404, resp.text

    def test_denegado_gestor_crear_usuario(self, api, gestor_token):
        resp = api.post(
            f"{API_PREFIX}/usuarios",
            json={
                "codigo": uuid.uuid4().hex[:10].upper(),
                "username": unique_username("gestor"),
                "email": "gestor@test.com",
                "nombre_completo": "Creado por Gestor",
                "password": "TestPassword2026!!",
            },
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 403, resp.text
        assert "security.usuarios.crear" in resp.json()["detail"]

    def test_denegado_gestor_listar_usuarios(self, api, gestor_token):
        resp = api.get(f"{API_PREFIX}/usuarios", headers=auth_header(gestor_token))
        assert resp.status_code == 403, resp.text
        assert "security.usuarios.ver" in resp.json()["detail"]

    def test_denegado_gestor_actualizar_usuario(self, api, gestor_token):
        resp = api.put(
            f"{API_PREFIX}/usuarios/{uuid.uuid4()}",
            json={"nombre_completo": "Hack"},
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 403, resp.text
        assert "security.usuarios.editar" in resp.json()["detail"]

    def test_denegado_gestor_eliminar_usuario(self, api, gestor_token):
        resp = api.delete(
            f"{API_PREFIX}/usuarios/{uuid.uuid4()}", headers=auth_header(gestor_token)
        )
        assert resp.status_code == 403, resp.text
        assert "security.usuarios.eliminar" in resp.json()["detail"]


class TestAuthFlujos:
    """Flujos de autenticación no cubiertos por test_mfa.py."""

    def _admin_login(self, api):
        resp = api.post(
            f"{API_PREFIX}/auth/login",
            json={
                "username": "admin",
                "password": "SigemAdmin2026!",
                "municipio_codigo": "00000",
            },
        )
        assert resp.status_code == 200, resp.text
        return resp.json()["access_token"]

    def test_login_exitoso_admin(self, api):
        resp = api.post(
            f"{API_PREFIX}/auth/login",
            json={
                "username": "admin",
                "password": "SigemAdmin2026!",
                "municipio_codigo": "00000",
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["mfa_required"] is False

    def test_login_usuario_inexistente(self, api):
        resp = api.post(
            f"{API_PREFIX}/auth/login",
            json={
                "username": "usuario_que_no_existe_xyz",
                "password": "cualquiercosa",
                "municipio_codigo": "00000",
            },
        )
        assert resp.status_code == 401, resp.text
        assert resp.json()["detail"] == "Credenciales inválidas"

    def test_login_credenciales_invalidas(self, api):
        resp = api.post(
            f"{API_PREFIX}/auth/login",
            json={
                "username": "admin",
                "password": "ContraseñaIncorrecta123!",
                "municipio_codigo": "00000",
            },
        )
        assert resp.status_code == 401, resp.text
        assert resp.json()["detail"] == "Credenciales inválidas"

    def test_login_municipio_inexistente(self, api):
        resp = api.post(
            f"{API_PREFIX}/auth/login",
            json={
                "username": "admin",
                "password": "SigemAdmin2026!",
                "municipio_codigo": "99999",
            },
        )
        assert resp.status_code in (401, 200), resp.text
        if resp.status_code == 200:
            assert "access_token" in resp.json()

    def test_refresh_token_valido(self, api):
        login = api.post(
            f"{API_PREFIX}/auth/login",
            json={
                "username": "admin",
                "password": "SigemAdmin2026!",
                "municipio_codigo": "00000",
            },
        )
        refresh_token = login.json()["refresh_token"]

        resp = api.post(
            f"{API_PREFIX}/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["mfa_required"] is False

    def test_refresh_token_invalido(self, api):
        resp = api.post(
            f"{API_PREFIX}/auth/refresh",
            json={"refresh_token": "token-invalido-xyz"},
        )
        assert resp.status_code == 401, resp.text
        assert resp.json()["detail"] == "Refresh token inválido o expirado."

    def test_refresh_token_expirado_o_revocado(self, api):
        login = api.post(
            f"{API_PREFIX}/auth/login",
            json={
                "username": "admin",
                "password": "SigemAdmin2026!",
                "municipio_codigo": "00000",
            },
        )
        refresh_token = login.json()["refresh_token"]
        access_token = login.json()["access_token"]

        api.post(f"{API_PREFIX}/auth/logout", headers=auth_header(access_token))

        resp = api.post(
            f"{API_PREFIX}/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 401, resp.text

    def test_logout(self, api):
        login = api.post(
            f"{API_PREFIX}/auth/login",
            json={
                "username": "admin",
                "password": "SigemAdmin2026!",
                "municipio_codigo": "00000",
            },
        )
        access_token = login.json()["access_token"]

        resp = api.post(f"{API_PREFIX}/auth/logout", headers=auth_header(access_token))
        assert resp.status_code == 200, resp.text
        assert resp.json()["message"] == "Sesión cerrada exitosamente"

    def test_logout_invalida_access_token(self, api):
        login = api.post(
            f"{API_PREFIX}/auth/login",
            json={
                "username": "admin",
                "password": "SigemAdmin2026!",
                "municipio_codigo": "00000",
            },
        )
        access_token = login.json()["access_token"]

        api.post(f"{API_PREFIX}/auth/logout", headers=auth_header(access_token))
        resp = api.get(f"{API_PREFIX}/auth/me", headers=auth_header(access_token))
        assert resp.status_code == 401, resp.text

    def test_get_me(self, api):
        login = api.post(
            f"{API_PREFIX}/auth/login",
            json={
                "username": "admin",
                "password": "SigemAdmin2026!",
                "municipio_codigo": "00000",
            },
        )
        access_token = login.json()["access_token"]

        resp = api.get(f"{API_PREFIX}/auth/me", headers=auth_header(access_token))
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "id" in data
        assert "username" in data
        assert "email" in data
        assert "nombre_completo" in data
        assert "municipio_id" in data
        assert "must_change_password" in data
        assert "mfa_activo" in data
        assert "roles" in data

    def test_get_me_sin_token(self, api):
        resp = api.get(f"{API_PREFIX}/auth/me")
        assert resp.status_code == 401

    def test_change_password_flujo_completo(self, api):
        admin_token = self._admin_login(api)
        user_id, username, password = create_temp_user(api, admin_token)
        try:
            login = login_as(api, username, password)
            assert login.status_code == 200, login.text
            token = login.json()["access_token"]
            assert login.json()["must_change_password"] is True

            new_password = "NuevaPassword2026!!"
            cp = api.post(
                f"{API_PREFIX}/auth/change-password",
                json={
                    "current_password": password,
                    "new_password": new_password,
                    "confirm_password": new_password,
                },
                headers=auth_header(token),
            )
            assert cp.status_code == 200, cp.text

            login2 = login_as(api, username, new_password)
            assert login2.status_code == 200, login2.text
            assert login2.json()["must_change_password"] is False
        finally:
            api.delete(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))

    def test_change_password_actual_incorrecta(self, api):
        admin_token = self._admin_login(api)
        user_id, username, password = create_temp_user(api, admin_token)
        try:
            login = login_as(api, username, password)
            token = login.json()["access_token"]

            cp = api.post(
                f"{API_PREFIX}/auth/change-password",
                json={
                    "current_password": "Incorrecta123!",
                    "new_password": "NuevaPassword2026!!",
                    "confirm_password": "NuevaPassword2026!!",
                },
                headers=auth_header(token),
            )
            assert cp.status_code == 400, cp.text
            assert "incorrecta" in cp.json()["detail"].lower()
        finally:
            api.delete(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))

    def test_change_password_no_coinciden(self, api):
        admin_token = self._admin_login(api)
        user_id, username, password = create_temp_user(api, admin_token)
        try:
            login = login_as(api, username, password)
            token = login.json()["access_token"]

            cp = api.post(
                f"{API_PREFIX}/auth/change-password",
                json={
                    "current_password": password,
                    "new_password": "NuevaPassword2026!!",
                    "confirm_password": "OtraPassword2026!!",
                },
                headers=auth_header(token),
            )
            assert cp.status_code == 400, cp.text
            assert "coinciden" in cp.json()["detail"].lower()
        finally:
            api.delete(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))

    def test_mfa_status_sin_setup(self, api):
        admin_token = self._admin_login(api)
        user_id, username, password = create_temp_user(api, admin_token)
        try:
            login = login_as(api, username, password)
            token = login.json()["access_token"]
            new_password = "TempMfaPassword2026!!"
            api.post(
                f"{API_PREFIX}/auth/change-password",
                json={
                    "current_password": password,
                    "new_password": new_password,
                    "confirm_password": new_password,
                },
                headers=auth_header(token),
            )
            login2 = login_as(api, username, new_password)
            token = login2.json()["access_token"]

            resp = api.get(f"{API_PREFIX}/auth/mfa/status", headers=auth_header(token))
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["mfa_activo"] is False
            assert data["pending"] is False
            assert data["secret"] is None
            assert data["qr_code_url"] is None
        finally:
            api.delete(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))

    def test_mfa_setup_verify_disable_flujo(self, api):
        import pyotp

        admin_token = self._admin_login(api)
        user_id, username, password = create_temp_user(api, admin_token)
        try:
            login = login_as(api, username, password)
            token = login.json()["access_token"]
            new_password = "TempMfaPassword2026!!"
            api.post(
                f"{API_PREFIX}/auth/change-password",
                json={
                    "current_password": password,
                    "new_password": new_password,
                    "confirm_password": new_password,
                },
                headers=auth_header(token),
            )
            login2 = login_as(api, username, new_password)
            token = login2.json()["access_token"]

            setup = api.post(f"{API_PREFIX}/auth/mfa/setup", headers=auth_header(token))
            assert setup.status_code == 200, setup.text
            secret = setup.json()["secret"]
            assert "otpauth" in setup.json()["qr_code_url"]

            bad = api.post(
                f"{API_PREFIX}/auth/mfa/verify",
                json={"code": "000000"},
                headers=auth_header(token),
            )
            assert bad.status_code == 401

            code = pyotp.TOTP(secret).now()
            ok = api.post(
                f"{API_PREFIX}/auth/mfa/verify",
                json={"code": code},
                headers=auth_header(token),
            )
            assert ok.status_code == 200, ok.text
            assert ok.json()["mfa_activo"] is True

            status = api.get(f"{API_PREFIX}/auth/mfa/status", headers=auth_header(token))
            assert status.status_code == 200
            assert status.json()["mfa_activo"] is True

            dis = api.post(
                f"{API_PREFIX}/auth/mfa/disable",
                json={
                    "password": new_password,
                    "code": pyotp.TOTP(secret).now(),
                },
                headers=auth_header(token),
            )
            assert dis.status_code == 200, dis.text
            assert dis.json()["mfa_activo"] is False
        finally:
            api.delete(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))

    def test_mfa_disable_password_incorrecta(self, api):
        import pyotp

        admin_token = self._admin_login(api)
        user_id, username, password = create_temp_user(api, admin_token)
        try:
            login = login_as(api, username, password)
            token = login.json()["access_token"]
            new_password = "TempMfaPassword2026!!"
            api.post(
                f"{API_PREFIX}/auth/change-password",
                json={
                    "current_password": password,
                    "new_password": new_password,
                    "confirm_password": new_password,
                },
                headers=auth_header(token),
            )
            login2 = login_as(api, username, new_password)
            token = login2.json()["access_token"]

            setup = api.post(f"{API_PREFIX}/auth/mfa/setup", headers=auth_header(token))
            secret = setup.json()["secret"]
            code = pyotp.TOTP(secret).now()
            api.post(
                f"{API_PREFIX}/auth/mfa/verify",
                json={"code": code},
                headers=auth_header(token),
            )

            dis_bad = api.post(
                f"{API_PREFIX}/auth/mfa/disable",
                json={
                    "password": "wrong_password",
                    "code": pyotp.TOTP(secret).now(),
                },
                headers=auth_header(token),
            )
            assert dis_bad.status_code == 401
        finally:
            api.delete(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))

    def test_mfa_disable_codigo_incorrecto(self, api):
        import pyotp

        admin_token = self._admin_login(api)
        user_id, username, password = create_temp_user(api, admin_token)
        try:
            login = login_as(api, username, password)
            token = login.json()["access_token"]
            new_password = "TempMfaPassword2026!!"
            api.post(
                f"{API_PREFIX}/auth/change-password",
                json={
                    "current_password": password,
                    "new_password": new_password,
                    "confirm_password": new_password,
                },
                headers=auth_header(token),
            )
            login2 = login_as(api, username, new_password)
            token = login2.json()["access_token"]

            setup = api.post(f"{API_PREFIX}/auth/mfa/setup", headers=auth_header(token))
            secret = setup.json()["secret"]
            code = pyotp.TOTP(secret).now()
            api.post(
                f"{API_PREFIX}/auth/mfa/verify",
                json={"code": code},
                headers=auth_header(token),
            )

            dis_bad = api.post(
                f"{API_PREFIX}/auth/mfa/disable",
                json={
                    "password": new_password,
                    "code": "000000",
                },
                headers=auth_header(token),
            )
            assert dis_bad.status_code == 401
        finally:
            api.delete(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))

    def test_mfa_login_segundo_factor(self, api):
        import pyotp

        admin_token = self._admin_login(api)
        user_id, username, password = create_temp_user(api, admin_token)
        try:
            login = login_as(api, username, password)
            token = login.json()["access_token"]
            new_password = "TempMfaPassword2026!!"
            api.post(
                f"{API_PREFIX}/auth/change-password",
                json={
                    "current_password": password,
                    "new_password": new_password,
                    "confirm_password": new_password,
                },
                headers=auth_header(token),
            )
            login2 = login_as(api, username, new_password)
            token = login2.json()["access_token"]

            setup = api.post(f"{API_PREFIX}/auth/mfa/setup", headers=auth_header(token))
            secret = setup.json()["secret"]
            code = pyotp.TOTP(secret).now()
            api.post(
                f"{API_PREFIX}/auth/mfa/verify",
                json={"code": code},
                headers=auth_header(token),
            )

            login3 = login_as(api, username, new_password)
            assert login3.status_code == 200
            assert login3.json()["mfa_required"] is True
            mfa_token = login3.json()["mfa_token"]

            not_access = api.get(f"{API_PREFIX}/auth/me", headers=auth_header(mfa_token))
            assert not_access.status_code == 401

            wrong = api.post(
                f"{API_PREFIX}/auth/mfa/login",
                json={"mfa_token": mfa_token, "code": "000000"},
            )
            assert wrong.status_code == 401

            good = api.post(
                f"{API_PREFIX}/auth/mfa/login",
                json={"mfa_token": mfa_token, "code": pyotp.TOTP(secret).now()},
            )
            assert good.status_code == 200, good.text
            assert "access_token" in good.json()
        finally:
            api.delete(f"{API_PREFIX}/usuarios/{user_id}", headers=auth_header(admin_token))

    def test_denegado_rutas_protegidas_sin_token(self, api):
        endpoints = [
            ("GET", "/usuarios"),
            ("GET", "/auditoria"),
            ("GET", "/cumplimiento/general"),
            ("GET", "/reportes/resumen-general"),
        ]
        for method, ep in endpoints:
            func = getattr(api, method.lower())
            resp = func(f"{API_PREFIX}{ep}")
            assert resp.status_code == 401, f"{method} {ep} debería requerir auth"

    def test_denegado_token_malformado(self, api):
        resp = api.get(
            f"{API_PREFIX}/auth/me",
            headers={"Authorization": "Bearer token_malformado"},
        )
        assert resp.status_code in (401, 429)

    def test_login_sin_municipio_codigo(self, api):
        resp = api.post(
            f"{API_PREFIX}/auth/login",
            json={"username": "admin", "password": "SigemAdmin2026!"},
        )
        assert resp.status_code in (200, 401), resp.text
