"""
Rutas API - Productos
=====================
Endpoints para la gestión completa del módulo de Productos de SIGEM Colombia.

Incluye operaciones CRUD para productos asociados a programas, con
referencias a dependencias responsables y gestores líderes.

Autor: SIGEM Colombia
Versión: 1.0
Fecha: 2026-09-20
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from ...core.database import get_db
from ...core.rbac import require_permission
from ...api.v1.auth import get_current_user_from_token
from ...services.producto_service import (
    create_producto,
    list_productos,
    get_producto,
    update_producto,
    delete_producto,
)
from ...schemas.producto import (
    ProductoCreate,
    ProductoUpdate,
    ProductoResponse,
    ProductoListResponse,
)

router = APIRouter(prefix="/productos", tags=["Productos"])


# ---------------------------------------------------------------------------
# POST /productos - Crear producto
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=ProductoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo producto",
    description=(
        "Crea un nuevo producto asociado a un programa. "
        "Valida que el programa pertenezca al municipio y unicidad de código. "
        "Opcionalmente valida existencia de dependencia y gestor líder. "
        "Permiso requerido: producto.crear"
    ),
)
async def crear_producto(
    producto_data: ProductoCreate,
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "producto.crear")

    municipio_id = current_user["municipio_id"]

    try:
        result = await create_producto(
            db=db,
            municipio_id=UUID(municipio_id),
            create_data=producto_data.model_dump(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al crear el producto",
        )

    return ProductoResponse(**result)


# ---------------------------------------------------------------------------
# GET /productos - Listar productos con filtros
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=ProductoListResponse,
    summary="Listar productos",
    description=(
        "Retorna una lista paginada de productos con filtros opcionales "
        "por búsqueda, programa, dependencia, gestor y estado. "
        "Permiso requerido: producto.ver"
    ),
)
async def listar_productos(
    search: Optional[str] = Query(None, description="Búsqueda por nombre o código"),
    programa_id: Optional[UUID] = Query(None, description="Filtrar por programa"),
    dependencia_id: Optional[UUID] = Query(None, description="Filtrar por dependencia responsable"),
    gestor_id: Optional[UUID] = Query(None, description="Filtrar por gestor líder"),
    estado: Optional[str] = Query(None, description="Filtrar por estado (ACTIVO, INACTIVO)"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(20, ge=1, le=100, description="Elementos por página"),
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "producto.ver")

    municipio_id = current_user["municipio_id"]

    result = await list_productos(
        db=db,
        municipio_id=UUID(municipio_id),
        filtros={
            "search": search,
            "programa_id": str(programa_id) if programa_id else None,
            "dependencia_id": str(dependencia_id) if dependencia_id else None,
            "gestor_lider_id": str(gestor_id) if gestor_id else None,
            "estado": estado,
            "page": page,
            "page_size": page_size,
        },
    )

    return ProductoListResponse(
        items=result["productos"],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


# ---------------------------------------------------------------------------
# GET /productos/{producto_id} - Obtener detalle de producto
# ---------------------------------------------------------------------------

@router.get(
    "/{producto_id}",
    response_model=ProductoResponse,
    summary="Obtener detalle de un producto",
    description=(
        "Retorna la información completa de un producto por su ID, "
        "incluyendo datos del programa, dependencia y gestor relacionados. "
        "Permiso requerido: producto.ver"
    ),
)
async def obtener_producto(
    producto_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "producto.ver")

    municipio_id = current_user["municipio_id"]

    result = await get_producto(
        db=db,
        municipio_id=UUID(municipio_id),
        producto_id=producto_id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado",
        )

    return ProductoResponse(**result)


# ---------------------------------------------------------------------------
# PUT /productos/{producto_id} - Actualizar producto
# ---------------------------------------------------------------------------

@router.put(
    "/{producto_id}",
    response_model=ProductoResponse,
    summary="Actualizar producto",
    description=(
        "Actualiza la información de un producto existente. "
        "Valida unicidad de código si se modifica. "
        "Valida existencia de dependencia y gestor si se cambian. "
        "Permiso requerido: producto.editar"
    ),
)
async def actualizar_producto(
    producto_id: UUID,
    producto_data: ProductoUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "producto.editar")

    municipio_id = current_user["municipio_id"]

    try:
        result = await update_producto(
            db=db,
            municipio_id=UUID(municipio_id),
            producto_id=producto_id,
            update_data=producto_data.model_dump(exclude_unset=True),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado",
        )

    return ProductoResponse(**result)


# ---------------------------------------------------------------------------
# DELETE /productos/{producto_id} - Eliminación lógica
# ---------------------------------------------------------------------------

@router.delete(
    "/{producto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar producto (lógicamente)",
    description=(
        "Realiza la eliminación lógica de un producto. "
        "No se eliminan registros físicos de la base de datos. "
        "Permiso requerido: producto.eliminar"
    ),
)
async def eliminar_producto(
    producto_id: UUID,
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "producto.eliminar")

    municipio_id = current_user["municipio_id"]
    user = current_user["user"]

    result = await delete_producto(
        db=db,
        municipio_id=UUID(municipio_id),
        producto_id=producto_id,
        user_id=UUID(str(user.id)),
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado",
        )

    return None
