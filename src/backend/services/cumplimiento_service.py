"""
Servicio de Cumplimiento de Metas - SIGEM Colombia
===================================================
Calcula el avance y cumplimiento de metas cuatrienales.
"""
import uuid
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.producto import Producto
from ..models.programa import Programa
from ..models.linea_estrategica import LineaEstrategica


async def get_cumplimiento_general(
    db: AsyncSession,
    municipio_id: uuid.UUID,
) -> dict:
    base = (
        select(Producto)
        .join(Programa, Producto.programa_id == Programa.id)
        .join(LineaEstrategica, Programa.linea_estrategica_id == LineaEstrategica.id)
        .where(
            and_(
                LineaEstrategica.municipio_id == municipio_id,
                Producto.deleted_at.is_(None),
                Programa.deleted_at.is_(None),
                LineaEstrategica.deleted_at.is_(None),
            )
        )
    )

    result = await db.execute(base)
    productos = result.scalars().all()

    total = len(productos)
    completados = 0
    en_progreso = 0
    sin_avance = 0
    total_porcentaje = 0
    count_con_meta = 0

    for p in productos:
        if p.meta_cuatrienio and p.meta_cuatrienio > 0:
            porcentaje = min(100, round((p.linea_base or 0) / p.meta_cuatrienio * 100))
            total_porcentaje += porcentaje
            count_con_meta += 1
            if porcentaje >= 100:
                completados += 1
            elif porcentaje > 0:
                en_progreso += 1
            else:
                sin_avance += 1
        else:
            sin_avance += 1

    promedio = round(total_porcentaje / count_con_meta, 1) if count_con_meta > 0 else 0

    return {
        "total_productos": total,
        "con_meta_definida": count_con_meta,
        "sin_meta_definida": total - count_con_meta,
        "completados": completados,
        "en_progreso": en_progreso,
        "sin_avance": sin_avance,
        "porcentaje_cumplimiento_general": promedio,
    }


async def get_cumplimiento_por_linea(
    db: AsyncSession,
    municipio_id: uuid.UUID,
) -> list:
    lineas_stmt = select(LineaEstrategica).where(
        and_(
            LineaEstrategica.municipio_id == municipio_id,
            LineaEstrategica.deleted_at.is_(None),
        )
    )
    lineas_result = await db.execute(lineas_stmt)
    lineas = lineas_result.scalars().all()

    items = []
    for linea in lineas:
        prod_stmt = (
            select(Producto)
            .join(Programa, Producto.programa_id == Programa.id)
            .where(
                and_(
                    Programa.linea_estrategica_id == linea.id,
                    Producto.deleted_at.is_(None),
                    Programa.deleted_at.is_(None),
                )
            )
        )
        prod_result = await db.execute(prod_stmt)
        productos = prod_result.scalars().all()

        total = len(productos)
        completados = 0
        en_progreso = 0
        sin_avance = 0
        total_porcentaje = 0
        count_con_meta = 0

        for p in productos:
            if p.meta_cuatrienio and p.meta_cuatrienio > 0:
                porcentaje = min(100, round((p.linea_base or 0) / p.meta_cuatrienio * 100))
                total_porcentaje += porcentaje
                count_con_meta += 1
                if porcentaje >= 100:
                    completados += 1
                elif porcentaje > 0:
                    en_progreso += 1
                else:
                    sin_avance += 1
            else:
                sin_avance += 1

        promedio = round(total_porcentaje / count_con_meta, 1) if count_con_meta > 0 else 0

        items.append({
            "id": str(linea.id),
            "codigo": linea.codigo,
            "nombre": linea.nombre,
            "total_productos": total,
            "con_meta_definida": count_con_meta,
            "completados": completados,
            "en_progreso": en_progreso,
            "sin_avance": sin_avance,
            "porcentaje_cumplimiento": promedio,
        })

    return items


async def get_cumplimiento_por_programa(
    db: AsyncSession,
    municipio_id: uuid.UUID,
) -> list:
    prog_stmt = (
        select(Programa, LineaEstrategica.nombre.label("linea_nombre"))
        .join(LineaEstrategica, Programa.linea_estrategica_id == LineaEstrategica.id)
        .where(
            and_(
                LineaEstrategica.municipio_id == municipio_id,
                Programa.deleted_at.is_(None),
                LineaEstrategica.deleted_at.is_(None),
            )
        )
    )
    prog_result = await db.execute(prog_stmt)
    programas = prog_result.all()

    items = []
    for prog, linea_nombre in programas:
        prod_stmt = select(Producto).where(
            and_(
                Producto.programa_id == prog.id,
                Producto.deleted_at.is_(None),
            )
        )
        prod_result = await db.execute(prod_stmt)
        productos = prod_result.scalars().all()

        total = len(productos)
        completados = 0
        en_progreso = 0
        sin_avance = 0
        total_porcentaje = 0
        count_con_meta = 0

        for p in productos:
            if p.meta_cuatrienio and p.meta_cuatrienio > 0:
                porcentaje = min(100, round((p.linea_base or 0) / p.meta_cuatrienio * 100))
                total_porcentaje += porcentaje
                count_con_meta += 1
                if porcentaje >= 100:
                    completados += 1
                elif porcentaje > 0:
                    en_progreso += 1
                else:
                    sin_avance += 1
            else:
                sin_avance += 1

        promedio = round(total_porcentaje / count_con_meta, 1) if count_con_meta > 0 else 0

        items.append({
            "id": str(prog.id),
            "codigo": prog.codigo,
            "nombre": prog.nombre,
            "linea_nombre": linea_nombre,
            "total_productos": total,
            "con_meta_definida": count_con_meta,
            "completados": completados,
            "en_progreso": en_progreso,
            "sin_avance": sin_avance,
            "porcentaje_cumplimiento": promedio,
        })

    return items


async def get_detalle_producto(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    producto_id: uuid.UUID,
) -> dict | None:
    stmt = (
        select(
            Producto,
            Programa.nombre.label("programa_nombre"),
            Programa.codigo.label("programa_codigo"),
            LineaEstrategica.nombre.label("linea_nombre"),
        )
        .join(Programa, Producto.programa_id == Programa.id)
        .join(LineaEstrategica, Programa.linea_estrategica_id == LineaEstrategica.id)
        .where(
            and_(
                Producto.id == producto_id,
                LineaEstrategica.municipio_id == municipio_id,
                Producto.deleted_at.is_(None),
                Programa.deleted_at.is_(None),
                LineaEstrategica.deleted_at.is_(None),
            )
        )
    )
    result = await db.execute(stmt)
    row = result.first()

    if row is None:
        return None

    p, prog_nombre, prog_codigo, linea_nombre = row

    porcentaje = 0
    if p.meta_cuatrienio and p.meta_cuatrienio > 0:
        porcentaje = min(100, round((p.linea_base or 0) / p.meta_cuatrienio * 100))

    estado_cumplimiento = "SIN_META"
    if p.meta_cuatrienio and p.meta_cuatrienio > 0:
        if porcentaje >= 100:
            estado_cumplimiento = "COMPLETADO"
        elif porcentaje > 0:
            estado_cumplimiento = "EN_PROGRESO"
        else:
            estado_cumplimiento = "SIN_AVANCE"

    return {
        "id": str(p.id),
        "codigo": p.codigo,
        "nombre": p.nombre,
        "codigo_indicador": p.codigo_indicador,
        "indicador": p.indicador,
        "meta_redactada": p.meta_redactada,
        "linea_base": p.linea_base,
        "meta_cuatrienio": p.meta_cuatrienio,
        "programa_codigo": prog_codigo,
        "programa_nombre": prog_nombre,
        "linea_nombre": linea_nombre,
        "porcentaje_avance": porcentaje,
        "estado_cumplimiento": estado_cumplimiento,
    }


async def get_listado_productos_cumplimiento(
    db: AsyncSession,
    municipio_id: uuid.UUID,
) -> list:
    stmt = (
        select(
            Producto,
            Programa.nombre.label("programa_nombre"),
            LineaEstrategica.nombre.label("linea_nombre"),
        )
        .join(Programa, Producto.programa_id == Programa.id)
        .join(LineaEstrategica, Programa.linea_estrategica_id == LineaEstrategica.id)
        .where(
            and_(
                LineaEstrategica.municipio_id == municipio_id,
                Producto.deleted_at.is_(None),
                Programa.deleted_at.is_(None),
                LineaEstrategica.deleted_at.is_(None),
            )
        )
        .order_by(Producto.codigo)
    )
    result = await db.execute(stmt)
    rows = result.all()

    items = []
    for p, prog_nombre, linea_nombre in rows:
        porcentaje = 0
        if p.meta_cuatrienio and p.meta_cuatrienio > 0:
            porcentaje = min(100, round((p.linea_base or 0) / p.meta_cuatrienio * 100))

        estado = "SIN_META"
        if p.meta_cuatrienio and p.meta_cuatrienio > 0:
            if porcentaje >= 100:
                estado = "COMPLETADO"
            elif porcentaje > 0:
                estado = "EN_PROGRESO"
            else:
                estado = "SIN_AVANCE"

        items.append({
            "id": str(p.id),
            "codigo": p.codigo,
            "nombre": p.nombre,
            "indicador": p.indicador,
            "linea_base": p.linea_base,
            "meta_cuatrienio": p.meta_cuatrienio,
            "programa_nombre": prog_nombre,
            "linea_nombre": linea_nombre,
            "porcentaje_avance": porcentaje,
            "estado_cumplimiento": estado,
        })

    return items
