"""
Schemas Pydantic para el módulo de Dependencias CRUD - SIGEM Colombia
"""
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class DependenciaCreate(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=50, description="Código único de la dependencia")
    nombre: str = Field(..., min_length=1, max_length=500, description="Nombre de la dependencia")
    descripcion: Optional[str] = Field(None, description="Descripción de la dependencia")
    dependencia_padre_id: Optional[UUID] = Field(None, description="ID de la dependencia padre")
    nivel: int = Field(1, ge=1, le=5, description="Nivel jerárquico (1-5)")
    estado: str = Field("ACTIVA", description="Estado: ACTIVA o INACTIVA")


class DependenciaUpdate(BaseModel):
    codigo: Optional[str] = Field(None, min_length=1, max_length=50)
    nombre: Optional[str] = Field(None, min_length=1, max_length=500)
    descripcion: Optional[str] = None
    dependencia_padre_id: Optional[UUID] = None
    nivel: Optional[int] = Field(None, ge=1, le=5)
    estado: Optional[str] = None


class DependenciaResponse(BaseModel):
    id: UUID
    municipio_id: UUID
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    dependencia_padre_id: Optional[UUID] = None
    nivel: int
    estado: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class DependenciaListResponse(BaseModel):
    items: List[DependenciaResponse]
    total: int
    page: int
    page_size: int
