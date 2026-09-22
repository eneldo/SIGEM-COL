"""
Rutas API - Dashboard Administrativo
=====================================
Endpoints para el panel de administración del municipio de SIGEM Colombia.

Incluye KPIs generales, resumen del plan de desarrollo, resumen de gestores,
alertas de seguridad y estadísticas por dependencia.

Autor: SIGEM Colombia
Versión: 1.0
Fecha: 2026-09-20
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.rbac import require_permission
from ..auth import get_current_user_from_token
from ....services.dashboard_admin_service import (
    get_kpis_generales,
    get_resumen_plan,
    get_gestores_summary,
    get_alertas,
    get_estadisticas_por_dependencia,
)

router = APIRouter(prefix="/admin", tags=["Dashboard Admin"])


# ---------------------------------------------------------------------------
# Helper - Verificar permisos del usuario actual
# ---------------------------------------------------------------------------

async def _require_permission(
    db: AsyncSession, current_user: dict, permission: str
) -> None:
    """
    Verifica que el usuario autenticado tenga el permiso especificado.
    Lanza HTTPException 403 si no tiene el permiso.
    """
    user = current_user.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no autenticado",
        )
    await require_permission(db, user.id, permission)


# ---------------------------------------------------------------------------
# GET /admin/kpis - KPIs Generales
# ---------------------------------------------------------------------------

@router.get(
    "/kpis",
    summary="Obtener KPIs generales del municipio",
    description=(
        "Retorna los indicadores clave de rendimiento generales del municipio: "
        "total de gestores (activos, inactivos, bloqueados), "
        "total de líneas estratégicas, programas, productos y dependencias. "
        "Permiso requerido: dashboard.admin.ver"
    ),
)
async def kpis_generales(
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await _require_permission(db, current_user, "dashboard.admin.ver")

    from uuid import UUID
    municipio_id = UUID(current_user["municipio_id"])

    try:
        result = await get_kpis_generales(db=db, municipio_id=municipio_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener los KPIs generales",
        )

    return result


# ---------------------------------------------------------------------------
# GET /admin/resumen-plan - Resumen del Plan de Desarrollo
# ---------------------------------------------------------------------------

@router.get(
    "/resumen-plan",
    summary="Obtener resumen del plan de desarrollo",
    description=(
        "Retorna un resumen del plan de desarrollo activo del municipio, "
        "incluyendo datos del plan, conteo de líneas estratégicas, "
        "programas y productos, y desglose por línea estratégica. "
        "Permiso requerido: dashboard.admin.ver"
    ),
)
async def resumen_plan(
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await _require_permission(db, current_user, "dashboard.admin.ver")

    from uuid import UUID
    municipio_id = UUID(current_user["municipio_id"])

    try:
        result = await get_resumen_plan(db=db, municipio_id=municipio_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener el resumen del plan de desarrollo",
        )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró un plan de desarrollo activo para el municipio",
        )

    return result


# ---------------------------------------------------------------------------
# GET /admin/gestores - Resumen de Gestores
# ---------------------------------------------------------------------------

@router.get(
    "/gestores",
    summary="Obtener resumen de gestores líderes",
    description=(
        "Retorna un resumen de todos los gestores líderes del municipio, "
        "incluyendo datos básicos, estado, último acceso y total de "
        "productos asignados. "
        "Permiso requerido: dashboard.admin.ver"
    ),
)
async def gestores_summary(
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await _require_permission(db, current_user, "dashboard.admin.ver")

    from uuid import UUID
    municipio_id = UUID(current_user["municipio_id"])

    try:
        result = await get_gestores_summary(db=db, municipio_id=municipio_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener el resumen de gestores",
        )

    return {"gestores": result, "total": len(result)}


# ---------------------------------------------------------------------------
# GET /admin/alertas - Alertas de Seguridad
# ---------------------------------------------------------------------------

@router.get(
    "/alertas",
    summary="Obtener alertas de seguridad del municipio",
    description=(
        "Retorna las alertas de seguridad activas del municipio: "
        "gestores con intentos fallidos, bloqueados y sin acceso reciente. "
        "Permiso requerido: dashboard.admin.ver"
    ),
)
async def alertas_seguridad(
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await _require_permission(db, current_user, "dashboard.admin.ver")

    from uuid import UUID
    municipio_id = UUID(current_user["municipio_id"])

    try:
        result = await get_alertas(db=db, municipio_id=municipio_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener las alertas de seguridad",
        )

    return {"alertas": result, "total": len(result)}


# ---------------------------------------------------------------------------
# GET /admin/estadisticas-dependencia - Estadísticas por Dependencia
# ---------------------------------------------------------------------------

@router.get(
    "/estadisticas-dependencia",
    summary="Obtener estadísticas por dependencia",
    description=(
        "Retorna estadísticas agrupadas por dependencia del municipio: "
        "total de productos responsables y total de gestores asignados. "
        "Permiso requerido: dashboard.admin.ver"
    ),
)
async def estadisticas_dependencia(
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await _require_permission(db, current_user, "dashboard.admin.ver")

    from uuid import UUID
    municipio_id = UUID(current_user["municipio_id"])

    try:
        result = await get_estadisticas_por_dependencia(
            db=db, municipio_id=municipio_id
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener las estadísticas por dependencia",
        )

    return {"dependencias": result, "total": len(result)}
