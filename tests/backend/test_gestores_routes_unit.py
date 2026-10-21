from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from src.backend.api.v1 import gestores as api
from src.backend.schemas.gestor import (
    GestorAccion,
    GestorCreate,
    GestorPasswordUpdate,
    GestorPermisosUpdate,
    GestorUpdate,
)

MID = uuid4()
UID = uuid4()
GID = uuid4()
RID = uuid4()
NOW = datetime.now(UTC)
CURRENT = {
    "user": SimpleNamespace(id=UID),
    "municipio_id": str(MID),
    "roles": ["GESTOR"],
}
ADMIN = {**CURRENT, "roles": ["ADMINISTRADOR_MUNICIPAL"]}


def gestor(**changes):
    data = {
        "id": GID,
        "codigo": "GES-1",
        "username": "gestor",
        "email": "g@example.com",
        "telefono": None,
        "nombre_completo": "Gestor Uno",
        "cargo": None,
        "rol": None,
        "rol_id": None,
        "roles": [],
        "dependencia_principal_id": None,
        "dependencia_principal": None,
        "dependencias": [],
        "estado": "ACTIVO",
        "mfa_activo": False,
        "must_change_password": False,
        "ultimo_acceso": None,
        "ip_ultimo_acceso": None,
        "intentos_fallidos": 0,
        "ultimo_cambio_password": None,
        "created_at": NOW,
        "updated_at": None,
    }
    data.update(changes)
    return data


def access():
    return {
        "id": uuid4(),
        "exitoso": True,
        "ip_address": "127.0.0.1",
        "user_agent": "pytest",
        "razon_fallo": None,
        "fecha_intento": NOW,
    }


async def raises_http(awaitable, code, detail=None):
    with pytest.raises(HTTPException) as caught:
        await awaitable
    assert caught.value.status_code == code
    if detail:
        assert detail in caught.value.detail


@pytest.fixture
def permission(monkeypatch):
    check = AsyncMock()
    monkeypatch.setattr(api, "require_permission", check)
    return check


def test_allowed_roles():
    assert api._allowed_role_codes(ADMIN) is None
    assert api._allowed_role_codes(CURRENT) == {"GESTOR"}
    assert api._allowed_role_codes({}) == {"GESTOR"}


async def test_create_success_and_errors(monkeypatch, permission):
    data = GestorCreate(nombre_completo="Gestor Uno", email="g@example.com")
    service = AsyncMock(
        return_value={
            "temp_password": "T" * 20,
            "id": GID,
            "codigo": "GES-1",
            "username": "gestor",
        }
    )
    monkeypatch.setattr(api, "svc_create", service)
    result = await api.create_gestor(data, Mock(), CURRENT, Mock())
    assert result.id == GID
    assert service.await_args.kwargs["allowed_role_codes"] == {"GESTOR"}
    permission.assert_awaited_once_with(service.await_args.kwargs["db"], UID, "gestor.crear")
    for error, code, detail in [
        (ValueError("invalid"), 422, "invalid"),
        (RuntimeError("secret"), 500, "Error interno"),
    ]:
        service.side_effect = error
        await raises_http(api.create_gestor(data, Mock(), CURRENT, Mock()), code, detail)


async def test_list_and_get(monkeypatch, permission):
    service = AsyncMock(
        return_value={
            "gestores": [gestor()],
            "total": 1,
            "page": 2,
            "page_size": 5,
            "total_pages": 1,
        }
    )
    monkeypatch.setattr(api, "svc_list", service)
    result = await api.list_gestores("ana", "Líder", RID, "ACTIVO", 2, 5, CURRENT, Mock())
    assert result.total == 1
    assert service.await_args.kwargs["filtros"]["rol_id"] == str(RID)
    service.return_value["gestores"] = []
    await api.list_gestores(None, None, None, None, 1, 20, CURRENT, Mock())
    assert service.await_args.kwargs["filtros"]["rol_id"] is None

    get = AsyncMock(return_value=gestor())
    monkeypatch.setattr(api, "svc_get", get)
    assert (await api.get_gestor(GID, CURRENT, Mock())).id == GID
    get.return_value = None
    await raises_http(api.get_gestor(GID, CURRENT, Mock()), 404)


@pytest.mark.parametrize(
    ("function_name", "service_name", "permission_code"),
    [
        ("activate_gestor", "svc_activate", "gestor.activar"),
        ("deactivate_gestor", "svc_deactivate", "gestor.desactivar"),
        ("unblock_gestor", "svc_unblock", "gestor.desbloquear"),
    ],
)
async def test_simple_mutations_success_and_not_found(
    monkeypatch, permission, function_name, service_name, permission_code
):
    service = AsyncMock(return_value=gestor())
    monkeypatch.setattr(api, service_name, service)
    function = getattr(api, function_name)
    args = [GID, Mock()]
    if function_name == "deactivate_gestor":
        args.append(GestorAccion(motivo="opcional"))
    args += [CURRENT, Mock()]
    assert (await function(*args)).id == GID
    assert permission.await_args.args[2] == permission_code
    service.return_value = None
    await raises_http(function(*args), 404)


async def test_update_and_permissions(monkeypatch, permission):
    update = AsyncMock(return_value=gestor(nombre_completo="Nuevo Nombre"))
    monkeypatch.setattr(api, "svc_update", update)
    data = GestorUpdate(nombre_completo="Nuevo Nombre")
    assert (
        await api.update_gestor(GID, data, Mock(), CURRENT, Mock())
    ).nombre_completo == "Nuevo Nombre"
    update.return_value = None
    await raises_http(api.update_gestor(GID, data, Mock(), CURRENT, Mock()), 404)

    permissions = AsyncMock(return_value=gestor())
    monkeypatch.setattr(api, "svc_update_permissions", permissions)
    pdata = GestorPermisosUpdate(rol_id=RID)
    assert (await api.update_gestor_permissions(GID, pdata, Mock(), CURRENT, Mock())).id == GID
    permissions.side_effect = ValueError("rol inválido")
    await raises_http(api.update_gestor_permissions(GID, pdata, Mock(), CURRENT, Mock()), 422)
    permissions.side_effect = None
    permissions.return_value = None
    await raises_http(api.update_gestor_permissions(GID, pdata, Mock(), CURRENT, Mock()), 404)


async def test_block_all_paths(monkeypatch, permission):
    service = AsyncMock(return_value=gestor(estado="BLOQUEADO"))
    monkeypatch.setattr(api, "svc_block", service)
    await raises_http(
        api.block_gestor(GID, GestorAccion(), Mock(), CURRENT, Mock()),
        422,
        "obligatorio",
    )
    await raises_http(
        api.block_gestor(GID, GestorAccion(motivo="  "), Mock(), CURRENT, Mock()), 422
    )
    result = await api.block_gestor(GID, GestorAccion(motivo=" razón "), Mock(), CURRENT, Mock())
    assert result.estado == "BLOQUEADO"
    assert service.await_args.kwargs["motivo"] == "razón"
    service.side_effect = ValueError("ya bloqueado")
    await raises_http(api.block_gestor(GID, GestorAccion(motivo="x"), Mock(), CURRENT, Mock()), 422)
    service.side_effect = None
    service.return_value = None
    await raises_http(api.block_gestor(GID, GestorAccion(motivo="x"), Mock(), CURRENT, Mock()), 404)


async def test_reset_password_all_paths(monkeypatch, permission):
    service = AsyncMock(
        return_value={
            "temp_password": "T" * 20,
            "id": GID,
            "codigo": "GES-1",
            "username": "gestor",
        }
    )
    monkeypatch.setattr(api, "svc_reset_password", service)
    result = await api.reset_password(GID, Mock(), None, CURRENT, Mock())
    assert result.nueva_password_temporal == "T" * 20
    assert service.await_args.kwargs["nueva_password"] is None
    body = GestorPasswordUpdate(nueva_password="C" * 15)
    await api.reset_password(GID, Mock(), body, CURRENT, Mock())
    assert service.await_args.kwargs["nueva_password"] == "C" * 15
    service.side_effect = ValueError("débil")
    await raises_http(api.reset_password(GID, Mock(), body, CURRENT, Mock()), 422)
    service.side_effect = None
    service.return_value = None
    await raises_http(api.reset_password(GID, Mock(), body, CURRENT, Mock()), 404)


async def test_delete_accesses_and_audit(monkeypatch, permission):
    delete = AsyncMock(return_value={"ok": True})
    monkeypatch.setattr(api, "svc_soft_delete", delete)
    assert await api.delete_gestor(GID, Mock(), CURRENT, Mock()) is None
    delete.return_value = None
    await raises_http(api.delete_gestor(GID, Mock(), CURRENT, Mock()), 404)

    accesses = AsyncMock(return_value=[access()])
    monkeypatch.setattr(api, "svc_list_accesos", accesses)
    rows = await api.get_gestor_accesos(GID, 10, 2, CURRENT, Mock())
    assert rows[0].exitoso is True
    accesses.return_value = []
    assert await api.get_gestor_accesos(GID, 10, 2, CURRENT, Mock()) == []
    accesses.return_value = None
    await raises_http(api.get_gestor_accesos(GID, 10, 2, CURRENT, Mock()), 404)

    event = SimpleNamespace(
        id=uuid4(),
        evento_tipo="LOGIN",
        resultado="OK",
        recurso_tipo="GestorLider",
        recurso_id=GID,
        ip_address="127.0.0.1",
        user_agent="pytest",
        metadata_json={"a": 1},
        fecha_evento=NOW,
    )
    event_empty = SimpleNamespace(
        id=uuid4(),
        evento_tipo="X",
        resultado="OK",
        recurso_tipo="GestorLider",
        recurso_id=None,
        ip_address=None,
        user_agent=None,
        metadata_json=None,
        fecha_evento=None,
    )
    get_events = AsyncMock(return_value=[event, event_empty])
    monkeypatch.setattr(
        api, "AuditService", Mock(return_value=SimpleNamespace(get_events=get_events))
    )
    result = await api.get_gestor_audit_events(GID, 5, 1, CURRENT, Mock())
    assert result[0]["recurso_id"] == str(GID)
    assert result[0]["fecha_evento"] == NOW.isoformat()
    assert result[1]["recurso_id"] is None and result[1]["fecha_evento"] is None
