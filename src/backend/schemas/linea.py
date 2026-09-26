from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LineaCreate(BaseModel):
    codigo: str | None = Field(None, max_length=20)
    numero: str | None = Field(None, max_length=20)
    nombre: str = Field(..., max_length=300)
    descripcion: str | None = None
    orden: int = 0
    plan_desarrollo_id: UUID


class LineaUpdate(BaseModel):
    codigo: str | None = None
    numero: str | None = None
    nombre: str | None = None
    descripcion: str | None = None
    orden: int | None = None


class LineaResponse(BaseModel):
    id: UUID
    codigo: str
    numero: str | None = None
    nombre: str
    descripcion: str | None = None
    orden: int
    estado: str
    municipio_id: UUID
    plan_desarrollo_id: UUID
    plan_desarrollo_nombre: str | None = None
    created_at: datetime
    updated_at: datetime


class LineaListResponse(BaseModel):
    items: list[LineaResponse]
    total: int
    page: int
    page_size: int


class LineaFiltros(BaseModel):
    search: str | None = None
    plan_desarrollo_id: UUID | None = None
    estado: str | None = None
    page: int = 1
    page_size: int = 20
