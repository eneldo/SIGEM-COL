from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.backend.services import (
    dependencia_service as ds,
)
from src.backend.services import (
    linea_service as ls,
)
from src.backend.services import (
    producto_service as xs,
)
from src.backend.services import (
    programa_service as ps,
)

NOW = datetime.now(UTC)


class Result:
    def __init__(self, value=None, rows=None):
        self.value = value
        self.rows = rows or []

    def scalar_one_or_none(self):
        return self.value

    def scalar_one(self):
        return self.value

    def scalar(self):
        return self.value

    def first(self):
        return self.rows[0] if self.rows else None

    def all(self):
        return self.rows

    def scalars(self):
        return self


def db_with(*results):
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=list(results)),
        add=Mock(),
        commit=AsyncMock(),
        refresh=AsyncMock(),
    )
    return db


def obj(**values):
    defaults = {
        "id": uuid4(),
        "municipio_id": uuid4(),
        "codigo": "COD-1",
        "numero": "1",
        "nombre": "Nombre",
        "sector": "Salud",
        "descripcion": "Descripción",
        "orden": 1,
        "estado": "ACTIVO",
        "created_at": NOW,
        "updated_at": NOW,
        "deleted_at": None,
        "deleted_by": None,
        "dependencia_padre_id": None,
        "nivel": 1,
        "codigo_indicador": "IND-1",
        "indicador": "Indicador",
        "meta_redactada": "Meta",
        "linea_base": 1,
        "meta_cuatrienio": 2,
        "unidad_medida": "Número",
        "dependencia_responsable_id": None,
        "gestor_lider_id": None,
        "asignado_at": None,
    }
    defaults.update(values)
    return SimpleNamespace(**defaults)


@pytest.mark.parametrize(
    ("service", "function", "data", "message"),
    [
        (ls, ls.create_linea, {}, "plan de desarrollo"),
        (ls, ls.create_linea, {"plan_desarrollo_id": uuid4()}, "nombre"),
        (ps, ps.create_programa, {}, "línea estratégica"),
        (ps, ps.create_programa, {"linea_estrategica_id": uuid4()}, "código"),
        (
            ps,
            ps.create_programa,
            {"linea_estrategica_id": uuid4(), "codigo": "P"},
            "nombre",
        ),
        (xs, xs.create_producto, {}, "programa"),
        (xs, xs.create_producto, {"programa_id": uuid4()}, "código"),
        (xs, xs.create_producto, {"programa_id": uuid4(), "codigo": "X"}, "nombre"),
    ],
)
async def test_required_create_fields(service, function, data, message):
    with pytest.raises(ValueError, match=message):
        await function(db_with(), uuid4(), data)


async def test_linea_crud_filters_and_errors():
    mid, plan_id, lid, uid = uuid4(), uuid4(), uuid4(), uuid4()
    plan = obj(id=plan_id, nombre="Plan")
    db = db_with(Result(plan), Result(0), Result(lid), Result(None))
    data = await ls.create_linea(
        db,
        mid,
        {"plan_desarrollo_id": plan_id, "numero": "2", "nombre": "Línea"},
    )
    assert data["codigo"] == "LE-002"
    db.add.assert_called_once()

    with pytest.raises(ValueError, match="no existe"):
        await ls.create_linea(
            db_with(Result(None)), mid, {"plan_desarrollo_id": plan_id, "nombre": "L"}
        )

    linea = obj(municipio_id=mid, plan_desarrollo_id=plan_id, estado="ACTIVA")
    listed = await ls.list_lineas(
        db_with(Result(1), Result(rows=[(linea, "Plan")])),
        mid,
        {
            "search": "x",
            "plan_desarrollo_id": plan_id,
            "estado": "ACTIVA",
            "page": 0,
            "page_size": 101,
        },
    )
    assert listed["lineas"][0]["plan_desarrollo_nombre"] == "Plan"
    assert listed["page"] == 1 and listed["page_size"] == 100
    assert (await ls.list_lineas(db_with(Result(0), Result(rows=[])), mid))[
        "total_pages"
    ] == 0
    assert await ls.get_linea(db_with(Result(rows=[])), mid, lid) is None
    assert (await ls.get_linea(db_with(Result(rows=[(linea, "Plan")])), mid, lid))[
        "id"
    ] == str(linea.id)
    assert await ls.update_linea(db_with(Result(None)), mid, lid, {}) is None

    with pytest.raises(ValueError, match="plan de desarrollo"):
        await ls.update_linea(
            db_with(Result(linea), Result(None)),
            mid,
            lid,
            {"plan_desarrollo_id": uuid4()},
        )
    with pytest.raises(ValueError, match="Ya existe"):
        await ls.update_linea(
            db_with(Result(linea), Result(obj())), mid, lid, {"codigo": "DUP"}
        )
    new_plan = uuid4()
    updated = await ls.update_linea(
        db_with(Result(linea), Result(plan), Result(None), Result("Plan nuevo")),
        mid,
        lid,
        {
            "plan_desarrollo_id": new_plan,
            "codigo": "N",
            "numero": "9",
            "nombre": "Nueva",
            "descripcion": None,
            "orden": 9,
            "estado": "INACTIVA",
        },
    )
    assert updated["codigo"] == "N" and updated["nombre"] == "Nueva"
    assert await ls.delete_linea(db_with(Result(None)), mid, lid) is None
    deleted = await ls.delete_linea(db_with(Result(linea)), mid, lid)
    assert deleted["deleted_at"]
    linea.soft_delete = Mock(side_effect=lambda user: setattr(linea, "deleted_at", NOW))
    deleted = await ls.delete_linea(db_with(Result(linea)), mid, lid, uid)
    assert deleted["id"] == str(linea.id) and linea.deleted_by == uid


async def test_programa_crud_filters_and_errors():
    mid, linea_id, pid, uid = uuid4(), uuid4(), uuid4(), uuid4()
    linea = obj(id=linea_id, codigo="LE-1")
    created = await ps.create_programa(
        db_with(Result(linea), Result(None)),
        mid,
        {"linea_estrategica_id": linea_id, "codigo": "P1", "nombre": "Programa"},
    )
    assert created["linea_estrategica_codigo"] == "LE-1"
    with pytest.raises(ValueError, match="no existe"):
        await ps.create_programa(
            db_with(Result(None)),
            mid,
            {"linea_estrategica_id": linea_id, "codigo": "P", "nombre": "N"},
        )
    with pytest.raises(ValueError, match="Ya existe"):
        await ps.create_programa(
            db_with(Result(linea), Result(obj())),
            mid,
            {"linea_estrategica_id": linea_id, "codigo": "P", "nombre": "N"},
        )

    programa = obj(municipio_id=mid, linea_estrategica_id=linea_id)
    listed = await ps.list_programas(
        db_with(Result(1), Result(rows=[(programa, "Línea", "LE-1")])),
        mid,
        {
            "search": "p",
            "linea_estrategica_id": linea_id,
            "estado": "ACTIVO",
            "page": -1,
            "page_size": 200,
        },
    )
    assert listed["programas"][0]["sector"] == "Salud"
    assert (await ps.list_programas(db_with(Result(0), Result(rows=[])), mid))[
        "programas"
    ] == []
    assert await ps.get_programa(db_with(Result(rows=[])), mid, pid) is None
    assert (
        await ps.get_programa(
            db_with(Result(rows=[(programa, "Línea", "LE-1")])), mid, pid
        )
    )["codigo"] == "COD-1"
    assert await ps.update_programa(db_with(Result(None)), mid, pid, {}) is None
    with pytest.raises(ValueError, match="línea estratégica"):
        await ps.update_programa(
            db_with(Result(programa), Result(None)),
            mid,
            pid,
            {"linea_estrategica_id": uuid4()},
        )
    with pytest.raises(ValueError, match="Ya existe"):
        await ps.update_programa(
            db_with(Result(programa), Result(obj())), mid, pid, {"codigo": "DUP"}
        )
    updated = await ps.update_programa(
        db_with(Result(programa), Result(linea), Result(None), Result(linea)),
        mid,
        pid,
        {
            "linea_estrategica_id": linea_id,
            "codigo": "NEW",
            "nombre": "Nuevo",
            "sector": "Otro",
            "descripcion": None,
            "estado": "INACTIVO",
        },
    )
    assert updated["codigo"] == "NEW" and updated["nombre"] == "Nuevo"
    assert await ps.delete_programa(db_with(Result(None)), mid, pid) is None
    assert (await ps.delete_programa(db_with(Result(programa)), mid, pid))["deleted_at"]
    assert (await ps.delete_programa(db_with(Result(programa)), mid, pid, uid))[
        "id"
    ] == str(programa.id)
    assert programa.deleted_by == uid


async def test_producto_create_list_get_and_errors():
    mid, prog_id, dep_id, gestor_id, xid = uuid4(), uuid4(), uuid4(), uuid4(), uuid4()
    prog = obj(id=prog_id, codigo="PR")
    payload = {
        "programa_id": prog_id,
        "codigo": "PX",
        "nombre": "Producto",
        "dependencia_responsable_id": dep_id,
        "gestor_lider_id": gestor_id,
    }
    made = await xs.create_producto(
        db_with(Result(prog), Result(obj()), Result(obj()), Result(None)), mid, payload
    )
    assert made["programa_codigo"] == "PR" and made["asignado_at"]
    for results, match in [
        ([Result(None)], "programa no existe"),
        ([Result(prog), Result(None)], "dependencia responsable"),
        ([Result(prog), Result(obj()), Result(None)], "gestor líder"),
        ([Result(prog), Result(obj()), Result(obj()), Result(obj())], "Ya existe"),
    ]:
        with pytest.raises(ValueError, match=match):
            await xs.create_producto(db_with(*results), mid, payload)
    minimal = {"programa_id": prog_id, "codigo": "P2", "nombre": "Mínimo"}
    assert (
        await xs.create_producto(db_with(Result(prog), Result(None)), mid, minimal)
    )["gestor_lider_id"] is None

    producto = obj(
        municipio_id=mid,
        programa_id=prog_id,
        dependencia_responsable_id=dep_id,
        gestor_lider_id=gestor_id,
        asignado_at=NOW,
    )
    filters = {
        "search": "x",
        "programa_id": prog_id,
        "dependencia_id": dep_id,
        "gestor_lider_id": gestor_id,
        "estado": "ACTIVO",
        "page": 0,
        "page_size": 200,
    }
    listed = await xs.list_productos(
        db_with(Result(1), Result(rows=[(producto, "Prog", "PR", "Dep", "Gestor")])),
        mid,
        filters,
    )
    assert listed["productos"][0]["gestor_lider_nombre"] == "Gestor"
    assert (await xs.list_productos(db_with(Result(0), Result(rows=[])), mid))[
        "productos"
    ] == []
    assert await xs.get_producto(db_with(Result(rows=[])), mid, xid) is None
    detail = await xs.get_producto(
        db_with(Result(rows=[(producto, "Prog", "PR", "Dep", "Gestor")])), mid, xid
    )
    assert detail["dependencia_responsable_nombre"] == "Dep"
    bare = obj(municipio_id=mid, programa_id=prog_id)
    detail = await xs.get_producto(
        db_with(Result(rows=[(bare, "Prog", "PR", None, None)])), mid, xid
    )
    assert detail["asignado_at"] is None


async def test_producto_update_delete_and_errors():
    mid, xid, prog_id, dep_id, gestor_id, uid = (uuid4() for _ in range(6))
    product = obj(municipio_id=mid, programa_id=prog_id)
    assert await xs.update_producto(db_with(Result(None)), mid, xid, {}) is None
    cases = [
        (
            {"programa_id": prog_id},
            [Result(product), Result(None)],
            "programa no existe",
        ),
        (
            {"dependencia_responsable_id": dep_id},
            [Result(product), Result(None)],
            "dependencia responsable",
        ),
        (
            {"gestor_lider_id": gestor_id},
            [Result(product), Result(None)],
            "gestor líder",
        ),
        ({"codigo": "DUP"}, [Result(product), Result(obj())], "Ya existe"),
    ]
    for data, results, match in cases:
        with pytest.raises(ValueError, match=match):
            await xs.update_producto(db_with(*results), mid, xid, data)
    prog = obj(id=prog_id, codigo="PR")
    update = {
        "programa_id": prog_id,
        "dependencia_responsable_id": dep_id,
        "gestor_lider_id": gestor_id,
        "codigo": "NEW",
        "nombre": "Nuevo",
        "codigo_indicador": "I2",
        "indicador": "Ind",
        "meta_redactada": "M",
        "linea_base": 3,
        "meta_cuatrienio": 4,
        "descripcion": None,
        "unidad_medida": "%",
        "estado": "INACTIVO",
    }
    results = [
        Result(product),
        Result(prog),
        Result(obj()),
        Result(obj()),
        Result(None),
        Result(prog),
        Result("Dep"),
        Result("Gestor"),
    ]
    updated = await xs.update_producto(db_with(*results), mid, xid, update)
    assert updated["codigo"] == "NEW" and updated["gestor_lider_nombre"] == "Gestor"
    same = await xs.update_producto(
        db_with(
            Result(product),
            Result(obj()),
            Result(prog),
            Result("Dep"),
            Result("Gestor"),
        ),
        mid,
        xid,
        {"gestor_lider_id": gestor_id},
    )
    assert same["gestor_lider_id"] == str(gestor_id)
    cleared = await xs.update_producto(
        db_with(Result(product), Result(prog)),
        mid,
        xid,
        {"dependencia_responsable_id": None, "gestor_lider_id": None},
    )
    assert (
        cleared["dependencia_responsable_id"] is None
        and cleared["gestor_lider_id"] is None
    )
    assert await xs.delete_producto(db_with(Result(None)), mid, xid) is None
    assert (await xs.delete_producto(db_with(Result(product)), mid, xid))["deleted_at"]
    assert (await xs.delete_producto(db_with(Result(product)), mid, xid, uid))[
        "id"
    ] == str(product.id)
    assert product.deleted_by == uid


async def test_dependencia_crud_filters_and_errors():
    mid, did, parent_id, uid = uuid4(), uuid4(), uuid4(), uuid4()
    dep = obj(municipio_id=mid, estado="ACTIVA", dependencia_padre_id=parent_id)
    listed = await ds.list_dependencias(
        db_with(Result(None), Result(rows=[dep])),
        mid,
        {"search": "a", "estado": "ACTIVO", "page": 2, "page_size": 200},
    )
    assert listed["total"] == 0 and listed["items"][0]["dependencia_padre_id"] == str(
        parent_id
    )
    await ds.list_dependencias(
        db_with(Result(1), Result(rows=[])), mid, {"estado": "INACTIVO"}
    )
    await ds.list_dependencias(
        db_with(Result(0), Result(rows=[])), mid, {"estado": "OTRO"}
    )
    assert await ds.get_dependencia(db_with(Result(None)), mid, did) is None
    assert (await ds.get_dependencia(db_with(Result(dep)), mid, did))[
        "codigo"
    ] == dep.codigo

    with pytest.raises(ValueError, match="Ya existe"):
        await ds.create_dependencia(
            db_with(Result(dep)), mid, {"codigo": "D", "nombre": "Dep"}
        )
    with pytest.raises(ValueError, match="padre no existe"):
        await ds.create_dependencia(
            db_with(Result(None), Result(None)),
            mid,
            {"codigo": "D", "nombre": "Dep", "dependencia_padre_id": parent_id},
        )
    create_db = db_with(Result(None), Result(dep))

    async def set_generated_fields(instance):
        instance.id = did
        instance.created_at = None
        instance.updated_at = None

    create_db.refresh.side_effect = set_generated_fields
    created = await ds.create_dependencia(
        create_db,
        mid,
        {"codigo": "D", "nombre": "Dep", "dependencia_padre_id": parent_id},
    )
    assert created["id"] == str(did)

    assert await ds.update_dependencia(db_with(Result(None)), mid, did, {}) is None
    with pytest.raises(ValueError, match="otra dependencia"):
        await ds.update_dependencia(
            db_with(Result(dep), Result(obj())), mid, did, {"codigo": "OTRO"}
        )
    with pytest.raises(ValueError, match="padre de sí misma"):
        await ds.update_dependencia(
            db_with(Result(dep)), mid, did, {"dependencia_padre_id": did}
        )
    with pytest.raises(ValueError, match="padre no existe"):
        await ds.update_dependencia(
            db_with(Result(dep), Result(None)),
            mid,
            did,
            {"dependencia_padre_id": parent_id},
        )
    updated = await ds.update_dependencia(
        db_with(Result(dep), Result(obj())),
        mid,
        did,
        {
            "codigo": dep.codigo,
            "dependencia_padre_id": parent_id,
            "nombre": "Nueva",
            "descripcion": None,
            "inexistente": "x",
        },
    )
    assert updated["nombre"] == "Nueva"

    dep.soft_delete = Mock()
    assert (
        await ds.delete_dependencia(db_with(Result(None)), str(mid), str(did), str(uid))
        is False
    )
    assert (
        await ds.delete_dependencia(db_with(Result(dep)), str(mid), str(did), str(uid))
        is True
    )
    dep.soft_delete.assert_called_once_with(uid)
    assert await ds.delete_dependencia(db_with(Result(dep)), mid, did, uid) is True
