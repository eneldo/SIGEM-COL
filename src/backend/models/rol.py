"""Rol and Permiso models - Modelos para roles y permisos"""
import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Rol(BaseModel):
    __tablename__ = "roles"

    codigo = Column(String(100), unique=True, nullable=False, index=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    nivel = Column(Integer, default=1, nullable=False)
    estado = Column(String(50), default="ACTIVO", nullable=False)

    # Relationships
    permisos = relationship("RolPermiso", backref="rol", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Rol {self.codigo} - {self.nombre}>"


class Permiso(BaseModel):
    __tablename__ = "permisos"

    codigo = Column(String(150), unique=True, nullable=False, index=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    modulo = Column(String(100), nullable=False)
    accion = Column(String(100), nullable=False)
    estado = Column(String(50), default="ACTIVO", nullable=False)

    def __repr__(self):
        return f"<Permiso {self.codigo}>"
