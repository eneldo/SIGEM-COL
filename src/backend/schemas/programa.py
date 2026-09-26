from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProgramaCreate(BaseModel):
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=300)
    sector: str | None = Field(None, max_length=100)
    descripcion: str | None = None
    linea_estrategica_id: UUID


class ProgramaUpdate(BaseModel):
    codigo: str | None = None
    nombre: str | None = None
    sector: str | None = None
    descripcion: str | None = None


class ProgramaResponse(BaseModel):
    id: UUID
    codigo: str
    nombre: str
    sector: str | None = None
    descripcion: str | None = None
    estado: str
    municipio_id: UUID
    linea_estrategica_id: UUID
    linea_estrategica_nombre: str | None = None
    created_at: datetime
    updated_at: datetime


class ProgramaListResponse(BaseModel):
    items: list[ProgramaResponse]
    total: int
    page: int
    page_size: int


class ProgramaFiltros(BaseModel):
    search: str | None = None
    linea_estrategica_id: UUID | None = None
    estado: str | None = None
    page: int = 1
    page_size: int = 20
