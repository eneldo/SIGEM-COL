"""Tests de integración CRUD para catálogos: líneas, programas, productos, dependencias."""

import uuid

from tests.conftest import API_PREFIX, auth_header

MUNICIPIO_ID = "3955c3f3-e036-4b74-b1fc-b330603d99a9"
PLAN_DESARROLLO_ID = "fba239a8-68a0-4d1b-9ff4-1b00857b629b"


def _get_plan_desarrollo_id(api, admin_token):
    resp = api.get(
        f"{API_PREFIX}/lineas-estrategicas?page_size=1",
        headers=auth_header(admin_token),
    )
    if resp.status_code == 200 and resp.json().get("items"):
        return resp.json()["items"][0]["plan_desarrollo_id"]
    return PLAN_DESARROLLO_ID


def _get_linea_id(api, admin_token):
    resp = api.get(
        f"{API_PREFIX}/lineas-estrategicas?estado=ACTIVA&page_size=1",
        headers=auth_header(admin_token),
    )
    if resp.status_code == 200 and resp.json().get("items"):
        return resp.json()["items"][0]["id"]
    return None


def _get_programa_id(api, admin_token):
    resp = api.get(
        f"{API_PREFIX}/programas?estado=ACTIVO&page_size=1",
        headers=auth_header(admin_token),
    )
    if resp.status_code == 200 and resp.json().get("items"):
        return resp.json()["items"][0]["id"]
    return None


def _get_dependencia_id(api, admin_token):
    resp = api.get(
        f"{API_PREFIX}/dependencias?estado=ACTIVA&page_size=1",
        headers=auth_header(admin_token),
    )
    if resp.status_code == 200 and resp.json().get("items"):
        return resp.json()["items"][0]["id"]
    return None


class TestLineasEstrategicasCRUD:
    def test_crear_linea_happy_path(self, api, admin_token):
        plan_id = _get_plan_desarrollo_id(api, admin_token)
        payload = {
            "nombre": "Línea de Prueba Integración",
            "descripcion": "Descripción de prueba",
            "numero": "1",
            "orden": 1,
            "plan_desarrollo_id": plan_id,
        }
        resp = api.post(
            f"{API_PREFIX}/lineas-estrategicas",
            json=payload,
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["nombre"] == payload["nombre"]
        assert data["plan_desarrollo_id"] == plan_id
        assert data["codigo"].startswith("LE-")
        linea_id = data["id"]

        try:
            # Verificar que se puede leer
            get_resp = api.get(
                f"{API_PREFIX}/lineas-estrategicas/{linea_id}",
                headers=auth_header(admin_token),
            )
            assert get_resp.status_code == 200, get_resp.text
            assert get_resp.json()["id"] == linea_id
        finally:
            api.delete(
                f"{API_PREFIX}/lineas-estrategicas/{linea_id}",
                headers=auth_header(admin_token),
            )

    def test_listar_lineas_con_filtros(self, api, admin_token):
        plan_id = _get_plan_desarrollo_id(api, admin_token)
        resp = api.get(
            f"{API_PREFIX}/lineas-estrategicas?plan_desarrollo_id={plan_id}&estado=ACTIVA&page=1&page_size=10",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        for item in data["items"]:
            assert item["plan_desarrollo_id"] == plan_id
            assert item["estado"] == "ACTIVA"

    def test_obtener_linea_detalle(self, api, admin_token):
        linea_id = _get_linea_id(api, admin_token)
        if not linea_id:
            return
        resp = api.get(
            f"{API_PREFIX}/lineas-estrategicas/{linea_id}",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["id"] == linea_id
        assert "plan_desarrollo_nombre" in data

    def test_actualizar_linea(self, api, admin_token):
        plan_id = _get_plan_desarrollo_id(api, admin_token)
        payload = {
            "nombre": "Línea para Actualizar",
            "descripcion": "Original",
            "plan_desarrollo_id": plan_id,
        }
        create_resp = api.post(
            f"{API_PREFIX}/lineas-estrategicas",
            json=payload,
            headers=auth_header(admin_token),
        )
        assert create_resp.status_code == 201, create_resp.text
        linea_id = create_resp.json()["id"]

        try:
            update_payload = {
                "nombre": "Línea Actualizada",
                "descripcion": "Modificada",
                "orden": 5,
            }
            resp = api.put(
                f"{API_PREFIX}/lineas-estrategicas/{linea_id}",
                json=update_payload,
                headers=auth_header(admin_token),
            )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["nombre"] == "Línea Actualizada"
            assert data["descripcion"] == "Modificada"
            assert data["orden"] == 5
        finally:
            api.delete(
                f"{API_PREFIX}/lineas-estrategicas/{linea_id}",
                headers=auth_header(admin_token),
            )

    def test_eliminar_linea(self, api, admin_token):
        plan_id = _get_plan_desarrollo_id(api, admin_token)
        payload = {"nombre": "Línea para Eliminar", "plan_desarrollo_id": plan_id}
        create_resp = api.post(
            f"{API_PREFIX}/lineas-estrategicas",
            json=payload,
            headers=auth_header(admin_token),
        )
        assert create_resp.status_code == 201, create_resp.text
        linea_id = create_resp.json()["id"]

        resp = api.delete(
            f"{API_PREFIX}/lineas-estrategicas/{linea_id}",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 204, resp.text

        get_resp = api.get(
            f"{API_PREFIX}/lineas-estrategicas/{linea_id}",
            headers=auth_header(admin_token),
        )
        assert get_resp.status_code == 404

    def test_id_invalido_devuelve_422_o_404(self, api, admin_token):
        resp = api.get(
            f"{API_PREFIX}/lineas-estrategicas/no-es-uuid",
            headers=auth_header(admin_token),
        )
        assert resp.status_code in (400, 422, 404)

    def test_codigo_duplicado_en_mismo_plan_al_actualizar(self, api, admin_token):
        plan_id = _get_plan_desarrollo_id(api, admin_token)
        payload1 = {"nombre": "Línea Original", "plan_desarrollo_id": plan_id}
        resp1 = api.post(
            f"{API_PREFIX}/lineas-estrategicas",
            json=payload1,
            headers=auth_header(admin_token),
        )
        if resp1.status_code != 201:
            return
        linea_id1 = resp1.json()["id"]
        codigo1 = resp1.json()["codigo"]

        payload2 = {"nombre": "Línea Segunda", "plan_desarrollo_id": plan_id}
        resp2 = api.post(
            f"{API_PREFIX}/lineas-estrategicas",
            json=payload2,
            headers=auth_header(admin_token),
        )
        if resp2.status_code != 201:
            api.delete(
                f"{API_PREFIX}/lineas-estrategicas/{linea_id1}",
                headers=auth_header(admin_token),
            )
            return
        linea_id2 = resp2.json()["id"]

        try:
            resp3 = api.put(
                f"{API_PREFIX}/lineas-estrategicas/{linea_id2}",
                json={"codigo": codigo1},
                headers=auth_header(admin_token),
            )
            assert resp3.status_code in (400, 409, 422), resp3.text
        finally:
            api.delete(
                f"{API_PREFIX}/lineas-estrategicas/{linea_id1}",
                headers=auth_header(admin_token),
            )
            api.delete(
                f"{API_PREFIX}/lineas-estrategicas/{linea_id2}",
                headers=auth_header(admin_token),
            )

    def test_gestor_sin_permiso_crear_403(self, api, gestor_token):
        plan_id = _get_plan_desarrollo_id(api, admin_token=None)
        payload = {"nombre": "Línea sin Permiso", "plan_desarrollo_id": plan_id}
        resp = api.post(
            f"{API_PREFIX}/lineas-estrategicas",
            json=payload,
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 403, resp.text
        assert "linea_estrategica.crear" in resp.json()["detail"]

    def test_gestor_sin_permiso_editar_403(self, api, admin_token, gestor_token):
        plan_id = _get_plan_desarrollo_id(api, admin_token)
        payload = {"nombre": "Línea para Editar", "plan_desarrollo_id": plan_id}
        create_resp = api.post(
            f"{API_PREFIX}/lineas-estrategicas",
            json=payload,
            headers=auth_header(admin_token),
        )
        assert create_resp.status_code == 201, create_resp.text
        linea_id = create_resp.json()["id"]

        try:
            resp = api.put(
                f"{API_PREFIX}/lineas-estrategicas/{linea_id}",
                json={"nombre": "Intento"},
                headers=auth_header(gestor_token),
            )
            assert resp.status_code == 403, resp.text
            assert "linea_estrategica.editar" in resp.json()["detail"]
        finally:
            api.delete(
                f"{API_PREFIX}/lineas-estrategicas/{linea_id}",
                headers=auth_header(admin_token),
            )

    def test_gestor_sin_permiso_eliminar_403(self, api, admin_token, gestor_token):
        plan_id = _get_plan_desarrollo_id(api, admin_token)
        payload = {
            "nombre": "Línea para Eliminar Sin Permiso",
            "plan_desarrollo_id": plan_id,
        }
        create_resp = api.post(
            f"{API_PREFIX}/lineas-estrategicas",
            json=payload,
            headers=auth_header(admin_token),
        )
        assert create_resp.status_code == 201, create_resp.text
        linea_id = create_resp.json()["id"]

        try:
            resp = api.delete(
                f"{API_PREFIX}/lineas-estrategicas/{linea_id}",
                headers=auth_header(gestor_token),
            )
            assert resp.status_code == 403, resp.text
            assert "linea_estrategica.eliminar" in resp.json()["detail"]
        finally:
            api.delete(
                f"{API_PREFIX}/lineas-estrategicas/{linea_id}",
                headers=auth_header(admin_token),
            )


class TestProgramasCRUD:
    def test_crear_programa_happy_path(self, api, admin_token):
        linea_id = _get_linea_id(api, admin_token)
        if not linea_id:
            return
        payload = {
            "codigo": f"PROG-{uuid.uuid4().hex[:6].upper()}",
            "nombre": "Programa de Prueba Integración",
            "sector": "Salud",
            "descripcion": "Descripción de prueba",
            "linea_estrategica_id": linea_id,
        }
        resp = api.post(f"{API_PREFIX}/programas", json=payload, headers=auth_header(admin_token))
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["nombre"] == payload["nombre"]
        assert data["linea_estrategica_id"] == linea_id
        programa_id = data["id"]

        try:
            get_resp = api.get(
                f"{API_PREFIX}/programas/{programa_id}",
                headers=auth_header(admin_token),
            )
            assert get_resp.status_code == 200, get_resp.text
            assert get_resp.json()["id"] == programa_id
        finally:
            api.delete(
                f"{API_PREFIX}/programas/{programa_id}",
                headers=auth_header(admin_token),
            )

    def test_listar_programas_con_filtros(self, api, admin_token):
        linea_id = _get_linea_id(api, admin_token)
        if not linea_id:
            return
        resp = api.get(
            f"{API_PREFIX}/programas?linea_estrategica_id={linea_id}&estado=ACTIVO&page=1&page_size=10",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "items" in data
        assert "total" in data
        for item in data["items"]:
            assert item["linea_estrategica_id"] == linea_id
            assert item["estado"] == "ACTIVO"

    def test_obtener_programa_detalle(self, api, admin_token):
        programa_id = _get_programa_id(api, admin_token)
        if not programa_id:
            return
        resp = api.get(f"{API_PREFIX}/programas/{programa_id}", headers=auth_header(admin_token))
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["id"] == programa_id
        assert "linea_estrategica_nombre" in data

    def test_actualizar_programa(self, api, admin_token):
        linea_id = _get_linea_id(api, admin_token)
        if not linea_id:
            return
        payload = {
            "codigo": f"PROG-UPD-{uuid.uuid4().hex[:6].upper()}",
            "nombre": "Programa para Actualizar",
            "linea_estrategica_id": linea_id,
        }
        create_resp = api.post(
            f"{API_PREFIX}/programas", json=payload, headers=auth_header(admin_token)
        )
        assert create_resp.status_code == 201, create_resp.text
        programa_id = create_resp.json()["id"]

        try:
            update_payload = {
                "nombre": "Programa Actualizado",
                "sector": "Educación",
                "descripcion": "Modificado",
            }
            resp = api.put(
                f"{API_PREFIX}/programas/{programa_id}",
                json=update_payload,
                headers=auth_header(admin_token),
            )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["nombre"] == "Programa Actualizado"
            assert data["sector"] == "Educación"
            assert data["descripcion"] == "Modificado"
        finally:
            api.delete(
                f"{API_PREFIX}/programas/{programa_id}",
                headers=auth_header(admin_token),
            )

    def test_eliminar_programa(self, api, admin_token):
        linea_id = _get_linea_id(api, admin_token)
        if not linea_id:
            return
        payload = {
            "codigo": f"PROG-DEL-{uuid.uuid4().hex[:6].upper()}",
            "nombre": "Programa para Eliminar",
            "linea_estrategica_id": linea_id,
        }
        create_resp = api.post(
            f"{API_PREFIX}/programas", json=payload, headers=auth_header(admin_token)
        )
        assert create_resp.status_code == 201, create_resp.text
        programa_id = create_resp.json()["id"]

        resp = api.delete(f"{API_PREFIX}/programas/{programa_id}", headers=auth_header(admin_token))
        assert resp.status_code == 204, resp.text

        get_resp = api.get(
            f"{API_PREFIX}/programas/{programa_id}", headers=auth_header(admin_token)
        )
        assert get_resp.status_code == 404

    def test_id_invalido_devuelve_422_o_404(self, api, admin_token):
        resp = api.get(f"{API_PREFIX}/programas/no-es-uuid", headers=auth_header(admin_token))
        assert resp.status_code in (400, 422, 404)

    def test_codigo_duplicado_en_misma_linea(self, api, admin_token):
        linea_id = _get_linea_id(api, admin_token)
        if not linea_id:
            return
        codigo = f"PROG-DUP-{uuid.uuid4().hex[:6].upper()}"
        payload = {
            "codigo": codigo,
            "nombre": "Programa Duplicado",
            "linea_estrategica_id": linea_id,
        }
        resp1 = api.post(f"{API_PREFIX}/programas", json=payload, headers=auth_header(admin_token))
        if resp1.status_code != 201:
            return
        programa_id = resp1.json()["id"]

        try:
            resp2 = api.post(
                f"{API_PREFIX}/programas",
                json=payload,
                headers=auth_header(admin_token),
            )
            assert resp2.status_code in (400, 409, 422), resp2.text
        finally:
            api.delete(
                f"{API_PREFIX}/programas/{programa_id}",
                headers=auth_header(admin_token),
            )

    def test_gestor_sin_permiso_crear_403(self, api, gestor_token):
        linea_id = _get_linea_id(api, admin_token=None)
        if not linea_id:
            return
        payload = {
            "codigo": f"PROG-SIN-{uuid.uuid4().hex[:6].upper()}",
            "nombre": "Sin Permiso",
            "linea_estrategica_id": linea_id,
        }
        resp = api.post(f"{API_PREFIX}/programas", json=payload, headers=auth_header(gestor_token))
        assert resp.status_code == 403, resp.text
        assert "programa.crear" in resp.json()["detail"]

    def test_gestor_sin_permiso_editar_403(self, api, admin_token, gestor_token):
        linea_id = _get_linea_id(api, admin_token)
        if not linea_id:
            return
        payload = {
            "codigo": f"PROG-EDT-{uuid.uuid4().hex[:6].upper()}",
            "nombre": "Para Editar",
            "linea_estrategica_id": linea_id,
        }
        create_resp = api.post(
            f"{API_PREFIX}/programas", json=payload, headers=auth_header(admin_token)
        )
        assert create_resp.status_code == 201, create_resp.text
        programa_id = create_resp.json()["id"]

        try:
            resp = api.put(
                f"{API_PREFIX}/programas/{programa_id}",
                json={"nombre": "Intento"},
                headers=auth_header(gestor_token),
            )
            assert resp.status_code == 403, resp.text
            assert "programa.editar" in resp.json()["detail"]
        finally:
            api.delete(
                f"{API_PREFIX}/programas/{programa_id}",
                headers=auth_header(admin_token),
            )

    def test_gestor_sin_permiso_eliminar_403(self, api, admin_token, gestor_token):
        linea_id = _get_linea_id(api, admin_token)
        if not linea_id:
            return
        payload = {
            "codigo": f"PROG-ELM-{uuid.uuid4().hex[:6].upper()}",
            "nombre": "Para Eliminar",
            "linea_estrategica_id": linea_id,
        }
        create_resp = api.post(
            f"{API_PREFIX}/programas", json=payload, headers=auth_header(admin_token)
        )
        assert create_resp.status_code == 201, create_resp.text
        programa_id = create_resp.json()["id"]

        try:
            resp = api.delete(
                f"{API_PREFIX}/programas/{programa_id}",
                headers=auth_header(gestor_token),
            )
            assert resp.status_code == 403, resp.text
            assert "programa.eliminar" in resp.json()["detail"]
        finally:
            api.delete(
                f"{API_PREFIX}/programas/{programa_id}",
                headers=auth_header(admin_token),
            )


class TestProductosCRUD:
    def test_crear_producto_happy_path(self, api, admin_token):
        programa_id = _get_programa_id(api, admin_token)
        if not programa_id:
            return
        dependencia_id = _get_dependencia_id(api, admin_token)
        payload = {
            "codigo": f"PROD-{uuid.uuid4().hex[:6].upper()}",
            "nombre": "Producto de Prueba Integración",
            "indicador": "Porcentaje de avance",
            "codigo_indicador": "IND-001",
            "meta_redactada": "Alcanzar 100%",
            "linea_base": 0,
            "meta_cuatrienio": 100,
            "descripcion": "Descripción de prueba",
            "unidad_medida": "%",
            "programa_id": programa_id,
            "dependencia_responsable_id": dependencia_id,
        }
        resp = api.post(f"{API_PREFIX}/productos", json=payload, headers=auth_header(admin_token))
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["nombre"] == payload["nombre"]
        assert data["programa_id"] == programa_id
        assert data["dependencia_responsable_id"] == dependencia_id
        producto_id = data["id"]

        try:
            get_resp = api.get(
                f"{API_PREFIX}/productos/{producto_id}",
                headers=auth_header(admin_token),
            )
            assert get_resp.status_code == 200, get_resp.text
            assert get_resp.json()["id"] == producto_id
        finally:
            api.delete(
                f"{API_PREFIX}/productos/{producto_id}",
                headers=auth_header(admin_token),
            )

    def test_listar_productos_con_filtros(self, api, admin_token):
        programa_id = _get_programa_id(api, admin_token)
        if not programa_id:
            return
        resp = api.get(
            f"{API_PREFIX}/productos?programa_id={programa_id}&estado=ACTIVO&page=1&page_size=10",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "items" in data
        assert "total" in data
        for item in data["items"]:
            assert item["programa_id"] == programa_id
            assert item["estado"] == "ACTIVO"

    def test_obtener_producto_detalle(self, api, admin_token):
        programa_id = _get_programa_id(api, admin_token)
        if not programa_id:
            return
        resp = api.get(
            f"{API_PREFIX}/productos?programa_id={programa_id}&page_size=1",
            headers=auth_header(admin_token),
        )
        if resp.status_code != 200 or not resp.json().get("items"):
            return
        producto_id = resp.json()["items"][0]["id"]

        resp = api.get(f"{API_PREFIX}/productos/{producto_id}", headers=auth_header(admin_token))
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["id"] == producto_id
        assert "programa_nombre" in data

    def test_actualizar_producto(self, api, admin_token):
        programa_id = _get_programa_id(api, admin_token)
        if not programa_id:
            return
        payload = {
            "codigo": f"PROD-UPD-{uuid.uuid4().hex[:6].upper()}",
            "nombre": "Producto para Actualizar",
            "programa_id": programa_id,
        }
        create_resp = api.post(
            f"{API_PREFIX}/productos", json=payload, headers=auth_header(admin_token)
        )
        assert create_resp.status_code == 201, create_resp.text
        producto_id = create_resp.json()["id"]

        try:
            update_payload = {
                "nombre": "Producto Actualizado",
                "indicador": "Nuevo indicador",
                "meta_cuatrienio": 200,
                "unidad_medida": "unidades",
            }
            resp = api.put(
                f"{API_PREFIX}/productos/{producto_id}",
                json=update_payload,
                headers=auth_header(admin_token),
            )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["nombre"] == "Producto Actualizado"
            assert data["indicador"] == "Nuevo indicador"
            assert data["meta_cuatrienio"] == 200
            assert data["unidad_medida"] == "unidades"
        finally:
            api.delete(
                f"{API_PREFIX}/productos/{producto_id}",
                headers=auth_header(admin_token),
            )

    def test_eliminar_producto(self, api, admin_token):
        programa_id = _get_programa_id(api, admin_token)
        if not programa_id:
            return
        payload = {
            "codigo": f"PROD-DEL-{uuid.uuid4().hex[:6].upper()}",
            "nombre": "Producto para Eliminar",
            "programa_id": programa_id,
        }
        create_resp = api.post(
            f"{API_PREFIX}/productos", json=payload, headers=auth_header(admin_token)
        )
        assert create_resp.status_code == 201, create_resp.text
        producto_id = create_resp.json()["id"]

        resp = api.delete(f"{API_PREFIX}/productos/{producto_id}", headers=auth_header(admin_token))
        assert resp.status_code == 204, resp.text

        get_resp = api.get(
            f"{API_PREFIX}/productos/{producto_id}", headers=auth_header(admin_token)
        )
        assert get_resp.status_code == 404

    def test_id_invalido_devuelve_422_o_404(self, api, admin_token):
        resp = api.get(f"{API_PREFIX}/productos/no-es-uuid", headers=auth_header(admin_token))
        assert resp.status_code in (400, 422, 404)

    def test_codigo_duplicado_en_mismo_programa(self, api, admin_token):
        programa_id = _get_programa_id(api, admin_token)
        if not programa_id:
            return
        codigo = f"PROD-DUP-{uuid.uuid4().hex[:6].upper()}"
        payload = {
            "codigo": codigo,
            "nombre": "Producto Duplicado",
            "programa_id": programa_id,
        }
        resp1 = api.post(f"{API_PREFIX}/productos", json=payload, headers=auth_header(admin_token))
        if resp1.status_code != 201:
            return
        producto_id = resp1.json()["id"]

        try:
            resp2 = api.post(
                f"{API_PREFIX}/productos",
                json=payload,
                headers=auth_header(admin_token),
            )
            assert resp2.status_code in (400, 409, 422), resp2.text
        finally:
            api.delete(
                f"{API_PREFIX}/productos/{producto_id}",
                headers=auth_header(admin_token),
            )

    def test_gestor_sin_permiso_crear_403(self, api, gestor_token):
        programa_id = _get_programa_id(api, admin_token=None)
        if not programa_id:
            return
        payload = {
            "codigo": f"PROD-SIN-{uuid.uuid4().hex[:6].upper()}",
            "nombre": "Sin Permiso",
            "programa_id": programa_id,
        }
        resp = api.post(f"{API_PREFIX}/productos", json=payload, headers=auth_header(gestor_token))
        assert resp.status_code == 403, resp.text
        assert "producto.crear" in resp.json()["detail"]

    def test_gestor_sin_permiso_editar_403(self, api, admin_token, gestor_token):
        programa_id = _get_programa_id(api, admin_token)
        if not programa_id:
            return
        payload = {
            "codigo": f"PROD-EDT-{uuid.uuid4().hex[:6].upper()}",
            "nombre": "Para Editar",
            "programa_id": programa_id,
        }
        create_resp = api.post(
            f"{API_PREFIX}/productos", json=payload, headers=auth_header(admin_token)
        )
        assert create_resp.status_code == 201, create_resp.text
        producto_id = create_resp.json()["id"]

        try:
            resp = api.put(
                f"{API_PREFIX}/productos/{producto_id}",
                json={"nombre": "Intento"},
                headers=auth_header(gestor_token),
            )
            assert resp.status_code == 403, resp.text
            assert "producto.editar" in resp.json()["detail"]
        finally:
            api.delete(
                f"{API_PREFIX}/productos/{producto_id}",
                headers=auth_header(admin_token),
            )

    def test_gestor_sin_permiso_eliminar_403(self, api, admin_token, gestor_token):
        programa_id = _get_programa_id(api, admin_token)
        if not programa_id:
            return
        payload = {
            "codigo": f"PROD-ELM-{uuid.uuid4().hex[:6].upper()}",
            "nombre": "Para Eliminar",
            "programa_id": programa_id,
        }
        create_resp = api.post(
            f"{API_PREFIX}/productos", json=payload, headers=auth_header(admin_token)
        )
        assert create_resp.status_code == 201, create_resp.text
        producto_id = create_resp.json()["id"]

        try:
            resp = api.delete(
                f"{API_PREFIX}/productos/{producto_id}",
                headers=auth_header(gestor_token),
            )
            assert resp.status_code == 403, resp.text
            assert "producto.eliminar" in resp.json()["detail"]
        finally:
            api.delete(
                f"{API_PREFIX}/productos/{producto_id}",
                headers=auth_header(admin_token),
            )


class TestDependenciasCRUD:
    def test_crear_dependencia_happy_path(self, api, admin_token):
        payload = {
            "codigo": f"DEP-{uuid.uuid4().hex[:6].upper()}",
            "nombre": "Dependencia de Prueba Integración",
            "descripcion": "Descripción de prueba",
            "nivel": 1,
            "estado": "ACTIVA",
        }
        resp = api.post(
            f"{API_PREFIX}/dependencias", json=payload, headers=auth_header(admin_token)
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["nombre"] == payload["nombre"]
        assert data["codigo"] == payload["codigo"]
        assert data["estado"] == "ACTIVA"
        dependencia_id = data["id"]

        try:
            get_resp = api.get(
                f"{API_PREFIX}/dependencias/{dependencia_id}",
                headers=auth_header(admin_token),
            )
            assert get_resp.status_code == 200, get_resp.text
            assert get_resp.json()["id"] == dependencia_id
        finally:
            api.delete(
                f"{API_PREFIX}/dependencias/{dependencia_id}",
                headers=auth_header(admin_token),
            )

    def test_listar_dependencias_con_filtros(self, api, admin_token):
        resp = api.get(
            f"{API_PREFIX}/dependencias?estado=ACTIVA&page=1&page_size=10",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "items" in data
        assert "total" in data
        for item in data["items"]:
            assert item["estado"] == "ACTIVA"

    def test_obtener_dependencia_detalle(self, api, admin_token):
        dependencia_id = _get_dependencia_id(api, admin_token)
        if not dependencia_id:
            return
        resp = api.get(
            f"{API_PREFIX}/dependencias/{dependencia_id}",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["id"] == dependencia_id

    def test_actualizar_dependencia(self, api, admin_token):
        payload = {
            "codigo": f"DEP-UPD-{uuid.uuid4().hex[:6].upper()}",
            "nombre": "Dependencia para Actualizar",
            "estado": "ACTIVA",
        }
        create_resp = api.post(
            f"{API_PREFIX}/dependencias", json=payload, headers=auth_header(admin_token)
        )
        assert create_resp.status_code == 201, create_resp.text
        dependencia_id = create_resp.json()["id"]

        try:
            update_payload = {
                "nombre": "Dependencia Actualizada",
                "descripcion": "Modificada",
                "nivel": 2,
            }
            resp = api.put(
                f"{API_PREFIX}/dependencias/{dependencia_id}",
                json=update_payload,
                headers=auth_header(admin_token),
            )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["nombre"] == "Dependencia Actualizada"
            assert data["descripcion"] == "Modificada"
            assert data["nivel"] == 2
        finally:
            api.delete(
                f"{API_PREFIX}/dependencias/{dependencia_id}",
                headers=auth_header(admin_token),
            )

    def test_eliminar_dependencia(self, api, admin_token):
        payload = {
            "codigo": f"DEP-DEL-{uuid.uuid4().hex[:6].upper()}",
            "nombre": "Dependencia para Eliminar",
            "estado": "ACTIVA",
        }
        create_resp = api.post(
            f"{API_PREFIX}/dependencias", json=payload, headers=auth_header(admin_token)
        )
        assert create_resp.status_code == 201, create_resp.text
        dependencia_id = create_resp.json()["id"]

        resp = api.delete(
            f"{API_PREFIX}/dependencias/{dependencia_id}",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 204, resp.text

        get_resp = api.get(
            f"{API_PREFIX}/dependencias/{dependencia_id}",
            headers=auth_header(admin_token),
        )
        assert get_resp.status_code == 404

    def test_id_invalido_devuelve_422_o_404(self, api, admin_token):
        resp = api.get(f"{API_PREFIX}/dependencias/no-es-uuid", headers=auth_header(admin_token))
        assert resp.status_code in (400, 422, 404)

    def test_codigo_duplicado_en_municipio(self, api, admin_token):
        codigo = f"DEP-DUP-{uuid.uuid4().hex[:6].upper()}"
        payload = {
            "codigo": codigo,
            "nombre": "Dependencia Duplicada",
            "estado": "ACTIVA",
        }
        resp1 = api.post(
            f"{API_PREFIX}/dependencias", json=payload, headers=auth_header(admin_token)
        )
        if resp1.status_code != 201:
            return
        dependencia_id = resp1.json()["id"]

        try:
            resp2 = api.post(
                f"{API_PREFIX}/dependencias",
                json=payload,
                headers=auth_header(admin_token),
            )
            assert resp2.status_code in (400, 409, 422), resp2.text
        finally:
            api.delete(
                f"{API_PREFIX}/dependencias/{dependencia_id}",
                headers=auth_header(admin_token),
            )

    def test_gestor_sin_permiso_crear_403(self, api, gestor_token):
        payload = {
            "codigo": f"DEP-SIN-{uuid.uuid4().hex[:6].upper()}",
            "nombre": "Sin Permiso",
            "estado": "ACTIVA",
        }
        resp = api.post(
            f"{API_PREFIX}/dependencias",
            json=payload,
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 403, resp.text
        assert "dependencia.crear" in resp.json()["detail"]

    def test_gestor_sin_permiso_editar_403(self, api, admin_token, gestor_token):
        payload = {
            "codigo": f"DEP-EDT-{uuid.uuid4().hex[:6].upper()}",
            "nombre": "Para Editar",
            "estado": "ACTIVA",
        }
        create_resp = api.post(
            f"{API_PREFIX}/dependencias", json=payload, headers=auth_header(admin_token)
        )
        assert create_resp.status_code == 201, create_resp.text
        dependencia_id = create_resp.json()["id"]

        try:
            resp = api.put(
                f"{API_PREFIX}/dependencias/{dependencia_id}",
                json={"nombre": "Intento"},
                headers=auth_header(gestor_token),
            )
            assert resp.status_code == 403, resp.text
            assert "dependencia.editar" in resp.json()["detail"]
        finally:
            api.delete(
                f"{API_PREFIX}/dependencias/{dependencia_id}",
                headers=auth_header(admin_token),
            )

    def test_gestor_sin_permiso_eliminar_403(self, api, admin_token, gestor_token):
        payload = {
            "codigo": f"DEP-ELM-{uuid.uuid4().hex[:6].upper()}",
            "nombre": "Para Eliminar",
            "estado": "ACTIVA",
        }
        create_resp = api.post(
            f"{API_PREFIX}/dependencias", json=payload, headers=auth_header(admin_token)
        )
        assert create_resp.status_code == 201, create_resp.text
        dependencia_id = create_resp.json()["id"]

        try:
            resp = api.delete(
                f"{API_PREFIX}/dependencias/{dependencia_id}",
                headers=auth_header(gestor_token),
            )
            assert resp.status_code == 403, resp.text
            assert "dependencia.eliminar" in resp.json()["detail"]
        finally:
            api.delete(
                f"{API_PREFIX}/dependencias/{dependencia_id}",
                headers=auth_header(admin_token),
            )
