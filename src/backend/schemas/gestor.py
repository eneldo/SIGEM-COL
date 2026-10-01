"""Schemas Gestores Líderes - Pydantic models para el módulo de Gestores"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class GestorDependencia(BaseModel):
    id: UUID
    nombre: str
    es_principal: bool = False


class GestorCreate(BaseModel):
    nombre_completo: str = Field(..., min_length=3, max_length=300)
    email: EmailStr
    telefono: str | None = Field(None, max_length=20)
    cargo: str | None = Field(None, max_length=100)
    rol_id: UUID | None = None
    dependencia_principal_id: UUID | None = None
    dependencias_adicionales: list[UUID] = []
    username: str | None = Field(
        None,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9._-]+$",
        description="Usuario opcional; si se omite se autogenera.",
    )
    password: str | None = Field(
        None,
        min_length=15,
        max_length=128,
        description="Contraseña opcional; si se omite se genera una temporal.",
    )


class GestorPasswordUpdate(BaseModel):
    nueva_password: str | None = Field(
        None,
        min_length=15,
        max_length=128,
        description="Contraseña personalizada; si se omite se genera una temporal.",
    )


class GestorUpdate(BaseModel):
    nombre_completo: str | None = Field(None, min_length=3, max_length=300)
    email: EmailStr | None = None
    telefono: str | None = Field(None, max_length=20)
    cargo: str | None = Field(None, max_length=100)
    dependencia_principal_id: UUID | None = None


class GestorPermisosUpdate(BaseModel):
    rol_id: UUID | None = None
    dependencia_principal_id: UUID | None = None
    dependencias_adicionales: list[UUID] = []


class GestorResponse(BaseModel):
    id: UUID
    codigo: str
    username: str
    email: str
    telefono: str | None = None
    nombre_completo: str
    cargo: str | None = None
    rol: str | None = None
    rol_id: UUID | None = None
    roles: list[str] = []
    dependencia_principal_id: UUID | None = None
    dependencia_principal: str | None = None
    dependencias: list[GestorDependencia] = []
    estado: str
    mfa_activo: bool
    must_change_password: bool
    ultimo_acceso: datetime | None = None
    ip_ultimo_acceso: str | None = None
    intentos_fallidos: int = 0
    ultimo_cambio_password: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None


class GestorListResponse(BaseModel):
    items: list[GestorResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class GestorAccion(BaseModel):
    motivo: str | None = None


class GestorPasswordReset(BaseModel):
    nueva_password_temporal: str = Field(..., json_schema_extra={"readOnly": True})
    id: UUID | None = None
    codigo: str | None = None
    username: str | None = None


class GestorAccesoResponse(BaseModel):
    id: UUID
    exitoso: bool
    ip_address: str | None = None
    user_agent: str | None = None
    razon_fallo: str | None = None
    fecha_intento: datetime
