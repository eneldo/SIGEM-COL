"""
Rutas API - Catálogos
=====================
Endpoints de catálogos (roles, dependencias) usados por los formularios
de los módulos administrativos de SIGEM Colombia.

Autor: SIGEM Colombia
Versión: 1.0
Fecha: 2026-09-20
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from ...core.database import get_db
from ...api.v1.auth import get_current_user_from_token
from ...models.rol import Rol
from ...models.dependencia import Dependencia
from ...schemas.catalogos import RolOut, DependenciaOut

router = APIRouter(prefix="/catalogos", tags=["Catálogos"])


@router.get(
    "/roles",
    response_model=List[RolOut],
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
    response_model=List[DependenciaOut],
    summary="Listar dependencias del municipio",
    description="Retorna las dependencias activas del municipio del usuario autenticado.",
)
async def list_dependencias(
    search: Optional[str] = Query(None, description="Filtro por nombre o código"),
    include_eliminadas: bool = Query(False, description="Incluir dependencias eliminadas"),
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    municipio_id = UUID(current_user["municipio_id"])

    stmt = select(Dependencia).where(Dependencia.municipio_id == municipio_id)
    if not include_eliminadas:
        stmt = stmt.where(Dependencia.deleted_at.is_(None))

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