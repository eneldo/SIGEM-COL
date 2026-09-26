from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProductoCreate(BaseModel):
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=300)
    codigo_indicador: str | None = Field(None, max_length=30)
    indicador: str | None = Field(None, max_length=300)
    meta_redactada: str | None = None
    linea_base: int | None = 0
    meta_cuatrienio: int | None = 0
    descripcion: str | None = None
    unidad_medida: str | None = None
    programa_id: UUID
    dependencia_responsable_id: UUID | None = None
    gestor_lider_id: UUID | None = None


class ProductoUpdate(BaseModel):
    codigo: str | None = None
    nombre: str | None = None
    codigo_indicador: str | None = None
    indicador: str | None = None
    meta_redactada: str | None = None
    linea_base: int | None = None
    meta_cuatrienio: int | None = None
    descripcion: str | None = None
    unidad_medida: str | None = None
    dependencia_responsable_id: UUID | None = None
    gestor_lider_id: UUID | None = None


class ProductoResponse(BaseModel):
    id: UUID
    codigo: str
    nombre: str
    codigo_indicador: str | None = None
    indicador: str | None = None
    meta_redactada: str | None = None
    linea_base: int | None = 0
    meta_cuatrienio: int | None = 0
    descripcion: str | None = None
    unidad_medida: str | None = None
    estado: str
    municipio_id: UUID
    programa_id: UUID
    programa_nombre: str | None = None
    dependencia_responsable_id: UUID | None = None
    dependencia_nombre: str | None = None
    gestor_lider_id: UUID | None = None
    gestor_nombre: str | None = None
    asignado_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ProductoListResponse(BaseModel):
    items: list[ProductoResponse]
    total: int
    page: int
    page_size: int


class ProductoFiltros(BaseModel):
    search: str | None = None
    programa_id: UUID | None = None
    dependencia_id: UUID | None = None
    gestor_id: UUID | None = None
    estado: str | None = None
    page: int = 1
    page_size: int = 20
