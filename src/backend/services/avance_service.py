"""
Servicio de Avances de Productos - SIGEM Colombia
=================================================

Permite a los gestores líderes registrar avances en sus productos asignados.

Autor: SIGEM Colombia
Versión: 1.0
Fecha: 2026-09-21
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.avance_producto import AvanceProducto
from ..models.producto import Producto
from ..models.gestor_lider import GestorLider
from ..models.usuario import Usuario
from ..services.audit_service import AuditService


async def get_mis_productos(
    db: AsyncSession,
    usuario_id: uuid.UUID,
    municipio_id: uuid.UUID,
) -> list[dict]:
    """
    Obtiene los productos asignados al gestor actual.
    """
    gestor_stmt = (
        select(GestorLider.id)
        .where(
            and_(
                GestorLider.usuario_id == usuario_id,
                GestorLider.municipio_id == municipio_id,
                GestorLider.deleted_at.is_(None),
            )
        )
    )
    gestor_id = await db.scalar(gestor_stmt)
    if not gestor_id:
        return []

    stmt = (
        select(Producto)
        .where(
            and_(
                Producto.gestor_lider_id == gestor_id,
                Producto.municipio_id == municipio_id,
                Producto.deleted_at.is_(None),
            )
        )
        .order_by(Producto.codigo.asc())
    )
    result = await db.execute(stmt)
    productos = list(result.scalars().all())

    return [
        {
            "id": str(p.id),
            "codigo": p.codigo,
            "nombre": p.nombre,
            "indicador": p.indicador,
            "codigo_indicador": p.codigo_indicador,
            "meta_redactada": p.meta_redactada,
            "linea_base": p.linea_base,
            "meta_cuatrienio": p.meta_cuatrienio,
            "unidad_medida": p.unidad_medida,
            "estado": p.estado,
        }
        for p in productos
    ]


async def get_avances_producto(
    db: AsyncSession,
    producto_id: uuid.UUID,
    municipio_id: uuid.UUID,
) -> list[dict]:
    """
    Obtiene los avances registrados para un producto específico.
    """
    stmt = (
        select(AvanceProducto)
        .where(
            and_(
                AvanceProducto.producto_id == producto_id,
                AvanceProducto.municipio_id == municipio_id,
                AvanceProducto.deleted_at.is_(None),
            )
        )
        .order_by(AvanceProducto.created_at.desc())
    )
    result = await db.execute(stmt)
    avances = list(result.scalars().all())

    return [
        {
            "id": str(a.id),
            "producto_id": str(a.producto_id),
            "avance_porcentaje": a.avance_porcentaje,
            "avance_valor": a.avance_valor,
            "observaciones": a.observaciones,
            "evidencia_url": a.evidencia_url,
            "indicador": a.indicador,
            "periodo": a.periodo,
            "fecha_registro": a.fecha_registro.isoformat() if a.fecha_registro else None,
            "estado_revision": a.estado_revision,
            "evidencia_nombre": a.evidencia_nombre,
            "evidencia_tipo": a.evidencia_tipo,
            "estado": a.estado,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in avances
    ]


async def registrar_avance(
    db: AsyncSession,
    usuario_id: uuid.UUID,
    municipio_id: uuid.UUID,
    producto_id: uuid.UUID,
    avance_data: dict,
) -> dict:
    """
    Registra un nuevo avance para un producto.
    """
    gestor_stmt = (
        select(GestorLider.id)
        .where(
            and_(
                GestorLider.usuario_id == usuario_id,
                GestorLider.municipio_id == municipio_id,
                GestorLider.deleted_at.is_(None),
            )
        )
    )
    gestor_id = await db.scalar(gestor_stmt)
    if not gestor_id:
        raise ValueError("No se encontró un gestor líder asociado al usuario actual.")

    producto_stmt = (
        select(Producto)
        .where(
            and_(
                Producto.id == producto_id,
                Producto.municipio_id == municipio_id,
                Producto.gestor_lider_id == gestor_id,
                Producto.deleted_at.is_(None),
            )
        )
    )
    producto = await db.scalar(producto_stmt)
    if not producto:
        raise ValueError("El producto no existe o no está asignado a este gestor.")

    now = datetime.now(timezone.utc)
    avance = AvanceProducto(
        municipio_id=municipio_id,
        producto_id=producto_id,
        gestor_lider_id=gestor_id,
        avance_porcentaje=avance_data.get("avance_porcentaje", 0.0),
        avance_valor=avance_data.get("avance_valor"),
        observaciones=avance_data.get("observaciones"),
        evidencia_url=avance_data.get("evidencia_url"),
        indicador=avance_data.get("indicador"),
        periodo=avance_data.get("periodo"),
        fecha_registro=now,
        estado_revision=avance_data.get("estado_revision", "PENDIENTE"),
        evidencia_nombre=avance_data.get("evidencia_nombre"),
        evidencia_tipo=avance_data.get("evidencia_tipo"),
        estado="REGISTRADO",
        registrado_por=usuario_id,
        created_at=now,
        updated_at=now,
    )
    db.add(avance)
    await db.flush()

    audit = AuditService(db)
    await audit.log_event(
        evento_tipo="AVANCE_REGISTRADO",
        resultado="EXITOSO",
        municipio_id=municipio_id,
        usuario_id=usuario_id,
        recurso_tipo="AvanceProducto",
        recurso_id=avance.id,
        metadata={
            "producto_id": str(producto_id),
            "avance_porcentaje": avance.avance_porcentaje,
        },
    )

    await db.commit()
    await db.refresh(avance)

    return {
        "id": str(avance.id),
        "producto_id": str(avance.producto_id),
        "avance_porcentaje": avance.avance_porcentaje,
        "avance_valor": avance.avance_valor,
        "observaciones": avance.observaciones,
        "evidencia_url": avance.evidencia_url,
        "indicador": avance.indicador,
        "periodo": avance.periodo,
        "fecha_registro": avance.fecha_registro.isoformat() if avance.fecha_registro else None,
        "estado_revision": avance.estado_revision,
        "evidencia_nombre": avance.evidencia_nombre,
        "evidencia_tipo": avance.evidencia_tipo,
        "estado": avance.estado,
        "created_at": avance.created_at.isoformat() if avance.created_at else None,
    }


async def get_resumen_avances(
    db: AsyncSession,
    usuario_id: uuid.UUID,
    municipio_id: uuid.UUID,
) -> dict:
    """
    Resumen de avances del gestor actual.
    """
    gestor_stmt = (
        select(GestorLider.id)
        .where(
            and_(
                GestorLider.usuario_id == usuario_id,
                GestorLider.municipio_id == municipio_id,
                GestorLider.deleted_at.is_(None),
            )
        )
    )
    gestor_id = await db.scalar(gestor_stmt)
    if not gestor_id:
        return {
            "total_productos": 0,
            "productos_con_avance": 0,
            "avance_promedio": 0.0,
            "productos_completados": 0,
        }

    productos_stmt = (
        select(Producto)
        .where(
            and_(
                Producto.gestor_lider_id == gestor_id,
                Producto.municipio_id == municipio_id,
                Producto.deleted_at.is_(None),
            )
        )
    )
    productos_result = await db.execute(productos_stmt)
    productos = list(productos_result.scalars().all())
    total_productos = len(productos)

    avances_stmt = (
        select(
            AvanceProducto.producto_id,
            func.max(AvanceProducto.avance_porcentaje).label("max_avance"),
        )
        .where(
            and_(
                AvanceProducto.gestor_lider_id == gestor_id,
                AvanceProducto.municipio_id == municipio_id,
                AvanceProducto.deleted_at.is_(None),
            )
        )
        .group_by(AvanceProducto.producto_id)
    )
    avances_result = await db.execute(avances_stmt)
    avances_map = {row[0]: row[1] for row in avances_result.all()}

    productos_con_avance = len(avances_map)
    avances_values = list(avances_map.values())
    avance_promedio = sum(avances_values) / len(avances_values) if avances_values else 0.0
    productos_completados = sum(1 for v in avances_values if v >= 100.0)

    return {
        "total_productos": total_productos,
        "productos_con_avance": productos_con_avance,
        "avance_promedio": round(avance_promedio, 1),
        "productos_completados": productos_completados,
    }


async def get_avances_para_revision(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    gestor_lider_id: uuid.UUID | None = None,
    estado_revision: str | None = None,
    search: str | None = None,
) -> list[dict]:
    """
    Obtiene avances para revisión con datos del gestor y producto.
    Si se proporciona gestor_lider_id, filtra solo los avances de ese gestor (para gestor líder).
    Si no, retorna todos los avances del municipio (para admin).
    """
    conditions = [
        AvanceProducto.municipio_id == municipio_id,
        AvanceProducto.deleted_at.is_(None),
    ]

    if gestor_lider_id:
        conditions.append(AvanceProducto.gestor_lider_id == gestor_lider_id)

    if estado_revision:
        conditions.append(AvanceProducto.estado_revision == estado_revision)

    if search:
        search_filter = f"%{search}%"
        conditions.append(
            GestorLider.codigo.ilike(search_filter)
            | GestorLider.nombre_completo.ilike(search_filter)
            | Producto.codigo_indicador.ilike(search_filter)
            | Producto.indicador.ilike(search_filter)
        )

    stmt = (
        select(AvanceProducto, GestorLider, Producto)
        .join(GestorLider, AvanceProducto.gestor_lider_id == GestorLider.id)
        .join(Producto, AvanceProducto.producto_id == Producto.id)
        .where(and_(*conditions))
        .order_by(AvanceProducto.created_at.desc())
    )

    result = await db.execute(stmt)
    rows = list(result.all())

    return [
        {
            "id": str(avance.id),
            "producto_id": str(avance.producto_id),
            "producto_codigo": producto.codigo,
            "producto_nombre": producto.nombre,
            "codigo_indicador": producto.codigo_indicador,
            "indicador": avance.indicador or producto.indicador,
            "gestor_id": str(gestor.id),
            "gestor_codigo": gestor.codigo,
            "gestor_nombre": gestor.nombre_completo,
            "avance_porcentaje": avance.avance_porcentaje,
            "avance_valor": avance.avance_valor,
            "periodo": avance.periodo,
            "fecha_registro": avance.fecha_registro.isoformat() if avance.fecha_registro else None,
            "estado_revision": avance.estado_revision,
            "evidencia_nombre": avance.evidencia_nombre,
            "evidencia_tipo": avance.evidencia_tipo,
            "evidencia_url": avance.evidencia_url,
            "observaciones": avance.observaciones,
            "created_at": avance.created_at.isoformat() if avance.created_at else None,
        }
        for avance, gestor, producto in rows
    ]


async def get_estadisticas_revision(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    gestor_lider_id: uuid.UUID | None = None,
) -> dict:
    """
    Estadísticas para el dashboard de revisión.
    """
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    base_conditions = [
        AvanceProducto.municipio_id == municipio_id,
        AvanceProducto.deleted_at.is_(None),
    ]
    if gestor_lider_id:
        base_conditions.append(AvanceProducto.gestor_lider_id == gestor_lider_id)

    pendientes = await db.scalar(
        select(func.count()).select_from(AvanceProducto).where(
            and_(*base_conditions, AvanceProducto.estado_revision == "PENDIENTE")
        )
    )
    aprobados_semana = await db.scalar(
        select(func.count()).select_from(AvanceProducto).where(
            and_(
                *base_conditions,
                AvanceProducto.estado_revision == "APROBADO",
                AvanceProducto.updated_at >= week_ago,
            )
        )
    )
    devueltos = await db.scalar(
        select(func.count()).select_from(AvanceProducto).where(
            and_(*base_conditions, AvanceProducto.estado_revision == "RECHAZADO")
        )
    )

    return {
        "pendientes": pendientes or 0,
        "aprobados_semana": aprobados_semana or 0,
        "devueltos": devueltos or 0,
    }


async def revisar_avance(
    db: AsyncSession,
    avance_id: uuid.UUID,
    municipio_id: uuid.UUID,
    usuario_id: uuid.UUID,
    nuevo_estado: str,
    observacion: str | None = None,
) -> dict:
    """
    Aprueba o rechaza un avance.
    """
    stmt = select(AvanceProducto).where(
        and_(
            AvanceProducto.id == avance_id,
            AvanceProducto.municipio_id == municipio_id,
            AvanceProducto.deleted_at.is_(None),
        )
    )
    avance = await db.scalar(stmt)
    if not avance:
        raise ValueError("Avance no encontrado.")

    if nuevo_estado not in ("APROBADO", "RECHAZADO"):
        raise ValueError("Estado inválido. Debe ser APROBADO o RECHAZADO.")

    if nuevo_estado == "RECHAZADO" and not observacion:
        raise ValueError("La observación es obligatoria al devolver un avance.")

    avance.estado_revision = nuevo_estado
    if observacion:
        avance.observaciones = observacion
    avance.updated_at = datetime.now(timezone.utc)

    audit = AuditService(db)
    await audit.log_event(
        evento_tipo="AVANCE_REVISADO",
        resultado="EXITOSO",
        municipio_id=municipio_id,
        usuario_id=usuario_id,
        recurso_tipo="AvanceProducto",
        recurso_id=avance.id,
        metadata={
            "nuevo_estado": nuevo_estado,
            "observacion": observacion,
        },
    )

    await db.commit()
    await db.refresh(avance)

    return {
        "id": str(avance.id),
        "estado_revision": avance.estado_revision,
        "observaciones": avance.observaciones,
    }
