"""
Servicio de Dashboard Administrativo - SIGEM Colombia
=====================================================

Proporciona funciones de consulta consolidada para el panel de administración
del municipio. Incluye KPIs generales, resumen del plan de desarrollo,
resumen de gestores, alertas de seguridad y estadísticas por dependencia.

Autor: SIGEM Colombia
Versión: 1.0
Fecha: 2026-09-20
"""

import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.usuario import Usuario
from ..models.gestor_lider import GestorLider
from ..models.dependencia import Dependencia
from ..models.linea_estrategica import LineaEstrategica
from ..models.programa import Programa
from ..models.producto import Producto
from ..models.plan_desarrollo import PlanDesarrollo
from ..models.auditoria_evento import AuditoriaEvento


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

ESTADO_ACTIVO = "ACTIVO"
ESTADO_INACTIVO = "INACTIVO"
ESTADO_BLOQUEADO = "BLOQUEADO"
ELIMINADO = False
DIAS_INACTIVIDAD = 30
INTENTOS_MAXIMOS_FALLIDOS = 3


# ---------------------------------------------------------------------------
# 1. KPIs Generales
# ---------------------------------------------------------------------------

async def get_kpis_generales(
    db: AsyncSession,
    municipio_id: uuid.UUID,
) -> dict:
    """
    Obtiene los indicadores clave de rendimiento generales del municipio.

    Retorna:
      - total_gestores: Total de gestores líderes registrados.
      - gestores_activos: Gestores con estado ACTIVO.
      - gestores_inactivos: Gestores con estado INACTIVO.
      - gestores_bloqueados: Gestores con estado BLOQUEADO.
      - total_lineas_estrategicas: Total de líneas estratégicas activas.
      - total_programas: Total de programas activos.
      - total_productos: Total de productos activos.
      - total_dependencias: Total de dependencias activas.

    :param db: Sesión de base de datos asíncrona.
    :param municipio_id: Identificador del municipio.
    :return: Diccionario con todos los contadores.
    """
    # --- Gestores ---
    total_gestores_stmt = (
        select(func.count(GestorLider.id))
        .where(
            and_(
                GestorLider.municipio_id == municipio_id,
                GestorLider.eliminado == ELIMINADO,
            )
        )
    )
    total_gestores = (await db.execute(total_gestores_stmt)).scalar_one()

    gestores_activos_stmt = (
        select(func.count(GestorLider.id))
        .where(
            and_(
                GestorLider.municipio_id == municipio_id,
                GestorLider.eliminado == ELIMINADO,
                GestorLider.estado == ESTADO_ACTIVO,
            )
        )
    )
    gestores_activos = (await db.execute(gestores_activos_stmt)).scalar_one()

    gestores_inactivos_stmt = (
        select(func.count(GestorLider.id))
        .where(
            and_(
                GestorLider.municipio_id == municipio_id,
                GestorLider.eliminado == ELIMINADO,
                GestorLider.estado == ESTADO_INACTIVO,
            )
        )
    )
    gestores_inactivos = (await db.execute(gestores_inactivos_stmt)).scalar_one()

    gestores_bloqueados_stmt = (
        select(func.count(GestorLider.id))
        .where(
            and_(
                GestorLider.municipio_id == municipio_id,
                GestorLider.eliminado == ELIMINADO,
                GestorLider.estado == ESTADO_BLOQUEADO,
            )
        )
    )
    gestores_bloqueados = (await db.execute(gestores_bloqueados_stmt)).scalar_one()

    # --- Líneas estratégicas ---
    lineas_stmt = (
        select(func.count(LineaEstrategica.id))
        .where(
            and_(
                LineaEstrategica.municipio_id == municipio_id,
                LineaEstrategica.estado != "ELIMINADO_LOGICAMENTE",
            )
        )
    )
    total_lineas = (await db.execute(lineas_stmt)).scalar_one()

    # --- Programas ---
    programas_stmt = (
        select(func.count(Programa.id))
        .where(
            and_(
                Programa.municipio_id == municipio_id,
                Programa.estado != "ELIMINADO_LOGICAMENTE",
            )
        )
    )
    total_programas = (await db.execute(programas_stmt)).scalar_one()

    # --- Productos ---
    productos_stmt = (
        select(func.count(Producto.id))
        .where(
            and_(
                Producto.municipio_id == municipio_id,
                Producto.estado != "ELIMINADO_LOGICAMENTE",
            )
        )
    )
    total_productos = (await db.execute(productos_stmt)).scalar_one()

    # --- Dependencias ---
    dependencias_stmt = (
        select(func.count(Dependencia.id))
        .where(
            and_(
                Dependencia.municipio_id == municipio_id,
                Dependencia.estado != "ELIMINADO_LOGICAMENTE",
            )
        )
    )
    total_dependencias = (await db.execute(dependencias_stmt)).scalar_one()

    return {
        "total_gestores": total_gestores,
        "gestores_activos": gestores_activos,
        "gestores_inactivos": gestores_inactivos,
        "gestores_bloqueados": gestores_bloqueados,
        "total_lineas_estrategicas": total_lineas,
        "total_programas": total_programas,
        "total_productos": total_productos,
        "total_dependencias": total_dependencias,
    }


# ---------------------------------------------------------------------------
# 2. Resumen del Plan de Desarrollo
# ---------------------------------------------------------------------------

async def get_resumen_plan(
    db: AsyncSession,
    municipio_id: uuid.UUID,
) -> dict | None:
    """
    Obtiene un resumen del plan de desarrollo activo del municipio.

    Incluye:
      - Datos del plan (id, código, nombre, fechas, vigencias).
      - Cantidad total de líneas estratégicas.
      - Cantidad total de programas.
      - Cantidad total de productos.
      - Desglose por línea estratégica con sus programas y productos.

    :param db: Sesión de base de datos asíncrona.
    :param municipio_id: Identificador del municipio.
    :return: Diccionario con el resumen del plan o None si no hay plan activo.
    """
    # Obtener plan activo
    plan_stmt = (
        select(PlanDesarrollo)
        .where(
            and_(
                PlanDesarrollo.municipio_id == municipio_id,
                PlanDesarrollo.estado == ESTADO_ACTIVO,
            )
        )
        .order_by(PlanDesarrollo.created_at.desc())
        .limit(1)
    )
    plan_result = await db.execute(plan_stmt)
    plan = plan_result.scalar_one_or_none()

    if plan is None:
        return None

    # Contar líneas estratégicas del plan
    lineas_stmt = (
        select(func.count(LineaEstrategica.id))
        .where(
            and_(
                LineaEstrategica.plan_desarrollo_id == plan.id,
                LineaEstrategica.municipio_id == municipio_id,
                LineaEstrategica.estado != "ELIMINADO_LOGICAMENTE",
            )
        )
    )
    total_lineas = (await db.execute(lineas_stmt)).scalar_one()

    # Contar programas del plan
    programas_stmt = (
        select(func.count(Programa.id))
        .join(LineaEstrategica, Programa.linea_estrategica_id == LineaEstrategica.id)
        .where(
            and_(
                LineaEstrategica.plan_desarrollo_id == plan.id,
                Programa.municipio_id == municipio_id,
                Programa.estado != "ELIMINADO_LOGICAMENTE",
            )
        )
    )
    total_programas = (await db.execute(programas_stmt)).scalar_one()

    # Contar productos del plan
    productos_stmt = (
        select(func.count(Producto.id))
        .join(Programa, Producto.programa_id == Programa.id)
        .join(LineaEstrategica, Programa.linea_estrategica_id == LineaEstrategica.id)
        .where(
            and_(
                LineaEstrategica.plan_desarrollo_id == plan.id,
                Producto.municipio_id == municipio_id,
                Producto.estado != "ELIMINADO_LOGICAMENTE",
            )
        )
    )
    total_productos = (await db.execute(productos_stmt)).scalar_one()

    # Desglose por línea estratégica
    lineas_detalle_stmt = (
        select(LineaEstrategica)
        .where(
            and_(
                LineaEstrategica.plan_desarrollo_id == plan.id,
                LineaEstrategica.municipio_id == municipio_id,
                LineaEstrategica.estado != "ELIMINADO_LOGICAMENTE",
            )
        )
        .order_by(LineaEstrategica.orden)
    )
    lineas_result = await db.execute(lineas_detalle_stmt)
    lineas = lineas_result.scalars().all()

    lineas_desglose = []
    for linea in lineas:
        # Contar programas de esta línea
        prog_count_stmt = (
            select(func.count(Programa.id))
            .where(
                and_(
                    Programa.linea_estrategica_id == linea.id,
                    Programa.municipio_id == municipio_id,
                    Programa.estado != "ELIMINADO_LOGICAMENTE",
                )
            )
        )
        prog_count = (await db.execute(prog_count_stmt)).scalar_one()

        # Contar productos de esta línea
        prod_count_stmt = (
            select(func.count(Producto.id))
            .join(Programa, Producto.programa_id == Programa.id)
            .where(
                and_(
                    Programa.linea_estrategica_id == linea.id,
                    Producto.municipio_id == municipio_id,
                    Producto.estado != "ELIMINADO_LOGICAMENTE",
                )
            )
        )
        prod_count = (await db.execute(prod_count_stmt)).scalar_one()

        lineas_desglose.append({
            "id": str(linea.id),
            "codigo": linea.codigo,
            "nombre": linea.nombre,
            "orden": linea.orden,
            "total_programas": prog_count,
            "total_productos": prod_count,
        })

    return {
        "plan": {
            "id": str(plan.id),
            "codigo": plan.codigo,
            "nombre": plan.nombre,
            "descripcion": plan.descripcion,
            "fecha_inicio": plan.fecha_inicio,
            "fecha_fin": plan.fecha_fin,
            "vigencias": plan.vigencias,
            "estado": plan.estado,
        },
        "total_lineas_estrategicas": total_lineas,
        "total_programas": total_programas,
        "total_productos": total_productos,
        "lineas_desglose": lineas_desglose,
    }


# ---------------------------------------------------------------------------
# 3. Resumen de Gestores
# ---------------------------------------------------------------------------

async def get_gestores_summary(
    db: AsyncSession,
    municipio_id: uuid.UUID,
) -> list[dict]:
    """
    Obtiene un resumen de todos los gestores líderes del municipio.

    Para cada gestor incluye:
      - Datos básicos (id, código, nombre, cargo).
      - Estado actual.
      - Último acceso del usuario asociado.
      - Total de productos asignados.

    :param db: Sesión de base de datos asíncrona.
    :param municipio_id: Identificador del municipio.
    :return: Lista de diccionarios con el resumen de cada gestor.
    """
    gestores_stmt = (
        select(GestorLider, Usuario)
        .join(Usuario, GestorLider.usuario_id == Usuario.id)
        .where(
            and_(
                GestorLider.municipio_id == municipio_id,
                GestorLider.eliminado == ELIMINADO,
                Usuario.eliminado == ELIMINADO,
            )
        )
        .order_by(GestorLider.created_at.desc())
    )
    result = await db.execute(gestores_stmt)
    rows = result.all()

    gestores = []
    for gestor, usuario in rows:
        # Contar productos asignados
        prod_count_stmt = (
            select(func.count(Producto.id))
            .where(
                and_(
                    Producto.gestor_lider_id == gestor.id,
                    Producto.municipio_id == municipio_id,
                    Producto.estado != "ELIMINADO_LOGICAMENTE",
                )
            )
        )
        prod_count = (await db.execute(prod_count_stmt)).scalar_one()

        gestores.append({
            "id": str(gestor.id),
            "usuario_id": str(usuario.id),
            "codigo": gestor.codigo,
            "nombre_completo": gestor.nombre_completo,
            "cargo": gestor.cargo,
            "estado": gestor.estado,
            "ultimo_acceso": usuario.ultimo_acceso.isoformat() if usuario.ultimo_acceso else None,
            "intentos_fallidos": usuario.intentos_fallidos,
            "mfa_activo": usuario.mfa_activo,
            "total_productos_asignados": prod_count,
            "created_at": gestor.created_at.isoformat(),
        })

    return gestores


# ---------------------------------------------------------------------------
# 4. Alertas de Seguridad
# ---------------------------------------------------------------------------

async def get_alertas(
    db: AsyncSession,
    municipio_id: uuid.UUID,
) -> list[dict]:
    """
    Obtiene las alertas de seguridad del municipio.

    Tipos de alerta:
      - intentos_fallidos: Gestores con más de 3 intentos fallidos de acceso.
      - bloqueado: Gestores actualmente bloqueados.
      - sin_acceso: Gestores sin acceso en los últimos 30 días.

    :param db: Sesión de base de datos asíncrona.
    :param municipio_id: Identificador del municipio.
    :return: Lista de diccionarios con las alertas detectadas.
    """
    alertas: list[dict] = []
    now = datetime.now(timezone.utc)
    cutoff_date = now - timedelta(days=DIAS_INACTIVIDAD)

    # --- Gestores con intentos fallidos > 3 ---
    intentos_stmt = (
        select(GestorLider, Usuario)
        .join(Usuario, GestorLider.usuario_id == Usuario.id)
        .where(
            and_(
                GestorLider.municipio_id == municipio_id,
                GestorLider.eliminado == ELIMINADO,
                Usuario.eliminado == ELIMINADO,
                Usuario.intentos_fallidos > INTENTOS_MAXIMOS_FALLIDOS,
            )
        )
    )
    intentos_result = await db.execute(intentos_stmt)
    intentos_rows = intentos_result.all()

    for gestor, usuario in intentos_rows:
        alertas.append({
            "tipo": "intentos_fallidos",
            "severidad": "ALTA",
            "gestor_id": str(gestor.id),
            "gestor_codigo": gestor.codigo,
            "gestor_nombre": gestor.nombre_completo,
            "mensaje": (
                f"El gestor {gestor.nombre_completo} tiene "
                f"{usuario.intentos_fallidos} intentos fallidos de acceso."
            ),
            "valor": usuario.intentos_fallidos,
            "detectado_en": now.isoformat(),
        })

    # --- Gestores bloqueados ---
    bloqueados_stmt = (
        select(GestorLider, Usuario)
        .join(Usuario, GestorLider.usuario_id == Usuario.id)
        .where(
            and_(
                GestorLider.municipio_id == municipio_id,
                GestorLider.eliminado == ELIMINADO,
                Usuario.eliminado == ELIMINADO,
                GestorLider.estado == ESTADO_BLOQUEADO,
            )
        )
    )
    bloqueados_result = await db.execute(bloqueados_stmt)
    bloqueados_rows = bloqueados_result.all()

    for gestor, usuario in bloqueados_rows:
        alertas.append({
            "tipo": "bloqueado",
            "severidad": "MEDIA",
            "gestor_id": str(gestor.id),
            "gestor_codigo": gestor.codigo,
            "gestor_nombre": gestor.nombre_completo,
            "mensaje": (
                f"El gestor {gestor.nombre_completo} se encuentra bloqueado."
                + (f" Motivo: {usuario.motivo_bloqueo}." if usuario.motivo_bloqueo else "")
            ),
            "motivo_bloqueo": usuario.motivo_bloqueo,
            "fecha_bloqueo": usuario.fecha_bloqueo.isoformat() if usuario.fecha_bloqueo else None,
            "detectado_en": now.isoformat(),
        })

    # --- Gestores sin acceso en los últimos 30 días ---
    sin_acceso_stmt = (
        select(GestorLider, Usuario)
        .join(Usuario, GestorLider.usuario_id == Usuario.id)
        .where(
            and_(
                GestorLider.municipio_id == municipio_id,
                GestorLider.eliminado == ELIMINADO,
                Usuario.eliminado == ELIMINADO,
                GestorLider.estado == ESTADO_ACTIVO,
                (
                    (Usuario.ultimo_acceso.is_(None))
                    | (Usuario.ultimo_acceso < cutoff_date)
                ),
            )
        )
    )
    sin_acceso_result = await db.execute(sin_acceso_stmt)
    sin_acceso_rows = sin_acceso_result.all()

    for gestor, usuario in sin_acceso_rows:
        ultima_vez = usuario.ultimo_acceso.isoformat() if usuario.ultimo_acceso else "nunca"
        alertas.append({
            "tipo": "sin_acceso",
            "severidad": "BAJA",
            "gestor_id": str(gestor.id),
            "gestor_codigo": gestor.codigo,
            "gestor_nombre": gestor.nombre_completo,
            "mensaje": (
                f"El gestor {gestor.nombre_completo} no accede al sistema "
                f"desde hace más de {DIAS_INACTIVIDAD} días. "
                f"Último acceso: {ultima_vez}."
            ),
            "ultimo_acceso": usuario.ultimo_acceso.isoformat() if usuario.ultimo_acceso else None,
            "dias_inactividad": (
                (now - usuario.ultimo_acceso).days
                if usuario.ultimo_acceso
                else None
            ),
            "detectado_en": now.isoformat(),
        })

    return alertas


# ---------------------------------------------------------------------------
# 5. Estadísticas por Dependencia
# ---------------------------------------------------------------------------

async def get_estadisticas_por_dependencia(
    db: AsyncSession,
    municipio_id: uuid.UUID,
) -> list[dict]:
    """
    Obtiene estadísticas agrupadas por dependencia del municipio.

    Para cada dependencia activa retorna:
      - Datos de la dependencia (id, código, nombre).
      - Total de productos responsables.
      - Total de gestores asignados (vía dependencia principal).

    :param db: Sesión de base de datos asíncrona.
    :param municipio_id: Identificador del municipio.
    :return: Lista de diccionarios con estadísticas por dependencia.
    """
    deps_stmt = (
        select(Dependencia)
        .where(
            and_(
                Dependencia.municipio_id == municipio_id,
                Dependencia.estado != "ELIMINADO_LOGICAMENTE",
            )
        )
        .order_by(Dependencia.nombre)
    )
    deps_result = await db.execute(deps_stmt)
    dependencias = deps_result.scalars().all()

    estadisticas: list[dict] = []

    for dep in dependencias:
        # Contar productos donde esta dependencia es la responsable
        prod_count_stmt = (
            select(func.count(Producto.id))
            .where(
                and_(
                    Producto.dependencia_responsable_id == dep.id,
                    Producto.municipio_id == municipio_id,
                    Producto.estado != "ELIMINADO_LOGICAMENTE",
                )
            )
        )
        prod_count = (await db.execute(prod_count_stmt)).scalar_one()

        # Contar gestores cuya dependencia principal es esta
        gestor_count_stmt = (
            select(func.count(GestorLider.id))
            .where(
                and_(
                    GestorLider.dependencia_principal_id == dep.id,
                    GestorLider.municipio_id == municipio_id,
                    GestorLider.eliminado == ELIMINADO,
                )
            )
        )
        gestor_count = (await db.execute(gestor_count_stmt)).scalar_one()

        estadisticas.append({
            "dependencia_id": str(dep.id),
            "dependencia_codigo": dep.codigo,
            "dependencia_nombre": dep.nombre,
            "nivel": dep.nivel,
            "total_productos": prod_count,
            "total_gestores": gestor_count,
        })

    return estadisticas
