"""Pruebas unitarias de las rutas y el servicio de Personalizacion (branding)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from src.backend.api.v1 import personalizacion
from src.backend.schemas.personalizacion import PersonalizacionUpdate
from src.backend.services import personalizacion_service as service

CURRENT_USER = {
    "municipio_id": str(uuid4()),
    "user": SimpleNamespace(id=str(uuid4())),
}
DB = object()


class ResultFake:
    def __init__(self, row=None):
        self.row = row

    def scalar_one_or_none(self):
        return self.row


def db_mock(row=None):
    return SimpleNamespace(
        execute=AsyncMock(return_value=ResultFake(row)),
        add=Mock(),
        commit=AsyncMock(),
        refresh=AsyncMock(),
    )


def fila(**overrides):
    values = {
        "color_primario": "#123456",
        "color_secundario": "#654321",
        "nombre_sistema": "Municipio Guardado",
        "logo_data_url": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def payload(**overrides):
    values = {
        "color_primario": "#112233",
        "color_secundario": "#445566",
        "nombre_sistema": "Municipio Demo",
        "logo_data_url": None,
    }
    values.update(overrides)
    return values


async def test_get_devuelve_defaults_cuando_no_hay_fila():
    db = db_mock(row=None)
    result = await service.get_personalizacion(db, uuid4())
    assert result == {
        "color_primario": "#0f3d3b",
        "color_secundario": "#b9852f",
        "nombre_sistema": "SIGEM Colombia",
        "logo_data_url": None,
    }
    assert db.execute.await_count == 1


async def test_get_serializa_la_fila_existente():
    row = fila(logo_data_url="data:image/png;base64,AAAA")
    result = await service.get_personalizacion(db_mock(row=row), uuid4())
    assert result == {
        "color_primario": "#123456",
        "color_secundario": "#654321",
        "nombre_sistema": "Municipio Guardado",
        "logo_data_url": "data:image/png;base64,AAAA",
    }


async def test_save_crea_la_fila_cuando_no_existe():
    db = db_mock(row=None)
    data = payload()
    result = await service.save_personalizacion(db, uuid4(), data)
    assert result == data
    db.add.assert_called_once()
    creada = db.add.call_args.args[0]
    assert creada.color_primario == "#112233"
    assert creada.color_secundario == "#445566"
    assert creada.nombre_sistema == "Municipio Demo"
    assert creada.logo_data_url is None
    assert "Personalizacion" in repr(creada)
    assert db.commit.await_count == 1
    assert db.refresh.await_count == 1


async def test_save_actualiza_la_fila_existente():
    row = fila()
    db = db_mock(row=row)
    data = payload(nombre_sistema="Actualizado", logo_data_url="data:image/png;base64,BBBB")
    result = await service.save_personalizacion(db, uuid4(), data)
    assert result["nombre_sistema"] == "Actualizado"
    assert result["logo_data_url"] == "data:image/png;base64,BBBB"
    assert row.color_primario == "#112233"
    assert row.color_secundario == "#445566"
    assert db.add.call_count == 0
    assert db.commit.await_count == 1
    assert db.refresh.await_count == 1


async def test_ruta_get_devuelve_la_configuracion():
    esperado = payload()
    with patch.object(
        personalizacion.personalizacion_service,
        "get_personalizacion",
        AsyncMock(return_value=esperado),
    ) as get_service:
        response = await personalizacion.obtener_personalizacion(CURRENT_USER, DB)
    assert response.color_primario == "#112233"
    assert response.nombre_sistema == "Municipio Demo"
    assert response.logo_data_url is None
    assert get_service.await_count == 1
    assert get_service.await_args.args[0] is DB
    assert str(get_service.await_args.args[1]) == CURRENT_USER["municipio_id"]


async def test_ruta_put_guarda_la_configuracion():
    esperado = payload()
    body = PersonalizacionUpdate(**esperado)
    with (
        patch.object(personalizacion, "require_permission", AsyncMock()) as permission,
        patch.object(
            personalizacion.personalizacion_service,
            "save_personalizacion",
            AsyncMock(return_value=esperado),
        ) as save_service,
    ):
        response = await personalizacion.actualizar_personalizacion(body, CURRENT_USER, DB)
    assert response.nombre_sistema == "Municipio Demo"
    assert permission.await_count == 1
    assert permission.await_args.args[1] == CURRENT_USER["user"].id
    assert save_service.await_count == 1
    assert save_service.await_args.args[0] is DB
    assert str(save_service.await_args.args[1]) == CURRENT_USER["municipio_id"]
