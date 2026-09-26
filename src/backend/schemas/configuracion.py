"""Schemas Configuración - Pydantic models para el módulo de Configuración"""
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

# --- Usuarios ---

class UsuarioCreate(BaseModel):
    codigo: str = Field(..., max_length=20)
    username: str = Field(..., max_length=100)
    email: EmailStr
    nombre_completo: str = Field(..., min_length=3, max_length=300)
    telefono: str | None = Field(None, max_length=20)
    cargo: str | None = Field(None, max_length=100)
    password: str = Field(..., min_length=8)
    rol_id: UUID | None = None
    dependencia_id: UUID | None = None


class UsuarioUpdate(BaseModel):
    email: EmailStr | None = None
    nombre_completo: str | None = Field(None, min_length=3, max_length=300)
    telefono: str | None = Field(None, max_length=20)
    cargo: str | None = Field(None, max_length=100)
    activo: int | None = None
    must_change_password: bool | None = None
    rol_id: UUID | None = None


class UsuarioRolInfo(BaseModel):
    id: str | None = None
    codigo: str
    nombre: str


class UsuarioResponse(BaseModel):
    id: str
    municipio_id: str
    codigo: str
    username: str
    email: str
    nombre_completo: str
    telefono: str | None = None
    cargo: str | None = None
    activo: int
    roles: list[UsuarioRolInfo] = []
    must_change_password: bool
    mfa_activo: bool = False
    ultimo_acceso: str | None = None
    intentos_fallidos: int = 0
    created_at: str
    updated_at: str


class UsuarioListResponse(BaseModel):
    items: list[UsuarioResponse]
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
    descripcion: str | None = Field(None, max_length=300)
    nivel: int = 1
    permisos_ids: list[UUID] = []


class RolUpdate(BaseModel):
    nombre: str | None = Field(None, max_length=100)
    descripcion: str | None = Field(None, max_length=300)
    nivel: int | None = None
    estado: str | None = None
    permisos_ids: list[UUID] | None = None


class RolResponse(BaseModel):
    id: str
    codigo: str
    nombre: str
    descripcion: str | None = None
    nivel: int
    estado: str
    permisos: list[PermisoInfo] = []
    created_at: str
    updated_at: str


class RolListResponse(BaseModel):
    items: list[RolResponse]
    total: int
    page: int
    page_size: int


# --- Permisos ---

class PermisoResponse(BaseModel):
    id: str
    codigo: str
    nombre: str
    descripcion: str | None = None
    modulo: str
    accion: str
    estado: str


class PermisoListResponse(BaseModel):
    items: list[PermisoResponse]
    total: int


# --- Auditoría ---

class AuditoriaEventoResponse(BaseModel):
    id: str
    evento_tipo: str
    recurso_tipo: str | None = None
    recurso_id: str | None = None
    resultado: str
    ip_address: str | None = None
    actor_nombre: str | None = None
    actor_id: str | None = None
    metadata_json: str | None = None
    fecha_evento: str


class AuditoriaListResponse(BaseModel):
    items: list[AuditoriaEventoResponse]
    total: int
    page: int
    page_size: int


class AuditoriaFiltros(BaseModel):
    evento_tipo: str | None = None
    recurso_tipo: str | None = None
    resultado: str | None = None
    usuario_id: str | None = None
    fecha_desde: str | None = None
    fecha_hasta: str | None = None
    page: int = 1
    page_size: int = 20


class AuditoriaStats(BaseModel):
    total_eventos: int
    exitosos: int
    fallidos: int
    hoy: int
    por_tipo: dict = {}
