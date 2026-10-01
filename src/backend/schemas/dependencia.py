"""
Schemas Pydantic para el módulo de Dependencias CRUD - SIGEM Colombia
"""

from uuid import UUID

from pydantic import BaseModel, Field


class DependenciaCreate(BaseModel):
    codigo: str = Field(
        ..., min_length=1, max_length=50, description="Código único de la dependencia"
    )
    nombre: str = Field(..., min_length=1, max_length=500, description="Nombre de la dependencia")
    descripcion: str | None = Field(None, description="Descripción de la dependencia")
    dependencia_padre_id: UUID | None = Field(None, description="ID de la dependencia padre")
    nivel: int = Field(1, ge=1, le=5, description="Nivel jerárquico (1-5)")
    estado: str = Field("ACTIVA", description="Estado: ACTIVA o INACTIVA")


class DependenciaUpdate(BaseModel):
    codigo: str | None = Field(None, min_length=1, max_length=50)
    nombre: str | None = Field(None, min_length=1, max_length=500)
    descripcion: str | None = None
    dependencia_padre_id: UUID | None = None
    nivel: int | None = Field(None, ge=1, le=5)
    estado: str | None = None


class DependenciaResponse(BaseModel):
    id: UUID
    municipio_id: UUID
    codigo: str
    nombre: str
    descripcion: str | None = None
    dependencia_padre_id: UUID | None = None
    nivel: int
    estado: str
    created_at: str | None = None
    updated_at: str | None = None

    class Config:
        from_attributes = True


class DependenciaListResponse(BaseModel):
    items: list[DependenciaResponse]
    total: int
    page: int
    page_size: int
