"""Auth routes - Authentication endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db, get_db_with_rls
from ...core.security import decode_token
from ...services.auth_service import AuthService
from ...services.audit_service import AuditService
from ...schemas.auth import (
    LoginRequest,
    TokenResponse,
    ChangePasswordRequest,
    UserResponse,
)

router = APIRouter()


async def get_current_user_from_token(
    request: Request, db: AsyncSession = Depends(get_db_with_rls)
):
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
    user = await auth_service.get_current_user(
        payload["sub"], payload["municipio_id"]
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )

    roles = await auth_service.get_user_roles(user.id)
    permissions = await auth_service.get_user_permissions(user.id)
    return {
        "user": user,
        "municipio_id": payload["municipio_id"],
        "roles": roles,
        "permissions": permissions,
    }


@router.post("/login", response_model=dict)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    auth_service = AuthService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent", "")

    result = await auth_service.authenticate_user(
        username=login_data.username,
        password=login_data.password,
        municipio_codigo=login_data.municipio_codigo,
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
    current_user=Depends(get_current_user_from_token),
):
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
    current_user=Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
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


@router.post("/logout")
async def logout(
    current_user=Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user = current_user["user"]

    auth_service = AuthService(db)
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
