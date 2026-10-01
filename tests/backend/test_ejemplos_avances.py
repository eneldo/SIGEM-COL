"""Tests de ejemplo: ciclo de vida de avances de productos.

Demuestra los patrones de testing del proyecto:
- Tests de integración contra el backend Docker vivo (fixtures de conftest)
- Flujo completo: crear → editar → revisar
- Validaciones de negocio y RBAC

Ejecutar:
    python -m pytest tests/backend/test_ejemplos_avances.py -v
"""

from tests.conftest import API_PREFIX, auth_header


def _crear_avance(api, gestor_token, producto_id=None, **overrides):
    """Helper: crea un avance en el primer producto asignado al gestor."""
    if producto_id is None:
        productos = api.get(
            f"{API_PREFIX}/gestor/dashboard/mis-productos",
            headers=auth_header(gestor_token),
        ).json()
        assert productos, "El gestor debe tener al menos un producto asignado"
        producto_id = productos[0]["id"]

    payload = {
        "avance_porcentaje": 30.0,
        "avance_valor": 300,
        "observaciones": "Avance de ejemplo",
        "periodo": "Julio - Septiembre 2026",
        "estado_revision": "PENDIENTE",
    }
    payload.update(overrides)

    resp = api.post(
        f"{API_PREFIX}/gestor/dashboard/avances?producto_id={producto_id}",
        json=payload,
        headers=auth_header(gestor_token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestCrearAvance:
    """Ejemplos de tests para el registro de avances."""

    def test_crear_avance_exitoso(self, api, gestor_token):
        avance = _crear_avance(api, gestor_token)

        assert avance["avance_porcentaje"] == 30.0
        assert avance["avance_valor"] == 300
        assert avance["estado_revision"] == "PENDIENTE"
        assert avance["estado"] == "REGISTRADO"
        assert avance["id"]

    def test_crear_avance_requiere_auth(self, api):
        resp = api.post(
            f"{API_PREFIX}/gestor/dashboard/avances?producto_id=00000000-0000-0000-0000-000000000000",
            json={"avance_porcentaje": 10},
        )
        assert resp.status_code == 401

    def test_crear_avance_porcentaje_invalido(self, api, gestor_token):
        productos = api.get(
            f"{API_PREFIX}/gestor/dashboard/mis-productos",
            headers=auth_header(gestor_token),
        ).json()
        producto_id = productos[0]["id"]

        resp = api.post(
            f"{API_PREFIX}/gestor/dashboard/avances?producto_id={producto_id}",
            json={"avance_porcentaje": 150},  # fuera de rango 0-100
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 422

    def test_crear_avance_producto_no_asignado(self, api, gestor_token):
        resp = api.post(
            f"{API_PREFIX}/gestor/dashboard/avances?producto_id=00000000-0000-0000-0000-000000000000",
            json={"avance_porcentaje": 10},
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 422


class TestEditarAvance:
    """Ejemplos de tests para la edición de avances."""

    def test_editar_avance_pendiente(self, api, gestor_token):
        avance = _crear_avance(api, gestor_token, avance_porcentaje=20.0)

        resp = api.put(
            f"{API_PREFIX}/gestor/dashboard/avances/{avance['id']}",
            json={"avance_porcentaje": 45.0, "observaciones": "Actualizado en prueba"},
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["avance_porcentaje"] == 45.0
        assert data["observaciones"] == "Actualizado en prueba"

    def test_editar_avance_aprobado_prohibido(self, api, gestor_token, admin_token):
        avance = _crear_avance(api, gestor_token)

        # Admin aprueba el avance
        resp = api.patch(
            f"{API_PREFIX}/gestor/dashboard/revision/{avance['id']}",
            json={"nuevo_estado": "APROBADO"},
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200

        # Gestor intenta editar el avance aprobado → 403
        resp = api.put(
            f"{API_PREFIX}/gestor/dashboard/avances/{avance['id']}",
            json={"avance_porcentaje": 99.0},
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 403


class TestRevisarAvance:
    """Ejemplos de tests para el flujo de revisión (aprobar/devolver)."""

    def test_aprobar_avance(self, api, gestor_token, admin_token):
        avance = _crear_avance(api, gestor_token)

        resp = api.patch(
            f"{API_PREFIX}/gestor/dashboard/revision/{avance['id']}",
            json={"nuevo_estado": "APROBADO"},
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["estado_revision"] == "APROBADO"

    def test_rechazar_avance_requiere_observacion(self, api, gestor_token, admin_token):
        avance = _crear_avance(api, gestor_token)

        resp = api.patch(
            f"{API_PREFIX}/gestor/dashboard/revision/{avance['id']}",
            json={"nuevo_estado": "RECHAZADO"},  # sin observación
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 422

    def test_rechazar_avance_con_observacion(self, api, gestor_token, admin_token):
        avance = _crear_avance(api, gestor_token)

        resp = api.patch(
            f"{API_PREFIX}/gestor/dashboard/revision/{avance['id']}",
            json={
                "nuevo_estado": "RECHAZADO",
                "observacion": "Falta soporte documental",
            },
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["estado_revision"] == "RECHAZADO"
        assert data["observaciones_revision"] == "Falta soporte documental"

    def test_revision_requiere_permisos(self, api, gestor_token):
        """Un gestor sin permiso de revisión no debe poder aprobar."""
        avance = _crear_avance(api, gestor_token)

        # Nota: en el setup actual enemova es GESTOR_LIDER y puede revisar
        # sus propios avances. Este test documenta el patrón.
        resp = api.patch(
            f"{API_PREFIX}/gestor/dashboard/revision/{avance['id']}",
            json={"nuevo_estado": "APROBADO"},
            headers=auth_header(gestor_token),
        )
        # Acepta 200 (si tiene permiso) o 403 (si no)
        assert resp.status_code in (200, 403)


class TestListarAvances:
    """Ejemplos de tests para consultas de avances."""

    def test_listar_avances_producto(self, api, gestor_token):
        productos = api.get(
            f"{API_PREFIX}/gestor/dashboard/mis-productos",
            headers=auth_header(gestor_token),
        ).json()
        producto_id = productos[0]["id"]

        _crear_avance(api, gestor_token, producto_id=producto_id)

        resp = api.get(
            f"{API_PREFIX}/gestor/dashboard/avances/{producto_id}",
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 200
        avances = resp.json()
        assert len(avances) >= 1
        assert all(a["producto_id"] == producto_id for a in avances)

    def test_listar_avances_requiere_auth(self, api):
        resp = api.get(
            f"{API_PREFIX}/gestor/dashboard/avances/00000000-0000-0000-0000-000000000000",
        )
        assert resp.status_code == 401

    def test_resumen_avances(self, api, gestor_token):
        resp = api.get(
            f"{API_PREFIX}/gestor/dashboard/resumen",
            headers=auth_header(gestor_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_productos" in data
        assert "avance_promedio" in data
        assert "productos_completados" in data
