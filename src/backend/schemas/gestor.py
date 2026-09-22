"""Schemas Gestores Líderes - Pydantic models para el módulo de Gestores"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class GestorDependencia(BaseModel):
    id: UUID
    nombre: str
    es_principal: bool = False


class GestorCreate(BaseModel):
    nombre_completo: str = Field(..., min_length=3, max_length=300)
    email: EmailStr
    telefono: Optional[str] = Field(None, max_length=20)
    cargo: Optional[str] = Field(None, max_length=100)
    rol_id: Optional[UUID] = None
    dependencia_principal_id: Optional[UUID] = None
    dependencias_adicionales: List[UUID] = []


class GestorUpdate(BaseModel):
    nombre_completo: Optional[str] = Field(None, min_length=3, max_length=300)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)
    cargo: Optional[str] = Field(None, max_length=100)
    dependencia_principal_id: Optional[UUID] = None


class GestorPermisosUpdate(BaseModel):
    rol_id: Optional[UUID] = None
    dependencia_principal_id: Optional[UUID] = None
    dependencias_adicionales: List[UUID] = []


class GestorResponse(BaseModel):
    id: UUID
    codigo: str
    username: str
    email: str
    telefono: Optional[str] = None
    nombre_completo: str
    cargo: Optional[str] = None
    rol: Optional[str] = None
    rol_id: Optional[UUID] = None
    roles: List[str] = []
    dependencia_principal_id: Optional[UUID] = None
    dependencia_principal: Optional[str] = None
    dependencias: List[GestorDependencia] = []
    estado: str
    mfa_activo: bool
    must_change_password: bool
    ultimo_acceso: Optional[datetime] = None
    ip_ultimo_acceso: Optional[str] = None
    intentos_fallidos: int = 0
    ultimo_cambio_password: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class GestorListResponse(BaseModel):
    items: List[GestorResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class GestorAccion(BaseModel):
    motivo: Optional[str] = None


class GestorPasswordReset(BaseModel):
    nueva_password_temporal: str = Field(..., read_only=True)
    id: Optional[UUID] = None
    codigo: Optional[str] = None
    username: Optional[str] = None


class GestorAccesoResponse(BaseModel):
    id: UUID
    exitoso: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    razon_fallo: Optional[str] = None
    fecha_intento: datetime
