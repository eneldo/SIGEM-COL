"""RBAC utilities - Role-Based Access Control"""
from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.usuario_rol import UsuarioRol, RolPermiso
from ..models.rol import Permiso


def _normalize_permission(perm: str) -> str:
    """Normalize permission code to UPPER_CASE with underscores."""
    return perm.upper().replace(".", "_")


async def get_user_permissions(db: AsyncSession, user_id: UUID) -> list[str]:
    """Get all permission codes for a user across all their roles."""
    result = await db.execute(
        select(Permiso.codigo)
        .join(RolPermiso, RolPermiso.permiso_id == Permiso.id)
        .join(UsuarioRol, UsuarioRol.rol_id == RolPermiso.rol_id)
        .where(UsuarioRol.usuario_id == user_id)
    )
    return list(result.scalars().all())


async def get_user_role_codes(db: AsyncSession, user_id: UUID) -> list[str]:
    """Get all role codes for a user."""
    from ..models.rol import Rol
    result = await db.execute(
        select(Rol.codigo)
        .join(UsuarioRol, UsuarioRol.rol_id == Rol.id)
        .where(UsuarioRol.usuario_id == user_id)
    )
    return list(result.scalars().all())


async def check_permission(
    db: AsyncSession,
    user_id: UUID,
    required_permission: str,
) -> bool:
    """Check if a user has a specific permission."""
    role_codes = await get_user_role_codes(db, user_id)
    if "ADMINISTRADOR_MUNICIPAL" in role_codes or "SUPERADMIN_PLATAFORMA" in role_codes:
        return True

    permissions = await get_user_permissions(db, user_id)
    normalized_required = _normalize_permission(required_permission)
    normalized_user_perms = {_normalize_permission(p) for p in permissions}
    return normalized_required in normalized_user_perms


async def require_permission(
    db: AsyncSession,
    user_id: UUID,
    required_permission: str,
) -> None:
    """Raise 403 if user lacks the required permission."""
    has_perm = await check_permission(db, user_id, required_permission)
    if not has_perm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permiso requerido: {required_permission}",
        )
