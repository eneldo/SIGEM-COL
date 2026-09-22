"""Programa model - Modelo para programas"""
import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Programa(BaseModel):
    __tablename__ = "programas"

    municipio_id = Column(UUID(as_uuid=True), ForeignKey("municipios.id"), nullable=False, index=True)
    linea_estrategica_id = Column(UUID(as_uuid=True), ForeignKey("lineas_estrategicas.id"), nullable=False, index=True)
    codigo = Column(String(50), nullable=False)
    nombre = Column(String(500), nullable=False)
    sector = Column(String(100), nullable=True)
    descripcion = Column(Text, nullable=True)
    estado = Column(String(50), default="ACTIVO", nullable=False)

    # Relationships
    municipio = relationship("Municipio", backref="programas")
    productos = relationship("Producto", backref="programa")

    def __repr__(self):
        return f"<Programa {self.codigo} - {self.nombre}>"
