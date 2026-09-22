"""
Servicio de Gestión de Productos - SIGEM Colombia
=================================================

Proporciona operaciones CRUD para el módulo de Productos
asociados a programas, con referencias a dependencias y
gestores líderes.

Autor: SIGEM Colombia
Versión: 1.0
Fecha: 2026-09-20
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.producto import Producto
from ..models.programa import Programa
from ..models.linea_estrategica import LineaEstrategica
from ..models.dependencia import Dependencia
from ..models.gestor_lider import GestorLider


# ---------------------------------------------------------------------------
# Creación de producto
# ---------------------------------------------------------------------------

async def create_producto(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    create_data: dict,
) -> dict:
    """
    Crea un nuevo producto asociado a un programa.

    Valida que el programa exista y pertenezca al municipio.
    Valida que dependencia_responsable y gestor_lider existan si se proporcionan.

    :param db: Sesión de base de datos asíncrona.
    :param municipio_id: Identificador del municipio.
    :param create_data: Diccionario con los datos de creación.
        Campos requeridos: programa_id, codigo, nombre.
        Campos opcionales: descripcion, unidad_medida,
            dependencia_responsable_id, gestor_lider_id, estado.
    :return: Diccionario con los datos del producto creado.
    :raises ValueError: Si faltan datos requeridos o las relaciones no existen.
    """
    programa_id = create_data.get("programa_id")
    codigo = create_data.get("codigo")
    nombre = create_data.get("nombre")
    codigo_indicador = create_data.get("codigo_indicador", None)
    indicador = create_data.get("indicador", None)
    meta_redactada = create_data.get("meta_redactada", None)
    linea_base = create_data.get("linea_base", 0)
    meta_cuatrienio = create_data.get("meta_cuatrienio", 0)
    descripcion = create_data.get("descripcion", None)
    unidad_medida = create_data.get("unidad_medida", None)
    dependencia_responsable_id = create_data.get("dependencia_responsable_id", None)
    gestor_lider_id = create_data.get("gestor_lider_id", None)
    estado = create_data.get("estado", "ACTIVO")

    if not programa_id:
        raise ValueError("El programa es obligatorio.")
    if not codigo:
        raise ValueError("El código es obligatorio.")
    if not nombre:
        raise ValueError("El nombre es obligatorio.")

    # Validar que el programa exista y pertenezca al municipio
    programa_stmt = select(Programa).where(
        and_(
            Programa.id == programa_id,
            Programa.municipio_id == municipio_id,
            Programa.deleted_at.is_(None),
        )
    )
    programa_result = await db.execute(programa_stmt)
    programa = programa_result.scalar_one_or_none()

    if programa is None:
        raise ValueError(
            "El programa no existe o no pertenece a este municipio."
        )

    # Validar que la dependencia exista si se proporciona
    if dependencia_responsable_id:
        dep_stmt = select(Dependencia).where(
            and_(
                Dependencia.id == dependencia_responsable_id,
                Dependencia.municipio_id == municipio_id,
                Dependencia.deleted_at.is_(None),
            )
        )
        dep_result = await db.execute(dep_stmt)
        dep = dep_result.scalar_one_or_none()
        if dep is None:
            raise ValueError(
                "La dependencia responsable no existe o no pertenece a este municipio."
            )

    # Validar que el gestor líder exista si se proporciona
    if gestor_lider_id:
        gestor_stmt = select(GestorLider).where(
            and_(
                GestorLider.id == gestor_lider_id,
                GestorLider.municipio_id == municipio_id,
                GestorLider.deleted_at.is_(None),
            )
        )
        gestor_result = await db.execute(gestor_stmt)
        gestor = gestor_result.scalar_one_or_none()
        if gestor is None:
            raise ValueError(
                "El gestor líder no existe o no pertenece a este municipio."
            )

    # Validar unicidad de código dentro del mismo programa
    exists_stmt = select(Producto.id).where(
        and_(
            Producto.programa_id == programa_id,
            Producto.codigo == codigo,
            Producto.deleted_at.is_(None),
        )
    )
    exists_result = await db.execute(exists_stmt)
    if exists_result.scalar_one_or_none() is not None:
        raise ValueError(
            f"Ya existe un producto con el código '{codigo}' "
            f"en este programa."
        )

    now = datetime.now(timezone.utc)

    producto = Producto(
        id=uuid.uuid4(),
        municipio_id=municipio_id,
        programa_id=programa_id,
        codigo=codigo,
        nombre=nombre,
        codigo_indicador=codigo_indicador,
        indicador=indicador,
        meta_redactada=meta_redactada,
        linea_base=linea_base,
        meta_cuatrienio=meta_cuatrienio,
        descripcion=descripcion,
        unidad_medida=unidad_medida,
        dependencia_responsable_id=dependencia_responsable_id,
        gestor_lider_id=gestor_lider_id,
        estado=estado,
        created_at=now,
        updated_at=now,
    )
    db.add(producto)
    await db.commit()
    await db.refresh(producto)

    return {
        "id": str(producto.id),
        "municipio_id": str(producto.municipio_id),
        "programa_id": str(producto.programa_id),
        "programa_nombre": programa.nombre,
        "programa_codigo": programa.codigo,
        "codigo": producto.codigo,
        "nombre": producto.nombre,
        "codigo_indicador": producto.codigo_indicador,
        "indicador": producto.indicador,
        "meta_redactada": producto.meta_redactada,
        "linea_base": producto.linea_base,
        "meta_cuatrienio": producto.meta_cuatrienio,
        "descripcion": producto.descripcion,
        "unidad_medida": producto.unidad_medida,
        "dependencia_responsable_id": str(producto.dependencia_responsable_id) if producto.dependencia_responsable_id else None,
        "gestor_lider_id": str(producto.gestor_lider_id) if producto.gestor_lider_id else None,
        "estado": producto.estado,
        "created_at": producto.created_at.isoformat(),
        "updated_at": producto.updated_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Listado de productos
# ---------------------------------------------------------------------------

async def list_productos(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    filtros: dict | None = None,
) -> dict:
    """
    Lista productos con filtros y paginación.

    Filtros disponibles:
      - search: Búsqueda por nombre o código.
      - programa_id: Filtrar por programa.
      - dependencia_id: Filtrar por dependencia responsable.
      - gestor_lider_id: Filtrar por gestor líder.
      - estado: Filtrar por estado (ACTIVO, INACTIVO).
      - page: Número de página (default: 1).
      - page_size: Elementos por página (default: 20, max: 100).

    :param db: Sesión de base de datos asíncrona.
    :param municipio_id: Identificador del municipio.
    :param filtros: Diccionario con los filtros de búsqueda.
    :return: Diccionario con productos, total, página y tamaño de página.
    """
    filtros = filtros or {}
    page = max(1, filtros.get("page", 1))
    page_size = min(100, max(1, filtros.get("page_size", 20)))
    offset = (page - 1) * page_size

    # Consulta base con joins para obtener nombres relacionados
    base_query = (
        select(
            Producto,
            Programa.nombre.label("programa_nombre"),
            Programa.codigo.label("programa_codigo"),
            Dependencia.nombre.label("dependencia_nombre"),
            GestorLider.nombre_completo.label("gestor_nombre"),
        )
        .join(
            Programa,
            Producto.programa_id == Programa.id,
        )
        .outerjoin(
            Dependencia,
            and_(
                Producto.dependencia_responsable_id == Dependencia.id,
                Dependencia.deleted_at.is_(None),
            ),
        )
        .outerjoin(
            GestorLider,
            and_(
                Producto.gestor_lider_id == GestorLider.id,
                GestorLider.deleted_at.is_(None),
            ),
        )
        .where(
            and_(
                Producto.municipio_id == municipio_id,
                Producto.deleted_at.is_(None),
            )
        )
    )

    # Filtro de búsqueda
    search = filtros.get("search")
    if search:
        search_pattern = f"%{search}%"
        base_query = base_query.where(
            or_(
                Producto.nombre.ilike(search_pattern),
                Producto.codigo.ilike(search_pattern),
            )
        )

    # Filtro por programa
    programa_id = filtros.get("programa_id")
    if programa_id:
        base_query = base_query.where(Producto.programa_id == programa_id)

    # Filtro por dependencia
    dependencia_id = filtros.get("dependencia_id")
    if dependencia_id:
        base_query = base_query.where(
            Producto.dependencia_responsable_id == dependencia_id
        )

    # Filtro por gestor líder
    gestor_lider_id = filtros.get("gestor_lider_id")
    if gestor_lider_id:
        base_query = base_query.where(
            Producto.gestor_lider_id == gestor_lider_id
        )

    # Filtro por estado
    estado = filtros.get("estado")
    if estado:
        base_query = base_query.where(Producto.estado == estado)

    # Contar total
    count_stmt = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Paginación
    query = base_query.order_by(Producto.created_at.desc())
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    rows = result.all()

    productos = []
    for producto, prog_nombre, prog_codigo, dep_nombre, gestor_nombre in rows:
        productos.append({
            "id": str(producto.id),
            "municipio_id": str(producto.municipio_id),
            "programa_id": str(producto.programa_id),
            "programa_nombre": prog_nombre,
            "programa_codigo": prog_codigo,
            "codigo": producto.codigo,
            "nombre": producto.nombre,
            "codigo_indicador": producto.codigo_indicador,
            "indicador": producto.indicador,
            "meta_redactada": producto.meta_redactada,
            "linea_base": producto.linea_base,
            "meta_cuatrienio": producto.meta_cuatrienio,
            "descripcion": producto.descripcion,
            "unidad_medida": producto.unidad_medida,
            "dependencia_responsable_id": str(producto.dependencia_responsable_id) if producto.dependencia_responsable_id else None,
            "dependencia_responsable_nombre": dep_nombre,
            "gestor_lider_id": str(producto.gestor_lider_id) if producto.gestor_lider_id else None,
            "gestor_lider_nombre": gestor_nombre,
            "estado": producto.estado,
            "created_at": producto.created_at.isoformat(),
            "updated_at": producto.updated_at.isoformat(),
        })

    return {
        "productos": productos,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


# ---------------------------------------------------------------------------
# Obtener producto por ID
# ---------------------------------------------------------------------------

async def get_producto(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    producto_id: uuid.UUID,
) -> dict | None:
    """
    Obtiene un producto por su ID dentro de un municipio.

    Incluye información del programa, dependencia y gestor relacionados.

    :param db: Sesión de base de datos asíncrona.
    :param municipio_id: Identificador del municipio.
    :param producto_id: Identificador del producto.
    :return: Diccionario con los datos del producto o None si no existe.
    """
    stmt = (
        select(
            Producto,
            Programa.nombre.label("programa_nombre"),
            Programa.codigo.label("programa_codigo"),
            Dependencia.nombre.label("dependencia_nombre"),
            GestorLider.nombre_completo.label("gestor_nombre"),
        )
        .join(
            Programa,
            Producto.programa_id == Programa.id,
        )
        .outerjoin(
            Dependencia,
            and_(
                Producto.dependencia_responsable_id == Dependencia.id,
                Dependencia.deleted_at.is_(None),
            ),
        )
        .outerjoin(
            GestorLider,
            and_(
                Producto.gestor_lider_id == GestorLider.id,
                GestorLider.deleted_at.is_(None),
            ),
        )
        .where(
            and_(
                Producto.id == producto_id,
                Producto.municipio_id == municipio_id,
                Producto.deleted_at.is_(None),
            )
        )
    )
    result = await db.execute(stmt)
    row = result.first()

    if row is None:
        return None

    producto, prog_nombre, prog_codigo, dep_nombre, gestor_nombre = row

    return {
        "id": str(producto.id),
        "municipio_id": str(producto.municipio_id),
        "programa_id": str(producto.programa_id),
        "programa_nombre": prog_nombre,
        "programa_codigo": prog_codigo,
        "codigo": producto.codigo,
        "nombre": producto.nombre,
        "codigo_indicador": producto.codigo_indicador,
        "indicador": producto.indicador,
        "meta_redactada": producto.meta_redactada,
        "linea_base": producto.linea_base,
        "meta_cuatrienio": producto.meta_cuatrienio,
        "descripcion": producto.descripcion,
        "unidad_medida": producto.unidad_medida,
        "dependencia_responsable_id": str(producto.dependencia_responsable_id) if producto.dependencia_responsable_id else None,
        "dependencia_responsable_nombre": dep_nombre,
        "gestor_lider_id": str(producto.gestor_lider_id) if producto.gestor_lider_id else None,
        "gestor_lider_nombre": gestor_nombre,
        "estado": producto.estado,
        "created_at": producto.created_at.isoformat(),
        "updated_at": producto.updated_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Actualizar producto
# ---------------------------------------------------------------------------

async def update_producto(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    producto_id: uuid.UUID,
    update_data: dict,
) -> dict | None:
    """
    Actualiza la información de un producto.

    Campos actualizables:
      - programa_id (con validación de existencia)
      - codigo (con validación de unicidad por programa)
      - nombre
      - descripcion
      - unidad_medida
      - dependencia_responsable_id (con validación de existencia)
      - gestor_lider_id (con validación de existencia)
      - estado

    :param db: Sesión de base de datos asíncrona.
    :param municipio_id: Identificador del municipio.
    :param producto_id: Identificador del producto.
    :param update_data: Diccionario con los campos a actualizar.
    :return: Diccionario actualizado o None si no existe.
    :raises ValueError: Si alguna relación referenciada no existe.
    """
    stmt = select(Producto).where(
        and_(
            Producto.id == producto_id,
            Producto.municipio_id == municipio_id,
            Producto.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    producto = result.scalar_one_or_none()

    if producto is None:
        return None

    now = datetime.now(timezone.utc)

    # Si se cambia el programa, validar que exista
    if "programa_id" in update_data:
        new_programa_id = update_data["programa_id"]
        programa_stmt = select(Programa).where(
            and_(
                Programa.id == new_programa_id,
                Programa.municipio_id == municipio_id,
                Programa.deleted_at.is_(None),
            )
        )
        programa_result = await db.execute(programa_stmt)
        programa = programa_result.scalar_one_or_none()
        if programa is None:
            raise ValueError(
                "El programa no existe o no pertenece a este municipio."
            )
        producto.programa_id = new_programa_id

    # Si se cambia la dependencia, validar que exista
    if "dependencia_responsable_id" in update_data:
        new_dep_id = update_data["dependencia_responsable_id"]
        if new_dep_id is not None:
            dep_stmt = select(Dependencia).where(
                and_(
                    Dependencia.id == new_dep_id,
                    Dependencia.municipio_id == municipio_id,
                    Dependencia.deleted_at.is_(None),
                )
            )
            dep_result = await db.execute(dep_stmt)
            dep = dep_result.scalar_one_or_none()
            if dep is None:
                raise ValueError(
                    "La dependencia responsable no existe o no pertenece a este municipio."
                )
        producto.dependencia_responsable_id = new_dep_id

    # Si se cambia el gestor, validar que exista
    if "gestor_lider_id" in update_data:
        new_gestor_id = update_data["gestor_lider_id"]
        if new_gestor_id is not None:
            gestor_stmt = select(GestorLider).where(
                and_(
                    GestorLider.id == new_gestor_id,
                    GestorLider.municipio_id == municipio_id,
                    GestorLider.deleted_at.is_(None),
                )
            )
            gestor_result = await db.execute(gestor_stmt)
            gestor = gestor_result.scalar_one_or_none()
            if gestor is None:
                raise ValueError(
                    "El gestor líder no existe o no pertenece a este municipio."
                )
        producto.gestor_lider_id = new_gestor_id

    # Si se cambia el código, validar unicidad dentro del programa
    if "codigo" in update_data:
        new_codigo = update_data["codigo"]
        programa_id = producto.programa_id
        exists_stmt = select(Producto.id).where(
            and_(
                Producto.programa_id == programa_id,
                Producto.codigo == new_codigo,
                Producto.id != producto_id,
                Producto.deleted_at.is_(None),
            )
        )
        exists_result = await db.execute(exists_stmt)
        if exists_result.scalar_one_or_none() is not None:
            raise ValueError(
                f"Ya existe un producto con el código '{new_codigo}' "
                f"en este programa."
            )
        producto.codigo = new_codigo

    # Actualizar campos simples
    updatable_fields = ["nombre", "codigo_indicador", "indicador", "meta_redactada", "linea_base", "meta_cuatrienio", "descripcion", "unidad_medida", "estado"]
    for field in updatable_fields:
        if field in update_data:
            setattr(producto, field, update_data[field])

    producto.updated_at = now
    await db.commit()
    await db.refresh(producto)

    # Obtener datos relacionados para la respuesta
    programa_stmt = select(Programa).where(
        Programa.id == producto.programa_id
    )
    prog_result = await db.execute(programa_stmt)
    prog = prog_result.scalar_one()

    dep_nombre = None
    if producto.dependencia_responsable_id:
        dep_stmt = select(Dependencia.nombre).where(
            Dependencia.id == producto.dependencia_responsable_id
        )
        dep_result = await db.execute(dep_stmt)
        dep_nombre = dep_result.scalar_one_or_none()

    gestor_nombre = None
    if producto.gestor_lider_id:
        gestor_stmt = select(GestorLider.nombre_completo).where(
            GestorLider.id == producto.gestor_lider_id
        )
        gestor_result = await db.execute(gestor_stmt)
        gestor_nombre = gestor_result.scalar_one_or_none()

    return {
        "id": str(producto.id),
        "municipio_id": str(producto.municipio_id),
        "programa_id": str(producto.programa_id),
        "programa_nombre": prog.nombre,
        "programa_codigo": prog.codigo,
        "codigo": producto.codigo,
        "nombre": producto.nombre,
        "codigo_indicador": producto.codigo_indicador,
        "indicador": producto.indicador,
        "meta_redactada": producto.meta_redactada,
        "linea_base": producto.linea_base,
        "meta_cuatrienio": producto.meta_cuatrienio,
        "descripcion": producto.descripcion,
        "unidad_medida": producto.unidad_medida,
        "dependencia_responsable_id": str(producto.dependencia_responsable_id) if producto.dependencia_responsable_id else None,
        "dependencia_responsable_nombre": dep_nombre,
        "gestor_lider_id": str(producto.gestor_lider_id) if producto.gestor_lider_id else None,
        "gestor_lider_nombre": gestor_nombre,
        "estado": producto.estado,
        "created_at": producto.created_at.isoformat(),
        "updated_at": producto.updated_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Eliminación lógica de producto
# ---------------------------------------------------------------------------

async def delete_producto(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    producto_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
) -> dict | None:
    """
    Realiza la eliminación lógica de un producto.

    Marca deleted_at y deleted_by en el registro. No se eliminan
    registros físicos de la base de datos.

    :param db: Sesión de base de datos asíncrona.
    :param municipio_id: Identificador del municipio.
    :param producto_id: Identificador del producto.
    :param user_id: Identificador del usuario que realiza la eliminación.
    :return: Diccionario de confirmación o None si no existe.
    """
    stmt = select(Producto).where(
        and_(
            Producto.id == producto_id,
            Producto.municipio_id == municipio_id,
            Producto.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    producto = result.scalar_one_or_none()

    if producto is None:
        return None

    now = datetime.now(timezone.utc)
    producto.deleted_at = now
    if user_id:
        producto.deleted_by = user_id
    producto.updated_at = now

    await db.commit()

    return {
        "id": str(producto.id),
        "codigo": producto.codigo,
        "nombre": producto.nombre,
        "deleted_at": producto.deleted_at.isoformat(),
        "message": f"Producto {producto.codigo} eliminado exitosamente.",
    }
