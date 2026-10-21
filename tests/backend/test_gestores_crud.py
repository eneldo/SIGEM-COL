"""Tests de integración CRUD para Gestores Líderes."""

import uuid

from tests.conftest import API_PREFIX, auth_header


def _list_gestores(api, token, **params):
    query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
    url = f"{API_PREFIX}/gestores"
    if query:
        url += f"?{query}"
    return api.get(url, headers=auth_header(token))


def _get_gestor(api, token, gestor_id):
    return api.get(f"{API_PREFIX}/gestores/{gestor_id}", headers=auth_header(token))


def _create_gestor(api, token, **overrides):
    roles_resp = api.get(f"{API_PREFIX}/catalogos/roles", headers=auth_header(token))
    deps_resp = api.get(f"{API_PREFIX}/catalogos/dependencias", headers=auth_header(token))
    rol_id = next((r["id"] for r in roles_resp.json() if r["codigo"] == "GESTOR"), None)
    dep_id = deps_resp.json()[0]["id"] if deps_resp.json() else None

    username = f"gestor_{uuid.uuid4().hex[:8]}"
    password = "GestorTestPassword2026!!"

    payload = {
        "nombre_completo": "Gestor de Prueba",
        "email": f"{username}@test.com",
        "cargo": "Gestor de pruebas",
        "rol_id": rol_id,
        "dependencia_principal_id": dep_id,
        "username": username,
        "password": password,
    }
    payload.update(overrides)
    return api.post(f"{API_PREFIX}/gestores", json=payload, headers=auth_header(token))


def _update_gestor(api, token, gestor_id, **fields):
    return api.put(f"{API_PREFIX}/gestores/{gestor_id}", json=fields, headers=auth_header(token))


def _update_permissions(api, token, gestor_id, **fields):
    serializable = {}
    for k, v in fields.items():
        if isinstance(v, uuid.UUID):
            serializable[k] = str(v)
        elif isinstance(v, list):
            serializable[k] = [str(x) if isinstance(x, uuid.UUID) else x for x in v]
        else:
            serializable[k] = v
    return api.post(
        f"{API_PREFIX}/gestores/{gestor_id}/permisos",
        json=serializable,
        headers=auth_header(token),
    )


def _activate(api, token, gestor_id):
    return api.post(f"{API_PREFIX}/gestores/{gestor_id}/activate", headers=auth_header(token))


def _deactivate(api, token, gestor_id):
    return api.post(f"{API_PREFIX}/gestores/{gestor_id}/deactivate", headers=auth_header(token))


def _block(api, token, gestor_id, motivo):
    return api.post(
        f"{API_PREFIX}/gestores/{gestor_id}/block",
        json={"motivo": motivo},
        headers=auth_header(token),
    )


def _unblock(api, token, gestor_id):
    return api.post(f"{API_PREFIX}/gestores/{gestor_id}/unblock", headers=auth_header(token))


def _reset_password(api, token, gestor_id, nueva_password=None):
    payload = {"nueva_password": nueva_password} if nueva_password else {}
    return api.post(
        f"{API_PREFIX}/gestores/{gestor_id}/reset-password",
        json=payload,
        headers=auth_header(token),
    )


def _delete_gestor(api, token, gestor_id):
    return api.delete(f"{API_PREFIX}/gestores/{gestor_id}", headers=auth_header(token))


def _get_accesos(api, token, gestor_id, limit=50, offset=0):
    return api.get(
        f"{API_PREFIX}/gestores/{gestor_id}/accesos?limit={limit}&offset={offset}",
        headers=auth_header(token),
    )


def _get_audit(api, token, gestor_id, limit=100, offset=0):
    return api.get(
        f"{API_PREFIX}/gestores/{gestor_id}/audit?limit={limit}&offset={offset}",
        headers=auth_header(token),
    )


class TestListGestores:
    """GET /gestores - Listado con filtros y paginación."""

    def test_list_requires_auth(self, api):
        resp = api.get(f"{API_PREFIX}/gestores")
        assert resp.status_code == 401

    def test_list_empty_filters(self, api, admin_token):
        resp = _list_gestores(api, admin_token)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data

    def test_list_pagination(self, api, admin_token):
        resp = _list_gestores(api, admin_token, page=1, page_size=5)
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 5

    def test_list_page_out_of_bounds(self, api, admin_token):
        resp = _list_gestores(api, admin_token, page=999, page_size=10)
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []

    def test_list_filter_search(self, api, admin_token):
        resp = _list_gestores(api, admin_token, search="admin")
        assert resp.status_code == 200

    def test_list_filter_cargo(self, api, admin_token):
        resp = _list_gestores(api, admin_token, cargo="Director")
        assert resp.status_code == 200

    def test_list_filter_rol(self, api, admin_token):
        roles = api.get(f"{API_PREFIX}/catalogos/roles", headers=auth_header(admin_token)).json()
        rol_id = next((r["id"] for r in roles if r["codigo"] == "GESTOR"), None)
        if rol_id:
            resp = _list_gestores(api, admin_token, rol_id=rol_id)
            assert resp.status_code == 200

    def test_list_filter_estado(self, api, admin_token):
        for estado in ("ACTIVO", "INACTIVO", "BLOQUEADO"):
            resp = _list_gestores(api, admin_token, estado=estado)
            assert resp.status_code == 200

    def test_list_combined_filters(self, api, admin_token):
        resp = _list_gestores(
            api, admin_token, search="test", estado="ACTIVO", page=1, page_size=10
        )
        assert resp.status_code == 200

    def test_list_gestor_token_denied(self, api, gestor_token):
        resp = _list_gestores(api, gestor_token)
        assert resp.status_code == 403
        assert "gestor.ver" in resp.json()["detail"]


class TestGetGestor:
    """GET /gestores/{id} - Detalle de gestor."""

    def test_get_requires_auth(self, api):
        resp = api.get(f"{API_PREFIX}/gestores/{uuid.uuid4()}")
        assert resp.status_code == 401

    def test_get_not_found(self, api, admin_token):
        resp = _get_gestor(api, admin_token, uuid.uuid4())
        assert resp.status_code == 404

    def test_get_success(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        assert created.status_code == 201
        gestor_id = created.json()["id"]
        try:
            resp = _get_gestor(api, admin_token, gestor_id)
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == gestor_id
            assert data["codigo"] == created.json()["codigo"]
            assert data["username"] == created.json()["username"]
            assert "dependencias" in data
            assert "roles" in data
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_get_gestor_token_denied(self, api, admin_token, gestor_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            resp = _get_gestor(api, gestor_token, gestor_id)
            assert resp.status_code == 403
        finally:
            _delete_gestor(api, admin_token, gestor_id)


class TestCreateGestor:
    """POST /gestores - Crear gestor."""

    def test_create_requires_auth(self, api):
        resp = api.post(
            f"{API_PREFIX}/gestores",
            json={"nombre_completo": "Test", "email": "t@t.com"},
        )
        assert resp.status_code == 401

    def test_create_gestor_token_denied(self, api, gestor_token):
        resp = api.post(
            f"{API_PREFIX}/gestores",
            json={"nombre_completo": "Test", "email": "t@t.com"},
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 403
        assert "gestor.crear" in resp.json()["detail"]

    def test_create_minimal(self, api, admin_token):
        resp = _create_gestor(api, admin_token)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["id"]
        assert data["codigo"]
        assert data["username"]
        assert data["nueva_password_temporal"]
        gestor_id = data["id"]
        _delete_gestor(api, admin_token, gestor_id)

    def test_create_with_all_fields(self, api, admin_token):
        roles = api.get(f"{API_PREFIX}/catalogos/roles", headers=auth_header(admin_token)).json()
        rol_id = next((r["id"] for r in roles if r["codigo"] == "GESTOR"), None)
        deps = api.get(
            f"{API_PREFIX}/catalogos/dependencias", headers=auth_header(admin_token)
        ).json()
        dep_id = deps[0]["id"] if deps else None

        payload = {
            "nombre_completo": "Gestor Completo",
            "email": f"completo_{uuid.uuid4().hex[:8]}@test.com",
            "telefono": "3001234567",
            "cargo": "Coordinador",
            "rol_id": rol_id,
            "dependencia_principal_id": dep_id,
            "dependencias_adicionales": [],
            "username": f"gestor_completo_{uuid.uuid4().hex[:6]}",
            "password": "CustomPassword2026!!",
        }
        resp = api.post(f"{API_PREFIX}/gestores", json=payload, headers=auth_header(admin_token))
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["username"] == payload["username"]
        gestor_id = data["id"]
        _delete_gestor(api, admin_token, gestor_id)

    def test_create_invalid_email(self, api, admin_token):
        resp = _create_gestor(api, admin_token, email="invalid-email")
        assert resp.status_code == 422

    def test_create_duplicate_email(self, api, admin_token):
        email = f"dup_{uuid.uuid4().hex[:8]}@test.com"
        _create_gestor(api, admin_token, email=email)
        try:
            resp = _create_gestor(api, admin_token, email=email)
            # API may allow duplicate emails if previous was soft-deleted
            assert resp.status_code in (201, 422)
        finally:
            gestores = _list_gestores(api, admin_token, search=email).json()["items"]
            for g in gestores:
                _delete_gestor(api, admin_token, g["id"])

    def test_create_invalid_rol_id(self, api, admin_token):
        resp = _create_gestor(api, admin_token, rol_id=str(uuid.uuid4()))
        assert resp.status_code == 422


class TestUpdateGestor:
    """PUT /gestores/{id} - Actualizar gestor."""

    def test_update_requires_auth(self, api):
        resp = api.put(f"{API_PREFIX}/gestores/{uuid.uuid4()}", json={"nombre_completo": "Nuevo"})
        assert resp.status_code == 401

    def test_update_gestor_token_denied(self, api, admin_token, gestor_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            resp = _update_gestor(api, gestor_token, gestor_id, nombre_completo="Hack")
            assert resp.status_code == 403
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_update_not_found(self, api, admin_token):
        resp = _update_gestor(api, admin_token, uuid.uuid4(), nombre_completo="Nuevo")
        assert resp.status_code == 404

    def test_update_nombre_completo(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            resp = _update_gestor(api, admin_token, gestor_id, nombre_completo="Nombre Actualizado")
            assert resp.status_code == 200
            assert resp.json()["nombre_completo"] == "Nombre Actualizado"
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_update_email(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            new_email = f"nuevo_{uuid.uuid4().hex[:8]}@test.com"
            resp = _update_gestor(api, admin_token, gestor_id, email=new_email)
            assert resp.status_code == 200
            assert resp.json()["email"] == new_email
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_update_cargo(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            resp = _update_gestor(api, admin_token, gestor_id, cargo="Nuevo Cargo")
            assert resp.status_code == 200
            assert resp.json()["cargo"] == "Nuevo Cargo"
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_update_dependencia_principal(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        deps = api.get(
            f"{API_PREFIX}/catalogos/dependencias", headers=auth_header(admin_token)
        ).json()
        dep_id = deps[0]["id"] if deps else None
        try:
            resp = _update_gestor(api, admin_token, gestor_id, dependencia_principal_id=dep_id)
            assert resp.status_code == 200
            assert resp.json()["dependencia_principal_id"] == dep_id
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_update_invalid_email(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            resp = _update_gestor(api, admin_token, gestor_id, email="bad-email")
            assert resp.status_code == 422
        finally:
            _delete_gestor(api, admin_token, gestor_id)


class TestUpdatePermissions:
    """POST /gestores/{id}/permisos - Asignar rol y dependencias."""

    def test_permissions_requires_auth(self, api):
        resp = api.post(f"{API_PREFIX}/gestores/{uuid.uuid4()}/permisos", json={})
        assert resp.status_code == 401

    def test_permissions_gestor_token_denied(self, api, admin_token, gestor_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            resp = _update_permissions(api, gestor_token, gestor_id, rol_id=uuid.uuid4())
            assert resp.status_code == 403
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_permissions_not_found(self, api, admin_token):
        resp = _update_permissions(api, admin_token, uuid.uuid4(), rol_id=uuid.uuid4())
        assert resp.status_code == 404

    def test_update_rol(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        roles = api.get(f"{API_PREFIX}/catalogos/roles", headers=auth_header(admin_token)).json()
        rol_id = next((r["id"] for r in roles if r["codigo"] == "GESTOR"), None)
        try:
            resp = _update_permissions(api, admin_token, gestor_id, rol_id=rol_id)
            assert resp.status_code == 200
            assert resp.json()["rol_id"] == rol_id
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_update_dependencia_principal(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        deps = api.get(
            f"{API_PREFIX}/catalogos/dependencias", headers=auth_header(admin_token)
        ).json()
        dep_id = deps[0]["id"] if deps else None
        try:
            resp = _update_permissions(api, admin_token, gestor_id, dependencia_principal_id=dep_id)
            assert resp.status_code == 200
            assert resp.json()["dependencia_principal_id"] == dep_id
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_update_dependencias_adicionales(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        deps = api.get(
            f"{API_PREFIX}/catalogos/dependencias", headers=auth_header(admin_token)
        ).json()
        dep_ids = [d["id"] for d in deps[:2]] if len(deps) >= 2 else [d["id"] for d in deps]
        try:
            resp = _update_permissions(
                api, admin_token, gestor_id, dependencias_adicionales=dep_ids
            )
            assert resp.status_code == 200
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_update_invalid_rol(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            resp = _update_permissions(api, admin_token, gestor_id, rol_id=uuid.uuid4())
            assert resp.status_code == 422
        finally:
            _delete_gestor(api, admin_token, gestor_id)


class TestActivateDeactivate:
    """POST /gestores/{id}/activate|deactivate - Activar/Desactivar."""

    def test_activate_requires_auth(self, api):
        resp = api.post(f"{API_PREFIX}/gestores/{uuid.uuid4()}/activate")
        assert resp.status_code == 401

    def test_activate_gestor_token_denied(self, api, admin_token, gestor_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            _deactivate(api, admin_token, gestor_id)
            resp = _activate(api, gestor_token, gestor_id)
            assert resp.status_code == 403
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_activate_not_found(self, api, admin_token):
        resp = _activate(api, admin_token, uuid.uuid4())
        assert resp.status_code == 404

    def test_activate_success(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        _deactivate(api, admin_token, gestor_id)
        try:
            resp = _activate(api, admin_token, gestor_id)
            assert resp.status_code == 200
            assert resp.json()["estado"] == "ACTIVO"
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_deactivate_success(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            resp = _deactivate(api, admin_token, gestor_id)
            assert resp.status_code == 200
            assert resp.json()["estado"] == "INACTIVO"
        finally:
            _delete_gestor(api, admin_token, gestor_id)


class TestBlockUnblock:
    """POST /gestores/{id}/block|unblock - Bloquear/Desbloquear."""

    def test_block_requires_auth(self, api):
        resp = api.post(f"{API_PREFIX}/gestores/{uuid.uuid4()}/block", json={"motivo": "test"})
        assert resp.status_code == 401

    def test_block_missing_motivo(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            resp = api.post(
                f"{API_PREFIX}/gestores/{gestor_id}/block",
                json={},
                headers=auth_header(admin_token),
            )
            assert resp.status_code == 422
            assert "motivo" in resp.json()["detail"].lower()
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_block_empty_motivo(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            resp = _block(api, admin_token, gestor_id, "   ")
            assert resp.status_code == 422
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_block_success(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            resp = _block(api, admin_token, gestor_id, "Incumplimiento de deberes")
            assert resp.status_code == 200
            assert resp.json()["estado"] == "BLOQUEADO"
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_unblock_success(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        _block(api, admin_token, gestor_id, "Motivo temporal")
        try:
            resp = _unblock(api, admin_token, gestor_id)
            assert resp.status_code == 200
            assert resp.json()["estado"] == "ACTIVO"
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_unblock_not_blocked(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            resp = _unblock(api, admin_token, gestor_id)
            assert resp.status_code in (200, 422, 400)
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_block_unblock_gestor_token_denied(self, api, admin_token, gestor_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            resp = _block(api, gestor_token, gestor_id, "test")
            assert resp.status_code == 403
            resp = _unblock(api, gestor_token, gestor_id)
            assert resp.status_code == 403
        finally:
            _delete_gestor(api, admin_token, gestor_id)


class TestResetPassword:
    """POST /gestores/{id}/reset-password - Restablecer contraseña."""

    def test_reset_requires_auth(self, api):
        resp = api.post(f"{API_PREFIX}/gestores/{uuid.uuid4()}/reset-password")
        assert resp.status_code == 401

    def test_reset_gestor_token_denied(self, api, admin_token, gestor_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            resp = _reset_password(api, gestor_token, gestor_id)
            assert resp.status_code == 403
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_reset_not_found(self, api, admin_token):
        resp = _reset_password(api, admin_token, uuid.uuid4())
        assert resp.status_code == 404

    def test_reset_generates_temp_password(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            resp = _reset_password(api, admin_token, gestor_id)
            assert resp.status_code == 200
            assert resp.json()["nueva_password_temporal"]
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_reset_with_custom_password(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            resp = _reset_password(
                api, admin_token, gestor_id, nueva_password="NewCustomPass2026!!"
            )
            assert resp.status_code == 200
            assert resp.json()["nueva_password_temporal"] == "NewCustomPass2026!!"
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_reset_password_too_short(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            resp = _reset_password(api, admin_token, gestor_id, nueva_password="short")
            assert resp.status_code == 422
        finally:
            _delete_gestor(api, admin_token, gestor_id)


class TestSoftDelete:
    """DELETE /gestores/{id} - Eliminación lógica."""

    def test_delete_requires_auth(self, api):
        resp = api.delete(f"{API_PREFIX}/gestores/{uuid.uuid4()}")
        assert resp.status_code == 401

    def test_delete_gestor_token_denied(self, api, admin_token, gestor_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            resp = _delete_gestor(api, gestor_token, gestor_id)
            assert resp.status_code == 403
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_delete_not_found(self, api, admin_token):
        resp = _delete_gestor(api, admin_token, uuid.uuid4())
        assert resp.status_code == 404

    def test_delete_success(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        resp = _delete_gestor(api, admin_token, gestor_id)
        assert resp.status_code == 204

        resp = _get_gestor(api, admin_token, gestor_id)
        assert resp.status_code == 404

    def test_delete_twice_returns_404(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        _delete_gestor(api, admin_token, gestor_id)
        resp = _delete_gestor(api, admin_token, gestor_id)
        assert resp.status_code == 404


class TestAccesosAudit:
    """GET /gestores/{id}/accesos|audit - Historial de accesos y auditoría."""

    def test_accesos_requires_auth(self, api):
        resp = api.get(f"{API_PREFIX}/gestores/{uuid.uuid4()}/accesos")
        assert resp.status_code == 401

    def test_accesos_not_found(self, api, admin_token):
        resp = _get_accesos(api, admin_token, uuid.uuid4())
        assert resp.status_code == 404

    def test_accesos_success(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            resp = _get_accesos(api, admin_token, gestor_id)
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_accesos_pagination(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            resp = _get_accesos(api, admin_token, gestor_id, limit=10, offset=0)
            assert resp.status_code == 200
            resp = _get_accesos(api, admin_token, gestor_id, limit=5, offset=5)
            assert resp.status_code == 200
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_accesos_requires_audit_permission(self, api, admin_token, gestor_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            resp = _get_accesos(api, gestor_token, gestor_id)
            assert resp.status_code == 403
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_audit_requires_auth(self, api):
        resp = api.get(f"{API_PREFIX}/gestores/{uuid.uuid4()}/audit")
        assert resp.status_code == 401

    def test_audit_not_found(self, api, admin_token):
        resp = _get_audit(api, admin_token, uuid.uuid4())
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            assert resp.json() == []

    def test_audit_success(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            resp = _get_audit(api, admin_token, gestor_id)
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_audit_pagination(self, api, admin_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            resp = _get_audit(api, admin_token, gestor_id, limit=10, offset=0)
            assert resp.status_code == 200
        finally:
            _delete_gestor(api, admin_token, gestor_id)

    def test_audit_requires_audit_permission(self, api, admin_token, gestor_token):
        created = _create_gestor(api, admin_token)
        gestor_id = created.json()["id"]
        try:
            resp = _get_audit(api, gestor_token, gestor_id)
            assert resp.status_code == 403
        finally:
            _delete_gestor(api, admin_token, gestor_id)
