"""
Servicio de Reportes y Rendición de Cuentas - SIGEM Colombia
============================================================
Genera estadísticas, resúmenes y métricas para rendición de cuentas.
"""
import uuid
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.linea_estrategica import LineaEstrategica
from ..models.programa import Programa
from ..models.producto import Producto
from ..models.dependencia import Dependencia
from ..models.gestor_lider import GestorLider


async def get_resumen_general(
    db: AsyncSession,
    municipio_id: uuid.UUID,
) -> dict:
    lineas_stmt = select(func.count()).select_from(LineaEstrategica).where(
        and_(LineaEstrategica.municipio_id == municipio_id, LineaEstrategica.deleted_at.is_(None))
    )
    total_lineas = (await db.execute(lineas_stmt)).scalar_one()

    programas_stmt = (
        select(func.count())
        .select_from(Programa)
        .join(LineaEstrategica, Programa.linea_estrategica_id == LineaEstrategica.id)
        .where(
            and_(
                LineaEstrategica.municipio_id == municipio_id,
                Programa.deleted_at.is_(None),
                LineaEstrategica.deleted_at.is_(None),
            )
        )
    )
    total_programas = (await db.execute(programas_stmt)).scalar_one()

    productos_stmt = (
        select(func.count())
        .select_from(Producto)
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
    total_productos = (await db.execute(productos_stmt)).scalar_one()

    activos_stmt = (
        select(func.count())
        .select_from(Producto)
        .join(Programa, Producto.programa_id == Programa.id)
        .join(LineaEstrategica, Programa.linea_estrategica_id == LineaEstrategica.id)
        .where(
            and_(
                LineaEstrategica.municipio_id == municipio_id,
                Producto.estado == "ACTIVO",
                Producto.deleted_at.is_(None),
                Programa.deleted_at.is_(None),
                LineaEstrategica.deleted_at.is_(None),
            )
        )
    )
    productos_activos = (await db.execute(activos_stmt)).scalar_one()

    gestores_stmt = select(func.count()).select_from(GestorLider).where(
        and_(GestorLider.municipio_id == municipio_id, GestorLider.deleted_at.is_(None))
    )
    total_gestores = (await db.execute(gestores_stmt)).scalar_one()

    return {
        "total_lineas": total_lineas,
        "total_programas": total_programas,
        "total_productos": total_productos,
        "productos_activos": productos_activos,
        "productos_inactivos": total_productos - productos_activos,
        "total_gestores": total_gestores,
    }


async def get_resumen_por_linea(
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
        prog_stmt = select(func.count()).select_from(Programa).where(
            and_(
                Programa.linea_estrategica_id == linea.id,
                Programa.deleted_at.is_(None),
            )
        )
        total_prog = (await db.execute(prog_stmt)).scalar_one()

        prod_stmt = (
            select(func.count())
            .select_from(Producto)
            .join(Programa, Producto.programa_id == Programa.id)
            .where(
                and_(
                    Programa.linea_estrategica_id == linea.id,
                    Producto.deleted_at.is_(None),
                    Programa.deleted_at.is_(None),
                )
            )
        )
        total_prod = (await db.execute(prod_stmt)).scalar_one()

        items.append({
            "id": str(linea.id),
            "codigo": linea.codigo,
            "nombre": linea.nombre,
            "total_programas": total_prog,
            "total_productos": total_prod,
            "estado": linea.estado,
        })

    return items


async def get_resumen_por_programa(
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
        prod_stmt = select(func.count()).select_from(Producto).where(
            and_(
                Producto.programa_id == prog.id,
                Producto.deleted_at.is_(None),
            )
        )
        total_prod = (await db.execute(prod_stmt)).scalar_one()

        activos_stmt = select(func.count()).select_from(Producto).where(
            and_(
                Producto.programa_id == prog.id,
                Producto.estado == "ACTIVO",
                Producto.deleted_at.is_(None),
            )
        )
        prod_activos = (await db.execute(activos_stmt)).scalar_one()

        items.append({
            "id": str(prog.id),
            "codigo": prog.codigo,
            "nombre": prog.nombre,
            "sector": prog.sector,
            "linea_nombre": linea_nombre,
            "total_productos": total_prod,
            "productos_activos": prod_activos,
            "estado": prog.estado,
        })

    return items


async def get_resumen_por_dependencia(
    db: AsyncSession,
    municipio_id: uuid.UUID,
) -> list:
    deps_stmt = select(Dependencia).where(
        and_(
            Dependencia.municipio_id == municipio_id,
            Dependencia.deleted_at.is_(None),
        )
    )
    deps_result = await db.execute(deps_stmt)
    dependencias = deps_result.scalars().all()

    items = []
    for dep in dependencias:
        prod_stmt = select(func.count()).select_from(Producto).where(
            and_(
                Producto.dependencia_responsable_id == dep.id,
                Producto.deleted_at.is_(None),
            )
        )
        total_prod = (await db.execute(prod_stmt)).scalar_one()

        gestores_stmt = select(func.count()).select_from(GestorLider).where(
            and_(
                GestorLider.dependencia_principal_id == dep.id,
                GestorLider.deleted_at.is_(None),
            )
        )
        total_gestores = (await db.execute(gestores_stmt)).scalar_one()

        if total_prod > 0 or total_gestores > 0:
            items.append({
                "id": str(dep.id),
                "codigo": dep.codigo,
                "nombre": dep.nombre,
                "total_productos": total_prod,
                "total_gestores": total_gestores,
            })

    return items


async def get_metricas_productos(
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
    con_indicador = sum(1 for p in productos if p.codigo_indicador)
    con_meta = sum(1 for p in productos if p.meta_cuatrienio and p.meta_cuatrienio > 0)
    con_linea_base = sum(1 for p in productos if p.linea_base and p.linea_base > 0)
    con_gestor = sum(1 for p in productos if p.gestor_lider_id)

    promedio_avance = 0
    if con_linea_base > 0 and con_meta > 0:
        avances = []
        for p in productos:
            if p.linea_base and p.meta_cuatrienio and p.meta_cuatrienio > 0:
                avance = min(100, ((p.linea_base) / p.meta_cuatrienio) * 100)
                avances.append(avance)
        if avances:
            promedio_avance = round(sum(avances) / len(avances), 1)

    return {
        "total_productos": total,
        "con_indicador": con_indicador,
        "sin_indicador": total - con_indicador,
        "con_meta_cuatrienio": con_meta,
        "con_linea_base": con_linea_base,
        "con_gestor_asignado": con_gestor,
        "sin_gestor_asignado": total - con_gestor,
        "porcentaje_cumplimiento_indicador": round((con_indicador / total * 100), 1) if total > 0 else 0,
        "porcentaje_cumplimiento_meta": round((con_meta / total * 100), 1) if total > 0 else 0,
        "promedio_avance": promedio_avance,
    }
