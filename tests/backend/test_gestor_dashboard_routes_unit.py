from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException, UploadFile

from src.backend.api.v1 import gestor_dashboard as api

MID = uuid4()
UID = uuid4()
AID = uuid4()
PID = uuid4()
EID = uuid4()
USER = SimpleNamespace(id=UID)
CURRENT = {"user": USER, "municipio_id": str(MID), "roles": ["GESTOR_LIDER"]}
NO_USER = {"municipio_id": str(MID), "roles": []}


def avance(**changes):
    data = {
        "id": str(AID),
        "producto_id": str(PID),
        "avance_porcentaje": 25.0,
        "avance_valor": 1,
        "observaciones": None,
        "evidencia_url": None,
        "indicador": None,
        "periodo": "2026-Q1",
        "fecha_registro": None,
        "estado_revision": "PENDIENTE",
        "evidencia_nombre": None,
        "evidencia_tipo": None,
        "observaciones_revision": None,
        "estado": "ACTIVO",
        "created_at": None,
    }
    data.update(changes)
    return data


def revision(**changes):
    data = avance()
    data.update(
        producto_codigo="P1",
        producto_nombre="Producto",
        codigo_indicador=None,
        gestor_id=str(uuid4()),
        gestor_codigo="G1",
        gestor_nombre="Gestor",
    )
    data.pop("estado")
    data.update(changes)
    return data


def evidencia(**changes):
    data = {
        "id": str(EID),
        "avance_id": str(AID),
        "nombre": "x.pdf",
        "tipo": "application/pdf",
        "url": "/x.pdf",
    }
    data.update(changes)
    return data


def producto():
    return {
        "id": str(PID),
        "codigo": "P1",
        "nombre": "Producto",
        "indicador": None,
        "codigo_indicador": None,
        "meta_redactada": None,
        "linea_base": None,
        "meta_cuatrienio": None,
        "unidad_medida": None,
        "estado": "ACTIVO",
    }


def upload(name="x.pdf", content_type="application/pdf", content=b"%PDF-ok"):
    from io import BytesIO

    return UploadFile(filename=name, file=BytesIO(content), headers={"content-type": content_type})


async def assert_http(awaitable, code, detail=None):
    with pytest.raises(HTTPException) as caught:
        await awaitable
    assert caught.value.status_code == code
    if detail:
        assert detail in caught.value.detail


async def test_helpers_access_and_basic_endpoints(monkeypatch):
    assert api._valid_evidence_signature("image/jpeg", b"\xff\xd8\xffx")
    assert api._valid_evidence_signature("image/png", b"\x89PNG\r\n\x1a\nx")
    assert api._valid_evidence_signature("application/pdf", b"%PDF-x")
    assert not api._valid_evidence_signature("text/plain", b"x")

    db = SimpleNamespace(scalar=AsyncMock(return_value=AID))
    assert (
        await api._require_revision_access(db, {**CURRENT, "roles": ["SUPERADMIN_PLATAFORMA"]})
        is None
    )
    assert (
        await api._require_revision_access(db, {**CURRENT, "roles": ["ADMINISTRADOR_MUNICIPAL"]})
        is None
    )
    assert await api._require_revision_access(db, CURRENT) is None
    await assert_http(
        api._require_revision_access(db, {**CURRENT, "roles": []}),
        403,
        "avance.revisar",
    )

    monkeypatch.setattr(api, "get_mis_productos", AsyncMock(return_value=[producto()]))
    result = await api.obtener_mis_productos(CURRENT, db)
    assert result[0].codigo == "P1"
    await assert_http(api.obtener_mis_productos(NO_USER, db), 401)

    summary = {
        "total_productos": 1,
        "productos_con_avance": 1,
        "avance_promedio": 25,
        "productos_completados": 0,
    }
    monkeypatch.setattr(api, "get_resumen_avances", AsyncMock(return_value=summary))
    assert (await api.obtener_resumen_avances(CURRENT, db)).total_productos == 1
    await assert_http(api.obtener_resumen_avances(NO_USER, db), 401)

    monkeypatch.setattr(api, "_require_revision_access", AsyncMock(return_value=AID))
    monkeypatch.setattr(
        api,
        "get_avances_para_revision",
        AsyncMock(return_value=[revision(), revision(periodo="2026-Q2")]),
    )
    rows = await api.obtener_avances_revision("PENDIENTE", "p", "2026-Q1", CURRENT, db)
    assert len(rows) == 1
    await assert_http(api.obtener_avances_revision(current_user=NO_USER, db=db), 401)

    monkeypatch.setattr(
        api,
        "get_estadisticas_revision",
        AsyncMock(return_value={"pendientes": 1, "aprobados_semana": 2, "devueltos": 3}),
    )
    assert (await api.obtener_estadisticas_revision(CURRENT, db)).devueltos == 3
    await assert_http(api.obtener_estadisticas_revision(NO_USER, db), 401)

    monkeypatch.setattr(api, "get_avances_producto", AsyncMock(return_value=[avance()]))
    assert len(await api.obtener_avances_producto(PID, CURRENT, db)) == 1
    await assert_http(api.obtener_avances_producto(PID, NO_USER, db), 401)


@pytest.mark.parametrize(
    ("function_name", "service_name", "args", "data", "success", "errors"),
    [
        (
            "revisar_avance_endpoint",
            "revisar_avance",
            (AID,),
            api.RevisionAvanceRequest(nuevo_estado="APROBADO"),
            {"ok": True},
            [
                (PermissionError("no"), 403),
                (ValueError("bad"), 422),
                (RuntimeError(), 500),
            ],
        ),
        (
            "crear_avance",
            "registrar_avance",
            (),
            api.AvanceCreate(avance_porcentaje=25),
            avance(),
            [(ValueError("bad"), 422), (RuntimeError(), 500)],
        ),
        (
            "editar_avance",
            "actualizar_avance",
            (AID,),
            api.AvanceUpdate(avance_porcentaje=30),
            avance(avance_porcentaje=30),
            [
                (PermissionError("no"), 403),
                (ValueError("bad"), 404),
                (RuntimeError(), 500),
            ],
        ),
        (
            "borrar_avance",
            "eliminar_avance",
            (AID,),
            None,
            {"ok": True},
            [
                (PermissionError("no"), 403),
                (ValueError("bad"), 404),
                (RuntimeError(), 500),
            ],
        ),
    ],
)
async def test_avance_mutations_success_auth_and_errors(
    monkeypatch, function_name, service_name, args, data, success, errors
):
    db = Mock()
    monkeypatch.setattr(api, "_require_revision_access", AsyncMock(return_value=AID))
    service = AsyncMock(return_value=success)
    monkeypatch.setattr(api, service_name, service)
    function = getattr(api, function_name)

    call_args = list(args)
    if function_name == "crear_avance":
        call_args = [data, PID]
    elif data is not None:
        call_args.append(data)
    call_args += [CURRENT, db]
    result = await function(*call_args)
    assert result

    no_user_args = list(args)
    if function_name == "crear_avance":
        no_user_args = [data, PID]
    elif data is not None:
        no_user_args.append(data)
    await assert_http(function(*no_user_args, NO_USER, db), 401)

    for error, code in errors:
        service.side_effect = error
        await assert_http(function(*call_args), code)


async def test_empty_update(monkeypatch):
    await assert_http(api.editar_avance(AID, api.AvanceUpdate(), CURRENT, Mock()), 422, "campos")


@pytest.mark.parametrize(
    ("file", "code", "detail"),
    [
        (upload("x.txt", "text/plain", b"x"), 422, "JPG"),
        (upload("x.jpg", "application/pdf"), 422, "extensión"),
        (upload("", "application/pdf"), 422, "extensión"),
        (upload(content=b""), 422, "vacío"),
        (upload(content=b"x" * (api.MAX_EVIDENCE_BYTES + 1)), 413, "10 MB"),
        (upload(content=b"not pdf"), 422, "tipo declarado"),
    ],
)
async def test_single_upload_validation(file, code, detail):
    await assert_http(api.subir_evidencia(AID, file, CURRENT, Mock()), code, detail)


async def test_single_upload_success_auth_and_translation(monkeypatch):
    db = Mock()
    save = AsyncMock(return_value={"ok": True})
    monkeypatch.setattr(api, "guardar_evidencia", save)
    result = await api.subir_evidencia(AID, upload("folder\\x.pdf"), CURRENT, db)
    assert result == {"ok": True}
    assert save.await_args.kwargs["filename"] == "x.pdf"
    await assert_http(api.subir_evidencia(AID, upload(), NO_USER, db), 401)
    for error, code in [
        (PermissionError("no"), 403),
        (ValueError("bad"), 422),
        (RuntimeError(), 500),
    ]:
        save.side_effect = error
        await assert_http(api.subir_evidencia(AID, upload(), CURRENT, db), code)


@pytest.mark.parametrize(
    ("file", "code"),
    [
        (upload("x.txt", "text/plain", b"x"), 422),
        (upload("x.jpg", "application/pdf"), 422),
        (upload(content=b""), 422),
        (upload(content=b"x" * (api.MAX_EVIDENCE_BYTES + 1)), 413),
        (upload(content=b"bad"), 422),
    ],
)
def test_multi_file_helper_rejections(file, code):
    with pytest.raises(HTTPException) as caught:
        api._validate_evidence_file(file)
    assert caught.value.status_code == code


def test_multi_file_helper_success():
    assert api._validate_evidence_file(upload("dir\\x.pdf")) == ("x.pdf", b"%PDF-ok")


async def test_multi_evidence_endpoints(monkeypatch, tmp_path):
    db = Mock()
    add = AsyncMock(return_value=[evidencia()])
    monkeypatch.setattr(api, "agregar_evidencias", add)
    result = await api.subir_evidencias(AID, [upload()], "desc", CURRENT, db)
    assert result[0].descripcion is None
    assert add.await_args.kwargs["archivos"][0]["descripcion"] == "desc"
    await assert_http(api.subir_evidencias(AID, [upload()], None, NO_USER, db), 401)
    await assert_http(
        api.subir_evidencias(AID, [upload() for _ in range(5)], None, CURRENT, db), 422
    )
    for error, code in [
        (PermissionError("no"), 403),
        (ValueError("bad"), 422),
        (RuntimeError(), 500),
    ]:
        add.side_effect = error
        await assert_http(api.subir_evidencias(AID, [upload()], None, CURRENT, db), code)

    listing = AsyncMock(return_value=[evidencia()])
    monkeypatch.setattr(api, "listar_evidencias", listing)
    assert len(await api.obtener_evidencias(AID, CURRENT, db)) == 1
    await assert_http(api.obtener_evidencias(AID, NO_USER, db), 401)
    listing.side_effect = ValueError("missing")
    await assert_http(api.obtener_evidencias(AID, CURRENT, db), 404)

    path = tmp_path / "x.pdf"
    path.write_bytes(b"%PDF-ok")
    old_download = AsyncMock(return_value=(path, "x.pdf", "application/pdf"))
    monkeypatch.setattr(api, "obtener_archivo_evidencia", old_download)
    response = await api.descargar_evidencia(AID, CURRENT, db)
    assert response.filename == "x.pdf"
    await assert_http(api.descargar_evidencia(AID, NO_USER, db), 401)
    old_download.side_effect = ValueError("missing")
    await assert_http(api.descargar_evidencia(AID, CURRENT, db), 404)

    download = AsyncMock(return_value=(path, "x.pdf", "application/pdf"))
    monkeypatch.setattr(api, "obtener_archivo_evidencia_por_id", download)
    assert (await api.descargar_evidencia_por_id(AID, EID, CURRENT, db)).filename == "x.pdf"
    await assert_http(api.descargar_evidencia_por_id(AID, EID, NO_USER, db), 401)
    for error, code in [(PermissionError("no"), 403), (ValueError("bad"), 404)]:
        download.side_effect = error
        await assert_http(api.descargar_evidencia_por_id(AID, EID, CURRENT, db), code)

    update = AsyncMock(return_value={"ok": True})
    monkeypatch.setattr(api, "actualizar_descripcion_evidencia", update)
    data = api.EvidenciaDescripcionUpdate(descripcion="nueva")
    assert await api.actualizar_evidencia(AID, EID, data, CURRENT, db) == {"ok": True}
    await assert_http(api.actualizar_evidencia(AID, EID, data, NO_USER, db), 401)
    for error, code in [(PermissionError("no"), 403), (ValueError("bad"), 404)]:
        update.side_effect = error
        await assert_http(api.actualizar_evidencia(AID, EID, data, CURRENT, db), code)

    delete = AsyncMock(return_value={"ok": True})
    monkeypatch.setattr(api, "eliminar_evidencia", delete)
    assert await api.borrar_evidencia(AID, EID, CURRENT, db) == {"ok": True}
    await assert_http(api.borrar_evidencia(AID, EID, NO_USER, db), 401)
    for error, code in [(PermissionError("no"), 403), (ValueError("bad"), 404)]:
        delete.side_effect = error
        await assert_http(api.borrar_evidencia(AID, EID, CURRENT, db), code)
