"""Schemas de catálogos - Roles y dependencias para módulos administrativos"""
from uuid import UUID

from pydantic import BaseModel


class RolOut(BaseModel):
    id: UUID
    codigo: str
    nombre: str
    nivel: int


class DependenciaOut(BaseModel):
    id: UUID
    codigo: str
    nombre: str
    descripcion: str | None = None
