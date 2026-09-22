"""
API Routes - Usuarios del Sistema
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.rbac import require_permission
from ...api.v1.auth import get_current_user_from_token
from ...schemas.configuracion import (
    UsuarioCreate, UsuarioUpdate, UsuarioResponse, UsuarioListResponse,
)
from ...services import usuario_service

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.post("", response_model=UsuarioResponse, status_code=201)
async def crear_usuario(
    body: UsuarioCreate,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "security.usuarios.crear")
    municipio_id = current_user["municipio_id"]
    try:
        result = await usuario_service.create_usuario(db, municipio_id, body.model_dump())
        return UsuarioResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("", response_model=UsuarioListResponse)
async def listar_usuarios(
    search: str = "",
    estado: str = "",
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "security.usuarios.ver")
    municipio_id = current_user["municipio_id"]
    filtros = {"page": page, "page_size": page_size}
    if search:
        filtros["search"] = search
    if estado:
        filtros["estado"] = estado
    result = await usuario_service.list_usuarios(db, municipio_id, filtros)
    return UsuarioListResponse(**result)


@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def obtener_usuario(
    usuario_id: str,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "security.usuarios.ver")
    import uuid as _uuid
    municipio_id = current_user["municipio_id"]
    result = await usuario_service.get_usuario(db, municipio_id, _uuid.UUID(usuario_id))
    if result is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return UsuarioResponse(**result)


@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def actualizar_usuario(
    usuario_id: str,
    body: UsuarioUpdate,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "security.usuarios.editar")
    import uuid as _uuid
    municipio_id = current_user["municipio_id"]
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    result = await usuario_service.update_usuario(db, municipio_id, _uuid.UUID(usuario_id), data)
    if result is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return UsuarioResponse(**result)


@router.delete("/{usuario_id}", status_code=204)
async def eliminar_usuario(
    usuario_id: str,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "security.usuarios.eliminar")
    import uuid as _uuid
    municipio_id = current_user["municipio_id"]
    user_id = _uuid.UUID(current_user["user"].id)
    result = await usuario_service.delete_usuario(db, municipio_id, _uuid.UUID(usuario_id), user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return None
