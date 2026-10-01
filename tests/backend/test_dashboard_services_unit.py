"""Pruebas unitarias de los servicios de dashboard."""

import uuid
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.backend.services import dashboard_admin_service as admin_service
from src.backend.services import dashboard_gestor_service as gestor_service


class ResultFake:
    def __init__(self, *, scalar=None, rows=None):
        self.scalar = scalar
        self.rows = rows or []

    def scalar_one(self):
        return self.scalar

    def scalar_one_or_none(self):
        return self.scalar

    def scalars(self):
        return self

    def all(self):
        return self.rows

    def first(self):
        return self.rows[0] if self.rows else None


def database(*results):
    return SimpleNamespace(execute=AsyncMock(side_effect=results))


def entity(**values):
    return SimpleNamespace(**values)


@pytest.mark.asyncio
async def test_admin_kpis_generales():
    db = database(*(ResultFake(scalar=value) for value in range(1, 9)))

    result = await admin_service.get_kpis_generales(db, uuid.uuid4())

    assert result == {
        "total_gestores": 1,
        "gestores_activos": 2,
        "gestores_inactivos": 3,
        "gestores_bloqueados": 4,
        "total_lineas_estrategicas": 5,
        "total_programas": 6,
        "total_productos": 7,
        "total_dependencias": 8,
    }
    assert db.execute.await_count == 8


@pytest.mark.asyncio
async def test_admin_resumen_plan_vacio():
    db = database(ResultFake())

    assert await admin_service.get_resumen_plan(db, uuid.uuid4()) is None


@pytest.mark.asyncio
async def test_admin_resumen_plan_poblado():
    plan_id = uuid.uuid4()
    linea_id = uuid.uuid4()
    plan = entity(
        id=plan_id,
        codigo="P-1",
        nombre="Plan",
        descripcion="Descripción",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2027, 12, 31),
        vigencias=[2024, 2025, 2026, 2027],
        estado="ACTIVO",
    )
    linea = entity(id=linea_id, codigo="L-1", nombre="Línea", orden=1)
    db = database(
        ResultFake(scalar=plan),
        ResultFake(scalar=1),
        ResultFake(scalar=2),
        ResultFake(scalar=3),
        ResultFake(rows=[linea]),
        ResultFake(scalar=2),
        ResultFake(scalar=3),
    )

    result = await admin_service.get_resumen_plan(db, uuid.uuid4())

    assert result["plan"]["id"] == str(plan_id)
    assert result["plan"]["vigencias"] == [2024, 2025, 2026, 2027]
    assert result["lineas_desglose"] == [
        {
            "id": str(linea_id),
            "codigo": "L-1",
            "nombre": "Línea",
            "orden": 1,
            "total_programas": 2,
            "total_productos": 3,
        }
    ]


@pytest.mark.asyncio
async def test_admin_gestores_summary_vacio_y_poblado():
    assert (
        await admin_service.get_gestores_summary(database(ResultFake()), uuid.uuid4())
        == []
    )

    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    ultimo_acceso = datetime(2026, 2, 1, tzinfo=UTC)
    gestor_uno = entity(
        id=uuid.uuid4(),
        codigo="G-1",
        nombre_completo="Ana Uno",
        cargo="Líder",
        estado="ACTIVO",
        created_at=created_at,
    )
    gestor_dos = entity(
        id=uuid.uuid4(),
        codigo="G-2",
        nombre_completo="Ana Dos",
        cargo="Líder",
        estado="INACTIVO",
        created_at=created_at,
    )
    usuario_uno = entity(
        id=uuid.uuid4(),
        ultimo_acceso=ultimo_acceso,
        intentos_fallidos=1,
        mfa_activo=True,
    )
    usuario_dos = entity(
        id=uuid.uuid4(), ultimo_acceso=None, intentos_fallidos=0, mfa_activo=False
    )
    db = database(
        ResultFake(rows=[(gestor_uno, usuario_uno), (gestor_dos, usuario_dos)]),
        ResultFake(scalar=4),
        ResultFake(scalar=0),
    )

    result = await admin_service.get_gestores_summary(db, uuid.uuid4())

    assert result[0]["ultimo_acceso"] == ultimo_acceso.isoformat()
    assert result[0]["total_productos_asignados"] == 4
    assert result[1]["ultimo_acceso"] is None


@pytest.mark.asyncio
async def test_admin_alertas_vacias():
    db = database(ResultFake(), ResultFake(), ResultFake())

    assert await admin_service.get_alertas(db, uuid.uuid4()) == []


@pytest.mark.asyncio
async def test_admin_alertas_pobladas_cubren_campos_opcionales():
    acceso = datetime.now(UTC) - timedelta(days=45)
    bloqueo = datetime(2026, 1, 2, tzinfo=UTC)
    gestores = [
        entity(id=uuid.uuid4(), codigo="G-1", nombre_completo="Uno"),
        entity(id=uuid.uuid4(), codigo="G-2", nombre_completo="Dos"),
    ]
    usuarios = [
        entity(
            intentos_fallidos=4,
            motivo_bloqueo="Riesgo",
            fecha_bloqueo=bloqueo,
            ultimo_acceso=acceso,
        ),
        entity(
            intentos_fallidos=5,
            motivo_bloqueo=None,
            fecha_bloqueo=None,
            ultimo_acceso=None,
        ),
    ]
    rows = list(zip(gestores, usuarios, strict=True))
    db = database(ResultFake(rows=rows), ResultFake(rows=rows), ResultFake(rows=rows))

    result = await admin_service.get_alertas(db, uuid.uuid4())

    assert [alerta["tipo"] for alerta in result] == [
        "intentos_fallidos",
        "intentos_fallidos",
        "bloqueado",
        "bloqueado",
        "sin_acceso",
        "sin_acceso",
    ]
    assert result[2]["fecha_bloqueo"] == bloqueo.isoformat()
    assert result[3]["fecha_bloqueo"] is None
    assert result[4]["dias_inactividad"] >= 45
    assert result[5]["ultimo_acceso"] is None


@pytest.mark.asyncio
async def test_admin_estadisticas_dependencia_vacias_y_pobladas():
    municipio_id = uuid.uuid4()
    assert (
        await admin_service.get_estadisticas_por_dependencia(
            database(ResultFake()), municipio_id
        )
        == []
    )

    dependencia = entity(id=uuid.uuid4(), codigo="D-1", nombre="Hacienda", nivel=2)
    db = database(
        ResultFake(rows=[dependencia]), ResultFake(scalar=7), ResultFake(scalar=3)
    )

    result = await admin_service.get_estadisticas_por_dependencia(db, municipio_id)

    assert result == [
        {
            "dependencia_id": str(dependencia.id),
            "dependencia_codigo": "D-1",
            "dependencia_nombre": "Hacienda",
            "nivel": 2,
            "total_productos": 7,
            "total_gestores": 3,
        }
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "gestor,total_dependencias", [(None, 0), (entity(usuario_id=uuid.uuid4()), 5)]
)
async def test_gestor_kpis_personales(gestor, total_dependencias):
    results = [ResultFake(scalar=8), ResultFake(scalar=gestor)]
    if gestor:
        results.append(ResultFake(scalar=total_dependencias))
    results.append(ResultFake(scalar=2))
    db = database(*results)

    result = await gestor_service.get_kpis_personales(db, uuid.uuid4(), uuid.uuid4())

    assert result == {
        "total_productos_asignados": 8,
        "total_dependencias_asignadas": total_dependencias,
        "total_lineas_estrategicas": 2,
    }


def producto(updated_at):
    return entity(
        id=uuid.uuid4(),
        codigo="PR-1",
        nombre="Producto",
        descripcion="Descripción",
        unidad_medida="Número",
        estado="ACTIVO",
        updated_at=updated_at,
    )


def programa():
    return entity(id=uuid.uuid4(), codigo="PG-1", nombre="Programa")


@pytest.mark.asyncio
async def test_gestor_mis_productos_vacios_y_con_dependencia_opcional():
    ids = (uuid.uuid4(), uuid.uuid4())
    assert await gestor_service.get_mis_productos(database(ResultFake()), *ids) == []

    actualizado = datetime(2026, 3, 1, tzinfo=UTC)
    dependencia = entity(id=uuid.uuid4(), codigo="D-1", nombre="Hacienda")
    db = database(
        ResultFake(
            rows=[
                (producto(actualizado), programa(), dependencia),
                (producto(actualizado), programa(), None),
            ]
        )
    )

    result = await gestor_service.get_mis_productos(db, *ids)

    assert result[0]["dependencia_responsable"]["codigo"] == "D-1"
    assert result[0]["updated_at"] == actualizado.isoformat()
    assert result[1]["dependencia_responsable"] is None


@pytest.mark.asyncio
async def test_gestor_mis_pendientes_vacios_y_con_fechas_opcionales():
    ids = (uuid.uuid4(), uuid.uuid4())
    assert await gestor_service.get_mis_pendientes(database(ResultFake()), *ids) == []

    actualizado = datetime.now(UTC) - timedelta(days=20)
    dependencia = entity(id=uuid.uuid4(), codigo="D-1", nombre="Hacienda")
    db = database(
        ResultFake(
            rows=[
                (producto(actualizado), programa(), dependencia),
                (producto(None), programa(), None),
            ]
        )
    )

    result = await gestor_service.get_mis_pendientes(db, *ids)

    assert result[0]["dias_sin_actualizacion"] >= 20
    assert result[0]["dependencia_responsable"]["nombre"] == "Hacienda"
    assert result[1]["dias_sin_actualizacion"] is None
    assert result[1]["updated_at"] is None
    assert result[1]["dependencia_responsable"] is None


@pytest.mark.asyncio
async def test_gestor_mis_alertas_sin_gestor():
    result = await gestor_service.get_mis_alertas(
        database(ResultFake()), uuid.uuid4(), uuid.uuid4()
    )

    assert result == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("intentos", "estado", "motivo", "fecha", "severidad", "fragmento"),
    [
        (1, "ACTIVO", None, None, "MEDIA", None),
        (3, "BLOQUEADO", "Riesgo", datetime(2026, 1, 2, tzinfo=UTC), "ALTA", "Riesgo"),
        (0, "BLOQUEADO", None, None, None, "Contacte al administrador"),
    ],
)
async def test_gestor_mis_alertas_todas_las_ramas(
    intentos, estado, motivo, fecha, severidad, fragmento
):
    gestor = entity(estado=estado)
    usuario = entity(
        intentos_fallidos=intentos,
        must_change_password=True,
        mfa_activo=False,
        motivo_bloqueo=motivo,
        fecha_bloqueo=fecha,
    )

    result = await gestor_service.get_mis_alertas(
        database(ResultFake(rows=[(gestor, usuario)])), uuid.uuid4(), uuid.uuid4()
    )

    tipos = [alerta["tipo"] for alerta in result]
    assert "password_pendiente" in tipos
    assert "mfa_desactivado" in tipos
    if severidad:
        assert result[0]["severidad"] == severidad
    if estado == "BLOQUEADO":
        bloqueo = next(
            alerta for alerta in result if alerta["tipo"] == "cuenta_bloqueada"
        )
        assert bloqueo["fecha_bloqueo"] == (fecha.isoformat() if fecha else None)
        assert fragmento in bloqueo["mensaje"]


@pytest.mark.asyncio
async def test_gestor_mis_alertas_sin_condiciones_activas():
    gestor = entity(estado="ACTIVO")
    usuario = entity(
        intentos_fallidos=0,
        must_change_password=False,
        mfa_activo=True,
        motivo_bloqueo=None,
        fecha_bloqueo=None,
    )

    result = await gestor_service.get_mis_alertas(
        database(ResultFake(rows=[(gestor, usuario)])), uuid.uuid4(), uuid.uuid4()
    )

    assert result == []
