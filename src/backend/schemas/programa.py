from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class ProgramaCreate(BaseModel):
    codigo: str = Field(..., max_length=20)
    nombre: str = Field(..., max_length=300)
    sector: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = None
    linea_estrategica_id: UUID


class ProgramaUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    sector: Optional[str] = None
    descripcion: Optional[str] = None


class ProgramaResponse(BaseModel):
    id: UUID
    codigo: str
    nombre: str
    sector: Optional[str] = None
    descripcion: Optional[str] = None
    estado: str
    municipio_id: UUID
    linea_estrategica_id: UUID
    linea_estrategica_nombre: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProgramaListResponse(BaseModel):
    items: List[ProgramaResponse]
    total: int
    page: int
    page_size: int


class ProgramaFiltros(BaseModel):
    search: Optional[str] = None
    linea_estrategica_id: Optional[UUID] = None
    estado: Optional[str] = None
    page: int = 1
    page_size: int = 20
