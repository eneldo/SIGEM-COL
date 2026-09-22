"""
Servicio de Dashboard del Gestor - SIGEM Colombia
==================================================

Proporciona funciones de consulta personalizadas para el panel individual
de cada gestor líder. Incluye KPIs personales, productos asignados,
productos pendientes y alertas de seguridad personal.

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
from ..models.usuario_dependencia import UsuarioDependencia


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

ELIMINADO = False
DIAS_SIN_ACTUALIZACION = 15


# ---------------------------------------------------------------------------
# 1. KPIs Personales
# ---------------------------------------------------------------------------

async def get_kpis_personales(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    gestor_id: uuid.UUID,
) -> dict:
    """
    Obtiene los indicadores clave de rendimiento personales del gestor.

    Retorna:
      - total_productos_asignados: Total de productos asignados al gestor.
      - total_dependencias_asignadas: Total de dependencias asociadas al usuario.
      - total_lineas_estrategicas: Total de líneas estratégicas asociadas
        (a través de los programas de sus productos).

    :param db: Sesión de base de datos asíncrona.
    :param municipio_id: Identificador del municipio.
    :param gestor_id: Identificador del gestor líder.
    :return: Diccionario con los KPIs personales.
    """
    # --- Total productos asignados ---
    productos_stmt = (
        select(func.count(Producto.id))
        .where(
            and_(
                Producto.gestor_lider_id == gestor_id,
                Producto.municipio_id == municipio_id,
                Producto.estado != "ELIMINADO_LOGICAMENTE",
            )
        )
    )
    total_productos = (await db.execute(productos_stmt)).scalar_one()

    # --- Total dependencias asignadas ---
    gestor_stmt = select(GestorLider).where(
        and_(
            GestorLider.id == gestor_id,
            GestorLider.municipio_id == municipio_id,
            GestorLider.eliminado == ELIMINADO,
        )
    )
    gestor_result = await db.execute(gestor_stmt)
    gestor = gestor_result.scalar_one_or_none()

    total_dependencias = 0
    if gestor:
        deps_stmt = (
            select(func.count(UsuarioDependencia.id))
            .where(
                and_(
                    UsuarioDependencia.usuario_id == gestor.usuario_id,
                    UsuarioDependencia.municipio_id == municipio_id,
                )
            )
        )
        total_dependencias = (await db.execute(deps_stmt)).scalar_one()

    # --- Total líneas estratégicas asociadas ---
    lineas_stmt = (
        select(func.count(func.distinct(LineaEstrategica.id)))
        .join(Programa, Programa.linea_estrategica_id == LineaEstrategica.id)
        .join(Producto, Producto.programa_id == Programa.id)
        .where(
            and_(
                Producto.gestor_lider_id == gestor_id,
                Producto.municipio_id == municipio_id,
                Producto.estado != "ELIMINADO_LOGICAMENTE",
                Programa.estado != "ELIMINADO_LOGICAMENTE",
                LineaEstrategica.estado != "ELIMINADO_LOGICAMENTE",
            )
        )
    )
    total_lineas = (await db.execute(lineas_stmt)).scalar_one()

    return {
        "total_productos_asignados": total_productos,
        "total_dependencias_asignadas": total_dependencias,
        "total_lineas_estrategicas": total_lineas,
    }


# ---------------------------------------------------------------------------
# 2. Mis Productos
# ---------------------------------------------------------------------------

async def get_mis_productos(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    gestor_id: uuid.UUID,
) -> list[dict]:
    """
    Lista todos los productos asignados al gestor líder.

    Para cada producto incluye:
      - Datos del producto (id, código, nombre, estado, unidad de medida).
      - Nombre del programa al que pertenece.
      - Nombre de la dependencia responsable.
      - Fecha de última actualización.

    :param db: Sesión de base de datos asíncrona.
    :param municipio_id: Identificador del municipio.
    :param gestor_id: Identificador del gestor líder.
    :return: Lista de diccionarios con los productos asignados.
    """
    productos_stmt = (
        select(Producto, Programa, Dependencia)
        .join(Programa, Producto.programa_id == Programa.id)
        .outerjoin(
            Dependencia,
            Producto.dependencia_responsable_id == Dependencia.id,
        )
        .where(
            and_(
                Producto.gestor_lider_id == gestor_id,
                Producto.municipio_id == municipio_id,
                Producto.estado != "ELIMINADO_LOGICAMENTE",
            )
        )
        .order_by(Producto.nombre)
    )
    result = await db.execute(productos_stmt)
    rows = result.all()

    productos: list[dict] = []
    for producto, programa, dependencia in rows:
        productos.append({
            "id": str(producto.id),
            "codigo": producto.codigo,
            "nombre": producto.nombre,
            "descripcion": producto.descripcion,
            "unidad_medida": producto.unidad_medida,
            "estado": producto.estado,
            "programa": {
                "id": str(programa.id),
                "codigo": programa.codigo,
                "nombre": programa.nombre,
            },
            "dependencia_responsable": {
                "id": str(dependencia.id) if dependencia else None,
                "codigo": dependencia.codigo if dependencia else None,
                "nombre": dependencia.nombre if dependencia else None,
            } if dependencia else None,
            "updated_at": producto.updated_at.isoformat(),
        })

    return productos


# ---------------------------------------------------------------------------
# 3. Mis Pendientes
# ---------------------------------------------------------------------------

async def get_mis_pendientes(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    gestor_id: uuid.UUID,
) -> list[dict]:
    """
    Obtiene los productos asignados al gestor que no han sido actualizados
    recientemente (en los últimos 15 días).

    Cada item pendiente incluye:
      - Datos del producto.
      - Nombre del programa.
      - Nombre de la dependencia responsable.
      - Días sin actualización.
      - Fecha de última actualización.

    :param db: Sesión de base de datos asíncrona.
    :param municipio_id: Identificador del municipio.
    :param gestor_id: Identificador del gestor líder.
    :return: Lista de diccionarios con los productos pendientes.
    """
    now = datetime.now(timezone.utc)
    cutoff_date = now - timedelta(days=DIAS_SIN_ACTUALIZACION)

    productos_stmt = (
        select(Producto, Programa, Dependencia)
        .join(Programa, Producto.programa_id == Programa.id)
        .outerjoin(
            Dependencia,
            Producto.dependencia_responsable_id == Dependencia.id,
        )
        .where(
            and_(
                Producto.gestor_lider_id == gestor_id,
                Producto.municipio_id == municipio_id,
                Producto.estado != "ELIMINADO_LOGICAMENTE",
                (
                    (Producto.updated_at < cutoff_date)
                    | (Producto.updated_at.is_(None))
                ),
            )
        )
        .order_by(Producto.updated_at.asc())
    )
    result = await db.execute(productos_stmt)
    rows = result.all()

    pendientes: list[dict] = []
    for producto, programa, dependencia in rows:
        if producto.updated_at:
            dias_sin_actualizacion = (now - producto.updated_at).days
        else:
            dias_sin_actualizacion = None

        pendientes.append({
            "id": str(producto.id),
            "codigo": producto.codigo,
            "nombre": producto.nombre,
            "descripcion": producto.descripcion,
            "unidad_medida": producto.unidad_medida,
            "estado": producto.estado,
            "programa": {
                "id": str(programa.id),
                "codigo": programa.codigo,
                "nombre": programa.nombre,
            },
            "dependencia_responsable": {
                "id": str(dependencia.id) if dependencia else None,
                "codigo": dependencia.codigo if dependencia else None,
                "nombre": dependencia.nombre if dependencia else None,
            } if dependencia else None,
            "dias_sin_actualizacion": dias_sin_actualizacion,
            "updated_at": producto.updated_at.isoformat() if producto.updated_at else None,
        })

    return pendientes


# ---------------------------------------------------------------------------
# 4. Mis Alertas Personales
# ---------------------------------------------------------------------------

async def get_mis_alertas(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    gestor_id: uuid.UUID,
) -> list[dict]:
    """
    Obtiene las alertas de seguridad personales del gestor.

    Tipos de alerta personal:
      - intentos_fallidos: Si el usuario tiene intentos fallidos > 0.
      - password_pendiente: Si el usuario debe cambiar su contraseña.
      - mfa_desactivado: Si el gestor no tiene MFA activo.
      - cuenta_bloqueada: Si el gestor se encuentra bloqueado.

    :param db: Sesión de base de datos asíncrona.
    :param municipio_id: Identificador del municipio.
    :param gestor_id: Identificador del gestor líder.
    :return: Lista de diccionarios con las alertas personales.
    """
    alertas: list[dict] = []
    now = datetime.now(timezone.utc)

    # Obtener gestor y usuario asociado
    gestor_stmt = (
        select(GestorLider, Usuario)
        .join(Usuario, GestorLider.usuario_id == Usuario.id)
        .where(
            and_(
                GestorLider.id == gestor_id,
                GestorLider.municipio_id == municipio_id,
                GestorLider.eliminado == ELIMINADO,
                Usuario.eliminado == ELIMINADO,
            )
        )
    )
    result = await db.execute(gestor_stmt)
    row = result.first()

    if row is None:
        return alertas

    gestor, usuario = row

    # --- Intentos fallidos ---
    if usuario.intentos_fallidos > 0:
        severidad = "ALTA" if usuario.intentos_fallidos >= 3 else "MEDIA"
        alertas.append({
            "tipo": "intentos_fallidos",
            "severidad": severidad,
            "mensaje": (
                f"Tiene {usuario.intentos_fallidos} intento(s) fallido(s) "
                f"de acceso. Si supera 3 intentos, su cuenta será bloqueada."
            ),
            "valor": usuario.intentos_fallidos,
            "detectado_en": now.isoformat(),
        })

    # --- Contraseña pendiente de cambio ---
    if usuario.must_change_password:
        alertas.append({
            "tipo": "password_pendiente",
            "severidad": "MEDIA",
            "mensaje": (
                "Debe cambiar su contraseña en el próximo inicio de sesión."
            ),
            "detectado_en": now.isoformat(),
        })

    # --- MFA desactivado ---
    if not usuario.mfa_activo:
        alertas.append({
            "tipo": "mfa_desactivado",
            "severidad": "BAJA",
            "mensaje": (
                "No tiene autenticación de dos factores (MFA) activada. "
                "Se recomienda activarla para mayor seguridad."
            ),
            "detectado_en": now.isoformat(),
        })

    # --- Cuenta bloqueada ---
    if gestor.estado == "BLOQUEADO":
        alertas.append({
            "tipo": "cuenta_bloqueada",
            "severidad": "CRITICA",
            "mensaje": (
                "Su cuenta se encuentra bloqueada. "
                + (
                    f" Motivo: {usuario.motivo_bloqueo}."
                    if usuario.motivo_bloqueo
                    else " Contacte al administrador."
                )
            ),
            "motivo_bloqueo": usuario.motivo_bloqueo,
            "fecha_bloqueo": (
                usuario.fecha_bloqueo.isoformat()
                if usuario.fecha_bloqueo
                else None
            ),
            "detectado_en": now.isoformat(),
        })

    return alertas
