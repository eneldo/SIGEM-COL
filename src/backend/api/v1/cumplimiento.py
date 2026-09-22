"""
API Routes - Cumplimiento de Metas
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...api.v1.auth import get_current_user_from_token
from ...schemas.cumplimiento import (
    CumplimientoGeneral,
    CumplimientoPorLinea,
    CumplimientoPorPrograma,
    DetalleProductoCumplimiento,
    ItemCumplimientoProducto,
)
from ...services.cumplimiento_service import (
    get_cumplimiento_general,
    get_cumplimiento_por_linea,
    get_cumplimiento_por_programa,
    get_detalle_producto,
    get_listado_productos_cumplimiento,
)

router = APIRouter(prefix="/cumplimiento", tags=["Cumplimiento de Metas"])


@router.get("/general", response_model=CumplimientoGeneral)
async def cumplimiento_general(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_from_token),
):
    return await get_cumplimiento_general(db, current_user["municipio_id"])


@router.get("/por-linea", response_model=list[CumplimientoPorLinea])
async def cumplimiento_por_linea(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_from_token),
):
    return await get_cumplimiento_por_linea(db, current_user["municipio_id"])


@router.get("/por-programa", response_model=list[CumplimientoPorPrograma])
async def cumplimiento_por_programa(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_from_token),
):
    return await get_cumplimiento_por_programa(db, current_user["municipio_id"])


@router.get("/productos", response_model=list[ItemCumplimientoProducto])
async def listado_productos(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_from_token),
):
    return await get_listado_productos_cumplimiento(db, current_user["municipio_id"])


@router.get("/producto/{producto_id}", response_model=DetalleProductoCumplimiento)
async def detalle_producto(
    producto_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_from_token),
):
    from uuid import UUID
    result = await get_detalle_producto(db, current_user["municipio_id"], UUID(producto_id))
    if result is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return result
