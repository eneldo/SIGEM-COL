"""
Servicio de Gestión de Programas - SIGEM Colombia
=================================================

Proporciona operaciones CRUD para el módulo de Programas
asociados a líneas estratégicas.

Autor: SIGEM Colombia
Versión: 1.0
Fecha: 2026-09-20
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.programa import Programa
from ..models.linea_estrategica import LineaEstrategica


# ---------------------------------------------------------------------------
# Creación de programa
# ---------------------------------------------------------------------------

async def create_programa(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    create_data: dict,
) -> dict:
    """
    Crea un nuevo programa asociado a una línea estratégica.

    Valida que la línea estratégica exista y pertenezca al municipio.

    :param db: Sesión de base de datos asíncrona.
    :param municipio_id: Identificador del municipio.
    :param create_data: Diccionario con los datos de creación.
        Campos requeridos: linea_estrategica_id, codigo, nombre.
        Campos opcionales: descripcion, estado.
    :return: Diccionario con los datos del programa creado.
    :raises ValueError: Si faltan datos requeridos o la relación no existe.
    """
    linea_estrategica_id = create_data.get("linea_estrategica_id")
    codigo = create_data.get("codigo")
    nombre = create_data.get("nombre")
    sector = create_data.get("sector", None)
    descripcion = create_data.get("descripcion", None)
    estado = create_data.get("estado", "ACTIVO")

    if not linea_estrategica_id:
        raise ValueError("La línea estratégica es obligatoria.")
    if not codigo:
        raise ValueError("El código es obligatorio.")
    if not nombre:
        raise ValueError("El nombre es obligatorio.")

    # Validar que la línea estratégica exista y pertenezca al municipio
    linea_stmt = select(LineaEstrategica).where(
        and_(
            LineaEstrategica.id == linea_estrategica_id,
            LineaEstrategica.municipio_id == municipio_id,
            LineaEstrategica.deleted_at.is_(None),
        )
    )
    linea_result = await db.execute(linea_stmt)
    linea = linea_result.scalar_one_or_none()

    if linea is None:
        raise ValueError(
            "La línea estratégica no existe o no pertenece a este municipio."
        )

    # Validar unicidad de código dentro de la misma línea
    exists_stmt = select(Programa.id).where(
        and_(
            Programa.linea_estrategica_id == linea_estrategica_id,
            Programa.codigo == codigo,
            Programa.deleted_at.is_(None),
        )
    )
    exists_result = await db.execute(exists_stmt)
    if exists_result.scalar_one_or_none() is not None:
        raise ValueError(
            f"Ya existe un programa con el código '{codigo}' "
            f"en esta línea estratégica."
        )

    now = datetime.now(timezone.utc)

    programa = Programa(
        id=uuid.uuid4(),
        municipio_id=municipio_id,
        linea_estrategica_id=linea_estrategica_id,
        codigo=codigo,
        nombre=nombre,
        sector=sector,
        descripcion=descripcion,
        estado=estado,
        created_at=now,
        updated_at=now,
    )
    db.add(programa)
    await db.commit()
    await db.refresh(programa)

    return {
        "id": str(programa.id),
        "municipio_id": str(programa.municipio_id),
        "linea_estrategica_id": str(programa.linea_estrategica_id),
        "linea_estrategica_nombre": linea.nombre,
        "linea_estrategica_codigo": linea.codigo,
        "codigo": programa.codigo,
        "nombre": programa.nombre,
        "sector": programa.sector,
        "descripcion": programa.descripcion,
        "estado": programa.estado,
        "created_at": programa.created_at.isoformat(),
        "updated_at": programa.updated_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Listado de programas
# ---------------------------------------------------------------------------

async def list_programas(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    filtros: dict | None = None,
) -> dict:
    """
    Lista programas con filtros y paginación.

    Filtros disponibles:
      - search: Búsqueda por nombre o código.
      - linea_estrategica_id: Filtrar por línea estratégica.
      - estado: Filtrar por estado (ACTIVO, INACTIVO).
      - page: Número de página (default: 1).
      - page_size: Elementos por página (default: 20, max: 100).

    :param db: Sesión de base de datos asíncrona.
    :param municipio_id: Identificador del municipio.
    :param filtros: Diccionario con los filtros de búsqueda.
    :return: Diccionario con programas, total, página y tamaño de página.
    """
    filtros = filtros or {}
    page = max(1, filtros.get("page", 1))
    page_size = min(100, max(1, filtros.get("page_size", 20)))
    offset = (page - 1) * page_size

    # Consulta base con join a línea estratégica
    base_query = (
        select(
            Programa,
            LineaEstrategica.nombre.label("linea_nombre"),
            LineaEstrategica.codigo.label("linea_codigo"),
        )
        .join(
            LineaEstrategica,
            Programa.linea_estrategica_id == LineaEstrategica.id,
        )
        .where(
            and_(
                Programa.municipio_id == municipio_id,
                Programa.deleted_at.is_(None),
            )
        )
    )

    # Filtro de búsqueda
    search = filtros.get("search")
    if search:
        search_pattern = f"%{search}%"
        base_query = base_query.where(
            or_(
                Programa.nombre.ilike(search_pattern),
                Programa.codigo.ilike(search_pattern),
            )
        )

    # Filtro por línea estratégica
    linea_estrategica_id = filtros.get("linea_estrategica_id")
    if linea_estrategica_id:
        base_query = base_query.where(
            Programa.linea_estrategica_id == linea_estrategica_id
        )

    # Filtro por estado
    estado = filtros.get("estado")
    if estado:
        base_query = base_query.where(Programa.estado == estado)

    # Contar total
    count_stmt = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Paginación
    query = base_query.order_by(Programa.created_at.desc())
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    rows = result.all()

    programas = []
    for programa, linea_nombre, linea_codigo in rows:
        programas.append({
            "id": str(programa.id),
            "municipio_id": str(programa.municipio_id),
            "linea_estrategica_id": str(programa.linea_estrategica_id),
            "linea_estrategica_nombre": linea_nombre,
            "linea_estrategica_codigo": linea_codigo,
            "codigo": programa.codigo,
            "nombre": programa.nombre,
            "sector": programa.sector,
            "descripcion": programa.descripcion,
            "estado": programa.estado,
            "created_at": programa.created_at.isoformat(),
            "updated_at": programa.updated_at.isoformat(),
        })

    return {
        "programas": programas,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


# ---------------------------------------------------------------------------
# Obtener programa por ID
# ---------------------------------------------------------------------------

async def get_programa(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    programa_id: uuid.UUID,
) -> dict | None:
    """
    Obtiene un programa por su ID dentro de un municipio.

    :param db: Sesión de base de datos asíncrona.
    :param municipio_id: Identificador del municipio.
    :param programa_id: Identificador del programa.
    :return: Diccionario con los datos del programa o None si no existe.
    """
    stmt = (
        select(
            Programa,
            LineaEstrategica.nombre.label("linea_nombre"),
            LineaEstrategica.codigo.label("linea_codigo"),
        )
        .join(
            LineaEstrategica,
            Programa.linea_estrategica_id == LineaEstrategica.id,
        )
        .where(
            and_(
                Programa.id == programa_id,
                Programa.municipio_id == municipio_id,
                Programa.deleted_at.is_(None),
            )
        )
    )
    result = await db.execute(stmt)
    row = result.first()

    if row is None:
        return None

    programa, linea_nombre, linea_codigo = row

    return {
        "id": str(programa.id),
        "municipio_id": str(programa.municipio_id),
        "linea_estrategica_id": str(programa.linea_estrategica_id),
        "linea_estrategica_nombre": linea_nombre,
        "linea_estrategica_codigo": linea_codigo,
        "codigo": programa.codigo,
        "nombre": programa.nombre,
        "sector": programa.sector,
        "descripcion": programa.descripcion,
        "estado": programa.estado,
        "created_at": programa.created_at.isoformat(),
        "updated_at": programa.updated_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Actualizar programa
# ---------------------------------------------------------------------------

async def update_programa(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    programa_id: uuid.UUID,
    update_data: dict,
) -> dict | None:
    """
    Actualiza la información de un programa.

    Campos actualizables:
      - linea_estrategica_id (con validación de existencia)
      - codigo (con validación de unicidad por línea)
      - nombre
      - descripcion
      - estado

    :param db: Sesión de base de datos asíncrona.
    :param municipio_id: Identificador del municipio.
    :param programa_id: Identificador del programa.
    :param update_data: Diccionario con los campos a actualizar.
    :return: Diccionario actualizado o None si no existe.
    :raises ValueError: Si el código ya existe en la línea o la línea no existe.
    """
    stmt = select(Programa).where(
        and_(
            Programa.id == programa_id,
            Programa.municipio_id == municipio_id,
            Programa.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    programa = result.scalar_one_or_none()

    if programa is None:
        return None

    now = datetime.now(timezone.utc)

    # Si se cambia la línea estratégica, validar que exista
    if "linea_estrategica_id" in update_data:
        new_linea_id = update_data["linea_estrategica_id"]
        linea_stmt = select(LineaEstrategica).where(
            and_(
                LineaEstrategica.id == new_linea_id,
                LineaEstrategica.municipio_id == municipio_id,
                LineaEstrategica.deleted_at.is_(None),
            )
        )
        linea_result = await db.execute(linea_stmt)
        linea = linea_result.scalar_one_or_none()
        if linea is None:
            raise ValueError(
                "La línea estratégica no existe o no pertenece a este municipio."
            )
        programa.linea_estrategica_id = new_linea_id

    # Si se cambia el código, validar unicidad dentro de la línea
    if "codigo" in update_data:
        new_codigo = update_data["codigo"]
        linea_id = programa.linea_estrategica_id
        exists_stmt = select(Programa.id).where(
            and_(
                Programa.linea_estrategica_id == linea_id,
                Programa.codigo == new_codigo,
                Programa.id != programa_id,
                Programa.deleted_at.is_(None),
            )
        )
        exists_result = await db.execute(exists_stmt)
        if exists_result.scalar_one_or_none() is not None:
            raise ValueError(
                f"Ya existe un programa con el código '{new_codigo}' "
                f"en esta línea estratégica."
            )
        programa.codigo = new_codigo

    # Actualizar campos simples
    updatable_fields = ["nombre", "sector", "descripcion", "estado"]
    for field in updatable_fields:
        if field in update_data:
            setattr(programa, field, update_data[field])

    programa.updated_at = now
    await db.commit()
    await db.refresh(programa)

    # Obtener datos de la línea para la respuesta
    linea_stmt = select(LineaEstrategica).where(
        LineaEstrategica.id == programa.linea_estrategica_id
    )
    linea_result = await db.execute(linea_stmt)
    linea = linea_result.scalar_one()

    return {
        "id": str(programa.id),
        "municipio_id": str(programa.municipio_id),
        "linea_estrategica_id": str(programa.linea_estrategica_id),
        "linea_estrategica_nombre": linea.nombre,
        "linea_estrategica_codigo": linea.codigo,
        "codigo": programa.codigo,
        "nombre": programa.nombre,
        "sector": programa.sector,
        "descripcion": programa.descripcion,
        "estado": programa.estado,
        "created_at": programa.created_at.isoformat(),
        "updated_at": programa.updated_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Eliminación lógica de programa
# ---------------------------------------------------------------------------

async def delete_programa(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    programa_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
) -> dict | None:
    """
    Realiza la eliminación lógica de un programa.

    Marca deleted_at y deleted_by en el registro. No se eliminan
    registros físicos de la base de datos.

    :param db: Sesión de base de datos asíncrona.
    :param municipio_id: Identificador del municipio.
    :param programa_id: Identificador del programa.
    :param user_id: Identificador del usuario que realiza la eliminación.
    :return: Diccionario de confirmación o None si no existe.
    """
    stmt = select(Programa).where(
        and_(
            Programa.id == programa_id,
            Programa.municipio_id == municipio_id,
            Programa.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    programa = result.scalar_one_or_none()

    if programa is None:
        return None

    now = datetime.now(timezone.utc)
    programa.deleted_at = now
    if user_id:
        programa.deleted_by = user_id
    programa.updated_at = now

    await db.commit()

    return {
        "id": str(programa.id),
        "codigo": programa.codigo,
        "nombre": programa.nombre,
        "deleted_at": programa.deleted_at.isoformat(),
        "message": f"Programa {programa.codigo} eliminado exitosamente.",
    }
