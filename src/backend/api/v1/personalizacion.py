"""
API Routes - Personalizacion (branding) del Municipio
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.v1.auth import get_current_user_from_token
from ...core.database import get_db
from ...core.rbac import require_permission
from ...schemas.personalizacion import PersonalizacionResponse, PersonalizacionUpdate
from ...services import personalizacion_service

router = APIRouter(prefix="/personalizacion", tags=["Personalizacion"])


@router.get("", response_model=PersonalizacionResponse)
async def obtener_personalizacion(
    current_user: dict[str, Any] = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
) -> PersonalizacionResponse:
    municipio_id = UUID(current_user["municipio_id"])
    result = await personalizacion_service.get_personalizacion(db, municipio_id)
    return PersonalizacionResponse(**result)


@router.put("", response_model=PersonalizacionResponse)
async def actualizar_personalizacion(
    body: PersonalizacionUpdate,
    current_user: dict[str, Any] = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
) -> PersonalizacionResponse:
    await require_permission(db, current_user["user"].id, "configuracion.editar")
    municipio_id = UUID(current_user["municipio_id"])
    result = await personalizacion_service.save_personalizacion(db, municipio_id, body.model_dump())
    return PersonalizacionResponse(**result)
