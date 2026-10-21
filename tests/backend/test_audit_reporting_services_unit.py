import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.backend.services import pdf_service
from src.backend.services.audit_admin_service import get_auditoria_stats, list_auditoria
from src.backend.services.audit_service import AuditService
from src.backend.services.pdf_service import InformePDF, generar_informe_gestion_pdf
from src.backend.services.reporte_service import (
    get_metricas_productos,
    get_resumen_general,
    get_resumen_por_dependencia,
    get_resumen_por_linea,
    get_resumen_por_programa,
)


class Result:
    def __init__(self, value=None, rows=None):
        self.value = value
        self.rows = rows or []

    def scalar_one(self):
        return self.value

    def scalars(self):
        return self

    def all(self):
        return self.rows

    def first(self):
        return self.rows[0] if self.rows else None


class FakeDB:
    def __init__(self, results=()):
        self.results = iter(results)
        self.added = []
        self.commit = AsyncMock()

    async def execute(self, statement):
        return next(self.results)

    def add(self, value):
        self.added.append(value)


@pytest.mark.unit
async def test_audit_admin_lists_filtered_events_and_resolves_actor():
    municipio_id = uuid.uuid4()
    usuario_id = uuid.uuid4()
    evento = SimpleNamespace(
        id=uuid.uuid4(),
        usuario_id=usuario_id,
        evento_tipo="LOGIN_OK",
        recurso_tipo="USUARIO",
        recurso_id=uuid.uuid4(),
        resultado="EXITOSO",
        ip_address="127.0.0.1",
        metadata_json='{"ok": true}',
        fecha_evento=datetime.now(UTC),
    )
    db = FakeDB([Result(value=1), Result(rows=[evento]), Result(rows=[("Ana", "ana")])])

    result = await list_auditoria(
        db,
        municipio_id,
        {
            "page": 0,
            "page_size": 999,
            "evento_tipo": "LOGIN_OK",
            "recurso_tipo": "USUARIO",
            "resultado": "EXITOSO",
            "usuario_id": str(usuario_id),
            "fecha_desde": datetime(2026, 1, 1, tzinfo=UTC),
            "fecha_hasta": datetime(2026, 12, 31, tzinfo=UTC),
        },
    )

    assert result["items"][0]["actor_nombre"] == "Ana (ana)"
    assert result["items"][0]["actor_id"] == str(usuario_id)
    assert result["page"] == 1
    assert result["page_size"] == 100
    assert result["total_pages"] == 1


@pytest.mark.unit
async def test_audit_admin_lists_anonymous_event_and_missing_actor():
    anonymous = SimpleNamespace(
        id=uuid.uuid4(),
        usuario_id=None,
        evento_tipo="PING",
        recurso_tipo=None,
        recurso_id=None,
        resultado="EXITOSO",
        ip_address=None,
        metadata_json=None,
        fecha_evento=datetime.now(UTC),
    )
    missing_actor = SimpleNamespace(
        **{**anonymous.__dict__, "id": uuid.uuid4(), "usuario_id": uuid.uuid4()}
    )
    db = FakeDB([Result(value=2), Result(rows=[anonymous, missing_actor]), Result(rows=[])])

    result = await list_auditoria(db, uuid.uuid4())

    assert [item["actor_nombre"] for item in result["items"]] == [None, None]
    assert result["items"][0]["recurso_id"] is None


@pytest.mark.unit
async def test_audit_admin_stats():
    db = FakeDB(
        [
            Result(value=10),
            Result(value=7),
            Result(value=3),
            Result(value=2),
            Result(rows=[("LOGIN", 6), ("UPDATE", 4)]),
        ]
    )

    result = await get_auditoria_stats(db, uuid.uuid4())

    assert result == {
        "total_eventos": 10,
        "exitosos": 7,
        "fallidos": 3,
        "hoy": 2,
        "por_tipo": {"LOGIN": 6, "UPDATE": 4},
    }


@pytest.mark.unit
async def test_audit_service_logs_and_queries_with_all_filters():
    db = FakeDB([Result(rows=["event-1", "event-2"])])
    service = AuditService(db)
    municipio_id = uuid.uuid4()
    usuario_id = uuid.uuid4()
    recurso_id = uuid.uuid4()

    event = await service.log_event(
        "UPDATE",
        "EXITOSO",
        municipio_id=municipio_id,
        usuario_id=usuario_id,
        actor_id=usuario_id,
        recurso_tipo="PRODUCTO",
        recurso_id=recurso_id,
        ip_address="127.0.0.1",
        user_agent="pytest",
        metadata={"field": "value"},
    )
    events = await service.get_events(
        municipio_id,
        limit=2,
        offset=1,
        usuario_id=usuario_id,
        evento_tipo="UPDATE",
        recurso_id=recurso_id,
        recurso_tipo="PRODUCTO",
    )

    assert db.added == [event]
    db.commit.assert_awaited_once()
    assert event.metadata_json == '{"field": "value"}'
    assert events == ["event-1", "event-2"]


@pytest.mark.unit
async def test_audit_service_accepts_empty_optional_values():
    db = FakeDB([Result(rows=[])])
    service = AuditService(db)

    event = await service.log_event("PING", "EXITOSO")
    events = await service.get_events(uuid.uuid4())

    assert event.metadata_json is None
    assert events == []


@pytest.mark.unit
async def test_reporte_resumen_general():
    db = FakeDB([Result(value=value) for value in (2, 3, 7, 5, 4)])

    result = await get_resumen_general(db, uuid.uuid4())

    assert result == {
        "total_lineas": 2,
        "total_programas": 3,
        "total_productos": 7,
        "productos_activos": 5,
        "productos_inactivos": 2,
        "total_gestores": 4,
    }


@pytest.mark.unit
async def test_reporte_resumen_por_linea():
    linea = SimpleNamespace(id=uuid.uuid4(), codigo="L1", nombre="Línea", estado="ACTIVO")
    db = FakeDB([Result(rows=[linea]), Result(value=2), Result(value=5)])

    result = await get_resumen_por_linea(db, uuid.uuid4())

    assert result == [
        {
            "id": str(linea.id),
            "codigo": "L1",
            "nombre": "Línea",
            "total_programas": 2,
            "total_productos": 5,
            "estado": "ACTIVO",
        }
    ]


@pytest.mark.unit
async def test_reporte_resumen_por_programa():
    programa = SimpleNamespace(
        id=uuid.uuid4(),
        codigo="PR1",
        nombre="Programa",
        sector="Salud",
        estado="ACTIVO",
    )
    db = FakeDB([Result(rows=[(programa, "Línea")]), Result(value=4), Result(value=3)])

    result = await get_resumen_por_programa(db, uuid.uuid4())

    assert result[0] == {
        "id": str(programa.id),
        "codigo": "PR1",
        "nombre": "Programa",
        "sector": "Salud",
        "linea_nombre": "Línea",
        "total_productos": 4,
        "productos_activos": 3,
        "estado": "ACTIVO",
    }


@pytest.mark.unit
async def test_reporte_resumen_por_dependencia_includes_only_nonempty():
    included = SimpleNamespace(id=uuid.uuid4(), codigo="D1", nombre="Planeación")
    excluded = SimpleNamespace(id=uuid.uuid4(), codigo="D2", nombre="Vacía")
    db = FakeDB(
        [
            Result(rows=[included, excluded]),
            Result(value=2),
            Result(value=1),
            Result(value=0),
            Result(value=0),
        ]
    )

    result = await get_resumen_por_dependencia(db, uuid.uuid4())

    assert result == [
        {
            "id": str(included.id),
            "codigo": "D1",
            "nombre": "Planeación",
            "total_productos": 2,
            "total_gestores": 1,
        }
    ]


@pytest.mark.unit
async def test_reporte_metricas_calculates_counts_and_capped_average():
    productos = [
        SimpleNamespace(
            codigo_indicador="I1",
            meta_cuatrienio=100,
            linea_base=120,
            gestor_lider_id=uuid.uuid4(),
        ),
        SimpleNamespace(
            codigo_indicador=None,
            meta_cuatrienio=100,
            linea_base=20,
            gestor_lider_id=None,
        ),
        SimpleNamespace(
            codigo_indicador="I3",
            meta_cuatrienio=None,
            linea_base=None,
            gestor_lider_id=None,
        ),
    ]
    db = FakeDB([Result(rows=productos)])

    result = await get_metricas_productos(db, uuid.uuid4())

    assert result["porcentaje_cumplimiento_indicador"] == 66.7
    assert result["porcentaje_cumplimiento_meta"] == 66.7
    assert result["promedio_avance"] == 60.0
    assert result["sin_gestor_asignado"] == 2


@pytest.mark.unit
async def test_reporte_metricas_handles_no_products():
    result = await get_metricas_productos(FakeDB([Result(rows=[])]), uuid.uuid4())

    assert result["total_productos"] == 0
    assert result["porcentaje_cumplimiento_indicador"] == 0
    assert result["porcentaje_cumplimiento_meta"] == 0
    assert result["promedio_avance"] == 0


def _pdf_data():
    return {
        "resumen": {
            "total_lineas": 1,
            "total_programas": 1,
            "total_productos": 1,
            "productos_activos": 1,
            "productos_inactivos": 0,
            "total_gestores": 1,
        },
        "lineas": [
            {
                "codigo": "L1",
                "nombre": "Línea estratégica",
                "total_programas": 1,
                "total_productos": 1,
                "estado": "ACTIVO",
            }
        ],
        "programas": [
            {
                "codigo": "P1",
                "nombre": "Programa",
                "sector": None,
                "total_productos": 1,
                "estado": "ACTIVO",
            }
        ],
        "dependencias": [
            {
                "codigo": "D1",
                "nombre": "Planeación",
                "total_productos": 1,
                "total_gestores": 1,
            }
        ],
        "metricas": {
            "con_indicador": 1,
            "total_productos": 1,
            "porcentaje_cumplimiento_indicador": 100,
            "con_meta_cuatrienio": 1,
            "porcentaje_cumplimiento_meta": 100,
            "con_gestor_asignado": 1,
            "promedio_avance": 50,
        },
        "cumplimiento": {
            "total_productos": 1,
            "con_meta_definida": 1,
            "sin_meta_definida": 0,
            "completados": 0,
            "en_progreso": 1,
            "sin_avance": 0,
            "porcentaje_cumplimiento_general": 50,
        },
        "cumplimiento_lineas": [
            {
                "codigo": "L1",
                "nombre": "Línea estratégica",
                "total_productos": 1,
                "completados": 0,
                "porcentaje_cumplimiento": 50,
            }
        ],
        "productos": [
            {
                "codigo": "PR1",
                "nombre": "Producto",
                "linea_base": None,
                "meta_cuatrienio": None,
                "porcentaje_avance": 0,
                "estado_cumplimiento": "SIN_META",
            }
        ],
    }


def _patch_pdf_sources(monkeypatch, data):
    names = (
        "get_resumen_general",
        "get_resumen_por_linea",
        "get_resumen_por_programa",
        "get_resumen_por_dependencia",
        "get_metricas_productos",
        "get_cumplimiento_general",
        "get_cumplimiento_por_linea",
        "get_listado_productos_cumplimiento",
    )
    values = tuple(data.values())
    for name, value in zip(names, values, strict=True):
        monkeypatch.setattr(pdf_service, name, AsyncMock(return_value=value))


@pytest.mark.unit
async def test_pdf_generates_real_document_with_all_sections(monkeypatch):
    _patch_pdf_sources(monkeypatch, _pdf_data())

    result = await generar_informe_gestion_pdf(object(), uuid.uuid4())

    assert bytes(result).startswith(b"%PDF")
    assert len(result) > 1000


@pytest.mark.unit
def test_pdf_component_helpers():
    pdf = InformePDF()
    pdf.add_page()
    pdf.section_title("Sección")
    pdf.subsection_title("Subsección")
    pdf.kpi_row("Indicador", 1)
    pdf.table_header(["A"], [20])
    pdf.table_row(["B"], [20], fill=True)

    assert bytes(pdf.output()).startswith(b"%PDF")


@pytest.mark.unit
async def test_pdf_encodes_legacy_string_output(monkeypatch):
    _patch_pdf_sources(monkeypatch, _pdf_data())
    monkeypatch.setattr(InformePDF, "output", lambda self: "%PDF-falso")

    result = await generar_informe_gestion_pdf(object(), uuid.uuid4())

    assert result == b"%PDF-falso"
