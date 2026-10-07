"""Tests de integración CRUD para roles y permisos."""

import uuid

from tests.conftest import API_PREFIX, auth_header


def _get_permiso_ids(api, admin_token, limit=3):
    resp = api.get(f"{API_PREFIX}/roles/permisos", headers=auth_header(admin_token))
    if resp.status_code != 200:
        return []
    items = resp.json().get("items", [])
    return [p["id"] for p in items[:limit]]


class TestRolesCRUD:
    def test_crear_rol_happy_path(self, api, admin_token):
        permiso_ids = _get_permiso_ids(api, admin_token)
        payload = {
            "codigo": f"ROL_TEST_{uuid.uuid4().hex[:8].upper()}",
            "nombre": "Rol de Prueba Integración",
            "descripcion": "Descripción de prueba",
            "nivel": 5,
            "permisos_ids": permiso_ids,
        }
        resp = api.post(f"{API_PREFIX}/roles", json=payload, headers=auth_header(admin_token))
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["nombre"] == payload["nombre"]
        assert data["codigo"] == payload["codigo"]
        assert data["nivel"] == payload["nivel"]
        assert len(data["permisos"]) == len(permiso_ids)
        rol_id = data["id"]

        try:
            get_resp = api.get(f"{API_PREFIX}/roles/{rol_id}", headers=auth_header(admin_token))
            assert get_resp.status_code == 200, get_resp.text
            assert get_resp.json()["id"] == rol_id
        finally:
            api.delete(f"{API_PREFIX}/roles/{rol_id}", headers=auth_header(admin_token))

    def test_listar_roles_con_filtros(self, api, admin_token):
        resp = api.get(f"{API_PREFIX}/roles?page=1&page_size=10", headers=auth_header(admin_token))
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        for item in data["items"]:
            assert "permisos" in item

    def test_listar_roles_con_busqueda(self, api, admin_token):
        resp = api.get(f"{API_PREFIX}/roles?search=ADMIN", headers=auth_header(admin_token))
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "items" in data
        for item in data["items"]:
            assert "ADMIN" in item["codigo"].upper() or "ADMIN" in item["nombre"].upper()

    def test_obtener_rol_detalle(self, api, admin_token):
        resp = api.get(f"{API_PREFIX}/roles?page_size=1", headers=auth_header(admin_token))
        if resp.status_code != 200 or not resp.json().get("items"):
            return
        rol_id = resp.json()["items"][0]["id"]

        resp = api.get(f"{API_PREFIX}/roles/{rol_id}", headers=auth_header(admin_token))
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["id"] == rol_id
        assert "permisos" in data

    def test_actualizar_rol(self, api, admin_token):
        permiso_ids = _get_permiso_ids(api, admin_token)
        payload = {
            "codigo": f"ROL_UPD_{uuid.uuid4().hex[:8].upper()}",
            "nombre": "Rol para Actualizar",
            "nivel": 3,
            "permisos_ids": permiso_ids[:1] if permiso_ids else [],
        }
        create_resp = api.post(
            f"{API_PREFIX}/roles", json=payload, headers=auth_header(admin_token)
        )
        assert create_resp.status_code == 201, create_resp.text
        rol_id = create_resp.json()["id"]

        try:
            new_permisos = _get_permiso_ids(api, admin_token, limit=2)
            update_payload = {
                "nombre": "Rol Actualizado",
                "descripcion": "Modificado",
                "nivel": 7,
                "estado": "INACTIVO",
                "permisos_ids": new_permisos,
            }
            resp = api.put(
                f"{API_PREFIX}/roles/{rol_id}",
                json=update_payload,
                headers=auth_header(admin_token),
            )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["nombre"] == "Rol Actualizado"
            assert data["descripcion"] == "Modificado"
            assert data["nivel"] == 7
            assert data["estado"] == "INACTIVO"
            assert len(data["permisos"]) == len(new_permisos)
        finally:
            api.delete(f"{API_PREFIX}/roles/{rol_id}", headers=auth_header(admin_token))

    def test_eliminar_rol(self, api, admin_token):
        payload = {
            "codigo": f"ROL_DEL_{uuid.uuid4().hex[:8].upper()}",
            "nombre": "Rol para Eliminar",
            "nivel": 1,
        }
        create_resp = api.post(
            f"{API_PREFIX}/roles", json=payload, headers=auth_header(admin_token)
        )
        assert create_resp.status_code == 201, create_resp.text
        rol_id = create_resp.json()["id"]

        resp = api.delete(f"{API_PREFIX}/roles/{rol_id}", headers=auth_header(admin_token))
        assert resp.status_code == 204, resp.text

        get_resp = api.get(f"{API_PREFIX}/roles/{rol_id}", headers=auth_header(admin_token))
        assert get_resp.status_code == 404

    def test_id_invalido_devuelve_422_o_404(self, api, admin_token):
        resp = api.get(f"{API_PREFIX}/roles/no-es-uuid", headers=auth_header(admin_token))
        assert resp.status_code in (400, 422, 404)

    def test_codigo_duplicado_devuelve_422(self, api, admin_token):
        codigo = f"ROL_DUP_{uuid.uuid4().hex[:8].upper()}"
        payload = {"codigo": codigo, "nombre": "Rol Duplicado", "nivel": 1}
        resp1 = api.post(f"{API_PREFIX}/roles", json=payload, headers=auth_header(admin_token))
        if resp1.status_code != 201:
            return
        rol_id = resp1.json()["id"]

        try:
            resp2 = api.post(f"{API_PREFIX}/roles", json=payload, headers=auth_header(admin_token))
            assert resp2.status_code in (400, 409, 422), resp2.text
        finally:
            api.delete(f"{API_PREFIX}/roles/{rol_id}", headers=auth_header(admin_token))

    def test_gestor_sin_permiso_crear_403(self, api, gestor_token):
        payload = {
            "codigo": f"ROL_SIN_{uuid.uuid4().hex[:8].upper()}",
            "nombre": "Sin Permiso",
            "nivel": 1,
        }
        resp = api.post(f"{API_PREFIX}/roles", json=payload, headers=auth_header(gestor_token))
        assert resp.status_code == 403, resp.text
        assert "security.roles.crear" in resp.json()["detail"]

    def test_gestor_sin_permiso_ver_403(self, api, gestor_token):
        resp = api.get(f"{API_PREFIX}/roles", headers=auth_header(gestor_token))
        assert resp.status_code == 403, resp.text
        assert "security.roles.ver" in resp.json()["detail"]

    def test_gestor_sin_permiso_editar_403(self, api, admin_token, gestor_token):
        payload = {
            "codigo": f"ROL_EDT_{uuid.uuid4().hex[:8].upper()}",
            "nombre": "Para Editar",
            "nivel": 1,
        }
        create_resp = api.post(
            f"{API_PREFIX}/roles", json=payload, headers=auth_header(admin_token)
        )
        assert create_resp.status_code == 201, create_resp.text
        rol_id = create_resp.json()["id"]

        try:
            resp = api.put(
                f"{API_PREFIX}/roles/{rol_id}",
                json={"nombre": "Intento"},
                headers=auth_header(gestor_token),
            )
            assert resp.status_code == 403, resp.text
            assert "security.roles.editar" in resp.json()["detail"]
        finally:
            api.delete(f"{API_PREFIX}/roles/{rol_id}", headers=auth_header(admin_token))

    def test_gestor_sin_permiso_eliminar_403(self, api, admin_token, gestor_token):
        payload = {
            "codigo": f"ROL_ELM_{uuid.uuid4().hex[:8].upper()}",
            "nombre": "Para Eliminar",
            "nivel": 1,
        }
        create_resp = api.post(
            f"{API_PREFIX}/roles", json=payload, headers=auth_header(admin_token)
        )
        assert create_resp.status_code == 201, create_resp.text
        rol_id = create_resp.json()["id"]

        try:
            resp = api.delete(f"{API_PREFIX}/roles/{rol_id}", headers=auth_header(gestor_token))
            assert resp.status_code == 403, resp.text
            assert "security.roles.eliminar" in resp.json()["detail"]
        finally:
            api.delete(f"{API_PREFIX}/roles/{rol_id}", headers=auth_header(admin_token))


class TestPermisosListado:
    def test_listar_todos_los_permisos(self, api, admin_token):
        resp = api.get(f"{API_PREFIX}/roles/permisos", headers=auth_header(admin_token))
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] > 0
        for item in data["items"]:
            assert "id" in item
            assert "codigo" in item
            assert "nombre" in item
            assert "modulo" in item
            assert "accion" in item
            assert "estado" in item

    def test_listar_permisos_por_modulo(self, api, admin_token):
        resp = api.get(
            f"{API_PREFIX}/roles/permisos?modulo=linea_estrategica",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "items" in data
        for item in data["items"]:
            assert item["modulo"] == "linea_estrategica"

    def test_gestor_sin_permiso_ver_permisos_403(self, api, gestor_token):
        resp = api.get(f"{API_PREFIX}/roles/permisos", headers=auth_header(gestor_token))
        assert resp.status_code == 403, resp.text
        assert "security.roles.ver" in resp.json()["detail"]
