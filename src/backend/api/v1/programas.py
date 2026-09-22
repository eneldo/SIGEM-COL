"""
Rutas API - Programas
=====================
Endpoints para la gestión completa del módulo de Programas de SIGEM Colombia.

Incluye operaciones CRUD para programas asociados a líneas estratégicas.

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
from ...services.programa_service import (
    create_programa,
    list_programas,
    get_programa,
    update_programa,
    delete_programa,
)
from ...schemas.programa import (
    ProgramaCreate,
    ProgramaUpdate,
    ProgramaResponse,
    ProgramaListResponse,
)

router = APIRouter(prefix="/programas", tags=["Programas"])


# ---------------------------------------------------------------------------
# POST /programas - Crear programa
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=ProgramaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo programa",
    description=(
        "Crea un nuevo programa asociado a una línea estratégica. "
        "Valida que la línea pertenezca al municipio y unicidad de código. "
        "Permiso requerido: programa.crear"
    ),
)
async def crear_programa(
    programa_data: ProgramaCreate,
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "programa.crear")

    municipio_id = current_user["municipio_id"]

    try:
        result = await create_programa(
            db=db,
            municipio_id=UUID(municipio_id),
            create_data=programa_data.model_dump(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al crear el programa",
        )

    return ProgramaResponse(**result)


# ---------------------------------------------------------------------------
# GET /programas - Listar programas con filtros
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=ProgramaListResponse,
    summary="Listar programas",
    description=(
        "Retorna una lista paginada de programas con filtros opcionales "
        "por búsqueda, línea estratégica y estado. "
        "Permiso requerido: programa.ver"
    ),
)
async def listar_programas(
    search: Optional[str] = Query(None, description="Búsqueda por nombre o código"),
    linea_estrategica_id: Optional[UUID] = Query(None, description="Filtrar por línea estratégica"),
    estado: Optional[str] = Query(None, description="Filtrar por estado (ACTIVO, INACTIVO)"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(20, ge=1, le=100, description="Elementos por página"),
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "programa.ver")

    municipio_id = current_user["municipio_id"]

    result = await list_programas(
        db=db,
        municipio_id=UUID(municipio_id),
        filtros={
            "search": search,
            "linea_estrategica_id": str(linea_estrategica_id) if linea_estrategica_id else None,
            "estado": estado,
            "page": page,
            "page_size": page_size,
        },
    )

    return ProgramaListResponse(
        items=result["programas"],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


# ---------------------------------------------------------------------------
# GET /programas/{programa_id} - Obtener detalle de programa
# ---------------------------------------------------------------------------

@router.get(
    "/{programa_id}",
    response_model=ProgramaResponse,
    summary="Obtener detalle de un programa",
    description=(
        "Retorna la información completa de un programa por su ID. "
        "Permiso requerido: programa.ver"
    ),
)
async def obtener_programa(
    programa_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "programa.ver")

    municipio_id = current_user["municipio_id"]

    result = await get_programa(
        db=db,
        municipio_id=UUID(municipio_id),
        programa_id=programa_id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programa no encontrado",
        )

    return ProgramaResponse(**result)


# ---------------------------------------------------------------------------
# PUT /programas/{programa_id} - Actualizar programa
# ---------------------------------------------------------------------------

@router.put(
    "/{programa_id}",
    response_model=ProgramaResponse,
    summary="Actualizar programa",
    description=(
        "Actualiza la información de un programa existente. "
        "Valida unicidad de código si se modifica. "
        "Permiso requerido: programa.editar"
    ),
)
async def actualizar_programa(
    programa_id: UUID,
    programa_data: ProgramaUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "programa.editar")

    municipio_id = current_user["municipio_id"]

    try:
        result = await update_programa(
            db=db,
            municipio_id=UUID(municipio_id),
            programa_id=programa_id,
            update_data=programa_data.model_dump(exclude_unset=True),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programa no encontrado",
        )

    return ProgramaResponse(**result)


# ---------------------------------------------------------------------------
# DELETE /programas/{programa_id} - Eliminación lógica
# ---------------------------------------------------------------------------

@router.delete(
    "/{programa_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar programa (lógicamente)",
    description=(
        "Realiza la eliminación lógica de un programa. "
        "No se eliminan registros físicos de la base de datos. "
        "Permiso requerido: programa.eliminar"
    ),
)
async def eliminar_programa(
    programa_id: UUID,
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "programa.eliminar")

    municipio_id = current_user["municipio_id"]
    user = current_user["user"]

    result = await delete_programa(
        db=db,
        municipio_id=UUID(municipio_id),
        programa_id=programa_id,
        user_id=UUID(str(user.id)),
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programa no encontrado",
        )

    return None
