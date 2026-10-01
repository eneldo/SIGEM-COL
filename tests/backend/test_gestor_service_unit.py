from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.backend.services import gestor_service as service

NOW = datetime.now(UTC)


class Result:
    def __init__(self, value=None, rows=None):
        self.value = value
        self.rows = [] if rows is None else rows

    def first(self):
        return self.rows[0] if self.rows else None

    def all(self):
        return self.rows

    def scalars(self):
        return self

    def scalar_one_or_none(self):
        return self.value


class DB:
    def __init__(self, *, executes=(), scalars=()):
        self.execute = AsyncMock(side_effect=list(executes))
        self.scalar = AsyncMock(side_effect=list(scalars))
        self.commit = AsyncMock()
        self.flush = AsyncMock(side_effect=self._assign_ids)
        self.refresh = AsyncMock()
        self.add = Mock(side_effect=self._capture)
        self.added = []

    def _capture(self, value):
        self.added.append(value)

    def _assign_ids(self):
        for value in self.added:
            if getattr(value, "id", None) is None:
                value.id = uuid4()


def obj(**values):
    defaults = {
        "id": uuid4(),
        "usuario_id": uuid4(),
        "municipio_id": uuid4(),
        "codigo": "GES-000001",
        "username": "jperez",
        "email": "j@example.com",
        "telefono": "300",
        "nombre_completo": "Juan Pérez",
        "cargo": "Gestor",
        "dependencia_principal_id": None,
        "estado": service.ESTADO_ACTIVO,
        "mfa_activo": False,
        "must_change_password": False,
        "ultimo_acceso": NOW,
        "ip_ultimo_acceso": "127.0.0.1",
        "intentos_fallidos": 0,
        "ultimo_cambio_password": NOW,
        "created_at": NOW,
        "updated_at": NOW,
        "activo": 1,
        "fecha_bloqueo": None,
        "motivo_bloqueo": None,
        "eliminado": False,
    }
    defaults.update(values)
    return SimpleNamespace(**defaults)


@pytest.fixture
def audit(monkeypatch):
    log = AsyncMock()
    monkeypatch.setattr(
        service, "AuditService", Mock(return_value=SimpleNamespace(log_event=log))
    )
    return log


async def test_query_helpers_and_build_dict():
    gestor, usuario = obj(), obj()
    assert await service._get_gestor_usuario(
        DB(executes=[Result(rows=[])]), uuid4(), uuid4()
    ) == (
        None,
        None,
    )
    assert await service._get_gestor_usuario(
        DB(executes=[Result(rows=[(gestor, usuario)])]), uuid4(), uuid4()
    ) == (gestor, usuario)

    role = obj(codigo=service.ROL_GESTOR_LIDER, nombre="Gestor líder", nivel=1)
    dep_id = uuid4()
    db = DB(
        executes=[
            Result(rows=[role]),
            Result(rows=[(dep_id, "Planeación", "PLA", True)]),
        ]
    )
    data = await service._build_gestor_dict(db, gestor, usuario)
    assert data["rol"] == "Gestor líder"
    assert data["roles"] == [service.ROL_GESTOR_LIDER]
    assert data["dependencia_principal"] == "Planeación"
    assert data["dependencias"] == [
        {"id": dep_id, "nombre": "Planeación", "es_principal": True}
    ]

    empty = await service._build_gestor_dict(
        DB(executes=[Result(rows=[]), Result(rows=[])]), gestor, usuario
    )
    assert empty["rol"] is None and empty["rol_id"] is None


async def test_role_and_dependency_validation():
    role = obj(codigo="GESTOR")
    assert await service._validar_rol(DB(scalars=[role]), role.id) is role
    assert await service._validar_rol(DB(scalars=[role]), None) is role
    with pytest.raises(ValueError, match="seleccionado no existe"):
        await service._validar_rol(DB(scalars=[None]), uuid4())
    with pytest.raises(ValueError, match="GESTOR_LIDER"):
        await service._validar_rol(DB(scalars=[None]), None)

    await service._validar_dependencias(DB(), uuid4(), set())
    dep_id = uuid4()
    await service._validar_dependencias(DB(scalars=[1]), uuid4(), {dep_id, None})
    with pytest.raises(ValueError, match="dependencias seleccionadas"):
        await service._validar_dependencias(DB(scalars=[0]), uuid4(), {dep_id})


@pytest.mark.parametrize(
    ("last", "expected"),
    [("GES-000009", "GES-000010"), (None, "GES-000001"), ("OTRO", "GES-000001")],
)
async def test_generate_gestor_code(last, expected):
    assert (
        await service.generate_gestor_code(DB(executes=[Result(value=last)]), uuid4())
        == expected
    )


async def test_username_generation_variants(monkeypatch):
    assert await service._username_existe(DB(scalars=[uuid4()]), "used") is True
    assert await service._username_existe(DB(scalars=[None]), "free") is False
    exists = AsyncMock(side_effect=[True, False])
    monkeypatch.setattr(service, "_username_existe", exists)
    assert (
        await service.generate_username(DB(), uuid4(), "Juan Carlos Pérez")
        == "jcarlospérez2"
    )
    monkeypatch.setattr(service, "_username_existe", AsyncMock(return_value=False))
    assert await service.generate_username(DB(), uuid4(), " Solo ") == "solo"
    assert await service.generate_username(DB(), uuid4(), "") == "usuario"


@pytest.mark.parametrize(
    ("data", "message"),
    [
        ({"email": "x@y.co"}, "nombre completo"),
        ({"nombre_completo": "Nombre"}, "correo electrónico"),
        (
            {"nombre_completo": "Nombre", "email": "x@y.co", "password": "short"},
            "al menos",
        ),
        (
            {"nombre_completo": "Nombre", "email": "x@y.co", "username": "?"},
            "usuario debe",
        ),
    ],
)
async def test_create_rejects_invalid_input(data, message):
    with pytest.raises(ValueError, match=message):
        await service.create_gestor(DB(), uuid4(), data)


async def test_create_rejects_role_dependency_and_duplicate(monkeypatch):
    role = obj(codigo="ADMINISTRADOR_MUNICIPAL")
    monkeypatch.setattr(service, "_validar_rol", AsyncMock(return_value=role))
    data = {"nombre_completo": "Nombre", "email": "x@y.co"}
    with pytest.raises(ValueError, match="permisos"):
        await service.create_gestor(DB(), uuid4(), data, {"GESTOR"})

    role.codigo = "GESTOR"
    with pytest.raises(ValueError, match="dependencia principal"):
        await service.create_gestor(DB(), uuid4(), data)

    data |= {"dependencia_principal_id": uuid4(), "username": "usuario"}
    monkeypatch.setattr(service, "_username_existe", AsyncMock(return_value=True))
    with pytest.raises(ValueError, match="ya está en uso"):
        await service.create_gestor(DB(), uuid4(), data)


async def test_create_generated_credentials_and_coordinator_dependencies(
    monkeypatch, audit
):
    mid, principal, extra = uuid4(), uuid4(), uuid4()
    role = obj(codigo=service.ROL_GESTOR_LIDER)
    monkeypatch.setattr(service, "_validar_rol", AsyncMock(return_value=role))
    validate = AsyncMock()
    monkeypatch.setattr(service, "_validar_dependencias", validate)
    monkeypatch.setattr(
        service, "generate_gestor_code", AsyncMock(return_value="GES-000007")
    )
    monkeypatch.setattr(service, "generate_username", AsyncMock(return_value="jperez"))
    monkeypatch.setattr(
        service, "generate_temporary_password", Mock(return_value="T" * 24)
    )
    monkeypatch.setattr(service, "get_password_hash", Mock(return_value="hash"))
    db = DB()
    result = await service.create_gestor(
        db,
        mid,
        {
            "nombre_completo": " Juan Pérez ",
            "email": "j@p.co",
            "telefono": "300",
            "cargo": "Líder",
            "dependencia_principal_id": principal,
            "dependencias_adicionales": [extra],
        },
    )
    assert result["username"] == "jperez"
    assert result["must_change_password"] is True
    assert len(db.added) == 4
    validate.assert_awaited_once_with(db, mid, {principal})
    db.commit.assert_awaited_once()
    audit.assert_awaited_once()


async def test_create_custom_credentials_and_additional_dependencies(
    monkeypatch, audit
):
    mid, principal, extra = uuid4(), uuid4(), uuid4()
    role = obj(codigo="ANALISTA")
    monkeypatch.setattr(service, "_validar_rol", AsyncMock(return_value=role))
    monkeypatch.setattr(service, "_validar_dependencias", AsyncMock())
    monkeypatch.setattr(
        service, "generate_gestor_code", AsyncMock(return_value="GES-000008")
    )
    monkeypatch.setattr(service, "_username_existe", AsyncMock(return_value=False))
    monkeypatch.setattr(service, "get_password_hash", Mock(return_value="hash"))
    db = DB()
    result = await service.create_gestor(
        db,
        mid,
        {
            "nombre_completo": "Ana Díaz",
            "email": "a@d.co",
            "username": "adiaz",
            "password": "A" * 15,
            "dependencia_principal_id": principal,
            "dependencias_adicionales": [principal, extra],
        },
    )
    assert result["temp_password"] == "A" * 15
    assert result["must_change_password"] is False
    assert len(db.added) == 5


async def test_list_gestores_all_filters_and_bounds(monkeypatch):
    gestor, usuario = obj(), obj()
    build = AsyncMock(return_value={"id": gestor.id})
    monkeypatch.setattr(service, "_build_gestor_dict", build)
    db = DB(scalars=[1], executes=[Result(rows=[(gestor, usuario)])])
    role_id = uuid4()
    result = await service.list_gestores(
        db,
        uuid4(),
        {
            "search": "ana",
            "estado": "ACTIVO",
            "cargo": "líder",
            "rol_id": str(role_id),
            "page": 0,
            "page_size": 101,
        },
    )
    assert result == {
        "gestores": [{"id": gestor.id}],
        "total": 1,
        "page": 1,
        "page_size": 100,
        "total_pages": 1,
    }
    empty = await service.list_gestores(
        DB(scalars=[None], executes=[Result(rows=[])]), uuid4()
    )
    assert empty["total"] == 0 and empty["total_pages"] == 0


async def test_get_gestor_found_and_missing(monkeypatch):
    gestor, usuario = obj(), obj()
    monkeypatch.setattr(
        service, "_get_gestor_usuario", AsyncMock(return_value=(None, None))
    )
    assert await service.get_gestor(DB(), uuid4(), uuid4()) is None
    monkeypatch.setattr(
        service, "_get_gestor_usuario", AsyncMock(return_value=(gestor, usuario))
    )
    monkeypatch.setattr(
        service, "_build_gestor_dict", AsyncMock(return_value={"id": gestor.id})
    )
    assert (await service.get_gestor(DB(), uuid4(), gestor.id))["id"] == gestor.id


async def test_mark_principal_updates_existing_and_adds_missing():
    dep1, dep2 = uuid4(), uuid4()
    rows = [
        obj(dependencia_id=dep1, es_principal=True),
        obj(dependencia_id=dep2, es_principal=False),
    ]
    db = DB(executes=[Result(rows=rows)])
    await service._marcar_principal(db, uuid4(), uuid4(), dep2)
    assert rows[0].es_principal is False and rows[1].es_principal is True
    assert not db.added
    db = DB(executes=[Result(rows=rows)])
    new_dep = uuid4()
    await service._marcar_principal(db, uuid4(), uuid4(), new_dep)
    assert db.added[0].dependencia_id == new_dep


async def test_update_gestor_missing_and_all_fields(monkeypatch, audit):
    monkeypatch.setattr(
        service, "_get_gestor_usuario", AsyncMock(return_value=(None, None))
    )
    assert await service.update_gestor(DB(), uuid4(), uuid4(), {}) is None

    gestor, usuario = obj(), obj()
    monkeypatch.setattr(
        service, "_get_gestor_usuario", AsyncMock(return_value=(gestor, usuario))
    )
    mark = AsyncMock()
    monkeypatch.setattr(service, "_marcar_principal", mark)
    monkeypatch.setattr(
        service, "_build_gestor_dict", AsyncMock(return_value={"ok": True})
    )
    dep = uuid4()
    db = DB()
    result = await service.update_gestor(
        db,
        uuid4(),
        gestor.id,
        {
            "nombre_completo": "Nuevo",
            "cargo": None,
            "email": "n@x.co",
            "telefono": "321",
            "dependencia_principal_id": dep,
        },
    )
    assert result == {"ok": True}
    assert usuario.nombre_completo == gestor.nombre_completo == "Nuevo"
    assert (
        usuario.cargo is None
        and usuario.email == "n@x.co"
        and usuario.telefono == "321"
    )
    mark.assert_awaited_once()
    assert db.refresh.await_count == 2


async def test_permissions_missing_role_only_and_no_changes(monkeypatch, audit):
    monkeypatch.setattr(
        service, "_get_gestor_usuario", AsyncMock(return_value=(None, None))
    )
    assert await service.update_gestor_permissions(DB(), uuid4(), uuid4(), {}) is None

    gestor, usuario, role = obj(), obj(), obj(codigo="ANALISTA")
    monkeypatch.setattr(
        service, "_get_gestor_usuario", AsyncMock(return_value=(gestor, usuario))
    )
    monkeypatch.setattr(service, "_validar_rol", AsyncMock(return_value=role))
    monkeypatch.setattr(
        service, "_build_gestor_dict", AsyncMock(return_value={"ok": True})
    )
    db = DB(executes=[Result()])
    result = await service.update_gestor_permissions(
        db, uuid4(), gestor.id, {"rol_id": role.id}
    )
    assert result == {"ok": True} and len(db.added) == 1

    db = DB()
    assert await service.update_gestor_permissions(db, uuid4(), gestor.id, {}) == {
        "ok": True
    }


async def test_permissions_dependencies_role_restriction_and_clear(monkeypatch, audit):
    gestor, usuario = obj(), obj()
    monkeypatch.setattr(
        service, "_get_gestor_usuario", AsyncMock(return_value=(gestor, usuario))
    )
    monkeypatch.setattr(
        service,
        "_get_roles",
        AsyncMock(return_value=[obj(codigo=service.ROL_GESTOR_LIDER)]),
    )
    validate = AsyncMock()
    monkeypatch.setattr(service, "_validar_dependencias", validate)
    monkeypatch.setattr(
        service, "_build_gestor_dict", AsyncMock(return_value={"ok": True})
    )
    principal, extra = uuid4(), uuid4()
    db = DB(executes=[Result()])
    await service.update_gestor_permissions(
        db,
        uuid4(),
        gestor.id,
        {"dependencia_principal_id": principal, "dependencias_adicionales": [extra]},
    )
    validate.assert_awaited_once()
    assert len(db.added) == 1
    assert gestor.dependencia_principal_id == principal

    monkeypatch.setattr(service, "_get_roles", AsyncMock(return_value=[]))
    monkeypatch.setattr(
        service,
        "_validar_rol",
        AsyncMock(return_value=obj(codigo=service.ROL_GESTOR_LIDER)),
    )
    db = DB(executes=[Result(), Result()])
    await service.update_gestor_permissions(
        db,
        uuid4(),
        gestor.id,
        {
            "rol_id": uuid4(),
            "dependencia_principal_id": None,
            "dependencias_adicionales": [extra, None],
        },
    )
    assert gestor.dependencia_principal_id is None
    assert len(db.added) == 1

    monkeypatch.setattr(
        service, "_validar_rol", AsyncMock(return_value=obj(codigo="ANALISTA"))
    )
    db = DB(executes=[Result(), Result()])
    await service.update_gestor_permissions(
        db,
        uuid4(),
        gestor.id,
        {
            "rol_id": uuid4(),
            "dependencia_principal_id": None,
            "dependencias_adicionales": [extra, None],
        },
    )
    assert len(db.added) == 2


@pytest.mark.parametrize(
    ("status", "activo", "blocked"),
    [
        (service.ESTADO_BLOQUEADO, 0, True),
        (service.ESTADO_ACTIVO, 1, False),
        (service.ESTADO_INACTIVO, 0, False),
    ],
)
async def test_change_status_branches(monkeypatch, audit, status, activo, blocked):
    gestor, usuario = obj(), obj()
    monkeypatch.setattr(
        service, "_get_gestor_usuario", AsyncMock(return_value=(gestor, usuario))
    )
    monkeypatch.setattr(
        service, "_build_gestor_dict", AsyncMock(return_value={"estado": status})
    )
    db = DB()
    result = await service._change_gestor_status(
        db, uuid4(), gestor.id, status, "EVENT", " razón " if blocked else None
    )
    assert result["estado"] == status and usuario.activo == activo
    if blocked:
        assert usuario.fecha_bloqueo is not None and usuario.motivo_bloqueo == " razón "
    elif status == service.ESTADO_ACTIVO:
        assert usuario.fecha_bloqueo is None and usuario.motivo_bloqueo is None


async def test_status_missing_wrappers_and_block_validation(monkeypatch):
    monkeypatch.setattr(
        service, "_get_gestor_usuario", AsyncMock(return_value=(None, None))
    )
    assert await service._change_gestor_status(DB(), uuid4(), uuid4(), "X", "E") is None
    change = AsyncMock(return_value={"ok": True})
    monkeypatch.setattr(service, "_change_gestor_status", change)
    mid, gid = uuid4(), uuid4()
    assert await service.activate_gestor(DB(), mid, gid) == {"ok": True}
    assert await service.deactivate_gestor(DB(), mid, gid) == {"ok": True}
    assert await service.unblock_gestor(DB(), mid, gid) == {"ok": True}
    assert await service.block_gestor(DB(), mid, gid, " motivo ") == {"ok": True}
    assert change.await_args_list[-1].kwargs["motivo"] == "motivo"
    for invalid in (None, "   "):
        with pytest.raises(ValueError, match="obligatorio"):
            await service.block_gestor(DB(), mid, gid, invalid)


async def test_reset_password_missing_short_custom_and_generated(monkeypatch, audit):
    monkeypatch.setattr(
        service, "_get_gestor_usuario", AsyncMock(return_value=(None, None))
    )
    assert await service.reset_password(DB(), uuid4(), uuid4()) is None

    gestor, usuario = obj(), obj()
    monkeypatch.setattr(
        service, "_get_gestor_usuario", AsyncMock(return_value=(gestor, usuario))
    )
    with pytest.raises(ValueError, match="al menos"):
        await service.reset_password(DB(), uuid4(), gestor.id, "short")

    monkeypatch.setattr(service, "get_password_hash", Mock(return_value="hash"))
    result = await service.reset_password(DB(), uuid4(), gestor.id, "C" * 15)
    assert (
        result["must_change_password"] is False and result["temp_password"] == "C" * 15
    )
    assert usuario.password_hash == "hash" and usuario.activo == 1

    monkeypatch.setattr(
        service, "generate_temporary_password", Mock(return_value="T" * 24)
    )
    result = await service.reset_password(DB(), uuid4(), gestor.id)
    assert (
        result["must_change_password"] is True and result["temp_password"] == "T" * 24
    )


async def test_soft_delete_missing_and_success(monkeypatch, audit):
    monkeypatch.setattr(
        service, "_get_gestor_usuario", AsyncMock(return_value=(None, None))
    )
    assert await service.soft_delete_gestor(DB(), uuid4(), uuid4()) is None

    gestor, usuario = obj(), obj()
    monkeypatch.setattr(
        service, "_get_gestor_usuario", AsyncMock(return_value=(gestor, usuario))
    )
    db = DB(executes=[Result(), Result()])
    result = await service.soft_delete_gestor(db, uuid4(), gestor.id)
    assert (
        gestor.eliminado is True and usuario.eliminado is True and usuario.activo == 0
    )
    assert result["eliminado"] is True and result["deleted_at"]
    assert db.execute.await_count == 2


async def test_list_accesses_missing_empty_and_rows(monkeypatch):
    monkeypatch.setattr(
        service, "_get_gestor_usuario", AsyncMock(return_value=(None, None))
    )
    assert await service.list_gestor_accesos(DB(), uuid4(), uuid4()) is None

    gestor, usuario = obj(), obj()
    monkeypatch.setattr(
        service, "_get_gestor_usuario", AsyncMock(return_value=(gestor, usuario))
    )
    assert (
        await service.list_gestor_accesos(
            DB(executes=[Result(rows=[])]), uuid4(), gestor.id
        )
        == []
    )
    access = obj(
        exitoso=False,
        ip_address="10.0.0.1",
        user_agent="pytest",
        razon_fallo="PASSWORD",
        fecha_intento=NOW,
    )
    rows = await service.list_gestor_accesos(
        DB(executes=[Result(rows=[access])]), uuid4(), gestor.id, limit=5, offset=2
    )
    assert rows == [
        {
            "id": access.id,
            "exitoso": False,
            "ip_address": "10.0.0.1",
            "user_agent": "pytest",
            "razon_fallo": "PASSWORD",
            "fecha_intento": NOW,
        }
    ]
