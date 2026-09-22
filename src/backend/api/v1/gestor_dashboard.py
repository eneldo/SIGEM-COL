"""
Rutas API - Dashboard del Gestor
================================
Endpoints para que los gestores líderes vean sus productos asignados,
registren avances y revisen avances de su equipo.

Autor: SIGEM Colombia
Versión: 1.0
Fecha: 2026-09-21
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

from ...core.database import get_db
from ...api.v1.auth import get_current_user_from_token
from ...services.avance_service import (
    get_mis_productos,
    get_avances_producto,
    registrar_avance,
    get_resumen_avances,
    get_avances_para_revision,
    get_estadisticas_revision,
    revisar_avance,
)
from ...models.gestor_lider import GestorLider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gestor/dashboard", tags=["Gestor Dashboard"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class AvanceCreate(BaseModel):
    avance_porcentaje: float = Field(..., ge=0, le=100, description="Porcentaje de avance (0-100)")
    avance_valor: Optional[int] = Field(None, ge=0, description="Valor numérico del avance")
    observaciones: Optional[str] = Field(None, max_length=1000, description="Observaciones del avance")
    evidencia_url: Optional[str] = Field(None, max_length=500, description="URL de evidencia")
    indicador: Optional[str] = Field(None, max_length=300, description="Indicador del producto")
    periodo: Optional[str] = Field(None, max_length=50, description="Periodo del avance")
    estado_revision: Optional[str] = Field("PENDIENTE", description="Estado de revisión")
    evidencia_nombre: Optional[str] = Field(None, max_length=255, description="Nombre del archivo de evidencia")
    evidencia_tipo: Optional[str] = Field(None, max_length=50, description="Tipo MIME del archivo")


class AvanceResponse(BaseModel):
    id: str
    producto_id: str
    avance_porcentaje: float
    avance_valor: Optional[int]
    observaciones: Optional[str]
    evidencia_url: Optional[str]
    indicador: Optional[str]
    periodo: Optional[str]
    fecha_registro: Optional[str]
    estado_revision: str
    evidencia_nombre: Optional[str]
    evidencia_tipo: Optional[str]
    estado: str
    created_at: Optional[str]


class ProductoAsignado(BaseModel):
    id: str
    codigo: str
    nombre: str
    indicador: Optional[str]
    codigo_indicador: Optional[str]
    meta_redactada: Optional[str]
    linea_base: Optional[int]
    meta_cuatrienio: Optional[int]
    unidad_medida: Optional[str]
    estado: str


class ResumenAvances(BaseModel):
    total_productos: int
    productos_con_avance: int
    avance_promedio: float
    productos_completados: int


class AvanceRevisionResponse(BaseModel):
    id: str
    producto_id: str
    producto_codigo: str
    producto_nombre: str
    codigo_indicador: Optional[str]
    indicador: Optional[str]
    gestor_id: str
    gestor_codigo: str
    gestor_nombre: str
    avance_porcentaje: float
    avance_valor: Optional[int]
    periodo: Optional[str]
    fecha_registro: Optional[str]
    estado_revision: str
    evidencia_nombre: Optional[str]
    evidencia_tipo: Optional[str]
    evidencia_url: Optional[str]
    observaciones: Optional[str]
    created_at: Optional[str]


class EstadisticasRevision(BaseModel):
    pendientes: int
    aprobados_semana: int
    devueltos: int


class RevisionAvanceRequest(BaseModel):
    nuevo_estado: str = Field(..., description="APROBADO o RECHAZADO")
    observacion: Optional[str] = Field(None, max_length=1000, description="Observación (obligatoria si se devuelve)")


# ---------------------------------------------------------------------------
# Helper: obtener gestor_lider_id del usuario actual
# ---------------------------------------------------------------------------

async def _get_gestor_lider_id(db, user, municipio_id):
    gestor_stmt = select(GestorLider.id).where(
        and_(
            GestorLider.usuario_id == UUID(str(user.id)),
            GestorLider.municipio_id == municipio_id,
            GestorLider.deleted_at.is_(None),
        )
    )
    return await db.scalar(gestor_stmt)


# ---------------------------------------------------------------------------
# Static routes FIRST (before /avances/{producto_id})
# ---------------------------------------------------------------------------

@router.get(
    "/mis-productos",
    response_model=list[ProductoAsignado],
    summary="Obtener productos asignados al gestor",
)
async def obtener_mis_productos(
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user = current_user.get("user")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado")

    productos = await get_mis_productos(
        db=db,
        usuario_id=UUID(str(user.id)),
        municipio_id=UUID(current_user["municipio_id"]),
    )
    return [ProductoAsignado(**p) for p in productos]


@router.get(
    "/resumen",
    response_model=ResumenAvances,
    summary="Resumen de avances del gestor",
)
async def obtener_resumen_avances(
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user = current_user.get("user")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado")

    resumen = await get_resumen_avances(
        db=db,
        usuario_id=UUID(str(user.id)),
        municipio_id=UUID(current_user["municipio_id"]),
    )
    return ResumenAvances(**resumen)


# ---------------------------------------------------------------------------
# Revision routes (static, before /avances/{producto_id})
# ---------------------------------------------------------------------------

@router.get(
    "/revision/avances",
    response_model=list[AvanceRevisionResponse],
    summary="Obtener avances para revisión",
)
async def obtener_avances_revision(
    estado: Optional[str] = None,
    search: Optional[str] = None,
    periodo: Optional[str] = None,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user = current_user.get("user")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado")

    municipio_id = UUID(current_user["municipio_id"])
    gestor_lider_id = None

    roles = current_user.get("roles", [])
    if "GESTOR_LIDER" in roles and "SUPERADMIN_PLATAFORMA" not in roles and "ADMINISTRADOR_MUNICIPAL" not in roles:
        gestor_lider_id = await _get_gestor_lider_id(db, user, municipio_id)

    avances = await get_avances_para_revision(
        db=db,
        municipio_id=municipio_id,
        gestor_lider_id=gestor_lider_id,
        estado_revision=estado,
        search=search,
    )

    if periodo:
        avances = [a for a in avances if a.get("periodo") == periodo]

    return [AvanceRevisionResponse(**a) for a in avances]


@router.get(
    "/revision/estadisticas",
    response_model=EstadisticasRevision,
    summary="Estadísticas de revisión de avances",
)
async def obtener_estadisticas_revision(
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user = current_user.get("user")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado")

    municipio_id = UUID(current_user["municipio_id"])
    gestor_lider_id = None

    roles = current_user.get("roles", [])
    if "GESTOR_LIDER" in roles and "SUPERADMIN_PLATAFORMA" not in roles and "ADMINISTRADOR_MUNICIPAL" not in roles:
        gestor_lider_id = await _get_gestor_lider_id(db, user, municipio_id)

    stats = await get_estadisticas_revision(
        db=db,
        municipio_id=municipio_id,
        gestor_lider_id=gestor_lider_id,
    )
    return EstadisticasRevision(**stats)


@router.patch(
    "/revision/{avance_id}",
    response_model=dict,
    summary="Revisar avance (aprobar o devolver)",
)
async def revisar_avance_endpoint(
    avance_id: UUID,
    data: RevisionAvanceRequest,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user = current_user.get("user")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado")

    try:
        result = await revisar_avance(
            db=db,
            avance_id=avance_id,
            municipio_id=UUID(current_user["municipio_id"]),
            usuario_id=UUID(str(user.id)),
            nuevo_estado=data.nuevo_estado,
            observacion=data.observacion,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception:
        logger.exception("Error interno al revisar avance")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al revisar el avance")

    return result


# ---------------------------------------------------------------------------
# POST /avances - Registrar avance (static, before /avances/{producto_id})
# ---------------------------------------------------------------------------

@router.post(
    "/avances",
    response_model=AvanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar avance en un producto",
)
async def crear_avance(
    avance_data: AvanceCreate,
    producto_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user = current_user.get("user")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado")

    try:
        result = await registrar_avance(
            db=db,
            usuario_id=UUID(str(user.id)),
            municipio_id=UUID(current_user["municipio_id"]),
            producto_id=producto_id,
            avance_data=avance_data.model_dump(),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception:
        logger.exception("Error interno al registrar avance")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno al registrar el avance")

    return AvanceResponse(**result)


# ---------------------------------------------------------------------------
# Dynamic routes LAST
# ---------------------------------------------------------------------------

@router.get(
    "/avances/{producto_id}",
    response_model=list[AvanceResponse],
    summary="Obtener avances de un producto",
)
async def obtener_avances_producto(
    producto_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user = current_user.get("user")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado")

    avances = await get_avances_producto(
        db=db,
        producto_id=producto_id,
        municipio_id=UUID(current_user["municipio_id"]),
    )
    return [AvanceResponse(**a) for a in avances]
