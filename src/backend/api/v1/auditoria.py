"""
API Routes - Administración de Auditoría
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.rbac import require_permission
from ...api.v1.auth import get_current_user_from_token
from ...schemas.configuracion import (
    AuditoriaListResponse, AuditoriaStats,
)
from ...services import audit_admin_service

router = APIRouter(prefix="/auditoria", tags=["Auditoría"])


@router.get("", response_model=AuditoriaListResponse)
async def listar_auditoria(
    evento_tipo: str = "",
    recurso_tipo: str = "",
    resultado: str = "",
    usuario_id: str = "",
    fecha_desde: str = "",
    fecha_hasta: str = "",
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "auditoria.ver")
    municipio_id = current_user["municipio_id"]
    filtros = {"page": page, "page_size": page_size}
    if evento_tipo:
        filtros["evento_tipo"] = evento_tipo
    if recurso_tipo:
        filtros["recurso_tipo"] = recurso_tipo
    if resultado:
        filtros["resultado"] = resultado
    if usuario_id:
        filtros["usuario_id"] = usuario_id
    if fecha_desde:
        filtros["fecha_desde"] = fecha_desde
    if fecha_hasta:
        filtros["fecha_hasta"] = fecha_hasta
    result = await audit_admin_service.list_auditoria(db, municipio_id, filtros)
    return AuditoriaListResponse(**result)


@router.get("/stats", response_model=AuditoriaStats)
async def estadisticas_auditoria(
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "auditoria.ver")
    municipio_id = current_user["municipio_id"]
    result = await audit_admin_service.get_auditoria_stats(db, municipio_id)
    return AuditoriaStats(**result)
