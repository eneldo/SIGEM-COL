from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class ProductoCreate(BaseModel):
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=300)
    codigo_indicador: Optional[str] = Field(None, max_length=30)
    indicador: Optional[str] = Field(None, max_length=300)
    meta_redactada: Optional[str] = None
    linea_base: Optional[int] = 0
    meta_cuatrienio: Optional[int] = 0
    descripcion: Optional[str] = None
    unidad_medida: Optional[str] = None
    programa_id: UUID
    dependencia_responsable_id: Optional[UUID] = None
    gestor_lider_id: Optional[UUID] = None


class ProductoUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    codigo_indicador: Optional[str] = None
    indicador: Optional[str] = None
    meta_redactada: Optional[str] = None
    linea_base: Optional[int] = None
    meta_cuatrienio: Optional[int] = None
    descripcion: Optional[str] = None
    unidad_medida: Optional[str] = None
    dependencia_responsable_id: Optional[UUID] = None
    gestor_lider_id: Optional[UUID] = None


class ProductoResponse(BaseModel):
    id: UUID
    codigo: str
    nombre: str
    codigo_indicador: Optional[str] = None
    indicador: Optional[str] = None
    meta_redactada: Optional[str] = None
    linea_base: Optional[int] = 0
    meta_cuatrienio: Optional[int] = 0
    descripcion: Optional[str] = None
    unidad_medida: Optional[str] = None
    estado: str
    municipio_id: UUID
    programa_id: UUID
    programa_nombre: Optional[str] = None
    dependencia_responsable_id: Optional[UUID] = None
    dependencia_nombre: Optional[str] = None
    gestor_lider_id: Optional[UUID] = None
    gestor_nombre: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProductoListResponse(BaseModel):
    items: List[ProductoResponse]
    total: int
    page: int
    page_size: int


class ProductoFiltros(BaseModel):
    search: Optional[str] = None
    programa_id: Optional[UUID] = None
    dependencia_id: Optional[UUID] = None
    gestor_id: Optional[UUID] = None
    estado: Optional[str] = None
    page: int = 1
    page_size: int = 20
