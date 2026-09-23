"""Tests de dashboards y RBAC."""
import pytest
from tests.conftest import API_PREFIX, auth_header


class TestDashboardAdmin:
    """Pruebas del dashboard de administrador."""

    def test_admin_dashboard_kpis(self, api, admin_token):
        resp = api.get(f"{API_PREFIX}/dashboard/admin/kpis", headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)

    def test_admin_dashboard_requires_auth(self, api):
        resp = api.get(f"{API_PREFIX}/dashboard/admin/kpis")
        assert resp.status_code == 401


class TestDashboardGestor:
    """Pruebas del dashboard de gestor."""

    def test_gestor_mis_productos(self, api, gestor_token):
        resp = api.get(f"{API_PREFIX}/gestor/dashboard/mis-productos", headers=auth_header(gestor_token))
        assert resp.status_code == 200

    def test_gestor_resumen(self, api, gestor_token):
        resp = api.get(f"{API_PREFIX}/gestor/dashboard/resumen", headers=auth_header(gestor_token))
        assert resp.status_code == 200

    def test_gestor_dashboard_requires_auth(self, api):
        resp = api.get(f"{API_PREFIX}/gestor/dashboard/mis-productos")
        assert resp.status_code == 401


class TestRBAC:
    """Pruebas de control de acceso basado en roles."""

    def test_gestor_no_acceso_usuarios(self, api, gestor_token):
        resp = api.get(f"{API_PREFIX}/usuarios", headers=auth_header(gestor_token))
        assert resp.status_code == 403

    def test_gestor_no_acceso_lineas(self, api, gestor_token):
        resp = api.get(f"{API_PREFIX}/lineas-estrategicas", headers=auth_header(gestor_token))
        assert resp.status_code == 403

    def test_gestor_no_acceso_programas(self, api, gestor_token):
        resp = api.get(f"{API_PREFIX}/programas", headers=auth_header(gestor_token))
        assert resp.status_code == 403

    def test_gestor_no_acceso_productos(self, api, gestor_token):
        resp = api.get(f"{API_PREFIX}/productos", headers=auth_header(gestor_token))
        assert resp.status_code == 403

    def test_admin_acceso_usuarios(self, api, admin_token):
        resp = api.get(f"{API_PREFIX}/usuarios", headers=auth_header(admin_token))
        assert resp.status_code == 200

    def test_admin_acceso_lineas(self, api, admin_token):
        resp = api.get(f"{API_PREFIX}/lineas-estrategicas", headers=auth_header(admin_token))
        assert resp.status_code == 200

    def test_admin_acceso_programas(self, api, admin_token):
        resp = api.get(f"{API_PREFIX}/programas", headers=auth_header(admin_token))
        assert resp.status_code == 200

    def test_admin_acceso_productos(self, api, admin_token):
        resp = api.get(f"{API_PREFIX}/productos", headers=auth_header(admin_token))
        assert resp.status_code == 200
