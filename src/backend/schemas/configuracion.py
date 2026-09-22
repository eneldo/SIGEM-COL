"""Schemas Configuración - Pydantic models para el módulo de Configuración"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# --- Usuarios ---

class UsuarioCreate(BaseModel):
    codigo: str = Field(..., max_length=20)
    username: str = Field(..., max_length=100)
    email: EmailStr
    nombre_completo: str = Field(..., min_length=3, max_length=300)
    telefono: Optional[str] = Field(None, max_length=20)
    cargo: Optional[str] = Field(None, max_length=100)
    password: str = Field(..., min_length=8)
    rol_id: Optional[UUID] = None
    dependencia_id: Optional[UUID] = None


class UsuarioUpdate(BaseModel):
    email: Optional[EmailStr] = None
    nombre_completo: Optional[str] = Field(None, min_length=3, max_length=300)
    telefono: Optional[str] = Field(None, max_length=20)
    cargo: Optional[str] = Field(None, max_length=100)
    activo: Optional[int] = None
    must_change_password: Optional[bool] = None
    rol_id: Optional[UUID] = None


class UsuarioRolInfo(BaseModel):
    id: Optional[str] = None
    codigo: str
    nombre: str


class UsuarioResponse(BaseModel):
    id: str
    municipio_id: str
    codigo: str
    username: str
    email: str
    nombre_completo: str
    telefono: Optional[str] = None
    cargo: Optional[str] = None
    activo: int
    roles: List[UsuarioRolInfo] = []
    must_change_password: bool
    mfa_activo: bool = False
    ultimo_acceso: Optional[str] = None
    intentos_fallidos: int = 0
    created_at: str
    updated_at: str


class UsuarioListResponse(BaseModel):
    items: List[UsuarioResponse]
    total: int
    page: int
    page_size: int


# --- Roles ---

class PermisoInfo(BaseModel):
    id: str
    codigo: str
    nombre: str
    modulo: str
    accion: str


class RolCreate(BaseModel):
    codigo: str = Field(..., max_length=50)
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = Field(None, max_length=300)
    nivel: int = 1
    permisos_ids: List[UUID] = []


class RolUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=300)
    nivel: Optional[int] = None
    estado: Optional[str] = None
    permisos_ids: Optional[List[UUID]] = None


class RolResponse(BaseModel):
    id: str
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    nivel: int
    estado: str
    permisos: List[PermisoInfo] = []
    created_at: str
    updated_at: str


class RolListResponse(BaseModel):
    items: List[RolResponse]
    total: int
    page: int
    page_size: int


# --- Permisos ---

class PermisoResponse(BaseModel):
    id: str
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    modulo: str
    accion: str
    estado: str


class PermisoListResponse(BaseModel):
    items: List[PermisoResponse]
    total: int


# --- Auditoría ---

class AuditoriaEventoResponse(BaseModel):
    id: str
    evento_tipo: str
    recurso_tipo: Optional[str] = None
    recurso_id: Optional[str] = None
    resultado: str
    ip_address: Optional[str] = None
    actor_nombre: Optional[str] = None
    actor_id: Optional[str] = None
    metadata_json: Optional[str] = None
    fecha_evento: str


class AuditoriaListResponse(BaseModel):
    items: List[AuditoriaEventoResponse]
    total: int
    page: int
    page_size: int


class AuditoriaFiltros(BaseModel):
    evento_tipo: Optional[str] = None
    recurso_tipo: Optional[str] = None
    resultado: Optional[str] = None
    usuario_id: Optional[str] = None
    fecha_desde: Optional[str] = None
    fecha_hasta: Optional[str] = None
    page: int = 1
    page_size: int = 20


class AuditoriaStats(BaseModel):
    total_eventos: int
    exitosos: int
    fallidos: int
    hoy: int
    por_tipo: dict = {}
