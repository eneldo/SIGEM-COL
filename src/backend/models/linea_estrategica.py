"""LineaEstrategica model - Modelo para líneas estratégicas del plan"""
import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class LineaEstrategica(BaseModel):
    __tablename__ = "lineas_estrategicas"

    municipio_id = Column(UUID(as_uuid=True), ForeignKey("municipios.id"), nullable=False, index=True)
    plan_desarrollo_id = Column(UUID(as_uuid=True), ForeignKey("planes_desarrollo.id"), nullable=False, index=True)
    codigo = Column(String(50), nullable=False)
    numero = Column(String(20), nullable=True)
    nombre = Column(String(500), nullable=False)
    descripcion = Column(Text, nullable=True)
    orden = Column(Integer, default=0, nullable=False)
    estado = Column(String(50), default="ACTIVA", nullable=False)

    # Relationships
    municipio = relationship("Municipio", backref="lineas_estrategicas")
    programas = relationship("Programa", backref="linea_estrategica")

    def __repr__(self):
        return f"<LineaEstrategica {self.codigo} - {self.nombre}>"
