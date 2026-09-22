"""Auth service - Authentication and authorization logic"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.usuario import Usuario
from ..models.rol import Rol
from ..models.usuario_rol import UsuarioRol
from ..models.sesion import Sesion
from ..models.intento_login import IntentoLogin
from ..models.municipio import Municipio
from ..core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_temporary_password,
)
from ..core.config import settings


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate_user(
        self, username: str, password: str, municipio_codigo: str = None, ip_address: str = None, user_agent: str = None
    ) -> Optional[dict]:
        # Get municipality
        if municipio_codigo:
            result = await self.db.execute(
                select(Municipio).where(Municipio.codigo == municipio_codigo, Municipio.estado == "ACTIVO")
            )
            municipio = result.scalar_one_or_none()
            if not municipio:
                return None

            # Get user by username + municipio
            result = await self.db.execute(
                select(Usuario).where(
                    and_(
                        Usuario.username == username,
                        Usuario.municipio_id == municipio.id,
                        Usuario.deleted_at.is_(None),
                    )
                )
            )
            user = result.scalar_one_or_none()
        else:
            # No municipio specified: find user by username only
            result = await self.db.execute(
                select(Usuario).where(
                    and_(
                        Usuario.username == username,
                        Usuario.deleted_at.is_(None),
                    )
                )
            )
            user = result.scalar_one_or_none()
            if not user:
                return None
            # Get the user's municipality
            result = await self.db.execute(
                select(Municipio).where(Municipio.id == user.municipio_id)
            )
            municipio = result.scalar_one_or_none()

        # Record login attempt
        attempt = IntentoLogin(
            usuario_id=user.id if user else None,
            username_intentado=username,
            municipio_id=municipio.id,
            ip_address=ip_address,
            user_agent=user_agent,
            fecha_intento=datetime.now(timezone.utc),
        )

        if not user:
            attempt.exitoso = False
            attempt.razon_fallo = "USER_NOT_FOUND"
            self.db.add(attempt)
            await self.db.commit()
            return None

        # Check if account is locked
        if user.fecha_bloqueo:
            attempt.exitoso = False
            attempt.razon_fallo = "ACCOUNT_LOCKED"
            self.db.add(attempt)
            await self.db.commit()
            return None

        # Check if account is active
        if not user.activo or user.estado == "ELIMINADO_LOGICAMENTE":
            attempt.exitoso = False
            attempt.razon_fallo = "ACCOUNT_INACTIVE"
            self.db.add(attempt)
            await self.db.commit()
            return None

        # Verify password
        if not verify_password(password, user.password_hash):
            user.intentos_fallidos += 1
            user.ultimo_intento_fallido = datetime.now(timezone.utc)

            # Lock account after max attempts
            if user.intentos_fallidos >= settings.RATE_LIMIT_LOGIN_ATTEMPTS:
                user.fecha_bloqueo = datetime.now(timezone.utc)
                user.motivo_bloqueo = "MAX_LOGIN_ATTEMPTS"

            attempt.exitoso = False
            attempt.razon_fallo = "INVALID_PASSWORD"
            attempt.usuario_id = user.id
            self.db.add(attempt)
            await self.db.commit()
            return None

        # Successful login
        user.intentos_fallidos = 0
        user.ultimo_intento_fallido = None
        user.ultimo_acceso = datetime.now(timezone.utc)
        user.ip_ultimo_acceso = ip_address
        user.user_agent_ultimo_acceso = user_agent

        attempt.exitoso = True
        attempt.usuario_id = user.id
        self.db.add(attempt)

        # Get user roles
        result = await self.db.execute(
            select(Rol.codigo)
            .join(UsuarioRol, UsuarioRol.rol_id == Rol.id)
            .where(UsuarioRol.usuario_id == user.id)
        )
        roles = [row[0] for row in result.all()]

        # Create tokens
        token_data = {
            "sub": str(user.id),
            "municipio_id": str(municipio.id),
            "username": user.username,
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        # Create session
        refresh_payload = decode_token(refresh_token)
        session = Sesion(
            usuario_id=user.id,
            municipio_id=municipio.id,
            token_jti=refresh_payload["jti"],
            ip_address=ip_address,
            user_agent=user_agent,
            fecha_creacion=datetime.now(timezone.utc),
            ultima_actividad=datetime.now(timezone.utc),
            fecha_expiracion=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.db.add(session)

        await self.db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "must_change_password": user.must_change_password,
            "mfa_required": user.mfa_activo,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "nombre_completo": user.nombre_completo,
                "municipio_id": municipio.id,
                "roles": roles,
            },
        }

    async def get_current_user(self, user_id: str, municipio_id: str) -> Optional[Usuario]:
        result = await self.db.execute(
            select(Usuario).where(
                and_(
                    Usuario.id == uuid.UUID(user_id),
                    Usuario.municipio_id == uuid.UUID(municipio_id),
                    Usuario.deleted_at.is_(None),
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_user_roles(self, user_id: uuid.UUID) -> list[str]:
        result = await self.db.execute(
            select(Rol.codigo)
            .join(UsuarioRol, UsuarioRol.rol_id == Rol.id)
            .where(UsuarioRol.usuario_id == user_id)
        )
        return list(result.scalars().all())

    async def get_user_permissions(self, user_id: uuid.UUID) -> list[str]:
        from ..models.rol import Permiso
        from ..models.usuario_rol import RolPermiso
        result = await self.db.execute(
            select(Permiso.codigo)
            .join(RolPermiso, RolPermiso.permiso_id == Permiso.id)
            .join(UsuarioRol, UsuarioRol.rol_id == RolPermiso.rol_id)
            .where(UsuarioRol.usuario_id == user_id)
        )
        return list(result.scalars().all())

    async def change_password(
        self, user_id: str, municipio_id: str, current_password: str, new_password: str
    ) -> bool:
        user = await self.get_current_user(user_id, municipio_id)
        if not user:
            return False

        if not verify_password(current_password, user.password_hash):
            return False

        user.password_hash = get_password_hash(new_password)
        user.must_change_password = False
        user.ultimo_cambio_password = datetime.now(timezone.utc)
        await self.db.commit()
        return True

    async def generate_temp_password(self) -> str:
        return generate_temporary_password(24)

    async def revoke_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(Sesion).where(
                and_(Sesion.id == session_id, Sesion.usuario_id == user_id)
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            return False
        session.activa = 0
        await self.db.commit()
        return True

    async def revoke_all_sessions(self, user_id: uuid.UUID) -> int:
        result = await self.db.execute(
            update(Sesion)
            .where(and_(Sesion.usuario_id == user_id, Sesion.activa == 1))
            .values(activa=0)
        )
        await self.db.commit()
        return result.rowcount
