"""PlanDesarrollo model - Modelo para planes de desarrollo municipal"""
import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Text, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class PlanDesarrollo(BaseModel):
    __tablename__ = "planes_desarrollo"

    municipio_id = Column(UUID(as_uuid=True), ForeignKey("municipios.id"), nullable=False, index=True)
    codigo = Column(String(50), nullable=False)
    nombre = Column(String(500), nullable=False)
    descripcion = Column(Text, nullable=True)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    vigencias = Column(Integer, nullable=False)
    estado = Column(String(50), default="ACTIVO", nullable=False)

    # Relationships
    municipio = relationship("Municipio", backref="planes_desarrollo")
    lineas_estrategicas = relationship("LineaEstrategica", backref="plan_desarrollo")

    def __repr__(self):
        return f"<PlanDesarrollo {self.codigo} - {self.nombre}>"
