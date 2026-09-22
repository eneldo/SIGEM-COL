"""
Servicio de Administración de Auditoría - SIGEM Colombia
========================================================
Consultas de auditoría y evidencias del sistema.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.auditoria_evento import AuditoriaEvento
from ..models.usuario import Usuario


async def list_auditoria(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    filtros: dict | None = None,
) -> dict:
    filtros = filtros or {}
    page = max(1, filtros.get("page", 1))
    page_size = min(100, max(1, filtros.get("page_size", 20)))
    offset = (page - 1) * page_size

    base_query = select(AuditoriaEvento).where(
        AuditoriaEvento.municipio_id == municipio_id
    )

    evento_tipo = filtros.get("evento_tipo")
    if evento_tipo:
        base_query = base_query.where(AuditoriaEvento.evento_tipo == evento_tipo)

    recurso_tipo = filtros.get("recurso_tipo")
    if recurso_tipo:
        base_query = base_query.where(AuditoriaEvento.recurso_tipo == recurso_tipo)

    resultado = filtros.get("resultado")
    if resultado:
        base_query = base_query.where(AuditoriaEvento.resultado == resultado)

    usuario_id = filtros.get("usuario_id")
    if usuario_id:
        base_query = base_query.where(AuditoriaEvento.usuario_id == uuid.UUID(usuario_id))

    fecha_desde = filtros.get("fecha_desde")
    if fecha_desde:
        base_query = base_query.where(AuditoriaEvento.fecha_evento >= fecha_desde)

    fecha_hasta = filtros.get("fecha_hasta")
    if fecha_hasta:
        base_query = base_query.where(AuditoriaEvento.fecha_evento <= fecha_hasta)

    count_stmt = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    query = base_query.order_by(AuditoriaEvento.fecha_evento.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    eventos = result.scalars().all()

    items = []
    for e in eventos:
        actor_nombre = None
        if e.usuario_id:
            u_stmt = select(Usuario.nombre_completo, Usuario.username).where(Usuario.id == e.usuario_id)
            u_result = await db.execute(u_stmt)
            u_row = u_result.first()
            if u_row:
                actor_nombre = f"{u_row[0]} ({u_row[1]})"

        items.append({
            "id": str(e.id),
            "evento_tipo": e.evento_tipo,
            "recurso_tipo": e.recurso_tipo,
            "recurso_id": str(e.recurso_id) if e.recurso_id else None,
            "resultado": e.resultado,
            "ip_address": e.ip_address,
            "actor_nombre": actor_nombre,
            "actor_id": str(e.usuario_id) if e.usuario_id else None,
            "metadata_json": e.metadata_json,
            "fecha_evento": e.fecha_evento.isoformat(),
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


async def get_auditoria_stats(
    db: AsyncSession,
    municipio_id: uuid.UUID,
) -> dict:
    base = select(func.count()).where(AuditoriaEvento.municipio_id == municipio_id)

    total_result = await db.execute(base)
    total = total_result.scalar_one()

    exitosos_stmt = base.where(AuditoriaEvento.resultado == "EXITOSO")
    exitosos_result = await db.execute(exitosos_stmt)
    exitosos = exitosos_result.scalar_one()

    fallidos_stmt = base.where(AuditoriaEvento.resultado == "FALLIDO")
    fallidos_result = await db.execute(fallidos_stmt)
    fallidos = fallidos_result.scalar_one()

    hoy = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    hoy_stmt = base.where(AuditoriaEvento.fecha_evento >= hoy)
    hoy_result = await db.execute(hoy_stmt)
    hoy_count = hoy_result.scalar_one()

    tipos_stmt = (
        select(AuditoriaEvento.evento_tipo, func.count())
        .where(AuditoriaEvento.municipio_id == municipio_id)
        .group_by(AuditoriaEvento.evento_tipo)
    )
    tipos_result = await db.execute(tipos_stmt)
    por_tipo = {r[0]: r[1] for r in tipos_result.all()}

    return {
        "total_eventos": total,
        "exitosos": exitosos,
        "fallidos": fallidos,
        "hoy": hoy_count,
        "por_tipo": por_tipo,
    }
