from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class LineaCreate(BaseModel):
    codigo: Optional[str] = Field(None, max_length=20)
    numero: Optional[str] = Field(None, max_length=20)
    nombre: str = Field(..., max_length=300)
    descripcion: Optional[str] = None
    orden: int = 0
    plan_desarrollo_id: UUID


class LineaUpdate(BaseModel):
    codigo: Optional[str] = None
    numero: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    orden: Optional[int] = None


class LineaResponse(BaseModel):
    id: UUID
    codigo: str
    numero: Optional[str] = None
    nombre: str
    descripcion: Optional[str] = None
    orden: int
    estado: str
    municipio_id: UUID
    plan_desarrollo_id: UUID
    plan_desarrollo_nombre: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class LineaListResponse(BaseModel):
    items: List[LineaResponse]
    total: int
    page: int
    page_size: int


class LineaFiltros(BaseModel):
    search: Optional[str] = None
    plan_desarrollo_id: Optional[UUID] = None
    estado: Optional[str] = None
    page: int = 1
    page_size: int = 20
