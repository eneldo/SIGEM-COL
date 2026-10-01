import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from src.backend.api.v1 import auditoria, catalogos, cumplimiento, reportes
from src.backend.api.v1.dashboard import admin, gestor


class ScalarResult:
    def __init__(self, values):
        self.values = values

    def scalars(self):
        return self

    def all(self):
        return self.values


class GestorResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


@pytest.fixture
def identity():
    return {
        "user": SimpleNamespace(id=uuid.uuid4()),
        "municipio_id": str(uuid.uuid4()),
        "roles": ["ADMINISTRADOR_MUNICIPAL"],
    }


@pytest.mark.unit
async def test_admin_permission_requires_user_and_delegates(monkeypatch, identity):
    required = AsyncMock()
    monkeypatch.setattr(admin, "require_permission", required)

    with pytest.raises(HTTPException) as exc_info:
        await admin._require_permission(object(), {}, "permiso")

    assert exc_info.value.status_code == 401
    db = object()
    await admin._require_permission(db, identity, "permiso")
    required.assert_awaited_once_with(db, identity["user"].id, "permiso")


@pytest.mark.unit
@pytest.mark.parametrize(
    ("route_name", "service_name", "service_result", "expected"),
    [
        ("kpis_generales", "get_kpis_generales", {"total": 2}, {"total": 2}),
        ("resumen_plan", "get_resumen_plan", {"plan": "activo"}, {"plan": "activo"}),
        (
            "gestores_summary",
            "get_gestores_summary",
            [{"id": "1"}],
            {"gestores": [{"id": "1"}], "total": 1},
        ),
        (
            "alertas_seguridad",
            "get_alertas",
            ["alerta"],
            {"alertas": ["alerta"], "total": 1},
        ),
        (
            "estadisticas_dependencia",
            "get_estadisticas_por_dependencia",
            ["dato"],
            {"dependencias": ["dato"], "total": 1},
        ),
    ],
)
async def test_admin_routes_success(
    monkeypatch, identity, route_name, service_name, service_result, expected
):
    permission = AsyncMock()
    service = AsyncMock(return_value=service_result)
    monkeypatch.setattr(admin, "_require_permission", permission)
    monkeypatch.setattr(admin, service_name, service)
    db = object()

    result = await getattr(admin, route_name)(current_user=identity, db=db)

    assert result == expected
    permission.assert_awaited_once_with(db, identity, "dashboard.admin.ver")
    service.assert_awaited_once_with(
        db=db, municipio_id=uuid.UUID(identity["municipio_id"])
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    ("route_name", "service_name", "detail"),
    [
        ("kpis_generales", "get_kpis_generales", "Error al obtener los KPIs generales"),
        (
            "resumen_plan",
            "get_resumen_plan",
            "Error al obtener el resumen del plan de desarrollo",
        ),
        (
            "gestores_summary",
            "get_gestores_summary",
            "Error al obtener el resumen de gestores",
        ),
        (
            "alertas_seguridad",
            "get_alertas",
            "Error al obtener las alertas de seguridad",
        ),
        (
            "estadisticas_dependencia",
            "get_estadisticas_por_dependencia",
            "Error al obtener las estadísticas por dependencia",
        ),
    ],
)
async def test_admin_routes_convert_service_errors(
    monkeypatch, identity, route_name, service_name, detail
):
    monkeypatch.setattr(admin, "_require_permission", AsyncMock())
    monkeypatch.setattr(
        admin, service_name, AsyncMock(side_effect=RuntimeError("database"))
    )

    with pytest.raises(HTTPException) as exc_info:
        await getattr(admin, route_name)(current_user=identity, db=object())

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == detail
    assert isinstance(exc_info.value.__cause__, RuntimeError)


@pytest.mark.unit
async def test_admin_resumen_plan_not_found(monkeypatch, identity):
    monkeypatch.setattr(admin, "_require_permission", AsyncMock())
    monkeypatch.setattr(admin, "get_resumen_plan", AsyncMock(return_value=None))

    with pytest.raises(HTTPException) as exc_info:
        await admin.resumen_plan(current_user=identity, db=object())

    assert exc_info.value.status_code == 404


@pytest.mark.unit
async def test_gestor_helpers(monkeypatch, identity):
    required = AsyncMock()
    monkeypatch.setattr(gestor, "require_permission", required)

    with pytest.raises(HTTPException) as exc_info:
        await gestor._require_permission(object(), {}, "permiso")
    assert exc_info.value.status_code == 401

    db = AsyncMock()
    gestor_id = uuid.uuid4()
    db.execute.return_value = GestorResult(SimpleNamespace(id=gestor_id))
    await gestor._require_permission(db, identity, "permiso")
    assert (
        await gestor._get_gestor_id(db, identity["user"].id, uuid.uuid4()) == gestor_id
    )
    required.assert_awaited_once_with(db, identity["user"].id, "permiso")

    db.execute.return_value = GestorResult(None)
    with pytest.raises(HTTPException) as missing:
        await gestor._get_gestor_id(db, identity["user"].id, uuid.uuid4())
    assert missing.value.status_code == 404


@pytest.mark.unit
@pytest.mark.parametrize(
    ("route_name", "service_name", "service_result", "expected"),
    [
        ("kpis_personales", "get_kpis_personales", {"total": 1}, {"total": 1}),
        (
            "mis_productos",
            "get_mis_productos",
            ["producto"],
            {"productos": ["producto"], "total": 1},
        ),
        (
            "mis_pendientes",
            "get_mis_pendientes",
            ["pendiente"],
            {"pendientes": ["pendiente"], "total": 1},
        ),
        (
            "mis_alertas",
            "get_mis_alertas",
            ["alerta"],
            {"alertas": ["alerta"], "total": 1},
        ),
    ],
)
async def test_gestor_routes_success(
    monkeypatch, identity, route_name, service_name, service_result, expected
):
    gestor_id = uuid.uuid4()
    permission = AsyncMock()
    lookup = AsyncMock(return_value=gestor_id)
    service = AsyncMock(return_value=service_result)
    monkeypatch.setattr(gestor, "_require_permission", permission)
    monkeypatch.setattr(gestor, "_get_gestor_id", lookup)
    monkeypatch.setattr(gestor, service_name, service)
    db = object()

    result = await getattr(gestor, route_name)(current_user=identity, db=db)

    assert result == expected
    municipio_id = uuid.UUID(identity["municipio_id"])
    permission.assert_awaited_once_with(db, identity, "dashboard.gestor.ver")
    lookup.assert_awaited_once_with(db, identity["user"].id, municipio_id)
    service.assert_awaited_once_with(
        db=db, municipio_id=municipio_id, gestor_id=gestor_id
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    ("route_name", "service_name", "detail"),
    [
        (
            "kpis_personales",
            "get_kpis_personales",
            "Error al obtener los KPIs personales",
        ),
        (
            "mis_productos",
            "get_mis_productos",
            "Error al obtener los productos asignados",
        ),
        (
            "mis_pendientes",
            "get_mis_pendientes",
            "Error al obtener los productos pendientes",
        ),
        ("mis_alertas", "get_mis_alertas", "Error al obtener las alertas personales"),
    ],
)
async def test_gestor_routes_convert_service_errors(
    monkeypatch, identity, route_name, service_name, detail
):
    monkeypatch.setattr(gestor, "_require_permission", AsyncMock())
    monkeypatch.setattr(gestor, "_get_gestor_id", AsyncMock(return_value=uuid.uuid4()))
    monkeypatch.setattr(
        gestor, service_name, AsyncMock(side_effect=RuntimeError("database"))
    )

    with pytest.raises(HTTPException) as exc_info:
        await getattr(gestor, route_name)(current_user=identity, db=object())

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == detail
    assert isinstance(exc_info.value.__cause__, RuntimeError)


@pytest.mark.unit
async def test_auditoria_routes_success_and_filters(monkeypatch, identity):
    permission = AsyncMock()
    listing = AsyncMock(
        return_value={"items": [], "total": 0, "page": 2, "page_size": 5}
    )
    stats = AsyncMock(
        return_value={
            "total_eventos": 3,
            "exitosos": 2,
            "fallidos": 1,
            "hoy": 1,
            "por_tipo": {},
        }
    )
    monkeypatch.setattr(auditoria, "require_permission", permission)
    monkeypatch.setattr(auditoria.audit_admin_service, "list_auditoria", listing)
    monkeypatch.setattr(auditoria.audit_admin_service, "get_auditoria_stats", stats)
    db = object()

    response = await auditoria.listar_auditoria(
        evento_tipo="LOGIN",
        recurso_tipo="USUARIO",
        resultado="EXITOSO",
        usuario_id=str(uuid.uuid4()),
        fecha_desde="2026-01-01",
        fecha_hasta="2026-12-31",
        page=2,
        page_size=5,
        current_user=identity,
        db=db,
    )
    stats_response = await auditoria.estadisticas_auditoria(
        current_user=identity, db=db
    )

    assert response.page == 2
    assert listing.await_args.args[2] == {
        "page": 2,
        "page_size": 5,
        "evento_tipo": "LOGIN",
        "recurso_tipo": "USUARIO",
        "resultado": "EXITOSO",
        "usuario_id": listing.await_args.args[2]["usuario_id"],
        "fecha_desde": "2026-01-01",
        "fecha_hasta": "2026-12-31",
    }
    assert stats_response.total_eventos == 3
    assert permission.await_count == 2


@pytest.mark.unit
async def test_auditoria_empty_filters_and_exception(monkeypatch, identity):
    listing = AsyncMock(
        return_value={"items": [], "total": 0, "page": 1, "page_size": 20}
    )
    monkeypatch.setattr(auditoria, "require_permission", AsyncMock())
    monkeypatch.setattr(auditoria.audit_admin_service, "list_auditoria", listing)

    await auditoria.listar_auditoria(current_user=identity, db=object())
    assert listing.await_args.args[2] == {"page": 1, "page_size": 20}

    monkeypatch.setattr(
        auditoria.audit_admin_service,
        "get_auditoria_stats",
        AsyncMock(side_effect=RuntimeError("database")),
    )
    with pytest.raises(RuntimeError, match="database"):
        await auditoria.estadisticas_auditoria(current_user=identity, db=object())


@pytest.mark.unit
async def test_catalogos_roles_success_and_exception(identity):
    role = SimpleNamespace(id=uuid.uuid4(), codigo="ADMIN", nombre="Admin", nivel=1)
    db = AsyncMock()
    db.execute.return_value = ScalarResult([role])

    result = await catalogos.list_roles(current_user=identity, db=db)
    assert result[0].codigo == "ADMIN"

    db.execute.side_effect = RuntimeError("database")
    with pytest.raises(RuntimeError, match="database"):
        await catalogos.list_roles(current_user=identity, db=db)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("roles", "search", "include_eliminadas"),
    [(["ADMINISTRADOR_MUNICIPAL"], None, False), ([], "planeación", True)],
)
async def test_catalogos_dependencias_all_query_paths(
    identity, roles, search, include_eliminadas
):
    dependency = SimpleNamespace(
        id=uuid.uuid4(), codigo="D1", nombre="Planeación", descripcion=None
    )
    db = AsyncMock()
    db.execute.return_value = ScalarResult([dependency])
    current_user = {**identity, "roles": roles}

    result = await catalogos.list_dependencias(
        search=search,
        include_eliminadas=include_eliminadas,
        current_user=current_user,
        db=db,
    )

    assert result[0].id == dependency.id
    assert result[0].nombre == "Planeación"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("route_name", "service_name"),
    [
        ("cumplimiento_general", "get_cumplimiento_general"),
        ("cumplimiento_por_linea", "get_cumplimiento_por_linea"),
        ("cumplimiento_por_programa", "get_cumplimiento_por_programa"),
        ("listado_productos", "get_listado_productos_cumplimiento"),
    ],
)
async def test_cumplimiento_passthrough_success_and_exception(
    monkeypatch, identity, route_name, service_name
):
    service = AsyncMock(return_value={"ok": True})
    monkeypatch.setattr(cumplimiento, service_name, service)
    db = object()

    assert await getattr(cumplimiento, route_name)(db=db, current_user=identity) == {
        "ok": True
    }
    service.assert_awaited_once_with(db, identity["municipio_id"])

    service.side_effect = RuntimeError("database")
    with pytest.raises(RuntimeError, match="database"):
        await getattr(cumplimiento, route_name)(db=db, current_user=identity)


@pytest.mark.unit
async def test_cumplimiento_detalle_success_not_found_and_invalid_uuid(
    monkeypatch, identity
):
    product_id = uuid.uuid4()
    service = AsyncMock(return_value={"id": str(product_id)})
    monkeypatch.setattr(cumplimiento, "get_detalle_producto", service)

    result = await cumplimiento.detalle_producto(
        str(product_id), db=object(), current_user=identity
    )
    assert result == {"id": str(product_id)}

    service.return_value = None
    with pytest.raises(HTTPException) as missing:
        await cumplimiento.detalle_producto(
            str(product_id), db=object(), current_user=identity
        )
    assert missing.value.status_code == 404

    with pytest.raises(ValueError):
        await cumplimiento.detalle_producto(
            "invalid", db=object(), current_user=identity
        )


@pytest.mark.unit
@pytest.mark.parametrize(
    ("route_name", "service_name"),
    [
        ("resumen_general", "get_resumen_general"),
        ("resumen_por_linea", "get_resumen_por_linea"),
        ("resumen_por_programa", "get_resumen_por_programa"),
        ("resumen_por_dependencia", "get_resumen_por_dependencia"),
        ("metricas_productos", "get_metricas_productos"),
    ],
)
async def test_reportes_passthrough_success_and_exception(
    monkeypatch, identity, route_name, service_name
):
    service = AsyncMock(return_value={"ok": True})
    monkeypatch.setattr(reportes, service_name, service)
    db = object()

    assert await getattr(reportes, route_name)(db=db, current_user=identity) == {
        "ok": True
    }
    service.assert_awaited_once_with(db, identity["municipio_id"])

    service.side_effect = RuntimeError("database")
    with pytest.raises(RuntimeError, match="database"):
        await getattr(reportes, route_name)(db=db, current_user=identity)


@pytest.mark.unit
async def test_reporte_pdf_success_and_exception(monkeypatch, identity):
    service = AsyncMock(return_value=b"%PDF-test")
    monkeypatch.setattr(reportes, "generar_informe_gestion_pdf", service)
    db = object()

    response = await reportes.informe_pdf(db=db, current_user=identity)
    body = b"".join([chunk async for chunk in response.body_iterator])

    assert body == b"%PDF-test"
    assert response.media_type == "application/pdf"
    assert response.headers["content-disposition"] == (
        "attachment; filename=informe_gestion_sigem.pdf"
    )
    service.assert_awaited_once_with(db, identity["municipio_id"])

    service.side_effect = RuntimeError("pdf")
    with pytest.raises(RuntimeError, match="pdf"):
        await reportes.informe_pdf(db=db, current_user=identity)
