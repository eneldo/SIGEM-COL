"""Tests de integración - Flujos completos de trabajo."""
import pytest
from tests.conftest import API_PREFIX, auth_header


class TestFullWorkflow:
    """Prueba flujo completo: crear línea -> programa -> producto."""

    def test_full_planning_cycle(self, api, admin_token):
        h = auth_header(admin_token)

        # 1. Create a línea estratégica
        resp = api.post(f"{API_PREFIX}/lineas-estrategicas", json={
            "nombre": "Línea Test Integración",
            "codigo": "LT-TEST-001",
            "descripcion": "Línea de prueba para integración",
        }, headers=h)
        if resp.status_code == 201:
            linea_id = resp.json()["id"]

            # 2. Get the línea
            resp = api.get(f"{API_PREFIX}/lineas-estrategicas/{linea_id}", headers=h)
            assert resp.status_code == 200
            assert resp.json()["nombre"] == "Línea Test Integración"

            # 3. Update
            resp = api.put(f"{API_PREFIX}/lineas-estrategicas/{linea_id}", json={
                "descripcion": "Actualizada para testing",
            }, headers=h)
            assert resp.status_code == 200

            # 4. Create a programa under this línea
            resp = api.post(f"{API_PREFIX}/programas", json={
                "nombre": "Programa Test Integración",
                "codigo": "PR-TEST-001",
                "linea_estrategica_id": linea_id,
                "descripcion": "Programa de prueba",
            }, headers=h)
            if resp.status_code == 201:
                prog_id = resp.json()["id"]

                # 5. Get the programa
                resp = api.get(f"{API_PREFIX}/programas/{prog_id}", headers=h)
                assert resp.status_code == 200

                # 6. Create a producto
                resp = api.post(f"{API_PREFIX}/productos", json={
                    "nombre": "Producto Test Integración",
                    "codigo": "PD-TEST-001",
                    "programa_id": prog_id,
                    "descripcion": "Producto de prueba",
                }, headers=h)
                if resp.status_code == 201:
                    prod_id = resp.json()["id"]

                    # 7. Get the producto
                    resp = api.get(f"{API_PREFIX}/productos/{prod_id}", headers=h)
                    assert resp.status_code == 200

                    # Cleanup: delete in reverse order
                    api.delete(f"{API_PREFIX}/productos/{prod_id}", headers=h)

                api.delete(f"{API_PREFIX}/programas/{prog_id}", headers=h)

            # Cleanup
            api.delete(f"{API_PREFIX}/lineas-estrategicas/{linea_id}", headers=h)


class TestHealthCheck:
    """Pruebas de health check."""

    def test_health_endpoint(self, api):
        resp = api.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["checks"]["database"] == "ok"

    def test_root_endpoint(self, api):
        resp = api.get("/")
        assert resp.status_code == 200
        assert "SIGEM" in resp.json()["message"]

    def test_api_health(self, api):
        resp = api.get(f"{API_PREFIX}/health/")
        assert resp.status_code == 200


class TestCatalogos:
    """Pruebas de catálogos del sistema."""

    def test_list_roles(self, api, admin_token):
        resp = api.get(f"{API_PREFIX}/catalogos/roles", headers=auth_header(admin_token))
        assert resp.status_code == 200

    def test_list_dependencias(self, api, admin_token):
        resp = api.get(f"{API_PREFIX}/catalogos/dependencias", headers=auth_header(admin_token))
        assert resp.status_code == 200

    def test_list_roles_unauthenticated(self, api):
        resp = api.get(f"{API_PREFIX}/catalogos/roles")
        assert resp.status_code == 401
