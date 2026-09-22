"""
Servicio de Gestión de Líneas Estratégicas - SIGEM Colombia
==========================================================

Proporciona operaciones CRUD para el módulo de Líneas Estratégicas
asociadas a planes de desarrollo municipales.

Autor: SIGEM Colombia
Versión: 1.0
Fecha: 2026-09-20
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.linea_estrategica import LineaEstrategica
from ..models.plan_desarrollo import PlanDesarrollo


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

ELIMINADO = False


# ---------------------------------------------------------------------------
# Creación de línea estratégica
# ---------------------------------------------------------------------------

async def create_linea(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    create_data: dict,
) -> dict:
    plan_desarrollo_id = create_data.get("plan_desarrollo_id")
    numero = create_data.get("numero")
    nombre = create_data.get("nombre")
    descripcion = create_data.get("descripcion", None)
    orden = create_data.get("orden", 0)
    estado = create_data.get("estado", "ACTIVA")

    if not plan_desarrollo_id:
        raise ValueError("El plan de desarrollo es obligatorio.")
    if not nombre:
        raise ValueError("El nombre es obligatorio.")

    # Validar que el plan de desarrollo exista y pertenezca al municipio
    plan_stmt = select(PlanDesarrollo).where(
        and_(
            PlanDesarrollo.id == plan_desarrollo_id,
            PlanDesarrollo.municipio_id == municipio_id,
            PlanDesarrollo.deleted_at.is_(None),
        )
    )
    plan_result = await db.execute(plan_stmt)
    plan = plan_result.scalar_one_or_none()

    if plan is None:
        raise ValueError(
            "El plan de desarrollo no existe o no pertenece a este municipio."
        )

    # Auto-generar código único LE-XXX
    count_stmt = select(func.count()).where(
        and_(
            LineaEstrategica.plan_desarrollo_id == plan_desarrollo_id,
            LineaEstrategica.deleted_at.is_(None),
        )
    )
    count_result = await db.execute(count_stmt)
    existing_count = count_result.scalar_one()
    codigo = f"LE-{str(existing_count + 1).zfill(3)}"

    # Asegurar unicidad del código generado
    while True:
        exists_stmt = select(LineaEstrategica.id).where(
            and_(
                LineaEstrategica.plan_desarrollo_id == plan_desarrollo_id,
                LineaEstrategica.codigo == codigo,
                LineaEstrategica.deleted_at.is_(None),
            )
        )
        exists_result = await db.execute(exists_stmt)
        if exists_result.scalar_one_or_none() is None:
            break
        existing_count += 1
        codigo = f"LE-{str(existing_count + 1).zfill(3)}"

    now = datetime.now(timezone.utc)

    linea = LineaEstrategica(
        id=uuid.uuid4(),
        municipio_id=municipio_id,
        plan_desarrollo_id=plan_desarrollo_id,
        codigo=codigo,
        numero=numero,
        nombre=nombre,
        descripcion=descripcion,
        orden=orden,
        estado=estado,
        created_at=now,
        updated_at=now,
    )
    db.add(linea)
    await db.commit()
    await db.refresh(linea)

    return {
        "id": str(linea.id),
        "municipio_id": str(linea.municipio_id),
        "plan_desarrollo_id": str(linea.plan_desarrollo_id),
        "plan_desarrollo_nombre": plan.nombre,
        "codigo": linea.codigo,
        "numero": linea.numero,
        "nombre": linea.nombre,
        "descripcion": linea.descripcion,
        "orden": linea.orden,
        "estado": linea.estado,
        "created_at": linea.created_at.isoformat(),
        "updated_at": linea.updated_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Listado de líneas estratégicas
# ---------------------------------------------------------------------------

async def list_lineas(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    filtros: dict | None = None,
) -> dict:
    """
    Lista líneas estratégicas con filtros y paginación.

    Filtros disponibles:
      - search: Búsqueda por nombre o código.
      - plan_desarrollo_id: Filtrar por plan de desarrollo.
      - estado: Filtrar por estado (ACTIVA, INACTIVA).
      - page: Número de página (default: 1).
      - page_size: Elementos por página (default: 20, max: 100).

    :param db: Sesión de base de datos asíncrona.
    :param municipio_id: Identificador del municipio.
    :param filtros: Diccionario con los filtros de búsqueda.
    :return: Diccionario con líneas, total, página y tamaño de página.
    """
    filtros = filtros or {}
    page = max(1, filtros.get("page", 1))
    page_size = min(100, max(1, filtros.get("page_size", 20)))
    offset = (page - 1) * page_size

    # Consulta base
    base_query = (
        select(LineaEstrategica, PlanDesarrollo.nombre.label("plan_nombre"))
        .join(
            PlanDesarrollo,
            LineaEstrategica.plan_desarrollo_id == PlanDesarrollo.id,
        )
        .where(
            and_(
                LineaEstrategica.municipio_id == municipio_id,
                LineaEstrategica.deleted_at.is_(None),
            )
        )
    )

    # Filtro de búsqueda
    search = filtros.get("search")
    if search:
        search_pattern = f"%{search}%"
        base_query = base_query.where(
            or_(
                LineaEstrategica.nombre.ilike(search_pattern),
                LineaEstrategica.codigo.ilike(search_pattern),
            )
        )

    # Filtro por plan de desarrollo
    plan_desarrollo_id = filtros.get("plan_desarrollo_id")
    if plan_desarrollo_id:
        base_query = base_query.where(
            LineaEstrategica.plan_desarrollo_id == plan_desarrollo_id
        )

    # Filtro por estado
    estado = filtros.get("estado")
    if estado:
        base_query = base_query.where(LineaEstrategica.estado == estado)

    # Contar total
    count_stmt = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Paginación
    query = base_query.order_by(LineaEstrategica.orden, LineaEstrategica.created_at.desc())
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    rows = result.all()

    lineas = []
    for linea, plan_nombre in rows:
        lineas.append({
            "id": str(linea.id),
            "municipio_id": str(linea.municipio_id),
            "plan_desarrollo_id": str(linea.plan_desarrollo_id),
            "plan_desarrollo_nombre": plan_nombre,
            "codigo": linea.codigo,
            "numero": linea.numero,
            "nombre": linea.nombre,
            "descripcion": linea.descripcion,
            "orden": linea.orden,
            "estado": linea.estado,
            "created_at": linea.created_at.isoformat(),
            "updated_at": linea.updated_at.isoformat(),
        })

    return {
        "lineas": lineas,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


# ---------------------------------------------------------------------------
# Obtener línea estratégica por ID
# ---------------------------------------------------------------------------

async def get_linea(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    linea_id: uuid.UUID,
) -> dict | None:
    """
    Obtiene una línea estratégica por su ID dentro de un municipio.

    :param db: Sesión de base de datos asíncrona.
    :param municipio_id: Identificador del municipio.
    :param linea_id: Identificador de la línea estratégica.
    :return: Diccionario con los datos de la línea o None si no existe.
    """
    stmt = (
        select(LineaEstrategica, PlanDesarrollo.nombre.label("plan_nombre"))
        .join(
            PlanDesarrollo,
            LineaEstrategica.plan_desarrollo_id == PlanDesarrollo.id,
        )
        .where(
            and_(
                LineaEstrategica.id == linea_id,
                LineaEstrategica.municipio_id == municipio_id,
                LineaEstrategica.deleted_at.is_(None),
            )
        )
    )
    result = await db.execute(stmt)
    row = result.first()

    if row is None:
        return None

    linea, plan_nombre = row

    return {
        "id": str(linea.id),
        "municipio_id": str(linea.municipio_id),
        "plan_desarrollo_id": str(linea.plan_desarrollo_id),
        "plan_desarrollo_nombre": plan_nombre,
        "codigo": linea.codigo,
        "numero": linea.numero,
        "nombre": linea.nombre,
        "descripcion": linea.descripcion,
        "orden": linea.orden,
        "estado": linea.estado,
        "created_at": linea.created_at.isoformat(),
        "updated_at": linea.updated_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Actualizar línea estratégica
# ---------------------------------------------------------------------------

async def update_linea(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    linea_id: uuid.UUID,
    update_data: dict,
) -> dict | None:
    """
    Actualiza la información de una línea estratégica.

    Campos actualizables:
      - codigo (con validación de unicidad por plan)
      - nombre
      - descripcion
      - orden
      - estado
      - plan_desarrollo_id (con validación de existencia)

    :param db: Sesión de base de datos asíncrona.
    :param municipio_id: Identificador del municipio.
    :param linea_id: Identificador de la línea estratégica.
    :param update_data: Diccionario con los campos a actualizar.
    :return: Diccionario actualizado o None si no existe.
    :raises ValueError: Si el código ya existe en el plan o el plan no existe.
    """
    stmt = select(LineaEstrategica).where(
        and_(
            LineaEstrategica.id == linea_id,
            LineaEstrategica.municipio_id == municipio_id,
            LineaEstrategica.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    linea = result.scalar_one_or_none()

    if linea is None:
        return None

    now = datetime.now(timezone.utc)

    # Si se cambia el plan de desarrollo, validar que exista
    if "plan_desarrollo_id" in update_data:
        new_plan_id = update_data["plan_desarrollo_id"]
        plan_stmt = select(PlanDesarrollo).where(
            and_(
                PlanDesarrollo.id == new_plan_id,
                PlanDesarrollo.municipio_id == municipio_id,
                PlanDesarrollo.deleted_at.is_(None),
            )
        )
        plan_result = await db.execute(plan_stmt)
        plan = plan_result.scalar_one_or_none()
        if plan is None:
            raise ValueError(
                "El plan de desarrollo no existe o no pertenece a este municipio."
            )
        linea.plan_desarrollo_id = new_plan_id

    # Si se cambia el código, validar unicidad dentro del plan
    if "codigo" in update_data:
        new_codigo = update_data["codigo"]
        plan_id = linea.plan_desarrollo_id
        exists_stmt = select(LineaEstrategica.id).where(
            and_(
                LineaEstrategica.plan_desarrollo_id == plan_id,
                LineaEstrategica.codigo == new_codigo,
                LineaEstrategica.id != linea_id,
                LineaEstrategica.deleted_at.is_(None),
            )
        )
        exists_result = await db.execute(exists_stmt)
        if exists_result.scalar_one_or_none() is not None:
            raise ValueError(
                f"Ya existe una línea estratégica con el código '{new_codigo}' "
                f"en este plan de desarrollo."
            )
        linea.codigo = new_codigo

    # Actualizar campos simples
    updatable_fields = ["numero", "nombre", "descripcion", "orden", "estado"]
    for field in updatable_fields:
        if field in update_data:
            setattr(linea, field, update_data[field])

    linea.updated_at = now
    await db.commit()
    await db.refresh(linea)

    # Obtener nombre del plan para la respuesta
    plan_stmt = select(PlanDesarrollo.nombre).where(
        PlanDesarrollo.id == linea.plan_desarrollo_id
    )
    plan_result = await db.execute(plan_stmt)
    plan_nombre = plan_result.scalar_one()

    return {
        "id": str(linea.id),
        "municipio_id": str(linea.municipio_id),
        "plan_desarrollo_id": str(linea.plan_desarrollo_id),
        "plan_desarrollo_nombre": plan_nombre,
        "codigo": linea.codigo,
        "numero": linea.numero,
        "nombre": linea.nombre,
        "descripcion": linea.descripcion,
        "orden": linea.orden,
        "estado": linea.estado,
        "created_at": linea.created_at.isoformat(),
        "updated_at": linea.updated_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Eliminación lógica de línea estratégica
# ---------------------------------------------------------------------------

async def delete_linea(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    linea_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
) -> dict | None:
    """
    Realiza la eliminación lógica de una línea estratégica.

    Marca deleted_at y deleted_by en el registro. No se eliminan
    registros físicos de la base de datos.

    :param db: Sesión de base de datos asíncrona.
    :param municipio_id: Identificador del municipio.
    :param linea_id: Identificador de la línea estratégica.
    :param user_id: Identificador del usuario que realiza la eliminación.
    :return: Diccionario de confirmación o None si no existe.
    """
    stmt = select(LineaEstrategica).where(
        and_(
            LineaEstrategica.id == linea_id,
            LineaEstrategica.municipio_id == municipio_id,
            LineaEstrategica.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    linea = result.scalar_one_or_none()

    if linea is None:
        return None

    now = datetime.now(timezone.utc)
    linea.soft_delete(user_id) if user_id else setattr(linea, "deleted_at", now)
    linea.updated_at = now

    if user_id:
        linea.deleted_by = user_id

    await db.commit()

    return {
        "id": str(linea.id),
        "codigo": linea.codigo,
        "nombre": linea.nombre,
        "deleted_at": linea.deleted_at.isoformat(),
        "message": f"Línea estratégica {linea.codigo} eliminada exitosamente.",
    }
