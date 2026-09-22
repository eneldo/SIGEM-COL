"""Vigencia model - Modelo para vigencias fiscales"""
import uuid
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Vigencia(BaseModel):
    __tablename__ = "vigencias"

    municipio_id = Column(UUID(as_uuid=True), ForeignKey("municipios.id"), nullable=False, index=True)
    plan_desarrollo_id = Column(UUID(as_uuid=True), ForeignKey("planes_desarrollo.id"), nullable=False, index=True)
    codigo = Column(String(10), nullable=False)
    anio = Column(Integer, nullable=False)
    estado = Column(String(50), default="ACTIVA", nullable=False)

    # Relationships
    municipio = relationship("Municipio", backref="vigencias")
    plan_desarrollo = relationship("PlanDesarrollo", backref="vigencias_fiscales")

    def __repr__(self):
        return f"<Vigencia {self.anio} - {self.estado}>"
