"""
Rutas API - Dashboard del Gestor
==================================
Endpoints para el panel individual de cada gestor líder de SIGEM Colombia.

Incluye KPIs personales, listado de productos asignados, productos
pendientes de actualización y alertas de seguridad personal.

Autor: SIGEM Colombia
Versión: 1.0
Fecha: 2026-09-20
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from ....core.database import get_db
from ....core.rbac import require_permission
from ..auth import get_current_user_from_token
from ....models.gestor_lider import GestorLider
from ....services.dashboard_gestor_service import (
    get_kpis_personales,
    get_mis_productos,
    get_mis_pendientes,
    get_mis_alertas,
)

router = APIRouter(prefix="/gestor", tags=["Dashboard Gestor"])


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
# Helper - Obtener gestor_id desde el usuario autenticado
# ---------------------------------------------------------------------------

async def _get_gestor_id(
    db: AsyncSession,
    usuario_id: UUID,
    municipio_id: UUID,
) -> UUID:
    """
    Busca el registro de GestorLider asociado al usuario autenticado.

    :param db: Sesión de base de datos asíncrona.
    :param usuario_id: ID del usuario autenticado.
    :param municipio_id: ID del municipio del usuario.
    :return: ID del gestor líder.
    :raises HTTPException 404: Si el usuario no tiene un gestor asociado.
    """
    gestor_stmt = (
        select(GestorLider)
        .where(
            and_(
                GestorLider.usuario_id == usuario_id,
                GestorLider.municipio_id == municipio_id,
                GestorLider.eliminado == False,
            )
        )
    )
    result = await db.execute(gestor_stmt)
    gestor = result.scalar_one_or_none()

    if gestor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró un registro de gestor líder para el usuario autenticado",
        )

    return gestor.id


# ---------------------------------------------------------------------------
# GET /gestor/kpis - KPIs Personales
# ---------------------------------------------------------------------------

@router.get(
    "/kpis",
    summary="Obtener KPIs personales del gestor",
    description=(
        "Retorna los indicadores clave de rendimiento personales del gestor: "
        "total de productos asignados, dependencias asociadas y "
        "líneas estratégicas relacionadas. "
        "Permiso requerido: dashboard.gestor.ver"
    ),
)
async def kpis_personales(
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await _require_permission(db, current_user, "dashboard.gestor.ver")

    usuario_id = UUID(str(current_user["user"].id))
    municipio_id = UUID(current_user["municipio_id"])

    gestor_id = await _get_gestor_id(db, usuario_id, municipio_id)

    try:
        result = await get_kpis_personales(
            db=db, municipio_id=municipio_id, gestor_id=gestor_id
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener los KPIs personales",
        )

    return result


# ---------------------------------------------------------------------------
# GET /gestor/mis-productos - Mis Productos
# ---------------------------------------------------------------------------

@router.get(
    "/mis-productos",
    summary="Obtener lista de productos asignados",
    description=(
        "Retorna la lista completa de productos asignados al gestor, "
        "incluyendo datos del producto, programa y dependencia responsable. "
        "Permiso requerido: dashboard.gestor.ver"
    ),
)
async def mis_productos(
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await _require_permission(db, current_user, "dashboard.gestor.ver")

    usuario_id = UUID(str(current_user["user"].id))
    municipio_id = UUID(current_user["municipio_id"])

    gestor_id = await _get_gestor_id(db, usuario_id, municipio_id)

    try:
        result = await get_mis_productos(
            db=db, municipio_id=municipio_id, gestor_id=gestor_id
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener los productos asignados",
        )

    return {"productos": result, "total": len(result)}


# ---------------------------------------------------------------------------
# GET /gestor/mis-pendientes - Mis Pendientes
# ---------------------------------------------------------------------------

@router.get(
    "/mis-pendientes",
    summary="Obtener productos pendientes de actualización",
    description=(
        "Retorna los productos asignados al gestor que no han sido "
        "actualizados en los últimos 15 días, incluyendo días sin "
        "actualización. "
        "Permiso requerido: dashboard.gestor.ver"
    ),
)
async def mis_pendientes(
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await _require_permission(db, current_user, "dashboard.gestor.ver")

    usuario_id = UUID(str(current_user["user"].id))
    municipio_id = UUID(current_user["municipio_id"])

    gestor_id = await _get_gestor_id(db, usuario_id, municipio_id)

    try:
        result = await get_mis_pendientes(
            db=db, municipio_id=municipio_id, gestor_id=gestor_id
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener los productos pendientes",
        )

    return {"pendientes": result, "total": len(result)}


# ---------------------------------------------------------------------------
# GET /gestor/mis-alertas - Mis Alertas Personales
# ---------------------------------------------------------------------------

@router.get(
    "/mis-alertas",
    summary="Obtener alertas personales del gestor",
    description=(
        "Retorna las alertas de seguridad personales del gestor: "
        "intentos fallidos, contraseña pendiente, MFA desactivado "
        "y estado de cuenta bloqueada. "
        "Permiso requerido: dashboard.gestor.ver"
    ),
)
async def mis_alertas(
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await _require_permission(db, current_user, "dashboard.gestor.ver")

    usuario_id = UUID(str(current_user["user"].id))
    municipio_id = UUID(current_user["municipio_id"])

    gestor_id = await _get_gestor_id(db, usuario_id, municipio_id)

    try:
        result = await get_mis_alertas(
            db=db, municipio_id=municipio_id, gestor_id=gestor_id
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener las alertas personales",
        )

    return {"alertas": result, "total": len(result)}
