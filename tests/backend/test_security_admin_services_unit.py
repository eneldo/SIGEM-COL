from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from src.backend.services import rol_service as rs
from src.backend.services import usuario_service as us

NOW = datetime(2026, 1, 2, tzinfo=UTC)


class Result:
    def __init__(self, value=None, rows=None):
        self.value = value
        self.rows = rows or []

    def scalar_one_or_none(self):
        return self.value

    def scalar_one(self):
        return self.value

    def scalars(self):
        return self

    def all(self):
        return self.rows


def database(*results):
    return SimpleNamespace(
        execute=AsyncMock(side_effect=list(results)),
        add=Mock(),
        delete=AsyncMock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
        refresh=AsyncMock(),
    )


def role(**values):
    defaults = {
        "id": uuid4(),
        "codigo": "ADMIN",
        "nombre": "Administrador",
        "descripcion": "Administra",
        "nivel": 1,
        "estado": "ACTIVO",
        "created_at": NOW,
        "updated_at": NOW,
        "deleted_at": None,
    }
    defaults.update(values)
    return SimpleNamespace(**defaults)


def permission(**values):
    defaults = {
        "id": uuid4(),
        "codigo": "USUARIOS_LEER",
        "nombre": "Leer usuarios",
        "descripcion": "Consulta",
        "modulo": "USUARIOS",
        "accion": "LEER",
        "estado": "ACTIVO",
    }
    defaults.update(values)
    return SimpleNamespace(**defaults)


def user(**values):
    defaults = {
        "id": uuid4(),
        "municipio_id": uuid4(),
        "codigo": "USR-1",
        "username": "ana",
        "email": "ana@example.com",
        "nombre_completo": "Ana Pérez",
        "telefono": "3000000000",
        "cargo": "Gestora",
        "activo": 1,
        "must_change_password": True,
        "mfa_activo": False,
        "ultimo_acceso": NOW,
        "intentos_fallidos": 0,
        "created_at": NOW,
        "updated_at": NOW,
        "deleted_at": None,
        "deleted_by": None,
    }
    defaults.update(values)
    return SimpleNamespace(**defaults)


@pytest.mark.parametrize(
    ("payload", "message"),
    [({}, "código"), ({"codigo": "R"}, "nombre")],
)
async def test_create_rol_requires_fields(payload, message):
    with pytest.raises(ValueError, match=message):
        await rs.create_rol(database(), payload)


async def test_create_rol_rejects_duplicate_and_adds_only_existing_permissions():
    with pytest.raises(ValueError, match="Ya existe"):
        await rs.create_rol(database(Result(uuid4())), {"codigo": "R", "nombre": "Rol"})

    valid_id, missing_id = uuid4(), uuid4()
    permiso = permission(id=valid_id)
    db = database(
        Result(None),
        Result(permiso),
        Result(None),
        Result(
            rows=[
                (
                    valid_id,
                    permiso.codigo,
                    permiso.nombre,
                    permiso.modulo,
                    permiso.accion,
                )
            ]
        ),
    )
    result = await rs.create_rol(
        db,
        {
            "codigo": "R",
            "nombre": "Rol",
            "descripcion": "Descripción",
            "nivel": 3,
            "permisos_ids": [valid_id, missing_id],
        },
    )

    assert result["codigo"] == "R"
    assert result["nivel"] == 3
    assert result["permisos"][0]["id"] == str(valid_id)
    assert db.add.call_count == 2
    db.commit.assert_awaited_once()


async def test_create_rol_defaults_without_permissions():
    db = database(Result(None), Result(rows=[]))
    result = await rs.create_rol(db, {"codigo": "R", "nombre": "Rol"})

    assert result["descripcion"] is None
    assert result["nivel"] == 1
    assert result["estado"] == "ACTIVO"


async def test_list_roles_filters_paginates_and_serializes_permissions():
    item = role()
    permiso_id = uuid4()
    db = database(
        Result(1),
        Result(rows=[item]),
        Result(rows=[(permiso_id, "P", "Permiso", "MOD", "VER")]),
    )
    result = await rs.list_roles(db, {"search": "adm", "page": 0, "page_size": 200})

    assert result["items"][0]["permisos"][0]["codigo"] == "P"
    assert result["page"] == 1
    assert result["page_size"] == 100
    assert result["total_pages"] == 1
    assert (await rs.list_roles(database(Result(0), Result(rows=[]))))["items"] == []


async def test_get_rol_found_and_missing():
    rid = uuid4()
    assert await rs.get_rol(database(Result(None)), rid) is None

    item = role(id=rid)
    result = await rs.get_rol(database(Result(item), Result(rows=[])), rid)
    assert result["id"] == str(rid)
    assert result["nombre"] == item.nombre


async def test_update_rol_missing_and_all_fields_permissions():
    rid, valid_id, invalid_id = uuid4(), uuid4(), uuid4()
    assert await rs.update_rol(database(Result(None)), rid, {}) is None

    item = role(id=rid)
    old_relation = SimpleNamespace(rol_id=rid, permiso_id=uuid4())
    db = database(
        Result(item),
        Result(rows=[old_relation]),
        Result(permission(id=valid_id)),
        Result(None),
        Result(item),
        Result(rows=[]),
    )
    result = await rs.update_rol(
        db,
        rid,
        {
            "nombre": "Nuevo",
            "descripcion": None,
            "nivel": 5,
            "estado": "INACTIVO",
            "permisos_ids": [valid_id, invalid_id],
        },
    )

    assert result["nombre"] == "Nuevo"
    assert result["nivel"] == 5
    assert result["estado"] == "INACTIVO"
    db.delete.assert_awaited_once_with(old_relation)
    db.add.assert_called_once()


async def test_update_rol_without_optional_changes():
    item = role()
    result = await rs.update_rol(
        database(Result(item), Result(item), Result(rows=[])), item.id, {}
    )
    assert result["codigo"] == item.codigo


async def test_delete_rol_soft_delete_and_missing():
    rid = uuid4()
    assert await rs.delete_rol(database(Result(None)), rid) is None

    item = role(id=rid)
    db = database(Result(item))
    result = await rs.delete_rol(db, rid)
    assert result["id"] == str(rid)
    assert result["deleted_at"]
    assert "eliminado exitosamente" in result["message"]
    db.commit.assert_awaited_once()


async def test_list_permisos_with_and_without_module_filter():
    item = permission()
    filtered = await rs.list_permisos(
        database(Result(rows=[item])), {"modulo": "USUARIOS"}
    )
    empty = await rs.list_permisos(database(Result(rows=[])))

    assert filtered == {
        "items": [
            {
                "id": str(item.id),
                "codigo": item.codigo,
                "nombre": item.nombre,
                "descripcion": item.descripcion,
                "modulo": item.modulo,
                "accion": item.accion,
                "estado": item.estado,
            }
        ],
        "total": 1,
    }
    assert empty == {"items": [], "total": 0}


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({}, "código"),
        ({"codigo": "U"}, "username"),
        ({"codigo": "U", "username": "ana"}, "email"),
        ({"codigo": "U", "username": "ana", "email": "a@x.co"}, "nombre completo"),
        (
            {
                "codigo": "U",
                "username": "ana",
                "email": "a@x.co",
                "nombre_completo": "Ana",
            },
            "contraseña",
        ),
    ],
)
async def test_create_usuario_requires_fields(payload, message):
    with pytest.raises(ValueError, match=message):
        await us.create_usuario(database(), uuid4(), payload)


def valid_user_payload(**values):
    payload = {
        "codigo": "USR-1",
        "username": "ana",
        "email": "ana@example.com",
        "nombre_completo": "Ana Pérez",
        "password": "Secret123!",
    }
    payload.update(values)
    return payload


async def test_create_usuario_rejects_duplicate_code_and_username():
    mid = uuid4()
    with pytest.raises(ValueError, match="código"):
        await us.create_usuario(database(Result(uuid4())), mid, valid_user_payload())
    with pytest.raises(ValueError, match="username"):
        await us.create_usuario(
            database(Result(None), Result(uuid4())), mid, valid_user_payload()
        )


async def test_create_usuario_translates_integrity_error():
    db = database(Result(None), Result(None))
    db.flush.side_effect = IntegrityError("insert", {}, Exception("duplicate"))

    with patch.object(us, "get_password_hash", return_value="hash"):
        with pytest.raises(ValueError, match="incluye usuarios eliminados"):
            await us.create_usuario(db, uuid4(), valid_user_payload())


async def test_create_usuario_with_valid_role_and_dependency():
    mid, rol_id, dependencia_id = uuid4(), uuid4(), uuid4()
    db = database(Result(None), Result(None), Result(role(id=rol_id)))

    with patch.object(us, "get_password_hash", return_value="hashed") as hasher:
        result = await us.create_usuario(
            db,
            mid,
            valid_user_payload(
                telefono="300",
                cargo="Gestora",
                rol_id=rol_id,
                dependencia_id=dependencia_id,
            ),
        )

    assert result["municipio_id"] == str(mid)
    assert result["telefono"] == "300"
    assert result["must_change_password"] is True
    assert db.add.call_count == 3
    assert db.flush.await_count == 2
    hasher.assert_called_once_with("Secret123!")


async def test_create_usuario_ignores_missing_role_and_uses_defaults():
    db = database(Result(None), Result(None), Result(None))
    with patch.object(us, "get_password_hash", return_value="hashed"):
        result = await us.create_usuario(
            db, uuid4(), valid_user_payload(rol_id=uuid4())
        )

    assert result["telefono"] is None
    assert result["cargo"] is None
    assert db.add.call_count == 1


async def test_list_usuarios_filters_states_and_serializes_roles_and_dates():
    mid = uuid4()
    first = user(municipio_id=mid)
    second = user(municipio_id=mid, ultimo_acceso=None, activo=0)
    db = database(
        Result(2),
        Result(rows=[first, second]),
        Result(rows=[("ADMIN", "Administrador")]),
        Result(rows=[]),
    )
    result = await us.list_usuarios(
        db,
        mid,
        {"search": "ana", "estado": "ACTIVO", "page": 0, "page_size": 101},
    )

    assert result["page"] == 1 and result["page_size"] == 100
    assert result["items"][0]["roles"] == [
        {"codigo": "ADMIN", "nombre": "Administrador"}
    ]
    assert result["items"][0]["ultimo_acceso"] == NOW.isoformat()
    assert result["items"][1]["ultimo_acceso"] is None

    inactive = await us.list_usuarios(
        database(Result(0), Result(rows=[])), mid, {"estado": "INACTIVO"}
    )
    other = await us.list_usuarios(
        database(Result(0), Result(rows=[])), mid, {"estado": "OTRO"}
    )
    assert inactive["total_pages"] == 0
    assert other["items"] == []


async def test_get_usuario_found_and_missing():
    mid, uid, rid = uuid4(), uuid4(), uuid4()
    assert await us.get_usuario(database(Result(None)), mid, uid) is None

    item = user(id=uid, municipio_id=mid, ultimo_acceso=None)
    result = await us.get_usuario(
        database(Result(item), Result(rows=[(rid, "ADMIN", "Administrador")])), mid, uid
    )
    assert result["id"] == str(uid)
    assert result["roles"][0] == {
        "id": str(rid),
        "codigo": "ADMIN",
        "nombre": "Administrador",
    }
    assert result["ultimo_acceso"] is None


async def test_update_usuario_missing_and_all_fields_with_role():
    mid, uid, rid = uuid4(), uuid4(), uuid4()
    assert await us.update_usuario(database(Result(None)), mid, uid, {}) is None

    item = user(id=uid, municipio_id=mid)
    old_relation = SimpleNamespace(usuario_id=uid, rol_id=uuid4())
    db = database(
        Result(item),
        Result(rows=[old_relation]),
        Result(role(id=rid)),
        Result(item),
        Result(rows=[(rid, "GESTOR", "Gestor")]),
    )
    result = await us.update_usuario(
        db,
        mid,
        uid,
        {
            "email": "nueva@example.com",
            "nombre_completo": "Ana Nueva",
            "telefono": None,
            "cargo": "Líder",
            "activo": 0,
            "must_change_password": False,
            "rol_id": rid,
        },
    )

    assert result["email"] == "nueva@example.com"
    assert result["activo"] == 0
    assert result["must_change_password"] is False
    db.delete.assert_awaited_once_with(old_relation)
    db.add.assert_called_once()


async def test_update_usuario_clears_role_and_ignores_invalid_role():
    mid, uid = uuid4(), uuid4()
    item = user(id=uid, municipio_id=mid)
    cleared = await us.update_usuario(
        database(Result(item), Result(rows=[]), Result(item), Result(rows=[])),
        mid,
        uid,
        {"rol_id": None},
    )
    assert cleared["roles"] == []

    db = database(
        Result(item),
        Result(rows=[]),
        Result(None),
        Result(item),
        Result(rows=[]),
    )
    await us.update_usuario(db, mid, uid, {"rol_id": uuid4()})
    db.add.assert_not_called()


async def test_update_usuario_without_optional_changes():
    item = user()
    result = await us.update_usuario(
        database(Result(item), Result(item), Result(rows=[])),
        item.municipio_id,
        item.id,
        {},
    )
    assert result["codigo"] == item.codigo


async def test_delete_usuario_soft_delete_with_and_without_actor():
    mid, uid, actor = uuid4(), uuid4(), uuid4()
    assert await us.delete_usuario(database(Result(None)), mid, uid) is None

    item = user(id=uid, municipio_id=mid)
    result = await us.delete_usuario(database(Result(item)), mid, uid, actor)
    assert result["id"] == str(uid)
    assert item.deleted_by == actor
    assert result["deleted_at"]

    item_without_actor = user(id=uid, municipio_id=mid)
    result = await us.delete_usuario(database(Result(item_without_actor)), mid, uid)
    assert result["nombre"] == item_without_actor.nombre_completo
    assert item_without_actor.deleted_by is None
