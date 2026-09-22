"""
Servicio de Gestión de Roles y Permisos - SIGEM Colombia
========================================================
CRUD completo para administración de roles y permisos del sistema.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.rol import Rol, Permiso
from ..models.usuario_rol import RolPermiso


async def create_rol(
    db: AsyncSession,
    create_data: dict,
) -> dict:
    codigo = create_data.get("codigo")
    nombre = create_data.get("nombre")
    descripcion = create_data.get("descripcion", None)
    nivel = create_data.get("nivel", 1)
    permisos_ids = create_data.get("permisos_ids", [])

    if not codigo:
        raise ValueError("El código es obligatorio.")
    if not nombre:
        raise ValueError("El nombre es obligatorio.")

    exists_stmt = select(Rol.id).where(
        and_(Rol.codigo == codigo, Rol.deleted_at.is_(None))
    )
    exists_result = await db.execute(exists_stmt)
    if exists_result.scalar_one_or_none() is not None:
        raise ValueError(f"Ya existe un rol con el código '{codigo}'.")

    now = datetime.now(timezone.utc)
    rol = Rol(
        id=uuid.uuid4(),
        codigo=codigo,
        nombre=nombre,
        descripcion=descripcion,
        nivel=nivel,
        estado="ACTIVO",
        created_at=now,
        updated_at=now,
    )
    db.add(rol)
    await db.flush()

    for pid in permisos_ids:
        permiso_stmt = select(Permiso).where(
            and_(Permiso.id == pid, Permiso.deleted_at.is_(None))
        )
        permiso_result = await db.execute(permiso_stmt)
        if permiso_result.scalar_one_or_none():
            rp = RolPermiso(rol_id=rol.id, permiso_id=pid)
            db.add(rp)

    await db.commit()
    await db.refresh(rol)

    permisos_list = await _get_rol_permisos(db, rol.id)

    return {
        "id": str(rol.id),
        "codigo": rol.codigo,
        "nombre": rol.nombre,
        "descripcion": rol.descripcion,
        "nivel": rol.nivel,
        "estado": rol.estado,
        "permisos": permisos_list,
        "created_at": rol.created_at.isoformat(),
        "updated_at": rol.updated_at.isoformat(),
    }


async def list_roles(
    db: AsyncSession,
    filtros: dict | None = None,
) -> dict:
    filtros = filtros or {}
    page = max(1, filtros.get("page", 1))
    page_size = min(100, max(1, filtros.get("page_size", 20)))
    offset = (page - 1) * page_size

    base_query = select(Rol).where(Rol.deleted_at.is_(None))

    search = filtros.get("search")
    if search:
        sp = f"%{search}%"
        base_query = base_query.where(
            or_(Rol.codigo.ilike(sp), Rol.nombre.ilike(sp))
        )

    count_stmt = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    query = base_query.order_by(Rol.nivel, Rol.codigo).offset(offset).limit(page_size)
    result = await db.execute(query)
    roles = result.scalars().all()

    items = []
    for r in roles:
        permisos_list = await _get_rol_permisos(db, r.id)
        items.append({
            "id": str(r.id),
            "codigo": r.codigo,
            "nombre": r.nombre,
            "descripcion": r.descripcion,
            "nivel": r.nivel,
            "estado": r.estado,
            "permisos": permisos_list,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat(),
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


async def get_rol(
    db: AsyncSession,
    rol_id: uuid.UUID,
) -> dict | None:
    stmt = select(Rol).where(
        and_(Rol.id == rol_id, Rol.deleted_at.is_(None))
    )
    result = await db.execute(stmt)
    rol = result.scalar_one_or_none()
    if rol is None:
        return None

    permisos_list = await _get_rol_permisos(db, rol.id)

    return {
        "id": str(rol.id),
        "codigo": rol.codigo,
        "nombre": rol.nombre,
        "descripcion": rol.descripcion,
        "nivel": rol.nivel,
        "estado": rol.estado,
        "permisos": permisos_list,
        "created_at": rol.created_at.isoformat(),
        "updated_at": rol.updated_at.isoformat(),
    }


async def update_rol(
    db: AsyncSession,
    rol_id: uuid.UUID,
    update_data: dict,
) -> dict | None:
    stmt = select(Rol).where(
        and_(Rol.id == rol_id, Rol.deleted_at.is_(None))
    )
    result = await db.execute(stmt)
    rol = result.scalar_one_or_none()
    if rol is None:
        return None

    now = datetime.now(timezone.utc)

    if "nombre" in update_data:
        rol.nombre = update_data["nombre"]
    if "descripcion" in update_data:
        rol.descripcion = update_data["descripcion"]
    if "nivel" in update_data:
        rol.nivel = update_data["nivel"]
    if "estado" in update_data:
        rol.estado = update_data["estado"]

    if "permisos_ids" in update_data:
        del_stmt = select(RolPermiso).where(RolPermiso.rol_id == rol_id)
        del_result = await db.execute(del_stmt)
        for rp in del_result.scalars().all():
            await db.delete(rp)

        for pid in update_data["permisos_ids"]:
            permiso_stmt = select(Permiso).where(
                and_(Permiso.id == pid, Permiso.deleted_at.is_(None))
            )
            permiso_result = await db.execute(permiso_stmt)
            if permiso_result.scalar_one_or_none():
                rp = RolPermiso(rol_id=rol_id, permiso_id=pid)
                db.add(rp)

    rol.updated_at = now
    await db.commit()
    await db.refresh(rol)

    return await get_rol(db, rol_id)


async def delete_rol(
    db: AsyncSession,
    rol_id: uuid.UUID,
) -> dict | None:
    stmt = select(Rol).where(
        and_(Rol.id == rol_id, Rol.deleted_at.is_(None))
    )
    result = await db.execute(stmt)
    rol = result.scalar_one_or_none()
    if rol is None:
        return None

    now = datetime.now(timezone.utc)
    rol.deleted_at = now
    rol.updated_at = now
    await db.commit()

    return {
        "id": str(rol.id),
        "codigo": rol.codigo,
        "nombre": rol.nombre,
        "deleted_at": rol.deleted_at.isoformat(),
        "message": f"Rol {rol.codigo} eliminado exitosamente.",
    }


async def list_permisos(
    db: AsyncSession,
    filtros: dict | None = None,
) -> dict:
    filtros = filtros or {}

    base_query = select(Permiso).where(Permiso.deleted_at.is_(None))

    modulo = filtros.get("modulo")
    if modulo:
        base_query = base_query.where(Permiso.modulo == modulo)

    result = await db.execute(base_query.order_by(Permiso.modulo, Permiso.accion))
    permisos = result.scalars().all()

    items = []
    for p in permisos:
        items.append({
            "id": str(p.id),
            "codigo": p.codigo,
            "nombre": p.nombre,
            "descripcion": p.descripcion,
            "modulo": p.modulo,
            "accion": p.accion,
            "estado": p.estado,
        })

    return {"items": items, "total": len(items)}


async def _get_rol_permisos(db: AsyncSession, rol_id: uuid.UUID) -> list:
    stmt = (
        select(Permiso.id, Permiso.codigo, Permiso.nombre, Permiso.modulo, Permiso.accion)
        .join(RolPermiso, RolPermiso.permiso_id == Permiso.id)
        .where(RolPermiso.rol_id == rol_id)
    )
    result = await db.execute(stmt)
    return [
        {"id": str(r[0]), "codigo": r[1], "nombre": r[2], "modulo": r[3], "accion": r[4]}
        for r in result.all()
    ]
