from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from src.backend.api.v1 import (
    dependencias,
    lineas,
    productos,
    programas,
    roles,
    usuarios,
)
from src.backend.schemas.configuracion import (
    RolCreate,
    RolUpdate,
    UsuarioCreate,
    UsuarioUpdate,
)
from src.backend.schemas.dependencia import DependenciaCreate, DependenciaUpdate
from src.backend.schemas.linea import LineaCreate, LineaUpdate
from src.backend.schemas.producto import ProductoCreate, ProductoUpdate
from src.backend.schemas.programa import ProgramaCreate, ProgramaUpdate

NOW = datetime(2026, 1, 1, tzinfo=UTC)
MUNICIPIO_ID = uuid4()
ACTOR_ID = uuid4()
RESOURCE_ID = uuid4()
RELATED_ID = uuid4()
DB = object()
REQUEST = object()
CURRENT_USER = {
    "municipio_id": str(MUNICIPIO_ID),
    "user": SimpleNamespace(id=str(ACTOR_ID)),
}


def dependencia_result():
    return {
        "id": RESOURCE_ID,
        "municipio_id": MUNICIPIO_ID,
        "codigo": "DEP-1",
        "nombre": "Planeación",
        "nivel": 1,
        "estado": "ACTIVA",
    }


def linea_result():
    return {
        "id": RESOURCE_ID,
        "codigo": "LIN-1",
        "nombre": "Línea uno",
        "orden": 1,
        "estado": "ACTIVA",
        "municipio_id": MUNICIPIO_ID,
        "plan_desarrollo_id": RELATED_ID,
        "created_at": NOW,
        "updated_at": NOW,
    }


def programa_result():
    return {
        "id": RESOURCE_ID,
        "codigo": "PRO-1",
        "nombre": "Programa uno",
        "estado": "ACTIVO",
        "municipio_id": MUNICIPIO_ID,
        "linea_estrategica_id": RELATED_ID,
        "created_at": NOW,
        "updated_at": NOW,
    }


def producto_result():
    return {
        "id": RESOURCE_ID,
        "codigo": "PRD-1",
        "nombre": "Producto uno",
        "estado": "ACTIVO",
        "municipio_id": MUNICIPIO_ID,
        "programa_id": RELATED_ID,
        "created_at": NOW,
        "updated_at": NOW,
    }


def rol_result():
    return {
        "id": str(RESOURCE_ID),
        "codigo": "ROL-1",
        "nombre": "Rol uno",
        "nivel": 1,
        "estado": "ACTIVO",
        "permisos": [],
        "created_at": NOW.isoformat(),
        "updated_at": NOW.isoformat(),
    }


def usuario_result():
    return {
        "id": str(RESOURCE_ID),
        "municipio_id": str(MUNICIPIO_ID),
        "codigo": "USR-1",
        "username": "usuario",
        "email": "usuario@example.com",
        "nombre_completo": "Usuario Prueba",
        "activo": 1,
        "roles": [],
        "must_change_password": True,
        "created_at": NOW.isoformat(),
        "updated_at": NOW.isoformat(),
    }


async def assert_http_error(call, status_code, detail):
    with pytest.raises(HTTPException) as exc_info:
        await call
    assert exc_info.value.status_code == status_code
    assert exc_info.value.detail == detail


async def test_dependencias_success_filters_and_crud():
    create = DependenciaCreate(codigo="DEP-1", nombre="Planeación")
    update = DependenciaUpdate(nombre="Planeación actualizada")
    with (
        patch.object(dependencias, "require_permission", AsyncMock()) as permission,
        patch.object(
            dependencias.dependencia_service, "list_dependencias", AsyncMock()
        ) as list_service,
        patch.object(
            dependencias.dependencia_service, "get_dependencia", AsyncMock()
        ) as get_service,
        patch.object(
            dependencias.dependencia_service, "create_dependencia", AsyncMock()
        ) as create_service,
        patch.object(
            dependencias.dependencia_service, "update_dependencia", AsyncMock()
        ) as update_service,
        patch.object(
            dependencias.dependencia_service, "delete_dependencia", AsyncMock()
        ) as delete_service,
    ):
        list_service.return_value = {
            "items": [dependencia_result()],
            "total": 1,
            "page": 2,
            "page_size": 5,
        }
        response = await dependencias.listar_dependencias(
            "plan", "ACTIVA", 2, 5, CURRENT_USER, DB
        )
        assert response.total == 1
        assert list_service.await_args.args[2] == {
            "page": 2,
            "page_size": 5,
            "search": "plan",
            "estado": "ACTIVA",
        }
        list_service.return_value = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 20,
        }
        await dependencias.listar_dependencias("", "", 1, 20, CURRENT_USER, DB)
        assert list_service.await_args.args[2] == {"page": 1, "page_size": 20}

        get_service.return_value = dependencia_result()
        assert (
            await dependencias.obtener_dependencia(str(RESOURCE_ID), CURRENT_USER, DB)
        ).id == RESOURCE_ID
        create_service.return_value = dependencia_result()
        assert (
            await dependencias.crear_dependencia(create, CURRENT_USER, DB)
        ).codigo == "DEP-1"
        update_service.return_value = dependencia_result()
        assert (
            await dependencias.actualizar_dependencia(
                str(RESOURCE_ID), update, CURRENT_USER, DB
            )
        ).nombre == "Planeación"
        delete_service.return_value = True
        assert (
            await dependencias.eliminar_dependencia(str(RESOURCE_ID), CURRENT_USER, DB)
            is None
        )
        assert delete_service.await_args.args[-1] == ACTOR_ID
        assert permission.await_count == 3


async def test_dependencias_errors_permissions_404_and_422():
    empty = DependenciaUpdate()
    update = DependenciaUpdate(nombre="Cambio")
    create = DependenciaCreate(codigo="DEP-1", nombre="Planeación")
    with (
        patch.object(dependencias, "require_permission", AsyncMock()),
        patch.object(
            dependencias.dependencia_service,
            "get_dependencia",
            AsyncMock(return_value=None),
        ),
    ):
        await assert_http_error(
            dependencias.obtener_dependencia(str(RESOURCE_ID), CURRENT_USER, DB),
            404,
            "Dependencia no encontrada",
        )
        await assert_http_error(
            dependencias.actualizar_dependencia(
                str(RESOURCE_ID), empty, CURRENT_USER, DB
            ),
            422,
            "No se enviaron campos para actualizar",
        )
    for function, body, service_name in (
        (dependencias.crear_dependencia, create, "create_dependencia"),
        (dependencias.actualizar_dependencia, update, "update_dependencia"),
    ):
        with (
            patch.object(dependencias, "require_permission", AsyncMock()),
            patch.object(
                dependencias.dependencia_service,
                service_name,
                AsyncMock(side_effect=ValueError("duplicada")),
            ),
        ):
            args = (
                (body, CURRENT_USER, DB)
                if function is dependencias.crear_dependencia
                else (str(RESOURCE_ID), body, CURRENT_USER, DB)
            )
            await assert_http_error(function(*args), 422, "duplicada")
    with (
        patch.object(dependencias, "require_permission", AsyncMock()),
        patch.object(
            dependencias.dependencia_service,
            "update_dependencia",
            AsyncMock(return_value=None),
        ),
    ):
        await assert_http_error(
            dependencias.actualizar_dependencia(
                str(RESOURCE_ID), update, CURRENT_USER, DB
            ),
            404,
            "Dependencia no encontrada",
        )
    with (
        patch.object(dependencias, "require_permission", AsyncMock()),
        patch.object(
            dependencias.dependencia_service,
            "delete_dependencia",
            AsyncMock(return_value=False),
        ),
    ):
        await assert_http_error(
            dependencias.eliminar_dependencia(str(RESOURCE_ID), CURRENT_USER, DB),
            404,
            "Dependencia no encontrada",
        )
    denied = HTTPException(status_code=403, detail="Sin permiso")
    with patch.object(
        dependencias, "require_permission", AsyncMock(side_effect=denied)
    ):
        await assert_http_error(
            dependencias.crear_dependencia(create, CURRENT_USER, DB), 403, "Sin permiso"
        )
    with pytest.raises(ValidationError):
        DependenciaCreate(codigo="", nombre="")


@pytest.mark.parametrize(
    (
        "module",
        "prefix",
        "create_schema",
        "update_schema",
        "create_data",
        "result_factory",
        "list_key",
        "filter_name",
        "not_found",
    ),
    [
        (
            lineas,
            "linea",
            LineaCreate,
            LineaUpdate,
            {"nombre": "Línea uno", "plan_desarrollo_id": RELATED_ID},
            linea_result,
            "lineas",
            "plan_desarrollo_id",
            "Línea estratégica no encontrada",
        ),
        (
            programas,
            "programa",
            ProgramaCreate,
            ProgramaUpdate,
            {
                "codigo": "PRO-1",
                "nombre": "Programa uno",
                "linea_estrategica_id": RELATED_ID,
            },
            programa_result,
            "programas",
            "linea_estrategica_id",
            "Programa no encontrado",
        ),
        (
            productos,
            "producto",
            ProductoCreate,
            ProductoUpdate,
            {"codigo": "PRD-1", "nombre": "Producto uno", "programa_id": RELATED_ID},
            producto_result,
            "productos",
            "programa_id",
            "Producto no encontrado",
        ),
    ],
)
async def test_plan_routes_success_filters_crud(
    module,
    prefix,
    create_schema,
    update_schema,
    create_data,
    result_factory,
    list_key,
    filter_name,
    not_found,
):
    create_function = getattr(
        module, f"crear_{prefix}" + ("_estrategica" if prefix == "linea" else "")
    )
    list_function = getattr(
        module, f"listar_{list_key}" + ("_estrategicas" if prefix == "linea" else "")
    )
    get_function = getattr(
        module, f"obtener_{prefix}" + ("_estrategica" if prefix == "linea" else "")
    )
    update_function = getattr(
        module, f"actualizar_{prefix}" + ("_estrategica" if prefix == "linea" else "")
    )
    delete_function = getattr(
        module, f"eliminar_{prefix}" + ("_estrategica" if prefix == "linea" else "")
    )
    service_create = getattr(module, f"create_{prefix}")
    service_list = getattr(module, f"list_{list_key}")
    service_get = getattr(module, f"get_{prefix}")
    service_update = getattr(module, f"update_{prefix}")
    service_delete = getattr(module, f"delete_{prefix}")
    create = create_schema(**create_data)
    update = update_schema(nombre="Actualizado")
    result = result_factory()
    with (
        patch.object(module, "require_permission", AsyncMock()) as permission,
        patch.object(
            module, f"create_{prefix}", AsyncMock(return_value=result)
        ) as create_mock,
        patch.object(
            module,
            f"list_{list_key}",
            AsyncMock(
                return_value={list_key: [result], "total": 1, "page": 2, "page_size": 5}
            ),
        ) as list_mock,
        patch.object(module, f"get_{prefix}", AsyncMock(return_value=result)),
        patch.object(
            module, f"update_{prefix}", AsyncMock(return_value=result)
        ) as update_mock,
        patch.object(
            module, f"delete_{prefix}", AsyncMock(return_value=True)
        ) as delete_mock,
    ):
        assert (
            await create_function(create, REQUEST, CURRENT_USER, DB)
        ).id == RESOURCE_ID
        if module is productos:
            listed = await list_function(
                "uno",
                RELATED_ID,
                RELATED_ID,
                RELATED_ID,
                "ACTIVO",
                2,
                5,
                CURRENT_USER,
                DB,
            )
        else:
            listed = await list_function(
                "uno", RELATED_ID, "ACTIVO", 2, 5, CURRENT_USER, DB
            )
        assert listed.total == 1
        filters = list_mock.await_args.kwargs["filtros"]
        assert filters[filter_name] == str(RELATED_ID)
        assert filters["search"] == "uno"
        assert filters["estado"] == "ACTIVO"
        assert (await get_function(RESOURCE_ID, CURRENT_USER, DB)).id == RESOURCE_ID
        assert (
            await update_function(RESOURCE_ID, update, REQUEST, CURRENT_USER, DB)
        ).id == RESOURCE_ID
        assert await delete_function(RESOURCE_ID, REQUEST, CURRENT_USER, DB) is None
        assert create_mock.await_args.kwargs["municipio_id"] == MUNICIPIO_ID
        assert update_mock.await_args.kwargs["update_data"] == {"nombre": "Actualizado"}
        assert delete_mock.await_args.kwargs["user_id"] == ACTOR_ID
        assert permission.await_count == 5
    assert service_create is not None and service_list is not None
    assert (
        service_get is not None
        and service_update is not None
        and service_delete is not None
    )


@pytest.mark.parametrize(
    (
        "module",
        "prefix",
        "create_schema",
        "update_schema",
        "create_data",
        "not_found",
        "internal_error",
    ),
    [
        (
            lineas,
            "linea",
            LineaCreate,
            LineaUpdate,
            {"nombre": "Línea", "plan_desarrollo_id": RELATED_ID},
            "Línea estratégica no encontrada",
            "Error interno al crear la línea estratégica",
        ),
        (
            programas,
            "programa",
            ProgramaCreate,
            ProgramaUpdate,
            {"codigo": "PRO", "nombre": "Programa", "linea_estrategica_id": RELATED_ID},
            "Programa no encontrado",
            "Error interno al crear el programa",
        ),
        (
            productos,
            "producto",
            ProductoCreate,
            ProductoUpdate,
            {"codigo": "PRD", "nombre": "Producto", "programa_id": RELATED_ID},
            "Producto no encontrado",
            "Error interno al crear el producto",
        ),
    ],
)
async def test_plan_routes_errors_permissions_404_422_500(
    module,
    prefix,
    create_schema,
    update_schema,
    create_data,
    not_found,
    internal_error,
):
    suffix = "_estrategica" if prefix == "linea" else ""
    create_function = getattr(module, f"crear_{prefix}{suffix}")
    get_function = getattr(module, f"obtener_{prefix}{suffix}")
    update_function = getattr(module, f"actualizar_{prefix}{suffix}")
    delete_function = getattr(module, f"eliminar_{prefix}{suffix}")
    create = create_schema(**create_data)
    update = update_schema(nombre="Cambio")
    with patch.object(module, "require_permission", AsyncMock()):
        with patch.object(
            module, f"create_{prefix}", AsyncMock(side_effect=ValueError("duplicado"))
        ):
            await assert_http_error(
                create_function(create, REQUEST, CURRENT_USER, DB), 422, "duplicado"
            )
        with patch.object(
            module, f"create_{prefix}", AsyncMock(side_effect=RuntimeError("db"))
        ):
            await assert_http_error(
                create_function(create, REQUEST, CURRENT_USER, DB), 500, internal_error
            )
        with patch.object(module, f"get_{prefix}", AsyncMock(return_value=None)):
            await assert_http_error(
                get_function(RESOURCE_ID, CURRENT_USER, DB), 404, not_found
            )
        with patch.object(
            module, f"update_{prefix}", AsyncMock(side_effect=ValueError("inválido"))
        ):
            await assert_http_error(
                update_function(RESOURCE_ID, update, REQUEST, CURRENT_USER, DB),
                422,
                "inválido",
            )
        with patch.object(module, f"update_{prefix}", AsyncMock(return_value=None)):
            await assert_http_error(
                update_function(RESOURCE_ID, update, REQUEST, CURRENT_USER, DB),
                404,
                not_found,
            )
        with patch.object(module, f"delete_{prefix}", AsyncMock(return_value=False)):
            await assert_http_error(
                delete_function(RESOURCE_ID, REQUEST, CURRENT_USER, DB),
                404,
                not_found,
            )
    with patch.object(
        module,
        "require_permission",
        AsyncMock(side_effect=HTTPException(status_code=403, detail="Sin permiso")),
    ):
        await assert_http_error(
            create_function(create, REQUEST, CURRENT_USER, DB), 403, "Sin permiso"
        )
    with pytest.raises(ValidationError):
        create_schema()


async def test_plan_route_empty_filters():
    with (
        patch.object(lineas, "require_permission", AsyncMock()),
        patch.object(
            lineas,
            "list_lineas",
            AsyncMock(
                return_value={"lineas": [], "total": 0, "page": 1, "page_size": 20}
            ),
        ) as service,
    ):
        await lineas.listar_lineas_estrategicas(
            None, None, None, 1, 20, CURRENT_USER, DB
        )
        assert service.await_args.kwargs["filtros"]["plan_desarrollo_id"] is None
    with (
        patch.object(programas, "require_permission", AsyncMock()),
        patch.object(
            programas,
            "list_programas",
            AsyncMock(
                return_value={"programas": [], "total": 0, "page": 1, "page_size": 20}
            ),
        ) as service,
    ):
        await programas.listar_programas(None, None, None, 1, 20, CURRENT_USER, DB)
        assert service.await_args.kwargs["filtros"]["linea_estrategica_id"] is None
    with (
        patch.object(productos, "require_permission", AsyncMock()),
        patch.object(
            productos,
            "list_productos",
            AsyncMock(
                return_value={"productos": [], "total": 0, "page": 1, "page_size": 20}
            ),
        ) as service,
    ):
        await productos.listar_productos(
            None, None, None, None, None, 1, 20, CURRENT_USER, DB
        )
        filters = service.await_args.kwargs["filtros"]
        assert filters["programa_id"] is None
        assert filters["dependencia_id"] is None
        assert filters["gestor_lider_id"] is None


async def test_roles_success_filters_and_crud():
    create = RolCreate(codigo="ROL-1", nombre="Rol uno")
    update = RolUpdate(nombre="Rol actualizado")
    with (
        patch.object(roles, "require_permission", AsyncMock()) as permission,
        patch.object(
            roles.rol_service, "create_rol", AsyncMock(return_value=rol_result())
        ),
        patch.object(
            roles.rol_service,
            "list_roles",
            AsyncMock(
                return_value={
                    "items": [rol_result()],
                    "total": 1,
                    "page": 2,
                    "page_size": 5,
                }
            ),
        ) as list_service,
        patch.object(
            roles.rol_service,
            "list_permisos",
            AsyncMock(return_value={"items": [], "total": 0}),
        ) as permisos_service,
        patch.object(
            roles.rol_service, "get_rol", AsyncMock(return_value=rol_result())
        ),
        patch.object(
            roles.rol_service, "update_rol", AsyncMock(return_value=rol_result())
        ) as update_service,
        patch.object(roles.rol_service, "delete_rol", AsyncMock(return_value=True)),
    ):
        assert (await roles.crear_rol(create, CURRENT_USER, DB)).codigo == "ROL-1"
        assert (await roles.listar_roles("rol", 2, 5, CURRENT_USER, DB)).total == 1
        assert list_service.await_args.args[1]["search"] == "rol"
        await roles.listar_roles("", 1, 20, CURRENT_USER, DB)
        assert "search" not in list_service.await_args.args[1]
        await roles.listar_permisos("seguridad", CURRENT_USER, DB)
        assert permisos_service.await_args.args[1] == {"modulo": "seguridad"}
        await roles.listar_permisos("", CURRENT_USER, DB)
        assert permisos_service.await_args.args[1] == {}
        assert (await roles.obtener_rol(str(RESOURCE_ID), CURRENT_USER, DB)).id == str(
            RESOURCE_ID
        )
        assert (
            await roles.actualizar_rol(str(RESOURCE_ID), update, CURRENT_USER, DB)
        ).nombre == "Rol uno"
        assert update_service.await_args.args[2] == {"nombre": "Rol actualizado"}
        assert await roles.eliminar_rol(str(RESOURCE_ID), CURRENT_USER, DB) is None
        assert permission.await_count == 8


async def test_roles_errors_permissions_404_and_422():
    create = RolCreate(codigo="ROL", nombre="Rol")
    with (
        patch.object(roles, "require_permission", AsyncMock()),
        patch.object(
            roles.rol_service,
            "create_rol",
            AsyncMock(side_effect=ValueError("duplicado")),
        ),
    ):
        await assert_http_error(
            roles.crear_rol(create, CURRENT_USER, DB), 422, "duplicado"
        )
    cases = (
        (roles.obtener_rol(str(RESOURCE_ID), CURRENT_USER, DB), "get_rol"),
        (
            roles.actualizar_rol(str(RESOURCE_ID), RolUpdate(), CURRENT_USER, DB),
            "update_rol",
        ),
        (roles.eliminar_rol(str(RESOURCE_ID), CURRENT_USER, DB), "delete_rol"),
    )
    for call, service_name in cases:
        with (
            patch.object(roles, "require_permission", AsyncMock()),
            patch.object(roles.rol_service, service_name, AsyncMock(return_value=None)),
        ):
            await assert_http_error(call, 404, "Rol no encontrado")
    with patch.object(
        roles,
        "require_permission",
        AsyncMock(side_effect=HTTPException(status_code=403, detail="Sin permiso")),
    ):
        await assert_http_error(
            roles.crear_rol(create, CURRENT_USER, DB), 403, "Sin permiso"
        )
    with pytest.raises(ValidationError):
        RolCreate()
    with (
        patch.object(roles, "require_permission", AsyncMock()),
        pytest.raises(ValueError),
    ):
        await roles.obtener_rol("no-es-uuid", CURRENT_USER, DB)


async def test_usuarios_success_filters_and_crud():
    create = UsuarioCreate(
        codigo="USR-1",
        username="usuario",
        email="usuario@example.com",
        nombre_completo="Usuario Prueba",
        password="password-segura",
    )
    update = UsuarioUpdate(nombre_completo="Usuario Actualizado")
    with (
        patch.object(usuarios, "require_permission", AsyncMock()) as permission,
        patch.object(
            usuarios.usuario_service,
            "create_usuario",
            AsyncMock(return_value=usuario_result()),
        ),
        patch.object(
            usuarios.usuario_service,
            "list_usuarios",
            AsyncMock(
                return_value={
                    "items": [usuario_result()],
                    "total": 1,
                    "page": 2,
                    "page_size": 5,
                }
            ),
        ) as list_service,
        patch.object(
            usuarios.usuario_service,
            "get_usuario",
            AsyncMock(return_value=usuario_result()),
        ),
        patch.object(
            usuarios.usuario_service,
            "update_usuario",
            AsyncMock(return_value=usuario_result()),
        ) as update_service,
        patch.object(
            usuarios.usuario_service, "delete_usuario", AsyncMock(return_value=True)
        ) as delete_service,
    ):
        assert (
            await usuarios.crear_usuario(create, CURRENT_USER, DB)
        ).username == "usuario"
        assert (
            await usuarios.listar_usuarios("usu", "ACTIVO", 2, 5, CURRENT_USER, DB)
        ).total == 1
        assert list_service.await_args.args[2]["search"] == "usu"
        assert list_service.await_args.args[2]["estado"] == "ACTIVO"
        await usuarios.listar_usuarios("", "", 1, 20, CURRENT_USER, DB)
        assert list_service.await_args.args[2] == {"page": 1, "page_size": 20}
        assert (
            await usuarios.obtener_usuario(str(RESOURCE_ID), CURRENT_USER, DB)
        ).id == str(RESOURCE_ID)
        assert (
            await usuarios.actualizar_usuario(
                str(RESOURCE_ID), update, CURRENT_USER, DB
            )
        ).username == "usuario"
        assert update_service.await_args.args[3] == {
            "nombre_completo": "Usuario Actualizado"
        }
        assert (
            await usuarios.eliminar_usuario(str(RESOURCE_ID), CURRENT_USER, DB) is None
        )
        assert delete_service.await_args.args[-1] == ACTOR_ID
        assert permission.await_count == 6


async def test_usuarios_errors_permissions_404_and_422():
    create = UsuarioCreate(
        codigo="USR-1",
        username="usuario",
        email="usuario@example.com",
        nombre_completo="Usuario Prueba",
        password="password-segura",
    )
    with (
        patch.object(usuarios, "require_permission", AsyncMock()),
        patch.object(
            usuarios.usuario_service,
            "create_usuario",
            AsyncMock(side_effect=ValueError("username duplicado")),
        ),
    ):
        await assert_http_error(
            usuarios.crear_usuario(create, CURRENT_USER, DB), 422, "username duplicado"
        )
    cases = (
        (usuarios.obtener_usuario(str(RESOURCE_ID), CURRENT_USER, DB), "get_usuario"),
        (
            usuarios.actualizar_usuario(
                str(RESOURCE_ID), UsuarioUpdate(), CURRENT_USER, DB
            ),
            "update_usuario",
        ),
        (
            usuarios.eliminar_usuario(str(RESOURCE_ID), CURRENT_USER, DB),
            "delete_usuario",
        ),
    )
    for call, service_name in cases:
        with (
            patch.object(usuarios, "require_permission", AsyncMock()),
            patch.object(
                usuarios.usuario_service, service_name, AsyncMock(return_value=None)
            ),
        ):
            await assert_http_error(call, 404, "Usuario no encontrado")
    with patch.object(
        usuarios,
        "require_permission",
        AsyncMock(side_effect=HTTPException(status_code=403, detail="Sin permiso")),
    ):
        await assert_http_error(
            usuarios.crear_usuario(create, CURRENT_USER, DB), 403, "Sin permiso"
        )
    with pytest.raises(ValidationError):
        UsuarioCreate()
    with (
        patch.object(usuarios, "require_permission", AsyncMock()),
        pytest.raises(ValueError),
    ):
        await usuarios.obtener_usuario("no-es-uuid", CURRENT_USER, DB)
