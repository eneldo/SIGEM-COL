"""
Servicio de Gestión de Usuarios - SIGEM Colombia
=================================================
CRUD completo para administración de usuarios del sistema.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.usuario import Usuario
from ..models.rol import Rol
from ..models.usuario_rol import UsuarioRol
from ..models.dependencia import Dependencia
from ..models.usuario_dependencia import UsuarioDependencia
from ..core.security import get_password_hash


async def create_usuario(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    create_data: dict,
) -> dict:
    codigo = create_data.get("codigo")
    username = create_data.get("username")
    email = create_data.get("email")
    nombre_completo = create_data.get("nombre_completo")
    telefono = create_data.get("telefono", None)
    cargo = create_data.get("cargo", None)
    password = create_data.get("password")
    rol_id = create_data.get("rol_id", None)
    dependencia_id = create_data.get("dependencia_id", None)

    if not codigo:
        raise ValueError("El código es obligatorio.")
    if not username:
        raise ValueError("El username es obligatorio.")
    if not email:
        raise ValueError("El email es obligatorio.")
    if not nombre_completo:
        raise ValueError("El nombre completo es obligatorio.")
    if not password:
        raise ValueError("La contraseña es obligatoria.")

    exists_stmt = select(Usuario.id).where(
        and_(
            Usuario.codigo == codigo,
            Usuario.municipio_id == municipio_id,
            Usuario.deleted_at.is_(None),
        )
    )
    exists_result = await db.execute(exists_stmt)
    if exists_result.scalar_one_or_none() is not None:
        raise ValueError(f"Ya existe un usuario con el código '{codigo}'.")

    exists_user_stmt = select(Usuario.id).where(
        and_(
            Usuario.username == username,
            Usuario.municipio_id == municipio_id,
            Usuario.deleted_at.is_(None),
        )
    )
    exists_user_result = await db.execute(exists_user_stmt)
    if exists_user_result.scalar_one_or_none() is not None:
        raise ValueError(f"Ya existe un usuario con el username '{username}'.")

    now = datetime.now(timezone.utc)
    usuario = Usuario(
        id=uuid.uuid4(),
        municipio_id=municipio_id,
        codigo=codigo,
        username=username,
        email=email,
        nombre_completo=nombre_completo,
        telefono=telefono,
        cargo=cargo,
        password_hash=get_password_hash(password),
        must_change_password=True,
        activo=1,
        created_at=now,
        updated_at=now,
    )
    db.add(usuario)
    await db.flush()

    if rol_id:
        rol_stmt = select(Rol).where(
            and_(Rol.id == rol_id, Rol.deleted_at.is_(None))
        )
        rol_result = await db.execute(rol_stmt)
        rol = rol_result.scalar_one_or_none()
        if rol:
            ur = UsuarioRol(usuario_id=usuario.id, rol_id=rol_id, municipio_id=municipio_id)
            db.add(ur)

    if dependencia_id:
        ud = UsuarioDependencia(
            usuario_id=usuario.id,
            dependencia_id=dependencia_id,
            municipio_id=municipio_id,
            es_principal=True,
        )
        db.add(ud)

    await db.commit()
    await db.refresh(usuario)

    return {
        "id": str(usuario.id),
        "municipio_id": str(usuario.municipio_id),
        "codigo": usuario.codigo,
        "username": usuario.username,
        "email": usuario.email,
        "nombre_completo": usuario.nombre_completo,
        "telefono": usuario.telefono,
        "cargo": usuario.cargo,
        "activo": usuario.activo,
        "must_change_password": usuario.must_change_password,
        "created_at": usuario.created_at.isoformat(),
        "updated_at": usuario.updated_at.isoformat(),
    }


async def list_usuarios(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    filtros: dict | None = None,
) -> dict:
    filtros = filtros or {}
    page = max(1, filtros.get("page", 1))
    page_size = min(100, max(1, filtros.get("page_size", 20)))
    offset = (page - 1) * page_size

    base_query = (
        select(Usuario)
        .where(
            and_(
                Usuario.municipio_id == municipio_id,
                Usuario.deleted_at.is_(None),
            )
        )
    )

    search = filtros.get("search")
    if search:
        sp = f"%{search}%"
        base_query = base_query.where(
            or_(
                Usuario.nombre_completo.ilike(sp),
                Usuario.username.ilike(sp),
                Usuario.email.ilike(sp),
                Usuario.codigo.ilike(sp),
            )
        )

    estado = filtros.get("estado")
    if estado == "ACTIVO":
        base_query = base_query.where(Usuario.activo == 1)
    elif estado == "INACTIVO":
        base_query = base_query.where(Usuario.activo == 0)

    count_stmt = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    query = base_query.order_by(Usuario.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    usuarios = result.scalars().all()

    items = []
    for u in usuarios:
        roles_stmt = (
            select(Rol.codigo, Rol.nombre)
            .join(UsuarioRol, UsuarioRol.rol_id == Rol.id)
            .where(UsuarioRol.usuario_id == u.id)
        )
        roles_result = await db.execute(roles_stmt)
        roles = [{"codigo": r[0], "nombre": r[1]} for r in roles_result.all()]

        items.append({
            "id": str(u.id),
            "municipio_id": str(u.municipio_id),
            "codigo": u.codigo,
            "username": u.username,
            "email": u.email,
            "nombre_completo": u.nombre_completo,
            "telefono": u.telefono,
            "cargo": u.cargo,
            "activo": u.activo,
            "roles": roles,
            "must_change_password": u.must_change_password,
            "mfa_activo": u.mfa_activo,
            "ultimo_acceso": u.ultimo_acceso.isoformat() if u.ultimo_acceso else None,
            "intentos_fallidos": u.intentos_fallidos,
            "created_at": u.created_at.isoformat(),
            "updated_at": u.updated_at.isoformat(),
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


async def get_usuario(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    usuario_id: uuid.UUID,
) -> dict | None:
    stmt = select(Usuario).where(
        and_(
            Usuario.id == usuario_id,
            Usuario.municipio_id == municipio_id,
            Usuario.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    u = result.scalar_one_or_none()
    if u is None:
        return None

    roles_stmt = (
        select(Rol.id, Rol.codigo, Rol.nombre)
        .join(UsuarioRol, UsuarioRol.rol_id == Rol.id)
        .where(UsuarioRol.usuario_id == u.id)
    )
    roles_result = await db.execute(roles_stmt)
    roles = [{"id": str(r[0]), "codigo": r[1], "nombre": r[2]} for r in roles_result.all()]

    return {
        "id": str(u.id),
        "municipio_id": str(u.municipio_id),
        "codigo": u.codigo,
        "username": u.username,
        "email": u.email,
        "nombre_completo": u.nombre_completo,
        "telefono": u.telefono,
        "cargo": u.cargo,
        "activo": u.activo,
        "roles": roles,
        "must_change_password": u.must_change_password,
        "mfa_activo": u.mfa_activo,
        "ultimo_acceso": u.ultimo_acceso.isoformat() if u.ultimo_acceso else None,
        "intentos_fallidos": u.intentos_fallidos,
        "created_at": u.created_at.isoformat(),
        "updated_at": u.updated_at.isoformat(),
    }


async def update_usuario(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    usuario_id: uuid.UUID,
    update_data: dict,
) -> dict | None:
    stmt = select(Usuario).where(
        and_(
            Usuario.id == usuario_id,
            Usuario.municipio_id == municipio_id,
            Usuario.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    usuario = result.scalar_one_or_none()
    if usuario is None:
        return None

    now = datetime.now(timezone.utc)

    if "email" in update_data:
        usuario.email = update_data["email"]
    if "nombre_completo" in update_data:
        usuario.nombre_completo = update_data["nombre_completo"]
    if "telefono" in update_data:
        usuario.telefono = update_data["telefono"]
    if "cargo" in update_data:
        usuario.cargo = update_data["cargo"]
    if "activo" in update_data:
        usuario.activo = update_data["activo"]
    if "must_change_password" in update_data:
        usuario.must_change_password = update_data["must_change_password"]

    if "rol_id" in update_data:
        del_stmt = select(UsuarioRol).where(UsuarioRol.usuario_id == usuario_id)
        del_result = await db.execute(del_stmt)
        for ur in del_result.scalars().all():
            await db.delete(ur)

        rol_id = update_data["rol_id"]
        if rol_id:
            rol_stmt = select(Rol).where(
                and_(Rol.id == rol_id, Rol.deleted_at.is_(None))
            )
            rol_result = await db.execute(rol_stmt)
            if rol_result.scalar_one_or_none():
                ur = UsuarioRol(usuario_id=usuario_id, rol_id=rol_id, municipio_id=municipio_id)
                db.add(ur)

    usuario.updated_at = now
    await db.commit()
    await db.refresh(usuario)

    return await get_usuario(db, municipio_id, usuario_id)


async def delete_usuario(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    usuario_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
) -> dict | None:
    stmt = select(Usuario).where(
        and_(
            Usuario.id == usuario_id,
            Usuario.municipio_id == municipio_id,
            Usuario.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    usuario = result.scalar_one_or_none()
    if usuario is None:
        return None

    now = datetime.now(timezone.utc)
    usuario.deleted_at = now
    if user_id:
        usuario.deleted_by = user_id
    usuario.updated_at = now
    await db.commit()

    return {
        "id": str(usuario.id),
        "codigo": usuario.codigo,
        "nombre": usuario.nombre_completo,
        "deleted_at": usuario.deleted_at.isoformat(),
        "message": f"Usuario {usuario.codigo} eliminado exitosamente.",
    }
