"""
API Routes - Roles y Permisos
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.rbac import require_permission
from ...api.v1.auth import get_current_user_from_token
from ...schemas.configuracion import (
    RolCreate, RolUpdate, RolResponse, RolListResponse,
    PermisoResponse, PermisoListResponse,
)
from ...services import rol_service

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.post("", response_model=RolResponse, status_code=201)
async def crear_rol(
    body: RolCreate,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "security.roles.crear")
    try:
        result = await rol_service.create_rol(db, body.model_dump())
        return RolResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("", response_model=RolListResponse)
async def listar_roles(
    search: str = "",
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "security.roles.ver")
    filtros = {"page": page, "page_size": page_size}
    if search:
        filtros["search"] = search
    result = await rol_service.list_roles(db, filtros)
    return RolListResponse(**result)


@router.get("/permisos", response_model=PermisoListResponse)
async def listar_permisos(
    modulo: str = "",
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "security.roles.ver")
    filtros = {}
    if modulo:
        filtros["modulo"] = modulo
    result = await rol_service.list_permisos(db, filtros)
    return PermisoListResponse(**result)


@router.get("/{rol_id}", response_model=RolResponse)
async def obtener_rol(
    rol_id: str,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "security.roles.ver")
    import uuid as _uuid
    result = await rol_service.get_rol(db, _uuid.UUID(rol_id))
    if result is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return RolResponse(**result)


@router.put("/{rol_id}", response_model=RolResponse)
async def actualizar_rol(
    rol_id: str,
    body: RolUpdate,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "security.roles.editar")
    import uuid as _uuid
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    result = await rol_service.update_rol(db, _uuid.UUID(rol_id), data)
    if result is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return RolResponse(**result)


@router.delete("/{rol_id}", status_code=204)
async def eliminar_rol(
    rol_id: str,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "security.roles.eliminar")
    import uuid as _uuid
    result = await rol_service.delete_rol(db, _uuid.UUID(rol_id))
    if result is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return None
