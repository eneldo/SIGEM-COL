"""
Rutas API - Líneas Estratégicas
================================
Endpoints para la gestión completa del módulo de Líneas Estratégicas de SIGEM Colombia.

Incluye operaciones CRUD para líneas estratégicas asociadas a planes
de desarrollo municipales.

Autor: SIGEM Colombia
Versión: 1.0
Fecha: 2026-09-20
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from ...core.database import get_db
from ...core.rbac import require_permission
from ...api.v1.auth import get_current_user_from_token
from ...services.linea_service import (
    create_linea,
    list_lineas,
    get_linea,
    update_linea,
    delete_linea,
)
from ...schemas.linea import (
    LineaCreate,
    LineaUpdate,
    LineaResponse,
    LineaListResponse,
)

router = APIRouter(prefix="/lineas-estrategicas", tags=["Líneas Estratégicas"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# POST /lineas-estrategicas - Crear línea estratégica
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=LineaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva línea estratégica",
    description=(
        "Crea una nueva línea estratégica asociada a un plan de desarrollo. "
        "Valida que el plan pertenezca al municipio y unicidad de código. "
        "Permiso requerido: linea_estrategica.crear"
    ),
)
async def crear_linea_estrategica(
    linea_data: LineaCreate,
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "linea_estrategica.crear")

    municipio_id = current_user["municipio_id"]

    try:
        result = await create_linea(
            db=db,
            municipio_id=UUID(municipio_id),
            create_data=linea_data.model_dump(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception:
        logger.exception("Error interno al crear la línea estratégica")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al crear la línea estratégica",
        )

    return LineaResponse(**result)


# ---------------------------------------------------------------------------
# GET /lineas-estrategicas - Listar líneas estratégicas con filtros
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=LineaListResponse,
    summary="Listar líneas estratégicas",
    description=(
        "Retorna una lista paginada de líneas estratégicas con filtros opcionales "
        "por búsqueda, plan de desarrollo y estado. "
        "Permiso requerido: linea_estrategica.ver"
    ),
)
async def listar_lineas_estrategicas(
    search: Optional[str] = Query(None, description="Búsqueda por nombre o código"),
    plan_desarrollo_id: Optional[UUID] = Query(None, description="Filtrar por plan de desarrollo"),
    estado: Optional[str] = Query(None, description="Filtrar por estado (ACTIVA, INACTIVA)"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(20, ge=1, le=100, description="Elementos por página"),
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "linea_estrategica.ver")

    municipio_id = current_user["municipio_id"]

    result = await list_lineas(
        db=db,
        municipio_id=UUID(municipio_id),
        filtros={
            "search": search,
            "plan_desarrollo_id": str(plan_desarrollo_id) if plan_desarrollo_id else None,
            "estado": estado,
            "page": page,
            "page_size": page_size,
        },
    )

    return LineaListResponse(
        items=result["lineas"],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


# ---------------------------------------------------------------------------
# GET /lineas-estrategicas/{linea_id} - Obtener detalle de línea estratégica
# ---------------------------------------------------------------------------

@router.get(
    "/{linea_id}",
    response_model=LineaResponse,
    summary="Obtener detalle de una línea estratégica",
    description=(
        "Retorna la información completa de una línea estratégica por su ID. "
        "Permiso requerido: linea_estrategica.ver"
    ),
)
async def obtener_linea_estrategica(
    linea_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "linea_estrategica.ver")

    municipio_id = current_user["municipio_id"]

    result = await get_linea(
        db=db,
        municipio_id=UUID(municipio_id),
        linea_id=linea_id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Línea estratégica no encontrada",
        )

    return LineaResponse(**result)


# ---------------------------------------------------------------------------
# PUT /lineas-estrategicas/{linea_id} - Actualizar línea estratégica
# ---------------------------------------------------------------------------

@router.put(
    "/{linea_id}",
    response_model=LineaResponse,
    summary="Actualizar línea estratégica",
    description=(
        "Actualiza la información de una línea estratégica existente. "
        "Valida unicidad de código si se modifica. "
        "Permiso requerido: linea_estrategica.editar"
    ),
)
async def actualizar_linea_estrategica(
    linea_id: UUID,
    linea_data: LineaUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "linea_estrategica.editar")

    municipio_id = current_user["municipio_id"]

    try:
        result = await update_linea(
            db=db,
            municipio_id=UUID(municipio_id),
            linea_id=linea_id,
            update_data=linea_data.model_dump(exclude_unset=True),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Línea estratégica no encontrada",
        )

    return LineaResponse(**result)


# ---------------------------------------------------------------------------
# DELETE /lineas-estrategicas/{linea_id} - Eliminación lógica
# ---------------------------------------------------------------------------

@router.delete(
    "/{linea_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar línea estratégica (lógicamente)",
    description=(
        "Realiza la eliminación lógica de una línea estratégica. "
        "No se eliminan registros físicos de la base de datos. "
        "Permiso requerido: linea_estrategica.eliminar"
    ),
)
async def eliminar_linea_estrategica(
    linea_id: UUID,
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "linea_estrategica.eliminar")

    municipio_id = current_user["municipio_id"]
    user = current_user["user"]

    result = await delete_linea(
        db=db,
        municipio_id=UUID(municipio_id),
        linea_id=linea_id,
        user_id=UUID(str(user.id)),
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Línea estratégica no encontrada",
        )

    return None
