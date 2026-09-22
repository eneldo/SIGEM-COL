"""
Servicio CRUD de Dependencias - SIGEM Colombia
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.dependencia import Dependencia


async def list_dependencias(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    filtros: dict,
) -> dict:
    """Listar dependencias con paginación, búsqueda y filtros."""
    page = filtros.get("page", 1)
    page_size = min(filtros.get("page_size", 20), 100)
    search = filtros.get("search", "")
    estado = filtros.get("estado", "")

    base = select(Dependencia).where(
        Dependencia.municipio_id == municipio_id,
        Dependencia.deleted_at.is_(None),
    )

    if search:
        patron = f"%{search}%"
        base = base.where(
            or_(
                Dependencia.nombre.ilike(patron),
                Dependencia.codigo.ilike(patron),
                Dependencia.descripcion.ilike(patron),
            )
        )

    if estado:
        if estado == "ACTIVO":
            base = base.where(Dependencia.estado == "ACTIVA")
        elif estado == "INACTIVO":
            base = base.where(Dependencia.estado == "INACTIVA")

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = base.order_by(Dependencia.codigo.asc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    rows = result.scalars().all()

    items = []
    for r in rows:
        items.append({
            "id": str(r.id),
            "municipio_id": str(r.municipio_id),
            "codigo": r.codigo,
            "nombre": r.nombre,
            "descripcion": r.descripcion,
            "dependencia_padre_id": str(r.dependencia_padre_id) if r.dependencia_padre_id else None,
            "nivel": r.nivel,
            "estado": r.estado,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


async def get_dependencia(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    dependencia_id: uuid.UUID,
) -> dict | None:
    """Obtener una dependencia por ID."""
    stmt = select(Dependencia).where(
        Dependencia.id == dependencia_id,
        Dependencia.municipio_id == municipio_id,
        Dependencia.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    r = result.scalar_one_or_none()
    if r is None:
        return None
    return {
        "id": str(r.id),
        "municipio_id": str(r.municipio_id),
        "codigo": r.codigo,
        "nombre": r.nombre,
        "descripcion": r.descripcion,
        "dependencia_padre_id": str(r.dependencia_padre_id) if r.dependencia_padre_id else None,
        "nivel": r.nivel,
        "estado": r.estado,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


async def create_dependencia(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    data: dict,
) -> dict:
    """Crear una nueva dependencia."""
    # Verificar que el código sea único dentro del municipio
    existing = await db.execute(
        select(Dependencia).where(
            Dependencia.codigo == data["codigo"],
            Dependencia.municipio_id == municipio_id,
            Dependencia.deleted_at.is_(None),
        )
    )
    if existing.scalar_one_or_none():
        raise ValueError(f"Ya existe una dependencia con el código '{data['codigo']}' en este municipio")

    # Validar dependencia padre si se proporciona
    if data.get("dependencia_padre_id"):
        padre = await db.execute(
            select(Dependencia).where(
                Dependencia.id == data["dependencia_padre_id"],
                Dependencia.municipio_id == municipio_id,
                Dependencia.deleted_at.is_(None),
            )
        )
        if not padre.scalar_one_or_none():
            raise ValueError("La dependencia padre no existe o no pertenece a este municipio")

    dep = Dependencia(
        municipio_id=municipio_id,
        codigo=data["codigo"],
        nombre=data["nombre"],
        descripcion=data.get("descripcion"),
        dependencia_padre_id=data.get("dependencia_padre_id"),
        nivel=data.get("nivel", 1),
        estado=data.get("estado", "ACTIVA"),
    )
    db.add(dep)
    await db.commit()
    await db.refresh(dep)

    return {
        "id": str(dep.id),
        "municipio_id": str(dep.municipio_id),
        "codigo": dep.codigo,
        "nombre": dep.nombre,
        "descripcion": dep.descripcion,
        "dependencia_padre_id": str(dep.dependencia_padre_id) if dep.dependencia_padre_id else None,
        "nivel": dep.nivel,
        "estado": dep.estado,
        "created_at": dep.created_at.isoformat() if dep.created_at else None,
        "updated_at": dep.updated_at.isoformat() if dep.updated_at else None,
    }


async def update_dependencia(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    dependencia_id: uuid.UUID,
    data: dict,
) -> dict | None:
    """Actualizar una dependencia existente."""
    stmt = select(Dependencia).where(
        Dependencia.id == dependencia_id,
        Dependencia.municipio_id == municipio_id,
        Dependencia.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    dep = result.scalar_one_or_none()
    if dep is None:
        return None

    # Verificar código duplicado si se está cambiando
    if "codigo" in data and data["codigo"] != dep.codigo:
        existing = await db.execute(
            select(Dependencia).where(
                Dependencia.codigo == data["codigo"],
                Dependencia.municipio_id == municipio_id,
                Dependencia.id != dependencia_id,
                Dependencia.deleted_at.is_(None),
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Ya existe otra dependencia con el código '{data['codigo']}'")

    # Validar dependencia padre si se proporciona
    if data.get("dependencia_padre_id"):
        if str(data["dependencia_padre_id"]) == str(dependencia_id):
            raise ValueError("Una dependencia no puede ser padre de sí misma")
        padre = await db.execute(
            select(Dependencia).where(
                Dependencia.id == data["dependencia_padre_id"],
                Dependencia.municipio_id == municipio_id,
                Dependencia.deleted_at.is_(None),
            )
        )
        if not padre.scalar_one_or_none():
            raise ValueError("La dependencia padre no existe o no pertenece a este municipio")

    for key, value in data.items():
        if value is not None and hasattr(dep, key):
            setattr(dep, key, value)

    dep.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(dep)

    return {
        "id": str(dep.id),
        "municipio_id": str(dep.municipio_id),
        "codigo": dep.codigo,
        "nombre": dep.nombre,
        "descripcion": dep.descripcion,
        "dependencia_padre_id": str(dep.dependencia_padre_id) if dep.dependencia_padre_id else None,
        "nivel": dep.nivel,
        "estado": dep.estado,
        "created_at": dep.created_at.isoformat() if dep.created_at else None,
        "updated_at": dep.updated_at.isoformat() if dep.updated_at else None,
    }


async def delete_dependencia(
    db: AsyncSession,
    municipio_id,
    dependencia_id,
    user_id,
) -> bool:
    """Eliminar lógicamente una dependencia."""
    if not isinstance(municipio_id, uuid.UUID):
        municipio_id = uuid.UUID(str(municipio_id))
    if not isinstance(dependencia_id, uuid.UUID):
        dependencia_id = uuid.UUID(str(dependencia_id))
    if not isinstance(user_id, uuid.UUID):
        user_id = uuid.UUID(str(user_id))

    stmt = select(Dependencia).where(
        Dependencia.id == dependencia_id,
        Dependencia.municipio_id == municipio_id,
        Dependencia.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    dep = result.scalar_one_or_none()
    if dep is None:
        return False

    dep.soft_delete(user_id)
    await db.commit()
    return True
