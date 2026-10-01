"""Pruebas unitarias exhaustivas del servicio de avances."""

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.backend.services import avance_service as service


class ResultFake:
    def __init__(self, rows=None):
        self.rows = rows or []

    def scalars(self):
        return self

    def all(self):
        return self.rows


def db_mock(*, scalars=(), executes=()):
    return SimpleNamespace(
        scalar=AsyncMock(side_effect=scalars),
        execute=AsyncMock(side_effect=executes),
        add=Mock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
        refresh=AsyncMock(),
        rollback=AsyncMock(),
    )


def entity(**overrides):
    values = {
        "id": uuid.uuid4(),
        "municipio_id": uuid.uuid4(),
        "producto_id": uuid.uuid4(),
        "gestor_lider_id": uuid.uuid4(),
        "registrado_por": uuid.uuid4(),
        "codigo": "PR-01",
        "nombre": "Producto",
        "indicador": "Indicador",
        "codigo_indicador": "IND-01",
        "meta_redactada": "Meta",
        "linea_base": 1,
        "meta_cuatrienio": 100,
        "unidad_medida": "Porcentaje",
        "estado": "REGISTRADO",
        "avance_porcentaje": 50.0,
        "avance_valor": 10,
        "observaciones": "Observación",
        "evidencia_url": None,
        "periodo": "2026-Q1",
        "fecha_registro": datetime(2026, 1, 1, tzinfo=UTC),
        "estado_revision": "PENDIENTE",
        "evidencia_nombre": None,
        "evidencia_tipo": None,
        "observaciones_revision": None,
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
        "updated_at": datetime(2026, 1, 1, tzinfo=UTC),
        "soft_delete": Mock(),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.fixture
def ids():
    return SimpleNamespace(
        usuario=uuid.uuid4(),
        municipio=uuid.uuid4(),
        avance=uuid.uuid4(),
        producto=uuid.uuid4(),
    )


@pytest.mark.asyncio
async def test_get_mis_productos_sin_gestor(ids):
    assert (
        await service.get_mis_productos(
            db_mock(scalars=[None]), ids.usuario, ids.municipio
        )
        == []
    )


@pytest.mark.asyncio
async def test_get_mis_productos_serializa_resultados(ids):
    producto = entity()
    db = db_mock(scalars=[uuid.uuid4()], executes=[ResultFake([producto])])
    result = await service.get_mis_productos(db, ids.usuario, ids.municipio)
    assert result == [
        {
            "id": str(producto.id),
            "codigo": "PR-01",
            "nombre": "Producto",
            "indicador": "Indicador",
            "codigo_indicador": "IND-01",
            "meta_redactada": "Meta",
            "linea_base": 1,
            "meta_cuatrienio": 100,
            "unidad_medida": "Porcentaje",
            "estado": "REGISTRADO",
        }
    ]


@pytest.mark.asyncio
async def test_get_avances_producto_serializa_fechas_opcionales(ids):
    completos = entity()
    vacios = entity(fecha_registro=None, created_at=None)
    result = await service.get_avances_producto(
        db_mock(executes=[ResultFake([completos, vacios])]), ids.producto, ids.municipio
    )
    assert result[0]["fecha_registro"] == completos.fecha_registro.isoformat()
    assert result[1]["fecha_registro"] is None
    assert result[1]["created_at"] is None


@pytest.mark.asyncio
async def test_registrar_avance_errores(ids):
    with pytest.raises(ValueError, match="gestor líder"):
        await service.registrar_avance(
            db_mock(scalars=[None]), ids.usuario, ids.municipio, ids.producto, {}
        )
    with pytest.raises(ValueError, match="producto"):
        await service.registrar_avance(
            db_mock(scalars=[uuid.uuid4(), None]),
            ids.usuario,
            ids.municipio,
            ids.producto,
            {},
        )


@pytest.mark.asyncio
async def test_registrar_avance_exitoso(ids):
    gestor_id = uuid.uuid4()
    db = db_mock(scalars=[gestor_id, entity()])

    async def refresh(avance):
        avance.id = ids.avance

    db.refresh.side_effect = refresh
    audit = SimpleNamespace(log_event=AsyncMock())
    data = {
        "avance_porcentaje": 25.0,
        "avance_valor": 5,
        "observaciones": "Bien",
        "evidencia_url": "ruta",
        "indicador": "Otro",
        "periodo": "Q2",
        "estado_revision": "BORRADOR",
        "evidencia_nombre": "a.pdf",
        "evidencia_tipo": "application/pdf",
    }
    with patch.object(service, "AuditService", return_value=audit):
        result = await service.registrar_avance(
            db, ids.usuario, ids.municipio, ids.producto, data
        )
    assert result["id"] == str(ids.avance)
    assert result["avance_porcentaje"] == 25.0
    assert result["estado_revision"] == "BORRADOR"
    db.add.assert_called_once()
    db.commit.assert_awaited_once()
    audit.log_event.assert_awaited_once()


@pytest.mark.asyncio
async def test_registrar_avance_valores_predeterminados(ids):
    db = db_mock(scalars=[uuid.uuid4(), entity()])

    async def refresh(avance):
        avance.id = ids.avance
        avance.observaciones_revision = None

    db.refresh.side_effect = refresh
    with patch.object(
        service, "AuditService", return_value=SimpleNamespace(log_event=AsyncMock())
    ):
        result = await service.registrar_avance(
            db, ids.usuario, ids.municipio, ids.producto, {}
        )
    assert result["avance_porcentaje"] == 0.0
    assert result["estado_revision"] == "PENDIENTE"


@pytest.mark.asyncio
async def test_actualizar_avance_exitoso(ids):
    avance = entity(registrado_por=ids.usuario, fecha_registro=None, created_at=None)
    db = db_mock()
    audit = SimpleNamespace(log_event=AsyncMock())
    with (
        patch.object(service, "_get_avance_or_404", AsyncMock(return_value=avance)),
        patch.object(service, "_check_evidence_permission", AsyncMock()),
        patch.object(service, "AuditService", return_value=audit),
    ):
        result = await service.actualizar_avance(
            db,
            ids.avance,
            ids.municipio,
            ids.usuario,
            {"avance_porcentaje": 80.0, "observaciones": None, "ignorado": "x"},
        )
    assert result["avance_porcentaje"] == 80.0
    assert result["fecha_registro"] is None
    assert result["created_at"] is None
    assert audit.log_event.await_args.kwargs["metadata"]["campos"] == [
        "avance_porcentaje"
    ]


@pytest.mark.asyncio
async def test_actualizar_avance_rechaza_aprobado_y_sin_cambios(ids):
    for avance, data, message in [
        (entity(estado_revision="APROBADO"), {"periodo": "Q2"}, "aprobado"),
        (entity(), {"observaciones": None}, "campos"),
    ]:
        with (
            patch.object(service, "_get_avance_or_404", AsyncMock(return_value=avance)),
            patch.object(service, "_check_evidence_permission", AsyncMock()),
            pytest.raises((PermissionError, ValueError), match=message),
        ):
            await service.actualizar_avance(
                db_mock(), ids.avance, ids.municipio, ids.usuario, data
            )


@pytest.mark.asyncio
async def test_eliminar_avance_exitoso_con_evidencias(ids):
    avance = entity(registrado_por=ids.usuario)
    evidencias = [entity(), entity()]
    db = db_mock(executes=[ResultFake(evidencias)])
    audit = SimpleNamespace(log_event=AsyncMock())
    with (
        patch.object(service, "_get_avance_or_404", AsyncMock(return_value=avance)),
        patch.object(service, "_check_evidence_permission", AsyncMock()),
        patch.object(service, "AuditService", return_value=audit),
    ):
        result = await service.eliminar_avance(
            db, ids.avance, ids.municipio, ids.usuario
        )
    assert result == {"id": str(avance.id), "eliminado": True}
    assert all(ev.soft_delete.called for ev in evidencias)
    avance.soft_delete.assert_called_once_with(ids.usuario)


@pytest.mark.asyncio
async def test_eliminar_avance_aprobado(ids):
    with (
        patch.object(
            service,
            "_get_avance_or_404",
            AsyncMock(return_value=entity(estado_revision="APROBADO")),
        ),
        patch.object(service, "_check_evidence_permission", AsyncMock()),
        pytest.raises(PermissionError, match="aprobado"),
    ):
        await service.eliminar_avance(db_mock(), ids.avance, ids.municipio, ids.usuario)


@pytest.mark.asyncio
async def test_resumen_sin_gestor(ids):
    result = await service.get_resumen_avances(
        db_mock(scalars=[None]), ids.usuario, ids.municipio
    )
    assert result == {
        "total_productos": 0,
        "productos_con_avance": 0,
        "avance_promedio": 0.0,
        "productos_completados": 0,
    }


@pytest.mark.asyncio
async def test_resumen_con_y_sin_avances(ids):
    productos = [entity(), entity(), entity()]
    gestor = uuid.uuid4()
    db = db_mock(
        scalars=[gestor],
        executes=[
            ResultFake(productos),
            ResultFake([(productos[0].id, 50.0), (productos[1].id, 100.0)]),
        ],
    )
    assert await service.get_resumen_avances(db, ids.usuario, ids.municipio) == {
        "total_productos": 3,
        "productos_con_avance": 2,
        "avance_promedio": 75.0,
        "productos_completados": 1,
    }
    empty = db_mock(scalars=[gestor], executes=[ResultFake(productos), ResultFake([])])
    assert (await service.get_resumen_avances(empty, ids.usuario, ids.municipio))[
        "avance_promedio"
    ] == 0.0


@pytest.mark.asyncio
async def test_avances_para_revision_filtros_y_serializacion(ids):
    avance = entity(indicador=None, fecha_registro=None, created_at=None)
    gestor = entity(codigo="GES-1", nombre_completo="Gestora")
    producto = entity(indicador="Indicador producto")
    db = db_mock(executes=[ResultFake([(avance, gestor, producto)])])
    result = await service.get_avances_para_revision(
        db, ids.municipio, gestor.id, "PENDIENTE", "texto"
    )
    assert result[0]["indicador"] == "Indicador producto"
    assert result[0]["gestor_nombre"] == "Gestora"
    assert result[0]["fecha_registro"] is None
    assert result[0]["created_at"] is None
    assert (
        await service.get_avances_para_revision(
            db_mock(executes=[ResultFake()]), ids.municipio
        )
        == []
    )


@pytest.mark.asyncio
async def test_estadisticas_revision_con_filtro_y_nulos(ids):
    db = db_mock(scalars=[3, 2, 1])
    assert await service.get_estadisticas_revision(db, ids.municipio, uuid.uuid4()) == {
        "pendientes": 3,
        "aprobados_semana": 2,
        "devueltos": 1,
    }
    db = db_mock(scalars=[None, None, None])
    assert await service.get_estadisticas_revision(db, ids.municipio) == {
        "pendientes": 0,
        "aprobados_semana": 0,
        "devueltos": 0,
    }


@pytest.mark.asyncio
async def test_revisar_avance_errores(ids):
    with pytest.raises(ValueError, match="no encontrado"):
        await service.revisar_avance(
            db_mock(scalars=[None]), ids.avance, ids.municipio, ids.usuario, "APROBADO"
        )
    avance = entity(gestor_lider_id=uuid.uuid4())
    with pytest.raises(PermissionError, match="otro gestor"):
        await service.revisar_avance(
            db_mock(scalars=[avance]),
            ids.avance,
            ids.municipio,
            ids.usuario,
            "APROBADO",
            gestor_lider_id=uuid.uuid4(),
        )
    for estado, observacion, message in [
        ("INVALIDO", None, "Estado inválido"),
        ("RECHAZADO", None, "obligatoria"),
    ]:
        with pytest.raises(ValueError, match=message):
            await service.revisar_avance(
                db_mock(scalars=[entity()]),
                ids.avance,
                ids.municipio,
                ids.usuario,
                estado,
                observacion,
            )


@pytest.mark.asyncio
async def test_revisar_avance_aprueba_y_rechaza(ids):
    for estado, observacion in [("APROBADO", None), ("RECHAZADO", "Corregir")]:
        avance = entity(observaciones_revision=None)
        db = db_mock(scalars=[avance])
        audit = SimpleNamespace(log_event=AsyncMock())
        with patch.object(service, "AuditService", return_value=audit):
            result = await service.revisar_avance(
                db,
                ids.avance,
                ids.municipio,
                ids.usuario,
                estado,
                observacion,
                gestor_lider_id=avance.gestor_lider_id,
            )
        assert result["estado_revision"] == estado
        assert result["observaciones_revision"] == observacion
        db.commit.assert_awaited_once()


def optimization(content=b"optimizado"):
    return SimpleNamespace(
        content=content,
        original_size=20,
        stored_size=len(content),
        saved_bytes=10,
        reduction_percent=50.0,
        optimized=True,
        method="test",
    )


@pytest.mark.asyncio
async def test_guardar_evidencia_errores(ids):
    with pytest.raises(ValueError, match="no encontrado"):
        await service.guardar_evidencia(
            db_mock(scalars=[None]),
            ids.avance,
            ids.municipio,
            ids.usuario,
            b"x",
            "a.pdf",
            "application/pdf",
        )
    avance = entity(registrado_por=uuid.uuid4(), gestor_lider_id=uuid.uuid4())
    with pytest.raises(PermissionError, match="adjuntar"):
        await service.guardar_evidencia(
            db_mock(scalars=[avance, uuid.uuid4()]),
            ids.avance,
            ids.municipio,
            ids.usuario,
            b"x",
            "a.pdf",
            "application/pdf",
        )


@pytest.mark.asyncio
async def test_guardar_evidencia_filesystem_y_reemplazo(tmp_path, ids):
    old = tmp_path / "old.pdf"
    old.write_bytes(b"old")
    avance = entity(registrado_por=ids.usuario, evidencia_url="old.pdf")
    db = db_mock(scalars=[avance, None])
    audit = SimpleNamespace(log_event=AsyncMock())
    with (
        patch.object(service.settings, "STORAGE_PATH", str(tmp_path)),
        patch.object(service, "optimize_evidence", return_value=optimization()),
        patch.object(service, "AuditService", return_value=audit),
        patch.object(service.uuid, "uuid4", return_value=SimpleNamespace(hex="fixed")),
    ):
        result = await service.guardar_evidencia(
            db,
            ids.avance,
            ids.municipio,
            ids.usuario,
            b"raw",
            "a.pdf",
            "application/pdf",
        )
    stored = tmp_path / str(ids.municipio) / str(ids.avance) / "fixed_a.pdf"
    assert stored.read_bytes() == b"optimizado"
    assert not old.exists()
    assert result["tamano_original"] == 20
    assert result["optimizada"] is True


@pytest.mark.asyncio
async def test_guardar_evidencia_rollback_borra_archivo(tmp_path, ids):
    avance = entity(registrado_por=ids.usuario)
    db = db_mock(scalars=[avance, None])
    audit = SimpleNamespace(log_event=AsyncMock(side_effect=RuntimeError("audit")))
    with (
        patch.object(service.settings, "STORAGE_PATH", str(tmp_path)),
        patch.object(service, "optimize_evidence", return_value=optimization()),
        patch.object(service, "AuditService", return_value=audit),
        pytest.raises(RuntimeError, match="audit"),
    ):
        await service.guardar_evidencia(
            db,
            ids.avance,
            ids.municipio,
            ids.usuario,
            b"raw",
            "a.pdf",
            "application/pdf",
        )
    db.rollback.assert_awaited_once()
    assert not list(tmp_path.rglob("*.pdf"))


@pytest.mark.asyncio
async def test_guardar_evidencia_ignora_error_al_borrar_anterior(tmp_path, ids):
    avance = entity(registrado_por=ids.usuario, evidencia_url="old.pdf")
    db = db_mock(scalars=[avance, None])
    old = tmp_path / "old.pdf"
    old.write_bytes(b"old")
    audit = SimpleNamespace(log_event=AsyncMock())
    with (
        patch.object(service.settings, "STORAGE_PATH", str(tmp_path)),
        patch.object(service, "optimize_evidence", return_value=optimization()),
        patch.object(service, "AuditService", return_value=audit),
        patch.object(type(old), "resolve", side_effect=OSError("disk")),
    ):
        await service.guardar_evidencia(
            db,
            ids.avance,
            ids.municipio,
            ids.usuario,
            b"raw",
            "a.pdf",
            "application/pdf",
        )


@pytest.mark.asyncio
async def test_obtener_archivo_evidencia_casos(tmp_path, ids):
    with pytest.raises(ValueError, match="no encontrada"):
        await service.obtener_archivo_evidencia(
            db_mock(scalars=[None]), ids.avance, ids.municipio, ids.usuario, []
        )
    avance = entity(
        evidencia_url="a.pdf", registrado_por=uuid.uuid4(), gestor_lider_id=uuid.uuid4()
    )
    with pytest.raises(ValueError, match="permiso"):
        await service.obtener_archivo_evidencia(
            db_mock(scalars=[avance, uuid.uuid4()]),
            ids.avance,
            ids.municipio,
            ids.usuario,
            [],
        )
    with (
        patch.object(service.settings, "STORAGE_PATH", str(tmp_path)),
        pytest.raises(ValueError, match="no existe"),
    ):
        await service.obtener_archivo_evidencia(
            db_mock(scalars=[avance]),
            ids.avance,
            ids.municipio,
            ids.usuario,
            ["ADMINISTRADOR_MUNICIPAL"],
        )
    path = tmp_path / "a.pdf"
    path.write_bytes(b"x")
    with patch.object(service.settings, "STORAGE_PATH", str(tmp_path)):
        result = await service.obtener_archivo_evidencia(
            db_mock(scalars=[avance]),
            ids.avance,
            ids.municipio,
            ids.usuario,
            ["GESTOR_LIDER"],
        )
    assert result == (path, "a.pdf", "application/octet-stream")
    avance.evidencia_nombre = "original.pdf"
    avance.evidencia_tipo = "application/pdf"
    with patch.object(service.settings, "STORAGE_PATH", str(tmp_path)):
        assert (
            await service.obtener_archivo_evidencia(
                db_mock(scalars=[avance, avance.gestor_lider_id]),
                ids.avance,
                ids.municipio,
                ids.usuario,
                [],
            )
        )[1:] == ("original.pdf", "application/pdf")


@pytest.mark.asyncio
async def test_helpers_permisos_y_busqueda(ids):
    avance = entity(registrado_por=ids.usuario)
    await service._check_evidence_permission(
        db_mock(scalars=[None]), avance, ids.usuario, ids.municipio
    )
    avance = entity(registrado_por=uuid.uuid4(), gestor_lider_id=uuid.uuid4())
    with pytest.raises(PermissionError, match="permiso"):
        await service._check_evidence_permission(
            db_mock(scalars=[uuid.uuid4()]), avance, ids.usuario, ids.municipio
        )
    assert (
        await service._get_avance_or_404(
            db_mock(scalars=[avance]), ids.avance, ids.municipio
        )
        is avance
    )
    with pytest.raises(ValueError, match="no encontrado"):
        await service._get_avance_or_404(
            db_mock(scalars=[None]), ids.avance, ids.municipio
        )


@pytest.mark.asyncio
async def test_agregar_evidencias_validaciones(ids):
    with pytest.raises(ValueError, match="al menos"):
        await service.agregar_evidencias(
            db_mock(), ids.avance, ids.municipio, ids.usuario, []
        )
    avance = entity()
    with (
        patch.object(service, "_get_avance_or_404", AsyncMock(return_value=avance)),
        patch.object(service, "_check_evidence_permission", AsyncMock()),
        pytest.raises(ValueError, match="máximo 4"),
    ):
        await service.agregar_evidencias(
            db_mock(scalars=[4]),
            ids.avance,
            ids.municipio,
            ids.usuario,
            [{"content": b"x", "filename": "x", "content_type": "text/plain"}],
        )


@pytest.mark.asyncio
async def test_agregar_evidencias_exitoso(tmp_path, ids):
    avance = entity()
    db = db_mock(scalars=[0])

    async def flush():
        added = db.add.call_args.args[0]
        added.id = uuid.uuid4()
        added.created_at = datetime(2026, 1, 1, tzinfo=UTC)

    db.flush.side_effect = flush
    audit = SimpleNamespace(log_event=AsyncMock())
    files = [
        {
            "content": b"a",
            "filename": "a.txt",
            "content_type": "text/plain",
            "descripcion": "A",
        },
        {"content": b"b", "filename": "b.txt", "content_type": "text/plain"},
    ]
    with (
        patch.object(service, "_get_avance_or_404", AsyncMock(return_value=avance)),
        patch.object(service, "_check_evidence_permission", AsyncMock()),
        patch.object(service.settings, "STORAGE_PATH", str(tmp_path)),
        patch.object(
            service,
            "optimize_evidence",
            side_effect=[optimization(b"A"), optimization(b"B")],
        ),
        patch.object(service, "AuditService", return_value=audit),
    ):
        result = await service.agregar_evidencias(
            db, ids.avance, ids.municipio, ids.usuario, files
        )
    assert [item["nombre"] for item in result] == ["a.txt", "b.txt"]
    assert result[1]["descripcion"] is None
    assert result[0]["created_at"] is not None
    assert audit.log_event.await_count == 2
    stored = sorted((tmp_path / str(ids.municipio) / str(ids.avance)).glob("*.txt"))
    assert sorted(path.read_bytes() for path in stored) == [b"A", b"B"]


@pytest.mark.asyncio
async def test_agregar_evidencias_rollback_limpia_archivos(tmp_path, ids):
    avance = entity()
    db = db_mock(scalars=[0])

    async def flush():
        ev = db.add.call_args.args[0]
        ev.id = uuid.uuid4()
        ev.created_at = None

    db.flush.side_effect = flush
    audit = SimpleNamespace(log_event=AsyncMock(side_effect=RuntimeError("audit")))
    with (
        patch.object(service, "_get_avance_or_404", AsyncMock(return_value=avance)),
        patch.object(service, "_check_evidence_permission", AsyncMock()),
        patch.object(service.settings, "STORAGE_PATH", str(tmp_path)),
        patch.object(service, "optimize_evidence", return_value=optimization()),
        patch.object(service, "AuditService", return_value=audit),
        pytest.raises(RuntimeError, match="audit"),
    ):
        await service.agregar_evidencias(
            db,
            ids.avance,
            ids.municipio,
            ids.usuario,
            [{"content": b"a", "filename": "a.txt", "content_type": "text/plain"}],
        )
    db.rollback.assert_awaited_once()
    assert not list(tmp_path.rglob("*.txt"))


@pytest.mark.asyncio
async def test_listar_evidencias(ids):
    avance = entity()
    fecha = datetime(2026, 1, 1, tzinfo=UTC)
    evidencias = [
        entity(
            avance_id=avance.id,
            tipo="text/plain",
            url="a",
            descripcion="d",
            tamano_original=2,
            tamano_almacenado=1,
            optimizada=True,
            created_at=fecha,
        ),
        entity(
            avance_id=avance.id,
            tipo="text/plain",
            url="b",
            descripcion=None,
            tamano_original=1,
            tamano_almacenado=1,
            optimizada=False,
            created_at=None,
        ),
    ]
    with patch.object(service, "_get_avance_or_404", AsyncMock(return_value=avance)):
        result = await service.listar_evidencias(
            db_mock(executes=[ResultFake(evidencias)]), ids.avance, ids.municipio
        )
    assert result[0]["created_at"] == fecha.isoformat()
    assert result[1]["created_at"] is None


@pytest.mark.asyncio
async def test_obtener_archivo_por_id_casos(tmp_path, ids):
    avance = entity(registrado_por=uuid.uuid4(), gestor_lider_id=uuid.uuid4())
    with (
        patch.object(service, "_get_avance_or_404", AsyncMock(return_value=avance)),
        pytest.raises(ValueError, match="no encontrada"),
    ):
        await service.obtener_archivo_evidencia_por_id(
            db_mock(scalars=[None]),
            ids.avance,
            uuid.uuid4(),
            ids.municipio,
            ids.usuario,
            [],
        )
    evidencia = entity(url="e.txt", nombre=None, tipo=None)
    with (
        patch.object(service, "_get_avance_or_404", AsyncMock(return_value=avance)),
        pytest.raises(PermissionError, match="permiso"),
    ):
        await service.obtener_archivo_evidencia_por_id(
            db_mock(scalars=[evidencia, uuid.uuid4()]),
            ids.avance,
            evidencia.id,
            ids.municipio,
            ids.usuario,
            [],
        )
    with (
        patch.object(service, "_get_avance_or_404", AsyncMock(return_value=avance)),
        patch.object(service.settings, "STORAGE_PATH", str(tmp_path)),
        pytest.raises(ValueError, match="no existe"),
    ):
        await service.obtener_archivo_evidencia_por_id(
            db_mock(scalars=[evidencia]),
            ids.avance,
            evidencia.id,
            ids.municipio,
            ids.usuario,
            ["SUPERADMIN_PLATAFORMA"],
        )
    path = tmp_path / "e.txt"
    path.write_bytes(b"x")
    with (
        patch.object(service, "_get_avance_or_404", AsyncMock(return_value=avance)),
        patch.object(service.settings, "STORAGE_PATH", str(tmp_path)),
    ):
        assert await service.obtener_archivo_evidencia_por_id(
            db_mock(scalars=[evidencia]),
            ids.avance,
            evidencia.id,
            ids.municipio,
            ids.usuario,
            ["GESTOR_LIDER"],
        ) == (path, "e.txt", "application/octet-stream")
    evidencia.nombre = "evidencia.txt"
    evidencia.tipo = "text/plain"
    with (
        patch.object(service, "_get_avance_or_404", AsyncMock(return_value=avance)),
        patch.object(service.settings, "STORAGE_PATH", str(tmp_path)),
    ):
        assert (
            await service.obtener_archivo_evidencia_por_id(
                db_mock(scalars=[evidencia, avance.gestor_lider_id]),
                ids.avance,
                evidencia.id,
                ids.municipio,
                ids.usuario,
                [],
            )
        )[1:] == ("evidencia.txt", "text/plain")


@pytest.mark.asyncio
async def test_actualizar_descripcion_evidencia(ids):
    avance = entity()
    evidencia = entity(descripcion=None)
    db = db_mock(scalars=[evidencia])
    with (
        patch.object(service, "_get_avance_or_404", AsyncMock(return_value=avance)),
        patch.object(service, "_check_evidence_permission", AsyncMock()),
    ):
        assert await service.actualizar_descripcion_evidencia(
            db, ids.avance, evidencia.id, ids.municipio, ids.usuario, "Nueva"
        ) == {"id": str(evidencia.id), "descripcion": "Nueva"}
    with (
        patch.object(service, "_get_avance_or_404", AsyncMock(return_value=avance)),
        patch.object(service, "_check_evidence_permission", AsyncMock()),
        pytest.raises(ValueError, match="no encontrada"),
    ):
        await service.actualizar_descripcion_evidencia(
            db_mock(scalars=[None]),
            ids.avance,
            uuid.uuid4(),
            ids.municipio,
            ids.usuario,
            None,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "remaining", [None, entity(url="otra", nombre="otra.txt", tipo="text/plain")]
)
async def test_eliminar_evidencia_actualiza_denormalizado(tmp_path, ids, remaining):
    avance = entity(evidencia_url="actual.txt")
    evidencia = entity(url="actual.txt", nombre="actual.txt")
    path = tmp_path / "actual.txt"
    path.write_bytes(b"x")
    db = db_mock(scalars=[evidencia, remaining])
    audit = SimpleNamespace(log_event=AsyncMock())
    with (
        patch.object(service, "_get_avance_or_404", AsyncMock(return_value=avance)),
        patch.object(service, "_check_evidence_permission", AsyncMock()),
        patch.object(service.settings, "STORAGE_PATH", str(tmp_path)),
        patch.object(service, "AuditService", return_value=audit),
    ):
        result = await service.eliminar_evidencia(
            db, ids.avance, evidencia.id, ids.municipio, ids.usuario
        )
    assert result == {"id": str(evidencia.id), "eliminada": True}
    assert not path.exists()
    assert avance.evidencia_url == (remaining.url if remaining else None)


@pytest.mark.asyncio
async def test_eliminar_evidencia_no_actualiza_si_no_es_actual_e_ignora_oserror(
    tmp_path, ids
):
    avance = entity(evidencia_url="otra.txt")
    evidencia = entity(url="actual.txt")
    db = db_mock(scalars=[evidencia])
    audit = SimpleNamespace(log_event=AsyncMock())
    with (
        patch.object(service, "_get_avance_or_404", AsyncMock(return_value=avance)),
        patch.object(service, "_check_evidence_permission", AsyncMock()),
        patch.object(service.settings, "STORAGE_PATH", str(tmp_path)),
        patch.object(type(tmp_path), "resolve", side_effect=OSError("disk")),
        patch.object(service, "AuditService", return_value=audit),
    ):
        await service.eliminar_evidencia(
            db, ids.avance, evidencia.id, ids.municipio, ids.usuario
        )
    assert avance.evidencia_url == "otra.txt"


@pytest.mark.asyncio
async def test_eliminar_evidencia_inexistente(ids):
    avance = entity()
    with (
        patch.object(service, "_get_avance_or_404", AsyncMock(return_value=avance)),
        patch.object(service, "_check_evidence_permission", AsyncMock()),
        pytest.raises(ValueError, match="no encontrada"),
    ):
        await service.eliminar_evidencia(
            db_mock(scalars=[None]),
            ids.avance,
            uuid.uuid4(),
            ids.municipio,
            ids.usuario,
        )
