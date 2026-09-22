"""
API Routes - CRUD Dependencias del Municipio
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...api.v1.auth import get_current_user_from_token
from ...schemas.dependencia import (
    DependenciaCreate,
    DependenciaUpdate,
    DependenciaResponse,
    DependenciaListResponse,
)
from ...services import dependencia_service

router = APIRouter(prefix="/dependencias", tags=["Dependencias"])


@router.get("", response_model=DependenciaListResponse)
async def listar_dependencias(
    search: str = "",
    estado: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    municipio_id = UUID(current_user["municipio_id"])
    filtros = {"page": page, "page_size": page_size}
    if search:
        filtros["search"] = search
    if estado:
        filtros["estado"] = estado
    result = await dependencia_service.list_dependencias(db, municipio_id, filtros)
    return DependenciaListResponse(**result)


@router.get("/{dependencia_id}", response_model=DependenciaResponse)
async def obtener_dependencia(
    dependencia_id: str,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    municipio_id = UUID(current_user["municipio_id"])
    result = await dependencia_service.get_dependencia(db, municipio_id, UUID(dependencia_id))
    if result is None:
        raise HTTPException(status_code=404, detail="Dependencia no encontrada")
    return DependenciaResponse(**result)


@router.post("", response_model=DependenciaResponse, status_code=201)
async def crear_dependencia(
    body: DependenciaCreate,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    municipio_id = UUID(current_user["municipio_id"])
    try:
        result = await dependencia_service.create_dependencia(db, municipio_id, body.model_dump())
        return DependenciaResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.put("/{dependencia_id}", response_model=DependenciaResponse)
async def actualizar_dependencia(
    dependencia_id: str,
    body: DependenciaUpdate,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    municipio_id = UUID(current_user["municipio_id"])
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(status_code=422, detail="No se enviaron campos para actualizar")
    try:
        result = await dependencia_service.update_dependencia(db, municipio_id, UUID(dependencia_id), data)
        if result is None:
            raise HTTPException(status_code=404, detail="Dependencia no encontrada")
        return DependenciaResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{dependencia_id}", status_code=204)
async def eliminar_dependencia(
    dependencia_id: str,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    municipio_id = UUID(current_user["municipio_id"])
    user_orm = current_user["user"]
    user_id = user_orm.id if isinstance(user_orm.id, UUID) else UUID(str(user_orm.id))
    result = await dependencia_service.delete_dependencia(db, municipio_id, UUID(dependencia_id), user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Dependencia no encontrada")
    return None
