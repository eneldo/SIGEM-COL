"""Dependencia model - Modelo para dependencias municipales"""
import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Dependencia(BaseModel):
    __tablename__ = "dependencias"

    municipio_id = Column(UUID(as_uuid=True), ForeignKey("municipios.id"), nullable=False, index=True)
    codigo = Column(String(50), nullable=False)
    nombre = Column(String(500), nullable=False)
    descripcion = Column(Text, nullable=True)
    dependencia_padre_id = Column(UUID(as_uuid=True), ForeignKey("dependencias.id"), nullable=True)
    nivel = Column(Integer, default=1, nullable=False)
    estado = Column(String(50), default="ACTIVA", nullable=False)

    # Relationships
    municipio = relationship("Municipio", backref="dependencias")
    dependencia_padre = relationship("Dependencia", remote_side="Dependencia.id", backref="subdependencias")

    def __repr__(self):
        return f"<Dependencia {self.codigo} - {self.nombre}>"
