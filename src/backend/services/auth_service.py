"""Auth service - Authentication and authorization logic"""

import uuid
from datetime import UTC, datetime, timedelta

import pyotp
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.database import set_tenant_context
from ..core.security import (
    create_access_token,
    create_mfa_token,
    create_refresh_token,
    decode_token,
    generate_temporary_password,
    get_password_hash,
    verify_password,
)
from ..models.intento_login import IntentoLogin
from ..models.municipio import Municipio
from ..models.rol import Rol
from ..models.sesion import Sesion
from ..models.usuario import Usuario
from ..models.usuario_rol import UsuarioRol


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate_user(
        self,
        username: str,
        password: str,
        municipio_codigo: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict | None:
        # Municipality is mandatory: it scopes the login lookup under RLS.
        if not municipio_codigo:
            return None

        # municipios is a global table (no RLS), safe to query unscoped.
        result = await self.db.execute(
            select(Municipio).where(
                Municipio.codigo == municipio_codigo, Municipio.estado == "ACTIVO"
            )
        )
        municipio = result.scalar_one_or_none()
        if not municipio:
            return None

        # Scope this session to the municipality before touching any
        # RLS-protected table (usuarios, intentos_login, sesiones, ...).
        await set_tenant_context(self.db, municipio.id)

        # Get user by username + municipio
        user_result = await self.db.execute(
            select(Usuario).where(
                and_(
                    Usuario.username == username,
                    Usuario.municipio_id == municipio.id,
                    Usuario.deleted_at.is_(None),
                )
            )
        )
        user = user_result.scalar_one_or_none()

        # Record login attempt
        attempt = IntentoLogin(
            usuario_id=user.id if user else None,
            username_intentado=username,
            municipio_id=municipio.id,
            ip_address=ip_address,
            user_agent=user_agent,
            fecha_intento=datetime.now(UTC),
        )

        if not user:
            attempt.exitoso = False  # type: ignore[assignment]
            attempt.razon_fallo = "USER_NOT_FOUND"  # type: ignore[assignment]
            self.db.add(attempt)
            await self.db.commit()
            return None

        # Check if account is locked
        if user.fecha_bloqueo:
            attempt.exitoso = False  # type: ignore[assignment]
            attempt.razon_fallo = "ACCOUNT_LOCKED"  # type: ignore[assignment]
            self.db.add(attempt)
            await self.db.commit()
            return None

        # Check if account is active
        if not user.activo or user.estado == "ELIMINADO_LOGICAMENTE":
            attempt.exitoso = False  # type: ignore[assignment]
            attempt.razon_fallo = "ACCOUNT_INACTIVE"  # type: ignore[assignment]
            self.db.add(attempt)
            await self.db.commit()
            return None

        # Verify password
        if not verify_password(password, str(user.password_hash)):
            user.intentos_fallidos += 1  # type: ignore[assignment]
            user.ultimo_intento_fallido = datetime.now(UTC)  # type: ignore[assignment]

            # Lock account after max attempts
            if user.intentos_fallidos >= settings.RATE_LIMIT_LOGIN_ATTEMPTS:
                user.fecha_bloqueo = datetime.now(UTC)  # type: ignore[assignment]
                user.motivo_bloqueo = "MAX_LOGIN_ATTEMPTS"  # type: ignore[assignment]

            attempt.exitoso = False  # type: ignore[assignment]
            attempt.razon_fallo = "INVALID_PASSWORD"  # type: ignore[assignment]
            attempt.usuario_id = user.id
            self.db.add(attempt)
            await self.db.commit()
            return None

        # Successful login
        user.intentos_fallidos = 0  # type: ignore[assignment]
        user.ultimo_intento_fallido = None  # type: ignore[assignment]
        user.ultimo_acceso = datetime.now(UTC)  # type: ignore[assignment]
        user.ip_ultimo_acceso = ip_address  # type: ignore[assignment]
        user.user_agent_ultimo_acceso = user_agent  # type: ignore[assignment]

        attempt.exitoso = True  # type: ignore[assignment]
        attempt.usuario_id = user.id
        self.db.add(attempt)

        # Get user roles
        roles = await self.get_user_roles(uuid.UUID(str(user.id)))

        token_data = {
            "sub": str(user.id),
            "municipio_id": str(municipio.id),
            "username": user.username,
        }

        # Second factor required: do NOT issue session tokens yet. The client
        # must exchange the short-lived mfa_token for real tokens via /auth/mfa/login.
        if user.mfa_activo:
            await self.db.commit()
            return {
                "mfa_required": True,
                "mfa_token": create_mfa_token(token_data),
                "expires_in": 300,
                "must_change_password": user.must_change_password,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "nombre_completo": user.nombre_completo,
                    "municipio_id": municipio.id,
                    "roles": roles,
                },
            }

        return await self._issue_tokens(
            user,
            municipio.id,  # type: ignore[arg-type]
            roles,
            token_data,
            ip_address,
            user_agent,
        )

    async def _issue_tokens(
        self,
        user: Usuario,
        municipio_id: uuid.UUID,
        roles: list[str],
        token_data: dict,
        ip_address: str | None,
        user_agent: str | None,
    ) -> dict:
        """Create access/refresh tokens, persist the session and return the login payload.

        The access token carries a `sid` claim pointing to the persisted
        session, so revoking the session invalidates the token immediately.
        """
        session_id = uuid.uuid4()
        refresh_token = create_refresh_token(token_data)
        refresh_payload = decode_token(refresh_token)
        if refresh_payload is None or "jti" not in refresh_payload:
            raise ValueError("Token de refresco inválido")
        access_token = create_access_token({**token_data, "sid": str(session_id)})

        session = Sesion(
            id=session_id,
            usuario_id=user.id,
            municipio_id=municipio_id,
            token_jti=refresh_payload["jti"],
            ip_address=ip_address,
            user_agent=user_agent,
            fecha_creacion=datetime.now(UTC),
            ultima_actividad=datetime.now(UTC),
            fecha_expiracion=datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.db.add(session)

        await self.db.commit()

        return self._login_payload(user, roles, access_token, refresh_token)

    @staticmethod
    def _login_payload(
        user: Usuario,
        roles: list[str],
        access_token: str,
        refresh_token: str,
    ) -> dict:
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "must_change_password": user.must_change_password,
            "mfa_required": False,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "nombre_completo": user.nombre_completo,
                "municipio_id": user.municipio_id,
                "roles": roles,
            },
        }

    async def get_active_session(self, session_id: str) -> bool:
        """Check that the session referenced by a token's `sid` is still active."""
        try:
            sid = uuid.UUID(session_id)
        except ValueError:
            return False
        result = await self.db.execute(
            select(Sesion.id).where(
                and_(
                    Sesion.id == sid,
                    Sesion.activa == 1,
                    Sesion.fecha_expiracion > datetime.now(UTC),
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def refresh_session(
        self,
        refresh_token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict | None:
        """Validate and rotate a refresh token, keeping the same session (`sid`).

        A refresh token that was already rotated (or whose session was revoked)
        revokes every session of the user, as it signals token theft.
        """
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh" or not payload.get("jti"):
            return None

        await set_tenant_context(self.db, uuid.UUID(payload["municipio_id"]))

        result = await self.db.execute(select(Sesion).where(Sesion.token_jti == payload["jti"]))
        session = result.scalar_one_or_none()
        if session is None:
            return None

        user = await self.get_current_user(payload["sub"], payload["municipio_id"])
        if user is None:
            return None

        now = datetime.now(UTC)
        if session.activa != 1 or session.fecha_expiracion <= now:
            await self.revoke_session(uuid.UUID(str(session.id)), uuid.UUID(str(user.id)))
            return None

        roles = await self.get_user_roles(uuid.UUID(str(user.id)))
        token_data = {
            "sub": str(user.id),
            "municipio_id": payload["municipio_id"],
            "username": user.username,
        }

        # Rotate: close the current session and issue a new one under a new
        # `sid`. The old row keeps its jti so a replay can be recognized.
        session.activa = 0  # type: ignore[assignment]
        new_session_id = uuid.uuid4()
        new_refresh = create_refresh_token(token_data)
        new_payload = decode_token(new_refresh)
        if new_payload is None or "jti" not in new_payload:
            raise ValueError("Token de refresco inválido")
        new_session = Sesion(
            id=new_session_id,
            usuario_id=uuid.UUID(str(user.id)),
            municipio_id=uuid.UUID(str(session.municipio_id)),
            token_jti=new_payload["jti"],
            ip_address=ip_address or session.ip_address,
            user_agent=user_agent or session.user_agent,
            fecha_creacion=now,
            ultima_actividad=now,
            fecha_expiracion=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.db.add(new_session)

        access_token = create_access_token({**token_data, "sid": str(new_session_id)})

        await self.db.commit()

        return self._login_payload(user, roles, access_token, new_refresh)

    async def mfa_login(
        self,
        mfa_token: str,
        code: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict | None:
        """Second login step: validate the TOTP code and issue real tokens."""
        payload = decode_token(mfa_token)
        if not payload or payload.get("type") != "mfa":
            return None

        await set_tenant_context(self.db, uuid.UUID(payload["municipio_id"]))

        user = await self.get_current_user(payload["sub"], payload["municipio_id"])
        if not user or not user.mfa_activo or not user.mfa_secret:
            return None

        if not pyotp.TOTP(str(user.mfa_secret)).verify(code, valid_window=1):
            return None

        roles = await self.get_user_roles(uuid.UUID(str(user.id)))
        token_data = {
            "sub": str(user.id),
            "municipio_id": payload["municipio_id"],
            "username": user.username,
        }
        return await self._issue_tokens(
            user, uuid.UUID(str(user.municipio_id)), roles, token_data, ip_address, user_agent
        )

    # ------------------------------------------------------------------
    # MFA management (TOTP)
    # ------------------------------------------------------------------

    async def mfa_status(self, user: Usuario) -> dict:
        if user.mfa_activo:
            return {"mfa_activo": True, "pending": False}
        if user.mfa_secret:
            totp = pyotp.TOTP(str(user.mfa_secret))
            return {
                "mfa_activo": False,
                "pending": True,
                "secret": user.mfa_secret,
                "qr_code_url": totp.provisioning_uri(
                    name=str(user.username), issuer_name=settings.MFA_ISSUER
                ),
            }
        return {"mfa_activo": False, "pending": False}

    async def mfa_setup(self, user: Usuario) -> dict:
        if user.mfa_activo:
            raise ValueError("MFA ya está activo; desactívelo antes de volver a configurarlo.")
        secret = pyotp.random_base32()
        user.mfa_secret = secret  # type: ignore[assignment]
        user.mfa_activo = False  # type: ignore[assignment]
        await self.db.commit()
        totp = pyotp.TOTP(secret)
        return {
            "secret": secret,
            "qr_code_url": totp.provisioning_uri(
                name=str(user.username), issuer_name=settings.MFA_ISSUER
            ),
        }

    async def mfa_verify(self, user: Usuario, code: str) -> bool:
        if not user.mfa_secret:
            raise ValueError("No hay un secreto MFA pendiente; ejecute setup primero.")
        if not pyotp.TOTP(str(user.mfa_secret)).verify(code, valid_window=1):
            return False
        user.mfa_activo = True  # type: ignore[assignment]
        await self.db.commit()
        return True

    async def mfa_disable(self, user: Usuario, password: str, code: str) -> bool:
        if not user.mfa_activo or not user.mfa_secret:
            raise ValueError("MFA no está activo en esta cuenta.")
        if not verify_password(password, str(user.password_hash)):
            return False
        if not pyotp.TOTP(str(user.mfa_secret)).verify(code, valid_window=1):
            return False
        user.mfa_activo = False  # type: ignore[assignment]
        user.mfa_secret = None  # type: ignore[assignment]
        await self.db.commit()
        return True

    async def get_current_user(self, user_id: str, municipio_id: str) -> Usuario | None:
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

        if not verify_password(current_password, user.password_hash):  # type: ignore[arg-type]
            return False

        user.password_hash = get_password_hash(new_password)  # type: ignore[assignment]
        user.must_change_password = False  # type: ignore[assignment]
        user.ultimo_cambio_password = datetime.now(UTC)  # type: ignore[assignment]
        await self.db.commit()
        return True

    async def generate_temp_password(self) -> str:
        return generate_temporary_password(24)

    async def revoke_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(Sesion).where(and_(Sesion.id == session_id, Sesion.usuario_id == user_id))
        )
        session = result.scalar_one_or_none()
        if not session:
            return False
        session.activa = 0  # type: ignore[assignment]
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
