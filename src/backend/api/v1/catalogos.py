"""
Rutas API - Catálogos
=====================
Endpoints de catálogos (roles, dependencias) usados por los formularios
de los módulos administrativos de SIGEM Colombia.

Autor: SIGEM Colombia
Versión: 1.1
Fecha: 2026-09-23
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.v1.auth import get_current_user_from_token
from ...core.database import get_db
from ...models.dependencia import Dependencia
from ...models.gestor_lider import GestorLider
from ...models.rol import Rol
from ...models.usuario_dependencia import UsuarioDependencia
from ...schemas.catalogos import DependenciaOut, RolOut

router = APIRouter(prefix="/catalogos", tags=["Catálogos"])

ADMIN_ROLE_CODES = {"SUPERADMIN_PLATAFORMA", "ADMINISTRADOR_MUNICIPAL"}


@router.get(
    "/roles",
    response_model=list[RolOut],
    summary="Listar roles del sistema",
    description="Retorna los roles activos del sistema ordenados por nivel.",
)
async def list_roles(
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Rol)
        .where(Rol.deleted_at.is_(None))
        .order_by(Rol.nivel.asc())
    )
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    return [RolOut(id=r.id, codigo=r.codigo, nombre=r.nombre, nivel=r.nivel) for r in rows]


@router.get(
    "/dependencias",
    response_model=list[DependenciaOut],
    summary="Listar dependencias del municipio",
    description=(
        "Los administradores ven todas las dependencias del municipio. "
        "Coordinadores y gestores solo ven la dependencia que tienen asignada "
        "(no las dependencias de otros coordinadores)."
    ),
)
async def list_dependencias(
    search: str | None = Query(None, description="Filtro por nombre o código"),
    include_eliminadas: bool = Query(False, description="Incluir dependencias eliminadas"),
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    municipio_id = UUID(current_user["municipio_id"])
    role_codes = set(current_user.get("roles") or [])
    is_admin = bool(role_codes & ADMIN_ROLE_CODES)

    stmt = select(Dependencia).where(Dependencia.municipio_id == municipio_id)
    if not include_eliminadas:
        stmt = stmt.where(Dependencia.deleted_at.is_(None))

    if not is_admin:
        user_id = current_user["user"].id
        asignadas = (
            select(UsuarioDependencia.dependencia_id)
            .where(UsuarioDependencia.usuario_id == user_id)
        )
        propias_gestor = (
            select(GestorLider.dependencia_principal_id)
            .where(
                and_(
                    GestorLider.usuario_id == user_id,
                    GestorLider.dependencia_principal_id.is_not(None),
                )
            )
        )
        stmt = stmt.where(
            or_(
                Dependencia.id.in_(asignadas),
                Dependencia.id.in_(propias_gestor),
            )
        )

    if search:
        patron = f"%{search}%"
        stmt = stmt.where(
            or_(
                Dependencia.nombre.ilike(patron),
                Dependencia.codigo.ilike(patron),
            )
        )

    stmt = stmt.order_by(Dependencia.nombre.asc())
    result = await db.execute(stmt)
    rows = list(result.scalars().all())

    return [
        DependenciaOut(
            id=r.id,
            codigo=r.codigo,
            nombre=r.nombre,
            descripcion=r.descripcion,
        )
        for r in rows
    ]
