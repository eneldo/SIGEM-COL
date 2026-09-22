"""Producto model - Modelo para productos"""
import uuid
from sqlalchemy import Column, String, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Producto(BaseModel):
    __tablename__ = "productos"

    municipio_id = Column(UUID(as_uuid=True), ForeignKey("municipios.id"), nullable=False, index=True)
    programa_id = Column(UUID(as_uuid=True), ForeignKey("programas.id"), nullable=False, index=True)
    codigo = Column(String(50), nullable=False)
    nombre = Column(String(500), nullable=False)
    codigo_indicador = Column(String(30), nullable=True)
    indicador = Column(String(300), nullable=True)
    meta_redactada = Column(Text, nullable=True)
    linea_base = Column(Integer, default=0, nullable=True)
    meta_cuatrienio = Column(Integer, default=0, nullable=True)
    descripcion = Column(Text, nullable=True)
    unidad_medida = Column(String(100), nullable=True)
    dependencia_responsable_id = Column(UUID(as_uuid=True), ForeignKey("dependencias.id"), nullable=True)
    gestor_lider_id = Column(UUID(as_uuid=True), ForeignKey("gestores_lideres.id"), nullable=True)
    estado = Column(String(50), default="ACTIVO", nullable=False)

    # Relationships
    municipio = relationship("Municipio", backref="productos")
    dependencia_responsable = relationship("Dependencia", backref="productos_responsables")

    def __repr__(self):
        return f"<Producto {self.codigo} - {self.nombre}>"
