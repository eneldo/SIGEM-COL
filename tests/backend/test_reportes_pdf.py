"""Tests de integración para Reportes y PDF."""

from tests.conftest import API_PREFIX, auth_header


class TestReportes:
    """Tests del módulo de Reportes JSON."""

    def test_resumen_general(self, api, admin_token):
        resp = api.get(
            f"{API_PREFIX}/reportes/resumen-general",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "total_lineas" in data
        assert "total_programas" in data
        assert "total_productos" in data
        assert "productos_activos" in data
        assert "productos_inactivos" in data
        assert "total_gestores" in data

    def test_resumen_por_linea(self, api, admin_token):
        resp = api.get(
            f"{API_PREFIX}/reportes/por-linea",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert isinstance(data, list)
        if data:
            item = data[0]
            assert "id" in item
            assert "codigo" in item
            assert "nombre" in item
            assert "total_programas" in item
            assert "total_productos" in item
            assert "estado" in item

    def test_resumen_por_programa(self, api, admin_token):
        resp = api.get(
            f"{API_PREFIX}/reportes/por-programa",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert isinstance(data, list)
        if data:
            item = data[0]
            assert "id" in item
            assert "codigo" in item
            assert "nombre" in item
            assert "sector" in item
            assert "linea_nombre" in item
            assert "total_productos" in item
            assert "productos_activos" in item
            assert "estado" in item

    def test_resumen_por_dependencia(self, api, admin_token):
        resp = api.get(
            f"{API_PREFIX}/reportes/por-dependencia",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert isinstance(data, list)
        if data:
            item = data[0]
            assert "id" in item
            assert "codigo" in item
            assert "nombre" in item
            assert "total_productos" in item
            assert "total_gestores" in item

    def test_metricas_productos(self, api, admin_token):
        resp = api.get(
            f"{API_PREFIX}/reportes/metricas-productos",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "total_productos" in data
        assert "con_indicador" in data
        assert "sin_indicador" in data
        assert "con_meta_cuatrienio" in data
        assert "con_linea_base" in data
        assert "con_gestor_asignado" in data
        assert "sin_gestor_asignado" in data
        assert "porcentaje_cumplimiento_indicador" in data
        assert "porcentaje_cumplimiento_meta" in data
        assert "promedio_avance" in data

    def test_denegado_sin_token_reportes(self, api):
        endpoints = [
            "/reportes/resumen-general",
            "/reportes/por-linea",
            "/reportes/por-programa",
            "/reportes/por-dependencia",
            "/reportes/metricas-productos",
        ]
        for ep in endpoints:
            resp = api.get(f"{API_PREFIX}{ep}")
            assert resp.status_code == 401, f"Endpoint {ep} debería requerir auth"

    def test_denegado_token_falso_reportes(self, api):
        fake_token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJoYWNrZXIifQ.fake"
        endpoints = [
            "/reportes/resumen-general",
            "/reportes/por-linea",
            "/reportes/por-programa",
            "/reportes/por-dependencia",
            "/reportes/metricas-productos",
        ]
        for ep in endpoints:
            resp = api.get(f"{API_PREFIX}{ep}", headers=auth_header(fake_token))
            assert resp.status_code in (401, 403, 429), f"Endpoint {ep}"


class TestInformePDF:
    """Tests del endpoint de generación de PDF."""

    def test_informe_pdf_generacion(self, api, admin_token):
        resp = api.get(
            f"{API_PREFIX}/reportes/informe-pdf",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200, resp.text
        assert resp.headers.get("content-type") == "application/pdf"
        assert "attachment" in resp.headers.get("content-disposition", "")
        assert "informe_gestion_sigem.pdf" in resp.headers.get(
            "content-disposition", ""
        )
        assert len(resp.content) > 0

    def test_informe_pdf_sin_token(self, api):
        resp = api.get(f"{API_PREFIX}/reportes/informe-pdf")
        assert resp.status_code == 401

    def test_informe_pdf_token_falso(self, api):
        fake_token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJoYWNrZXIifQ.fake"
        resp = api.get(
            f"{API_PREFIX}/reportes/informe-pdf",
            headers=auth_header(fake_token),
        )
        assert resp.status_code in (401, 403, 429)

    def test_informe_pdf_gestor_token(self, api, gestor_token):
        resp = api.get(
            f"{API_PREFIX}/reportes/informe-pdf",
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 200, resp.text
        assert resp.headers.get("content-type") == "application/pdf"
        assert len(resp.content) > 0
