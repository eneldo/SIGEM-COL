"""
API Routes - Reportes y Rendición de Cuentas
"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io

from ...core.database import get_db
from ...api.v1.auth import get_current_user_from_token
from ...schemas.reporte import (
    ResumenGeneral,
    ResumenPorLinea,
    ResumenPorPrograma,
    ResumenPorDependencia,
    MetricasProductos,
)
from ...services.reporte_service import (
    get_resumen_general,
    get_resumen_por_linea,
    get_resumen_por_programa,
    get_resumen_por_dependencia,
    get_metricas_productos,
)
from ...services.pdf_service import generar_informe_gestion_pdf

router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get("/resumen-general", response_model=ResumenGeneral)
async def resumen_general(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_from_token),
):
    return await get_resumen_general(db, current_user["municipio_id"])


@router.get("/por-linea", response_model=list[ResumenPorLinea])
async def resumen_por_linea(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_from_token),
):
    return await get_resumen_por_linea(db, current_user["municipio_id"])


@router.get("/por-programa", response_model=list[ResumenPorPrograma])
async def resumen_por_programa(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_from_token),
):
    return await get_resumen_por_programa(db, current_user["municipio_id"])


@router.get("/por-dependencia", response_model=list[ResumenPorDependencia])
async def resumen_por_dependencia(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_from_token),
):
    return await get_resumen_por_dependencia(db, current_user["municipio_id"])


@router.get("/metricas-productos", response_model=MetricasProductos)
async def metricas_productos(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_from_token),
):
    return await get_metricas_productos(db, current_user["municipio_id"])


@router.get("/informe-pdf")
async def informe_pdf(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_from_token),
):
    pdf_bytes = await generar_informe_gestion_pdf(db, current_user["municipio_id"])
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=informe_gestion_sigem.pdf"},
    )
