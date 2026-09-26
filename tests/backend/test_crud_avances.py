"""Tests del CRUD de avances: crear → editar → eliminar (soft delete)."""
from tests.conftest import API_PREFIX, auth_header

AVANCES = f"{API_PREFIX}/gestor/dashboard/avances"


def _crear_avance(api, gestor_token, producto_id=None, **overrides):
    if producto_id is None:
        productos = api.get(
            f"{API_PREFIX}/gestor/dashboard/mis-productos",
            headers=auth_header(gestor_token),
        ).json()
        assert productos, "El gestor debe tener al menos un producto asignado"
        producto_id = productos[0]["id"]

    payload = {
        "avance_porcentaje": 10.0,
        "avance_valor": 100,
        "observaciones": "Avance de prueba CRUD",
        "periodo": "Enero - Marzo 2026",
        "estado_revision": "BORRADOR",
    }
    payload.update(overrides)

    resp = api.post(
        f"{AVANCES}?producto_id={producto_id}",
        json=payload,
        headers=auth_header(gestor_token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _listar_ids(api, gestor_token, producto_id=None):
    if producto_id is None:
        productos = api.get(
            f"{API_PREFIX}/gestor/dashboard/mis-productos",
            headers=auth_header(gestor_token),
        ).json()
        producto_id = productos[0]["id"]
    resp = api.get(f"{AVANCES}/{producto_id}", headers=auth_header(gestor_token))
    assert resp.status_code == 200
    return {a["id"] for a in resp.json()}


def _png():
    from io import BytesIO
    from PIL import Image

    buf = BytesIO()
    Image.new("RGB", (32, 32), color=(15, 61, 59)).save(buf, format="PNG")
    return buf.getvalue()


class TestEliminarAvance:
    """Pruebas del endpoint DELETE /avances/{avance_id}."""

    def test_eliminar_requiere_auth(self, api):
        resp = api.delete(f"{AVANCES}/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 401

    def test_eliminar_avance_inexistente(self, api, gestor_token):
        resp = api.delete(
            f"{AVANCES}/00000000-0000-0000-0000-000000000000",
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 404

    def test_eliminar_borrador_exitoso(self, api, gestor_token):
        avance = _crear_avance(api, gestor_token, estado_revision="BORRADOR")

        resp = api.delete(
            f"{AVANCES}/{avance['id']}",
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["id"] == avance["id"]
        assert data["eliminado"] is True

    def test_eliminar_pendiente_exitoso(self, api, gestor_token):
        avance = _crear_avance(api, gestor_token, estado_revision="PENDIENTE")

        resp = api.delete(
            f"{AVANCES}/{avance['id']}",
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["eliminado"] is True

    def test_eliminar_rechazado_exitoso(self, api, gestor_token, admin_token):
        avance = _crear_avance(api, gestor_token, estado_revision="PENDIENTE")
        rev = api.patch(
            f"{API_PREFIX}/gestor/dashboard/revision/{avance['id']}",
            json={"nuevo_estado": "RECHAZADO", "observacion": "Devuelto en prueba"},
            headers=auth_header(admin_token),
        )
        assert rev.status_code == 200, rev.text

        resp = api.delete(
            f"{AVANCES}/{avance['id']}",
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 200, resp.text

    def test_eliminar_desaparece_del_listado(self, api, gestor_token):
        avance = _crear_avance(api, gestor_token)
        assert avance["id"] in _listar_ids(api, gestor_token)

        resp = api.delete(
            f"{AVANCES}/{avance['id']}",
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 200

        assert avance["id"] not in _listar_ids(api, gestor_token)

    def test_eliminar_dos_veces_da_404(self, api, gestor_token):
        avance = _crear_avance(api, gestor_token)

        first = api.delete(
            f"{AVANCES}/{avance['id']}",
            headers=auth_header(gestor_token),
        )
        assert first.status_code == 200

        second = api.delete(
            f"{AVANCES}/{avance['id']}",
            headers=auth_header(gestor_token),
        )
        assert second.status_code == 404

    def test_editar_avance_eliminado_da_404(self, api, gestor_token):
        avance = _crear_avance(api, gestor_token)
        api.delete(f"{AVANCES}/{avance['id']}", headers=auth_header(gestor_token))

        resp = api.put(
            f"{AVANCES}/{avance['id']}",
            json={"avance_porcentaje": 80.0},
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 404

    def test_eliminar_avance_aprobado_prohibido(self, api, gestor_token, admin_token):
        avance = _crear_avance(api, gestor_token, estado_revision="PENDIENTE")
        rev = api.patch(
            f"{API_PREFIX}/gestor/dashboard/revision/{avance['id']}",
            json={"nuevo_estado": "APROBADO"},
            headers=auth_header(admin_token),
        )
        assert rev.status_code == 200, rev.text

        resp = api.delete(
            f"{AVANCES}/{avance['id']}",
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 403
        assert "aprobado" in resp.json()["detail"].lower()

        # El avance sigue visible en el listado
        assert avance["id"] in _listar_ids(api, gestor_token)

    def test_eliminar_avance_ajeno_prohibido(self, api, gestor_token, admin_token):
        avance = _crear_avance(api, gestor_token)

        resp = api.delete(
            f"{AVANCES}/{avance['id']}",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 403

    def test_eliminar_cascada_evidencias(self, api, gestor_token):
        avance = _crear_avance(api, gestor_token)
        avance_id = avance["id"]
        png = _png()

        subida = api.post(
            f"{AVANCES}/{avance_id}/evidencias",
            files=[
                ("files", ("cascada1.png", png, "image/png")),
                ("files", ("cascada2.png", png, "image/png")),
            ],
            headers=auth_header(gestor_token),
        )
        assert subida.status_code == 201, subida.text
        assert len(subida.json()) == 2

        listing_antes = api.get(
            f"{AVANCES}/{avance_id}/evidencias",
            headers=auth_header(gestor_token),
        )
        assert listing_antes.status_code == 200
        assert len(listing_antes.json()) == 2

        delete = api.delete(f"{AVANCES}/{avance_id}", headers=auth_header(gestor_token))
        assert delete.status_code == 200

        # El avance borrado no expone sus evidencias
        listing_despues = api.get(
            f"{AVANCES}/{avance_id}/evidencias",
            headers=auth_header(gestor_token),
        )
        assert listing_despues.status_code == 404


class TestCicloCompletoCRUD:
    """Flujo end-to-end: crear → listar → editar → eliminar → verificar."""

    def test_crud_completo(self, api, gestor_token, admin_token):
        productos = api.get(
            f"{API_PREFIX}/gestor/dashboard/mis-productos",
            headers=auth_header(gestor_token),
        ).json()
        assert productos
        producto_id = productos[0]["id"]

        # CREATE
        avance = _crear_avance(
            api,
            gestor_token,
            producto_id=producto_id,
            avance_porcentaje=15.0,
            estado_revision="BORRADOR",
        )
        avance_id = avance["id"]
        assert avance["estado_revision"] == "BORRADOR"

        # READ
        ids = _listar_ids(api, gestor_token, producto_id)
        assert avance_id in ids

        # UPDATE
        upd = api.put(
            f"{AVANCES}/{avance_id}",
            json={
                "avance_porcentaje": 55.0,
                "avance_valor": 550,
                "observaciones": "Actualizado en ciclo CRUD",
                "periodo": "Abril - Junio 2026",
            },
            headers=auth_header(gestor_token),
        )
        assert upd.status_code == 200, upd.text
        data = upd.json()
        assert data["avance_porcentaje"] == 55.0
        assert data["avance_valor"] == 550
        assert data["observaciones"] == "Actualizado en ciclo CRUD"
        assert data["periodo"] == "Abril - Junio 2026"

        # Aprobar (bloquea borrado)
        rev = api.patch(
            f"{API_PREFIX}/gestor/dashboard/revision/{avance_id}",
            json={"nuevo_estado": "APROBADO"},
            headers=auth_header(admin_token),
        )
        assert rev.status_code == 200, rev.text

        # DELETE bloqueado en APROBADO
        blocked = api.delete(f"{AVANCES}/{avance_id}", headers=auth_header(gestor_token))
        assert blocked.status_code == 403

        # Devolver y poder eliminar
        dev = api.patch(
            f"{API_PREFIX}/gestor/dashboard/revision/{avance_id}",
            json={"nuevo_estado": "RECHAZADO", "observacion": "Rehacer evidencia"},
            headers=auth_header(admin_token),
        )
        assert dev.status_code == 200, dev.text

        delete = api.delete(f"{AVANCES}/{avance_id}", headers=auth_header(gestor_token))
        assert delete.status_code == 200, delete.text
        assert delete.json()["eliminado"] is True

        # READ tras DELETE
        ids = _listar_ids(api, gestor_token, producto_id)
        assert avance_id not in ids
        again = api.delete(f"{AVANCES}/{avance_id}", headers=auth_header(gestor_token))
        assert again.status_code == 404


class TestEdicionAvance:
    """Casos adicionales de edición usados por el modal del frontend."""

    def test_editar_borrador(self, api, gestor_token):
        avance = _crear_avance(api, gestor_token, estado_revision="BORRADOR", avance_porcentaje=5.0)

        resp = api.put(
            f"{AVANCES}/{avance['id']}",
            json={"avance_porcentaje": 12.5, "avance_valor": 12},
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["avance_porcentaje"] == 12.5
        assert data["avance_valor"] == 12

    def test_editar_sin_campos_da_422(self, api, gestor_token):
        avance = _crear_avance(api, gestor_token)

        resp = api.put(
            f"{AVANCES}/{avance['id']}",
            json={},
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 422

    def test_editar_porcentaje_invalido_da_422(self, api, gestor_token):
        avance = _crear_avance(api, gestor_token)

        resp = api.put(
            f"{AVANCES}/{avance['id']}",
            json={"avance_porcentaje": 200},
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 422

    def test_editar_avance_inexistente_da_404(self, api, gestor_token):
        resp = api.put(
            f"{AVANCES}/00000000-0000-0000-0000-000000000000",
            json={"avance_porcentaje": 50},
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 404
