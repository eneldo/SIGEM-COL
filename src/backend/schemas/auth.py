"""Auth schemas - Pydantic schemas for authentication"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=1, max_length=128)
    municipio_codigo: Optional[str] = Field(None, max_length=10)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    must_change_password: bool
    mfa_required: bool


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=15, max_length=128)
    confirm_password: str = Field(..., min_length=1)


class MFASetupResponse(BaseModel):
    secret: str
    qr_code_url: str
    backup_codes: list[str]


class MFAVerifyRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)
    factor_id: Optional[UUID] = None


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    nombre_completo: str
    municipio_id: UUID
    must_change_password: bool
    mfa_activo: bool
    roles: list[str] = []

    class Config:
        from_attributes = True


class TokenPayload(BaseModel):
    sub: str
    municipio_id: str
    username: str
    type: str
    exp: int
    jti: str
