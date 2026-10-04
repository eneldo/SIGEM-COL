"""Tests de integración del flujo completo de Avances de Producto."""

import uuid
from decimal import ROUND_HALF_UP, Decimal

from tests.conftest import API_PREFIX, auth_header


AVANCES_URL = f"{API_PREFIX}/gestor/dashboard/avances"
REVISION_URL = f"{API_PREFIX}/gestor/dashboard/revision"

ESTADOS_QUE_RESERVAN_META = ("PENDIENTE", "EN_REVISION", "APROBADO")


def _mis_productos(api, token):
    return api.get(
        f"{API_PREFIX}/gestor/dashboard/mis-productos", headers=auth_header(token)
    )


def _producto_gestor(api, token):
    productos = _mis_productos(api, token).json()
    assert productos, "El gestor debe tener al menos un producto asignado"
    return productos[0]


def _acumulado_reservado(api, token, producto_id, excluir_id=None):
    resp = api.get(f"{AVANCES_URL}/{producto_id}", headers=auth_header(token))
    assert resp.status_code == 200, resp.text
    total = Decimal("0")
    for avance in resp.json():
        if avance["estado_revision"] not in ESTADOS_QUE_RESERVAN_META:
            continue
        if excluir_id is not None and avance["id"] == excluir_id:
            continue
        total += Decimal(str(avance["avance_valor"] or 0))
    return total


def _porcentaje_esperado(acumulado, meta):
    return float(
        (Decimal(str(acumulado)) / meta * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    )


def _crear_avance(api, token, producto_id=None, **overrides):
    if producto_id is None:
        productos = _mis_productos(api, token).json()
        assert productos, "El gestor debe tener al menos un producto asignado"
        producto_id = productos[0]["id"]

    payload = {
        "avance_porcentaje": 25.0,
        "avance_valor": 250,
        "observaciones": "Avance de prueba",
        "periodo": "Enero - Marzo 2026",
        "estado_revision": "BORRADOR",
        "indicador": "Porcentaje de cumplimiento",
        "evidencia_url": None,
        "evidencia_nombre": None,
        "evidencia_tipo": None,
    }
    payload.update(overrides)

    resp = api.post(
        f"{AVANCES_URL}?producto_id={producto_id}",
        json=payload,
        headers=auth_header(token),
    )
    return resp


def _listar_avances(api, token, producto_id):
    return api.get(f"{AVANCES_URL}/{producto_id}", headers=auth_header(token))


def _editar_avance(api, token, avance_id, **fields):
    return api.put(
        f"{AVANCES_URL}/{avance_id}", json=fields, headers=auth_header(token)
    )


def _eliminar_avance(api, token, avance_id):
    return api.delete(f"{AVANCES_URL}/{avance_id}", headers=auth_header(token))


def _revisar_avance(api, token, avance_id, nuevo_estado, observacion=None):
    payload = {"nuevo_estado": nuevo_estado}
    if observacion is not None:
        payload["observacion"] = observacion
    return api.patch(
        f"{REVISION_URL}/{avance_id}", json=payload, headers=auth_header(token)
    )


def _avances_revision(api, token, estado=None, search=None, periodo=None):
    params = []
    if estado:
        params.append(f"estado={estado}")
    if search:
        params.append(f"search={search}")
    if periodo:
        params.append(f"periodo={periodo}")
    query = "&".join(params)
    url = f"{REVISION_URL}/avances"
    if query:
        url += f"?{query}"
    return api.get(url, headers=auth_header(token))


def _estadisticas_revision(api, token):
    return api.get(f"{REVISION_URL}/estadisticas", headers=auth_header(token))


def _resumen_avances(api, token):
    return api.get(f"{API_PREFIX}/gestor/dashboard/resumen", headers=auth_header(token))


class TestCrearAvance:
    """POST /avances - Crear avance de producto."""

    def test_crear_requiere_auth(self, api):
        resp = api.post(
            f"{AVANCES_URL}?producto_id={uuid.uuid4()}", json={"avance_porcentaje": 10}
        )
        assert resp.status_code == 401

    def test_crear_exitoso_borrador(self, api, gestor_token):
        producto = _producto_gestor(api, gestor_token)
        meta = Decimal(str(producto["meta_cuatrienio"]))
        previo = _acumulado_reservado(api, gestor_token, producto["id"])

        resp = _crear_avance(
            api,
            gestor_token,
            producto_id=producto["id"],
            estado_revision="BORRADOR",
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["avance_porcentaje"] == _porcentaje_esperado(
            previo + Decimal("250"), meta
        )
        assert data["estado_revision"] == "BORRADOR"
        assert data["estado"] == "REGISTRADO"
        assert data["id"]

    def test_crear_exitoso_pendiente(self, api, gestor_token):
        resp = _crear_avance(api, gestor_token, estado_revision="PENDIENTE")
        assert resp.status_code == 201
        assert resp.json()["estado_revision"] == "PENDIENTE"

    def test_crear_campos_opcionales(self, api, gestor_token):
        resp = _crear_avance(
            api,
            gestor_token,
            avance_valor=500,
            indicador="Indicador personalizado",
            evidencia_url="https://example.com/evidencia.pdf",
            evidencia_nombre="evidencia.pdf",
            evidencia_tipo="application/pdf",
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["avance_valor"] == 500
        assert data["indicador"] == "Porcentaje de avance de pruebas"
        assert data["evidencia_url"] == "https://example.com/evidencia.pdf"

    def test_crear_validacion_porcentaje_fuera_rango(self, api, gestor_token):
        for val in (-1, 101, 150):
            resp = _crear_avance(api, gestor_token, avance_porcentaje=val)
            assert resp.status_code == 422, f"Debería fallar con {val}: {resp.text}"

    def test_crear_validacion_avance_valor_negativo(self, api, gestor_token):
        resp = _crear_avance(api, gestor_token, avance_valor=-10)
        assert resp.status_code == 422

    def test_crear_validacion_observaciones_muy_larga(self, api, gestor_token):
        resp = _crear_avance(api, gestor_token, observaciones="x" * 1001)
        assert resp.status_code == 422

    def test_crear_validacion_periodo_largo(self, api, gestor_token):
        resp = _crear_avance(api, gestor_token, periodo="x" * 51)
        assert resp.status_code == 422

    def test_crear_producto_no_asignado(self, api, gestor_token):
        resp = _crear_avance(api, gestor_token, producto_id=uuid.uuid4())
        assert resp.status_code == 422

    def test_crear_producto_inexistente(self, api, gestor_token):
        resp = _crear_avance(
            api, gestor_token, producto_id="00000000-0000-0000-0000-000000000000"
        )
        assert resp.status_code == 422


class TestListarAvances:
    """GET /avances/{producto_id} - Listar avances de un producto."""

    def test_listar_requiere_auth(self, api):
        resp = api.get(f"{AVANCES_URL}/{uuid.uuid4()}")
        assert resp.status_code == 401

    def test_listar_exitoso(self, api, gestor_token):
        productos = _mis_productos(api, gestor_token).json()
        producto_id = productos[0]["id"]
        _crear_avance(api, gestor_token, producto_id=producto_id)
        resp = _listar_avances(api, gestor_token, producto_id)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all(a["producto_id"] == producto_id for a in data)

    def test_listar_producto_inexistente(self, api, gestor_token):
        resp = _listar_avances(api, gestor_token, uuid.uuid4())
        assert resp.status_code == 200
        assert resp.json() == []

    def test_listar_producto_no_asignado(self, api, gestor_token):
        resp = _listar_avances(api, gestor_token, uuid.uuid4())
        assert resp.status_code == 200


class TestEditarAvance:
    """PUT /avances/{avance_id} - Editar avance existente."""

    def test_editar_requiere_auth(self, api):
        resp = api.put(f"{AVANCES_URL}/{uuid.uuid4()}", json={"avance_porcentaje": 50})
        assert resp.status_code == 401

    def test_editar_avance_inexistente(self, api, gestor_token):
        resp = _editar_avance(api, gestor_token, uuid.uuid4(), avance_porcentaje=50)
        assert resp.status_code == 404

    def test_editar_sin_campos_da_422(self, api, gestor_token):
        avance = _crear_avance(api, gestor_token).json()
        resp = _editar_avance(api, gestor_token, avance["id"])
        assert resp.status_code == 422
        assert "campos" in resp.json()["detail"].lower()

    def test_editar_borrador_exitoso(self, api, gestor_token):
        avance = _crear_avance(api, gestor_token, estado_revision="BORRADOR").json()
        resp = _editar_avance(
            api,
            gestor_token,
            avance["id"],
            avance_porcentaje=60.0,
            avance_valor=600,
            observaciones="Actualizado",
            periodo="Abril - Junio 2026",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["avance_porcentaje"] != 60.0
        assert data["avance_valor"] == 600
        assert data["observaciones"] == "Actualizado"
        assert data["periodo"] == "Abril - Junio 2026"

    def test_editar_pendiente_exitoso(self, api, gestor_token):
        avance = _crear_avance(api, gestor_token, estado_revision="PENDIENTE").json()
        resp = _editar_avance(api, gestor_token, avance["id"], avance_valor=400)
        assert resp.status_code == 200
        assert resp.json()["avance_porcentaje"] != 40.0

    def test_editar_aprobado_prohibido(self, api, gestor_token, admin_token):
        avance = _crear_avance(api, gestor_token, estado_revision="PENDIENTE").json()
        _revisar_avance(api, admin_token, avance["id"], "APROBADO")
        resp = _editar_avance(api, gestor_token, avance["id"], avance_porcentaje=80.0)
        assert resp.status_code == 403
        assert "aprobado" in resp.json()["detail"].lower()

    def test_editar_rechazado_permitido(self, api, gestor_token, admin_token):
        avance = _crear_avance(api, gestor_token, estado_revision="PENDIENTE").json()
        _revisar_avance(api, admin_token, avance["id"], "RECHAZADO", "Falta evidencia")
        resp = _editar_avance(api, gestor_token, avance["id"], avance_valor=300)
        assert resp.status_code == 200

    def test_editar_validacion_porcentaje(self, api, gestor_token):
        avance = _crear_avance(api, gestor_token).json()
        resp = _editar_avance(api, gestor_token, avance["id"], avance_porcentaje=200)
        assert resp.status_code == 422

    def test_editar_parcial_solo_observaciones(self, api, gestor_token):
        avance = _crear_avance(api, gestor_token).json()
        resp = _editar_avance(
            api, gestor_token, avance["id"], observaciones="Solo observaciones"
        )
        assert resp.status_code == 200
        assert resp.json()["observaciones"] == "Solo observaciones"


class TestEliminarAvance:
    """DELETE /avances/{avance_id} - Eliminar avance (soft delete)."""

    def test_eliminar_requiere_auth(self, api):
        resp = api.delete(f"{AVANCES_URL}/{uuid.uuid4()}")
        assert resp.status_code == 401

    def test_eliminar_avance_inexistente(self, api, gestor_token):
        resp = _eliminar_avance(api, gestor_token, uuid.uuid4())
        assert resp.status_code == 404

    def test_eliminar_borrador(self, api, gestor_token):
        avance = _crear_avance(api, gestor_token, estado_revision="BORRADOR").json()
        resp = _eliminar_avance(api, gestor_token, avance["id"])
        assert resp.status_code == 200
        assert resp.json()["eliminado"] is True

    def test_eliminar_pendiente(self, api, gestor_token):
        avance = _crear_avance(api, gestor_token, estado_revision="PENDIENTE").json()
        resp = _eliminar_avance(api, gestor_token, avance["id"])
        assert resp.status_code == 200
        assert resp.json()["eliminado"] is True

    def test_eliminar_rechazado(self, api, gestor_token, admin_token):
        avance = _crear_avance(api, gestor_token, estado_revision="PENDIENTE").json()
        _revisar_avance(api, admin_token, avance["id"], "RECHAZADO", "Devuelto")
        resp = _eliminar_avance(api, gestor_token, avance["id"])
        assert resp.status_code == 200

    def test_eliminar_aprobado_prohibido(self, api, gestor_token, admin_token):
        avance = _crear_avance(api, gestor_token, estado_revision="PENDIENTE").json()
        _revisar_avance(api, admin_token, avance["id"], "APROBADO")
        resp = _eliminar_avance(api, gestor_token, avance["id"])
        assert resp.status_code == 403
        assert "aprobado" in resp.json()["detail"].lower()

    def test_eliminar_desaparece_del_listado(self, api, gestor_token):
        productos = _mis_productos(api, gestor_token).json()
        producto_id = productos[0]["id"]
        avance = _crear_avance(api, gestor_token, producto_id=producto_id).json()
        assert avance["id"] in {
            a["id"] for a in _listar_avances(api, gestor_token, producto_id).json()
        }
        _eliminar_avance(api, gestor_token, avance["id"])
        assert avance["id"] not in {
            a["id"] for a in _listar_avances(api, gestor_token, producto_id).json()
        }

    def test_eliminar_dos_veces_da_404(self, api, gestor_token):
        avance = _crear_avance(api, gestor_token).json()
        _eliminar_avance(api, gestor_token, avance["id"])
        resp = _eliminar_avance(api, gestor_token, avance["id"])
        assert resp.status_code == 404


class TestRevisarAvance:
    """PATCH /revision/{avance_id} - Aprobar o rechazar avance."""

    def test_revisar_requiere_auth(self, api):
        resp = api.patch(
            f"{REVISION_URL}/{uuid.uuid4()}", json={"nuevo_estado": "APROBADO"}
        )
        assert resp.status_code == 401

    def test_revisar_avance_inexistente(self, api, admin_token):
        resp = _revisar_avance(api, admin_token, uuid.uuid4(), "APROBADO")
        assert resp.status_code in (404, 422)

    def test_aprobar_avance(self, api, gestor_token, admin_token):
        avance = _crear_avance(api, gestor_token, estado_revision="PENDIENTE").json()
        resp = _revisar_avance(api, admin_token, avance["id"], "APROBADO")
        assert resp.status_code == 200
        assert resp.json()["estado_revision"] == "APROBADO"

    def test_rechazar_requiere_observacion(self, api, gestor_token, admin_token):
        avance = _crear_avance(api, gestor_token, estado_revision="PENDIENTE").json()
        resp = _revisar_avance(api, admin_token, avance["id"], "RECHAZADO")
        assert resp.status_code == 422
        assert "observaci" in resp.json()["detail"].lower()

    def test_rechazar_con_observacion(self, api, gestor_token, admin_token):
        avance = _crear_avance(api, gestor_token, estado_revision="PENDIENTE").json()
        resp = _revisar_avance(
            api, admin_token, avance["id"], "RECHAZADO", "Falta evidencia documental"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["estado_revision"] == "RECHAZADO"
        assert data["observaciones_revision"] == "Falta evidencia documental"

    def test_revisar_estado_invalido(self, api, gestor_token, admin_token):
        avance = _crear_avance(api, gestor_token).json()
        resp = _revisar_avance(api, admin_token, avance["id"], "INVALIDO")
        assert resp.status_code == 422

    def test_revisar_gestor_sin_permiso(self, api, gestor_token):
        avance = _crear_avance(api, gestor_token, estado_revision="PENDIENTE").json()
        resp = _revisar_avance(api, gestor_token, avance["id"], "APROBADO")
        assert resp.status_code == 403
        assert "avance.revisar" in resp.json()["detail"]

    def test_revision_aprobado_a_rechazado(self, api, gestor_token, admin_token):
        avance = _crear_avance(api, gestor_token, estado_revision="PENDIENTE").json()
        _revisar_avance(api, admin_token, avance["id"], "APROBADO")
        resp = _revisar_avance(
            api, admin_token, avance["id"], "RECHAZADO", "Revisión posterior"
        )
        assert resp.status_code == 200
        assert resp.json()["estado_revision"] == "RECHAZADO"

    def test_revision_rechazado_a_aprobado(self, api, gestor_token, admin_token):
        avance = _crear_avance(api, gestor_token, estado_revision="PENDIENTE").json()
        _revisar_avance(api, admin_token, avance["id"], "RECHAZADO", "Falta evidencia")
        resp = _revisar_avance(api, admin_token, avance["id"], "APROBADO")
        assert resp.status_code == 200
        assert resp.json()["estado_revision"] == "APROBADO"


class TestAvancesRevision:
    """GET /revision/avances - Listar avances para revisión (admin/líder)."""

    def test_revision_requiere_auth(self, api):
        resp = api.get(f"{REVISION_URL}/avances")
        assert resp.status_code == 401

    def test_revision_admin_exitoso(self, api, admin_token):
        resp = _avances_revision(api, admin_token)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_revision_gestor_lider_exitoso(self, api, gestor_token):
        resp = _avances_revision(api, gestor_token)
        assert resp.status_code in (200, 403)

    def test_revision_filtro_estado(self, api, admin_token):
        for estado in ("PENDIENTE", "APROBADO", "RECHAZADO", "BORRADOR"):
            resp = _avances_revision(api, admin_token, estado=estado)
            assert resp.status_code == 200

    def test_revision_filtro_search(self, api, admin_token):
        resp = _avances_revision(api, admin_token, search="test")
        assert resp.status_code == 200

    def test_revision_filtro_periodo(self, api, admin_token):
        resp = _avances_revision(api, admin_token, periodo="Enero - Marzo 2026")
        assert resp.status_code == 200

    def test_revision_filtros_combinados(self, api, admin_token):
        resp = _avances_revision(
            api,
            admin_token,
            estado="PENDIENTE",
            search="avance",
            periodo="Enero - Marzo 2026",
        )
        assert resp.status_code == 200


class TestEstadisticasRevision:
    """GET /revision/estadisticas - Estadísticas de revisión."""

    def test_estadisticas_requiere_auth(self, api):
        resp = api.get(f"{REVISION_URL}/estadisticas")
        assert resp.status_code == 401

    def test_estadisticas_admin(self, api, admin_token):
        resp = _estadisticas_revision(api, admin_token)
        assert resp.status_code == 200
        data = resp.json()
        assert "pendientes" in data
        assert "aprobados_semana" in data
        assert "devueltos" in data

    def test_estadisticas_gestor_lider(self, api, gestor_token):
        resp = _estadisticas_revision(api, gestor_token)
        assert resp.status_code in (200, 403)


class TestResumenAvances:
    """GET /resumen - Resumen de avances del gestor."""

    def test_resumen_requiere_auth(self, api):
        resp = api.get(f"{API_PREFIX}/gestor/dashboard/resumen")
        assert resp.status_code == 401

    def test_resumen_exitoso(self, api, gestor_token):
        resp = _resumen_avances(api, gestor_token)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_productos" in data
        assert "productos_con_avance" in data
        assert "avance_promedio" in data
        assert "productos_completados" in data


class TestFlujoCompleto:
    """Flujo end-to-end: crear → editar → revisar → eliminar."""

    def test_flujo_borrador_a_aprobado(self, api, gestor_token, admin_token):
        producto = _producto_gestor(api, gestor_token)
        meta = Decimal(str(producto["meta_cuatrienio"]))
        previo = _acumulado_reservado(api, gestor_token, producto["id"])

        # Crear
        avance = _crear_avance(
            api,
            gestor_token,
            producto_id=producto["id"],
            estado_revision="BORRADOR",
        ).json()
        avance_id = avance["id"]

        # Editar borrador
        upd = _editar_avance(api, gestor_token, avance_id, avance_valor=500)
        assert upd.status_code == 200
        assert upd.json()["avance_porcentaje"] == _porcentaje_esperado(
            previo + Decimal("500"), meta
        )

        # Cambiar a PENDIENTE (simulando envío a revisión)
        upd2 = _editar_avance(api, gestor_token, avance_id, estado_revision="PENDIENTE")
        assert upd2.status_code == 200
        assert upd2.json()["estado_revision"] == "PENDIENTE"

        # Admin aprueba
        rev = _revisar_avance(api, admin_token, avance_id, "APROBADO")
        assert rev.status_code == 200
        assert rev.json()["estado_revision"] == "APROBADO"

        # No se puede editar ni eliminar aprobado
        assert (
            _editar_avance(
                api, gestor_token, avance_id, avance_porcentaje=80
            ).status_code
            == 403
        )
        assert _eliminar_avance(api, gestor_token, avance_id).status_code == 403

    def test_flujo_rechazado_eliminado(self, api, gestor_token, admin_token):
        avance = _crear_avance(api, gestor_token, estado_revision="PENDIENTE").json()
        _revisar_avance(api, admin_token, avance["id"], "RECHAZADO", "Falta soporte")
        resp = _eliminar_avance(api, gestor_token, avance["id"])
        assert resp.status_code == 200
        assert resp.json()["eliminado"] is True


class TestCasosBorde:
    """Casos de borde y validaciones adicionales."""

    def test_crear_avance_sin_avance_valor(self, api, gestor_token):
        resp = _crear_avance(api, gestor_token, avance_valor=None)
        assert resp.status_code == 201
        assert resp.json()["avance_valor"] == 0

    def test_crear_ignora_porcentaje_enviado_por_cliente(self, api, gestor_token):
        producto = _producto_gestor(api, gestor_token)
        meta = Decimal(str(producto["meta_cuatrienio"]))
        previo = _acumulado_reservado(api, gestor_token, producto["id"])

        resp = _crear_avance(
            api,
            gestor_token,
            producto_id=producto["id"],
            avance_porcentaje=100.0,
            avance_valor=100,
        )
        assert resp.status_code == 201
        assert resp.json()["avance_porcentaje"] == _porcentaje_esperado(
            previo + Decimal("100"), meta
        )

    def test_editar_avance_valor_cero_es_invalido(self, api, gestor_token):
        avance = _crear_avance(api, gestor_token).json()
        resp = _editar_avance(api, gestor_token, avance["id"], avance_valor=0)
        assert resp.status_code == 422

    def test_varios_avances_mismo_producto(self, api, gestor_token):
        productos = _mis_productos(api, gestor_token).json()
        producto_id = productos[0]["id"]
        for i in range(3):
            resp = _crear_avance(
                api,
                gestor_token,
                producto_id=producto_id,
                avance_porcentaje=float(i * 10 + 10),
            )
            assert resp.status_code == 201
        listado = _listar_avances(api, gestor_token, producto_id).json()
        assert len(listado) >= 3
