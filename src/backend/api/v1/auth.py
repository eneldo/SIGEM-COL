"""Auth routes - Authentication endpoints"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db, get_db_with_rls
from ...core.security import decode_token
from ...schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    MFADisableRequest,
    MFALoginRequest,
    MFASetupResponse,
    MFAStatusResponse,
    MFAVerifyRequest,
    RefreshTokenRequest,
    UserResponse,
)
from ...services.audit_service import AuditService
from ...services.auth_service import AuthService

router = APIRouter()

# Rutas del flujo MFA (el suffix-match exige la ruta completa, no un prefijo).
MFA_SUFFIXES = (
    "/auth/mfa/status",
    "/auth/mfa/setup",
    "/auth/mfa/verify",
    "/auth/mfa/login",
    "/auth/mfa/disable",
)

# Endpoints a los que un usuario con must_change_password=True todavía puede acceder.
PASSWORD_CHANGE_ALLOWED_SUFFIXES = (
    "/auth/login",
    "/auth/change-password",
    "/auth/logout",
    "/auth/me",
    "/auth/refresh",
    *MFA_SUFFIXES,
)

# Endpoints a los que un usuario obligado a activar MFA todavía puede acceder:
# mismo conjunto que el cambio de contraseña, para que un usuario recién creado
# complete ambos pasos (password y MFA) sin quedarse sin salida.
MFA_ALLOWED_SUFFIXES = PASSWORD_CHANGE_ALLOWED_SUFFIXES

# Roles que deben operar con MFA activo. SUPERADMIN_PLATAFORMA queda exento:
# es la cuenta de plataforma de arranque y el estado dev documentado trabaja
# sin MFA (ver context/decisions.md).
MFA_ENFORCED_ROLES = ("ADMINISTRADOR_MUNICIPAL",)


async def get_current_user_from_token(
    request: Request, db: AsyncSession = Depends(get_db_with_rls)
) -> dict[str, Any]:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación requerido",
        )

    token = auth_header.split(" ")[1]
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )

    auth_service = AuthService(db)

    # A revoked or expired session invalidates its access token immediately,
    # even when the JWT itself is still signature-valid.
    sid = payload.get("sid")
    if sid is not None and not await auth_service.get_active_session(sid):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión revocada o expirada",
        )

    user = await auth_service.get_current_user(payload["sub"], payload["municipio_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )

    roles = await auth_service.get_user_roles(user.id)  # type: ignore[arg-type]

    # Server-side enforcement of the mandatory password change: while the flag
    # is set, only the password-change flow itself is reachable.
    if user.must_change_password and not any(
        request.url.path.endswith(suffix) for suffix in PASSWORD_CHANGE_ALLOWED_SUFFIXES
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="PASSWORD_CHANGE_REQUIRED",
        )

    # Enforcement de MFA obligatorio (espejo del cambio de contraseña): hasta
    # que activa MFA solo el flujo MFA (y /auth/me, logout) queda alcanzable.
    if (
        not user.mfa_activo
        and any(role in MFA_ENFORCED_ROLES for role in roles)
        and not any(request.url.path.endswith(suffix) for suffix in MFA_ALLOWED_SUFFIXES)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MFA_SETUP_REQUIRED",
        )

    permissions = await auth_service.get_user_permissions(user.id)  # type: ignore[arg-type]
    return {
        "user": user,
        "municipio_id": payload["municipio_id"],
        "roles": roles,
        "permissions": permissions,
        "sid": payload.get("sid"),
    }


@router.post("/login", response_model=dict)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    auth_service = AuthService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent", "")

    # Usar un municipio por defecto (ej. '00000') para compatibilidad
    result = await auth_service.authenticate_user(
        username=login_data.username,
        password=login_data.password,
        municipio_codigo="00000",
        ip_address=ip_address,
        user_agent=user_agent,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    # Log successful login
    audit_service = AuditService(db)
    await audit_service.log_event(
        evento_tipo="LOGIN_OK",
        resultado="EXITOSO",
        municipio_id=result["user"]["municipio_id"],
        usuario_id=result["user"]["id"],
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return result


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: dict[str, Any] = Depends(get_current_user_from_token),
) -> UserResponse:
    user = current_user["user"]
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        nombre_completo=user.nombre_completo,
        municipio_id=user.municipio_id,
        must_change_password=user.must_change_password,
        mfa_activo=user.mfa_activo,
        roles=current_user["roles"],
    )


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: dict[str, Any] = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    user = current_user["user"]
    municipio_id = current_user["municipio_id"]

    if data.new_password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Las contraseñas no coinciden",
        )

    auth_service = AuthService(db)
    success = await auth_service.change_password(
        user_id=str(user.id),
        municipio_id=municipio_id,
        current_password=data.current_password,
        new_password=data.new_password,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta",
        )

    # Log password change
    audit_service = AuditService(db)
    await audit_service.log_event(
        evento_tipo="PASSWORD_CHANGED",
        resultado="EXITOSO",
        municipio_id=user.municipio_id,
        usuario_id=user.id,
    )

    return {"message": "Contraseña cambiada exitosamente"}


@router.get("/mfa/status", response_model=MFAStatusResponse)
async def mfa_status(
    current_user: dict[str, Any] = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
) -> MFAStatusResponse:
    auth_service = AuthService(db)
    return MFAStatusResponse(**await auth_service.mfa_status(current_user["user"]))


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def mfa_setup(
    current_user: dict[str, Any] = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
) -> MFASetupResponse:
    auth_service = AuthService(db)
    try:
        result = await auth_service.mfa_setup(current_user["user"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e

    audit_service = AuditService(db)
    await audit_service.log_event(
        evento_tipo="MFA_SETUP",
        resultado="EXITOSO",
        municipio_id=current_user["user"].municipio_id,
        usuario_id=current_user["user"].id,
    )
    return MFASetupResponse(**result)


@router.post("/mfa/verify")
async def mfa_verify(
    data: MFAVerifyRequest,
    current_user: dict[str, Any] = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    auth_service = AuthService(db)
    try:
        ok = await auth_service.mfa_verify(current_user["user"], data.code)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    if not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código MFA inválido.",
        )

    audit_service = AuditService(db)
    await audit_service.log_event(
        evento_tipo="MFA_ENABLED",
        resultado="EXITOSO",
        municipio_id=current_user["user"].municipio_id,
        usuario_id=current_user["user"].id,
    )
    return {"message": "MFA activado exitosamente", "mfa_activo": True}


@router.post("/mfa/login", response_model=dict)
async def mfa_login(
    data: MFALoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    auth_service = AuthService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent", "")

    result = await auth_service.mfa_login(
        mfa_token=data.mfa_token,
        code=data.code,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código MFA inválido o token expirado.",
        )

    audit_service = AuditService(db)
    await audit_service.log_event(
        evento_tipo="LOGIN_OK_MFA",
        resultado="EXITOSO",
        municipio_id=result["user"]["municipio_id"],
        usuario_id=result["user"]["id"],
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return result


@router.post("/mfa/disable")
async def mfa_disable(
    data: MFADisableRequest,
    current_user: dict[str, Any] = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    auth_service = AuthService(db)
    try:
        ok = await auth_service.mfa_disable(current_user["user"], data.password, data.code)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    if not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña o código MFA inválido.",
        )

    audit_service = AuditService(db)
    await audit_service.log_event(
        evento_tipo="MFA_DISABLED",
        resultado="EXITOSO",
        municipio_id=current_user["user"].municipio_id,
        usuario_id=current_user["user"].id,
    )
    return {"message": "MFA desactivado exitosamente", "mfa_activo": False}


@router.post("/refresh")
async def refresh_tokens(
    data: RefreshTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    auth_service = AuthService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent", "")

    result = await auth_service.refresh_session(data.refresh_token, ip_address, user_agent)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado.",
        )

    audit_service = AuditService(db)
    await audit_service.log_event(
        evento_tipo="TOKEN_REFRESH",
        resultado="EXITOSO",
        municipio_id=result["user"]["municipio_id"],
        usuario_id=result["user"]["id"],
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return result


@router.post("/logout")
async def logout(
    current_user: dict[str, Any] = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    user = current_user["user"]
    sid = current_user.get("sid")

    auth_service = AuthService(db)
    if sid:
        await auth_service.revoke_session(uuid.UUID(sid), user.id)
    else:
        await auth_service.revoke_all_sessions(user.id)

    # Log logout
    audit_service = AuditService(db)
    await audit_service.log_event(
        evento_tipo="LOGOUT",
        resultado="EXITOSO",
        municipio_id=user.municipio_id,
        usuario_id=user.id,
    )

    return {"message": "Sesión cerrada exitosamente"}
