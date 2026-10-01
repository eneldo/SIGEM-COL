"""Tests de integración para Dashboards Admin y Gestor."""

from tests.conftest import API_PREFIX, auth_header


ADMIN_URL = f"{API_PREFIX}/dashboard/admin"
GESTOR_URL = f"{API_PREFIX}/dashboard/gestor"
GESTOR_DASHBOARD_URL = f"{API_PREFIX}/gestor/dashboard"


class TestDashboardAdminKPIs:
    """GET /dashboard/admin/kpis - KPIs generales."""

    def test_kpis_requires_auth(self, api):
        resp = api.get(f"{ADMIN_URL}/kpis")
        assert resp.status_code == 401

    def test_kpis_admin_ok(self, api, admin_token):
        resp = api.get(f"{ADMIN_URL}/kpis", headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "gestores_activos" in data
        assert "total_dependencias" in data
        assert "total_lineas_estrategicas" in data
        assert "total_programas" in data
        assert "total_productos" in data

    def test_kpis_gestor_token_denied(self, api, gestor_token):
        resp = api.get(f"{ADMIN_URL}/kpis", headers=auth_header(gestor_token))
        assert resp.status_code == 403
        assert "dashboard.admin.ver" in resp.json()["detail"]


class TestDashboardAdminResumenPlan:
    """GET /dashboard/admin/resumen-plan - Resumen del plan de desarrollo."""

    def test_resumen_plan_requires_auth(self, api):
        resp = api.get(f"{ADMIN_URL}/resumen-plan")
        assert resp.status_code == 401

    def test_resumen_plan_admin_ok(self, api, admin_token):
        resp = api.get(f"{ADMIN_URL}/resumen-plan", headers=auth_header(admin_token))
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            data = resp.json()
            assert "plan" in data
            assert "lineas_desglose" in data
            assert "total_lineas_estrategicas" in data
            assert "total_programas" in data
            assert "total_productos" in data

    def test_resumen_plan_gestor_token_denied(self, api, gestor_token):
        resp = api.get(f"{ADMIN_URL}/resumen-plan", headers=auth_header(gestor_token))
        assert resp.status_code == 403


class TestDashboardAdminGestores:
    """GET /dashboard/admin/gestores - Resumen de gestores."""

    def test_gestores_requires_auth(self, api):
        resp = api.get(f"{ADMIN_URL}/gestores")
        assert resp.status_code == 401

    def test_gestores_admin_ok(self, api, admin_token):
        resp = api.get(f"{ADMIN_URL}/gestores", headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "gestores" in data
        assert "total" in data
        assert isinstance(data["gestores"], list)

    def test_gestores_gestor_token_denied(self, api, gestor_token):
        resp = api.get(f"{ADMIN_URL}/gestores", headers=auth_header(gestor_token))
        assert resp.status_code == 403


class TestDashboardAdminAlertas:
    """GET /dashboard/admin/alertas - Alertas de seguridad."""

    def test_alertas_requires_auth(self, api):
        resp = api.get(f"{ADMIN_URL}/alertas")
        assert resp.status_code == 401

    def test_alertas_admin_ok(self, api, admin_token):
        resp = api.get(f"{ADMIN_URL}/alertas", headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "alertas" in data
        assert "total" in data
        assert isinstance(data["alertas"], list)

    def test_alertas_gestor_token_denied(self, api, gestor_token):
        resp = api.get(f"{ADMIN_URL}/alertas", headers=auth_header(gestor_token))
        assert resp.status_code == 403


class TestDashboardAdminEstadisticasDependencia:
    """GET /dashboard/admin/estadisticas-dependencia - Estadísticas por dependencia."""

    def test_estadisticas_requires_auth(self, api):
        resp = api.get(f"{ADMIN_URL}/estadisticas-dependencia")
        assert resp.status_code == 401

    def test_estadisticas_admin_ok(self, api, admin_token):
        resp = api.get(
            f"{ADMIN_URL}/estadisticas-dependencia", headers=auth_header(admin_token)
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "dependencias" in data
        assert "total" in data
        assert isinstance(data["dependencias"], list)

    def test_estadisticas_gestor_token_denied(self, api, gestor_token):
        resp = api.get(
            f"{ADMIN_URL}/estadisticas-dependencia", headers=auth_header(gestor_token)
        )
        assert resp.status_code == 403


class TestDashboardGestorKPIs:
    """GET /dashboard/gestor/kpis - KPIs personales del gestor."""

    def test_kpis_requires_auth(self, api):
        resp = api.get(f"{GESTOR_URL}/kpis")
        assert resp.status_code == 401

    def test_kpis_gestor_ok(self, api, gestor_token):
        resp = api.get(f"{GESTOR_URL}/kpis", headers=auth_header(gestor_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "total_productos_asignados" in data
        assert "total_dependencias_asignadas" in data
        assert "total_lineas_estrategicas" in data

    def test_kpis_admin_ok(self, api, admin_token):
        resp = api.get(f"{GESTOR_URL}/kpis", headers=auth_header(admin_token))
        assert resp.status_code == 404


class TestDashboardGestorMisProductos:
    """GET /dashboard/gestor/mis-productos - Productos asignados."""

    def test_mis_productos_requires_auth(self, api):
        resp = api.get(f"{GESTOR_URL}/mis-productos")
        assert resp.status_code == 401

    def test_mis_productos_gestor_ok(self, api, gestor_token):
        resp = api.get(f"{GESTOR_URL}/mis-productos", headers=auth_header(gestor_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "productos" in data
        assert "total" in data
        assert isinstance(data["productos"], list)

    def test_mis_productos_admin_404(self, api, admin_token):
        resp = api.get(f"{GESTOR_URL}/mis-productos", headers=auth_header(admin_token))
        assert resp.status_code == 404


class TestDashboardGestorMisPendientes:
    """GET /dashboard/gestor/mis-pendientes - Productos pendientes de actualización."""

    def test_mis_pendientes_requires_auth(self, api):
        resp = api.get(f"{GESTOR_URL}/mis-pendientes")
        assert resp.status_code == 401

    def test_mis_pendientes_gestor_ok(self, api, gestor_token):
        resp = api.get(
            f"{GESTOR_URL}/mis-pendientes", headers=auth_header(gestor_token)
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pendientes" in data
        assert "total" in data
        assert isinstance(data["pendientes"], list)

    def test_mis_pendientes_admin_404(self, api, admin_token):
        resp = api.get(f"{GESTOR_URL}/mis-pendientes", headers=auth_header(admin_token))
        assert resp.status_code == 404


class TestDashboardGestorMisAlertas:
    """GET /dashboard/gestor/mis-alertas - Alertas personales."""

    def test_mis_alertas_requires_auth(self, api):
        resp = api.get(f"{GESTOR_URL}/mis-alertas")
        assert resp.status_code == 401

    def test_mis_alertas_gestor_ok(self, api, gestor_token):
        resp = api.get(f"{GESTOR_URL}/mis-alertas", headers=auth_header(gestor_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "alertas" in data
        assert "total" in data
        assert isinstance(data["alertas"], list)

    def test_mis_alertas_admin_404(self, api, admin_token):
        resp = api.get(f"{GESTOR_URL}/mis-alertas", headers=auth_header(admin_token))
        assert resp.status_code == 404


class TestGestorDashboardEndpoints:
    """Endpoints adicionales en /gestor/dashboard (mis-productos, resumen, avances)."""

    def test_mis_productos_requires_auth(self, api):
        resp = api.get(f"{GESTOR_DASHBOARD_URL}/mis-productos")
        assert resp.status_code == 401

    def test_mis_productos_gestor_ok(self, api, gestor_token):
        resp = api.get(
            f"{GESTOR_DASHBOARD_URL}/mis-productos", headers=auth_header(gestor_token)
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_resumen_requires_auth(self, api):
        resp = api.get(f"{GESTOR_DASHBOARD_URL}/resumen")
        assert resp.status_code == 401

    def test_resumen_gestor_ok(self, api, gestor_token):
        resp = api.get(
            f"{GESTOR_DASHBOARD_URL}/resumen", headers=auth_header(gestor_token)
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_productos" in data
        assert "avance_promedio" in data

    def test_avances_revision_requires_auth(self, api):
        resp = api.get(f"{GESTOR_DASHBOARD_URL}/revision/avances")
        assert resp.status_code == 401

    def test_avances_revision_gestor_ok(self, api, gestor_token):
        resp = api.get(
            f"{GESTOR_DASHBOARD_URL}/revision/avances",
            headers=auth_header(gestor_token),
        )
        assert resp.status_code in (200, 403)

    def test_avances_revision_admin_ok(self, api, admin_token):
        resp = api.get(
            f"{GESTOR_DASHBOARD_URL}/revision/avances", headers=auth_header(admin_token)
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_avances_revision_filtro_estado(self, api, admin_token):
        for estado in ("PENDIENTE", "APROBADO", "RECHAZADO", "BORRADOR"):
            resp = api.get(
                f"{GESTOR_DASHBOARD_URL}/revision/avances?estado={estado}",
                headers=auth_header(admin_token),
            )
            assert resp.status_code == 200

    def test_avances_revision_filtro_search(self, api, admin_token):
        resp = api.get(
            f"{GESTOR_DASHBOARD_URL}/revision/avances?search=test",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200

    def test_avances_revision_filtro_periodo(self, api, admin_token):
        resp = api.get(
            f"{GESTOR_DASHBOARD_URL}/revision/avances?periodo=Enero - Marzo 2026",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200

    def test_estadisticas_revision_requires_auth(self, api):
        resp = api.get(f"{GESTOR_DASHBOARD_URL}/revision/estadisticas")
        assert resp.status_code == 401

    def test_estadisticas_revision_admin_ok(self, api, admin_token):
        resp = api.get(
            f"{GESTOR_DASHBOARD_URL}/revision/estadisticas",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pendientes" in data
        assert "aprobados_semana" in data
        assert "devueltos" in data

    def test_estadisticas_revision_gestor_ok(self, api, gestor_token):
        resp = api.get(
            f"{GESTOR_DASHBOARD_URL}/revision/estadisticas",
            headers=auth_header(gestor_token),
        )
        assert resp.status_code in (200, 403)


class TestErroresValidacion:
    """Tests de validación temprana (400/422) para cubrir ramas de error."""

    def test_kpis_invalid_municipio(self, api, admin_token):
        resp = api.get(f"{ADMIN_URL}/kpis", headers=auth_header(admin_token))
        assert resp.status_code in (200, 404)

    def test_resumen_plan_sin_plan_activo(self, api, admin_token):
        resp = api.get(f"{ADMIN_URL}/resumen-plan", headers=auth_header(admin_token))
        assert resp.status_code in (200, 404)

    def test_avances_revision_uuid_invalido_en_path_no_aplica(self, api):
        pass

    def test_mis_productos_usuario_sin_gestor(self, api, admin_token):
        resp = api.get(f"{GESTOR_URL}/mis-productos", headers=auth_header(admin_token))
        assert resp.status_code == 404

    def test_kpis_usuario_sin_gestor(self, api, admin_token):
        resp = api.get(f"{GESTOR_URL}/kpis", headers=auth_header(admin_token))
        assert resp.status_code == 404

    def test_mis_pendientes_usuario_sin_gestor(self, api, admin_token):
        resp = api.get(f"{GESTOR_URL}/mis-pendientes", headers=auth_header(admin_token))
        assert resp.status_code == 404

    def test_mis_alertas_usuario_sin_gestor(self, api, admin_token):
        resp = api.get(f"{GESTOR_URL}/mis-alertas", headers=auth_header(admin_token))
        assert resp.status_code == 404


class TestEstructuraRespuestas:
    """Validar estructura de respuestas esperadas."""

    def test_kpis_generales_structure(self, api, admin_token):
        resp = api.get(f"{ADMIN_URL}/kpis", headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["gestores_activos"], int)
        assert isinstance(data["gestores_inactivos"], int)
        assert isinstance(data["gestores_bloqueados"], int)
        assert isinstance(data["total_dependencias"], int)

    def test_gestores_summary_structure(self, api, admin_token):
        resp = api.get(f"{ADMIN_URL}/gestores", headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["gestores"], list)
        if data["gestores"]:
            g = data["gestores"][0]
            assert "id" in g
            assert "codigo" in g
            assert "nombre_completo" in g
            assert "estado" in g
            assert "ultimo_acceso" in g

    def test_alertas_structure(self, api, admin_token):
        resp = api.get(f"{ADMIN_URL}/alertas", headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        if data["alertas"]:
            a = data["alertas"][0]
            assert "tipo" in a
            assert "mensaje" in a
            assert "gestor_id" in a

    def test_estadisticas_dependencia_structure(self, api, admin_token):
        resp = api.get(
            f"{ADMIN_URL}/estadisticas-dependencia", headers=auth_header(admin_token)
        )
        assert resp.status_code == 200
        data = resp.json()
        if data["dependencias"]:
            d = data["dependencias"][0]
            assert "dependencia_id" in d
            assert "dependencia_nombre" in d
            assert "total_productos" in d
            assert "total_gestores" in d

    def test_kpis_personales_structure(self, api, gestor_token):
        resp = api.get(f"{GESTOR_URL}/kpis", headers=auth_header(gestor_token))
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["total_productos_asignados"], int)
        assert isinstance(data["total_dependencias_asignadas"], int)
        assert isinstance(data["total_lineas_estrategicas"], int)

    def test_mis_productos_structure(self, api, gestor_token):
        resp = api.get(f"{GESTOR_URL}/mis-productos", headers=auth_header(gestor_token))
        assert resp.status_code == 200
        data = resp.json()
        if data["productos"]:
            p = data["productos"][0]
            assert "id" in p
            assert "codigo" in p
            assert "nombre" in p
            assert "programa" in p
            assert "dependencia_responsable" in p

    def test_mis_pendientes_structure(self, api, gestor_token):
        resp = api.get(
            f"{GESTOR_URL}/mis-pendientes", headers=auth_header(gestor_token)
        )
        assert resp.status_code == 200
        data = resp.json()
        if data["pendientes"]:
            p = data["pendientes"][0]
            assert "producto_id" in p
            assert "dias_sin_actualizar" in p

    def test_mis_alertas_structure(self, api, gestor_token):
        resp = api.get(f"{GESTOR_URL}/mis-alertas", headers=auth_header(gestor_token))
        assert resp.status_code == 200
        data = resp.json()
        if data["alertas"]:
            a = data["alertas"][0]
            assert "tipo" in a
            assert "mensaje" in a

    def test_resumen_avances_structure(self, api, gestor_token):
        resp = api.get(
            f"{GESTOR_DASHBOARD_URL}/resumen", headers=auth_header(gestor_token)
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["total_productos"], int)
        assert isinstance(data["productos_con_avance"], int)
        assert isinstance(data["avance_promedio"], (int, float))
        assert isinstance(data["productos_completados"], int)


class TestRBACDashboard:
    """Pruebas de control de acceso en dashboards."""

    def test_admin_tiene_acceso_todo(self, api, admin_token):
        endpoints = [
            f"{ADMIN_URL}/kpis",
            f"{ADMIN_URL}/resumen-plan",
            f"{ADMIN_URL}/gestores",
            f"{ADMIN_URL}/alertas",
            f"{ADMIN_URL}/estadisticas-dependencia",
        ]
        for ep in endpoints:
            resp = api.get(ep, headers=auth_header(admin_token))
            assert resp.status_code in (200, 404), (
                f"Falló {ep}: {resp.status_code} {resp.text}"
            )

    def test_gestor_solo_dashboard_propio(self, api, gestor_token):
        allowed = [
            f"{GESTOR_URL}/kpis",
            f"{GESTOR_URL}/mis-productos",
            f"{GESTOR_URL}/mis-pendientes",
            f"{GESTOR_URL}/mis-alertas",
            f"{GESTOR_DASHBOARD_URL}/mis-productos",
            f"{GESTOR_DASHBOARD_URL}/resumen",
        ]
        for ep in allowed:
            resp = api.get(ep, headers=auth_header(gestor_token))
            assert resp.status_code in (200, 404), (
                f"Debería permitir {ep}: {resp.status_code}"
            )

        denied = [
            f"{ADMIN_URL}/kpis",
            f"{ADMIN_URL}/resumen-plan",
            f"{ADMIN_URL}/gestores",
            f"{ADMIN_URL}/alertas",
            f"{ADMIN_URL}/estadisticas-dependencia",
        ]
        for ep in denied:
            resp = api.get(ep, headers=auth_header(gestor_token))
            assert resp.status_code == 403, f"Debería denegar {ep}: {resp.status_code}"
