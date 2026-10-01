"""Tests del sistema de evidencias múltiples."""

from io import BytesIO

from PIL import Image

from tests.conftest import API_PREFIX, auth_header


class TestEvidenciasEndpoint:
    """Pruebas de los endpoints de evidencias múltiples."""

    def test_listar_evidencias_requires_auth(self, api):
        resp = api.get(
            f"{API_PREFIX}/gestor/dashboard/avances/00000000-0000-0000-0000-000000000000/evidencias"
        )
        assert resp.status_code == 401

    def test_subir_evidencia_requires_auth(self, api):
        resp = api.post(
            f"{API_PREFIX}/gestor/dashboard/avances/00000000-0000-0000-0000-000000000000/evidencias",
        )
        assert resp.status_code in (401, 422)

    def test_listar_evidencias_avance_inexistente(self, api, gestor_token):
        resp = api.get(
            f"{API_PREFIX}/gestor/dashboard/avances/00000000-0000-0000-0000-000000000000/evidencias",
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 404

    def test_descargar_evidencia_inexistente(self, api, gestor_token):
        resp = api.get(
            f"{API_PREFIX}/gestor/dashboard/avances/00000000-0000-0000-0000-000000000000/evidencias/00000000-0000-0000-0000-000000000000",
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 404

    def test_eliminar_evidencia_inexistente(self, api, gestor_token):
        resp = api.delete(
            f"{API_PREFIX}/gestor/dashboard/avances/00000000-0000-0000-0000-000000000000/evidencias/00000000-0000-0000-0000-000000000000",
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 404

    def test_actualizar_descripcion_inexistente(self, api, gestor_token):
        resp = api.put(
            f"{API_PREFIX}/gestor/dashboard/avances/00000000-0000-0000-0000-000000000000/evidencias/00000000-0000-0000-0000-000000000000",
            json={"descripcion": "test"},
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 404


class TestSubirYListarEvidencias:
    """Pruebas de subida y listado de evidencias."""

    def _create_avance(self, api, gestor_token):
        productos = api.get(
            f"{API_PREFIX}/gestor/dashboard/mis-productos",
            headers=auth_header(gestor_token),
        ).json()
        assert len(productos) > 0, "El gestor debe tener al menos un producto asignado"
        producto_id = productos[0]["id"]
        resp = api.post(
            f"{API_PREFIX}/gestor/dashboard/avances?producto_id={producto_id}",
            json={
                "avance_porcentaje": 42.0,
                "avance_valor": 420,
                "observaciones": "Prueba multi-evidencia",
                "periodo": "Julio - Septiembre 2026",
                "estado_revision": "PENDIENTE",
            },
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 201, resp.text
        return resp.json()["id"]

    def _png_bytes(self) -> bytes:
        buf = BytesIO()
        Image.new("RGB", (64, 64), color=(10, 43, 41)).save(buf, format="PNG")
        return buf.getvalue()

    def test_subir_multiples_evidencias(self, api, gestor_token):
        avance_id = self._create_avance(api, gestor_token)
        png = self._png_bytes()

        resp = api.post(
            f"{API_PREFIX}/gestor/dashboard/avances/{avance_id}/evidencias",
            files=[
                ("files", ("evidencia1.png", png, "image/png")),
                ("files", ("evidencia2.png", png, "image/png")),
            ],
            data={"descripcion": "Documentos de prueba"},
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 201, resp.text
        result = resp.json()
        assert len(result) == 2
        assert result[0]["nombre"] == "evidencia1.png"
        assert result[0]["descripcion"] == "Documentos de prueba"
        assert result[0]["tipo"] == "image/png"
        assert result[1]["nombre"] == "evidencia2.png"

    def test_acepta_maximo_cuatro_evidencias(self, api, gestor_token):
        avance_id = self._create_avance(api, gestor_token)
        png = self._png_bytes()

        resp = api.post(
            f"{API_PREFIX}/gestor/dashboard/avances/{avance_id}/evidencias",
            files=[
                ("files", (f"evidencia{i}.png", png, "image/png")) for i in range(1, 5)
            ],
            headers=auth_header(gestor_token),
        )

        assert resp.status_code == 201, resp.text
        assert len(resp.json()) == 4

    def test_rechaza_mas_de_cuatro_evidencias_acumuladas(self, api, gestor_token):
        avance_id = self._create_avance(api, gestor_token)
        png = self._png_bytes()
        primera_carga = api.post(
            f"{API_PREFIX}/gestor/dashboard/avances/{avance_id}/evidencias",
            files=[
                ("files", (f"evidencia{i}.png", png, "image/png")) for i in range(1, 5)
            ],
            headers=auth_header(gestor_token),
        )
        assert primera_carga.status_code == 201, primera_carga.text

        resp = api.post(
            f"{API_PREFIX}/gestor/dashboard/avances/{avance_id}/evidencias",
            files=[("files", ("evidencia5.png", png, "image/png"))],
            headers=auth_header(gestor_token),
        )

        assert resp.status_code == 422
        assert (
            resp.json()["detail"]
            == "El avance admite máximo 4 evidencias; actualmente tiene 4."
        )

    def test_listar_evidencias_despues_de_subir(self, api, gestor_token):
        avance_id = self._create_avance(api, gestor_token)
        png = self._png_bytes()

        api.post(
            f"{API_PREFIX}/gestor/dashboard/avances/{avance_id}/evidencias",
            files=[("files", ("list_test.png", png, "image/png"))],
            data={"descripcion": "Para listar"},
            headers=auth_header(gestor_token),
        )

        resp = api.get(
            f"{API_PREFIX}/gestor/dashboard/avances/{avance_id}/evidencias",
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 200
        evidencias = resp.json()
        assert len(evidencias) == 1
        assert evidencias[0]["nombre"] == "list_test.png"
        assert evidencias[0]["descripcion"] == "Para listar"

    def test_descargar_evidencia_por_id(self, api, gestor_token):
        avance_id = self._create_avance(api, gestor_token)
        png = self._png_bytes()

        subida = api.post(
            f"{API_PREFIX}/gestor/dashboard/avances/{avance_id}/evidencias",
            files=[("files", ("download_test.png", png, "image/png"))],
            headers=auth_header(gestor_token),
        )
        ev_id = subida.json()[0]["id"]

        resp = api.get(
            f"{API_PREFIX}/gestor/dashboard/avances/{avance_id}/evidencias/{ev_id}",
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
        assert len(resp.content) > 0

    def test_actualizar_descripcion(self, api, gestor_token):
        avance_id = self._create_avance(api, gestor_token)
        png = self._png_bytes()

        subida = api.post(
            f"{API_PREFIX}/gestor/dashboard/avances/{avance_id}/evidencias",
            files=[("files", ("edit_desc.png", png, "image/png"))],
            headers=auth_header(gestor_token),
        )
        ev_id = subida.json()[0]["id"]

        resp = api.put(
            f"{API_PREFIX}/gestor/dashboard/avances/{avance_id}/evidencias/{ev_id}",
            json={"descripcion": "Descripción actualizada"},
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 200
        assert resp.json()["descripcion"] == "Descripción actualizada"

        listing = api.get(
            f"{API_PREFIX}/gestor/dashboard/avances/{avance_id}/evidencias",
            headers=auth_header(gestor_token),
        )
        assert listing.json()[0]["descripcion"] == "Descripción actualizada"

    def test_eliminar_evidencia(self, api, gestor_token):
        avance_id = self._create_avance(api, gestor_token)
        png = self._png_bytes()

        subida = api.post(
            f"{API_PREFIX}/gestor/dashboard/avances/{avance_id}/evidencias",
            files=[
                ("files", ("keep.png", png, "image/png")),
                ("files", ("delete_me.png", png, "image/png")),
            ],
            headers=auth_header(gestor_token),
        )
        evidencias = subida.json()
        assert len(evidencias) == 2
        delete_id = next(e["id"] for e in evidencias if e["nombre"] == "delete_me.png")

        resp = api.delete(
            f"{API_PREFIX}/gestor/dashboard/avances/{avance_id}/evidencias/{delete_id}",
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 200
        assert resp.json()["eliminada"] is True

        listing = api.get(
            f"{API_PREFIX}/gestor/dashboard/avances/{avance_id}/evidencias",
            headers=auth_header(gestor_token),
        )
        remaining = listing.json()
        assert len(remaining) == 1
        assert remaining[0]["nombre"] == "keep.png"

    def test_subir_evidencia_archivo_invalido(self, api, gestor_token):
        avance_id = self._create_avance(api, gestor_token)

        resp = api.post(
            f"{API_PREFIX}/gestor/dashboard/avances/{avance_id}/evidencias",
            files=[("files", ("malicioso.txt", b"contenido invalido", "text/plain"))],
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 422

    def test_subir_evidencia_firma_falsa(self, api, gestor_token):
        avance_id = self._create_avance(api, gestor_token)

        resp = api.post(
            f"{API_PREFIX}/gestor/dashboard/avances/{avance_id}/evidencias",
            files=[("files", ("falso.png", b"esto no es un png real", "image/png"))],
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 422
