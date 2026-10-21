"""Evidencia model - Archivos de soporte adjuntos a avances"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import BaseModel


class Evidencia(BaseModel):
    __tablename__ = "evidencias"

    avance_id = Column(
        UUID(as_uuid=True), ForeignKey("avances_producto.id"), nullable=False, index=True
    )
    municipio_id = Column(
        UUID(as_uuid=True), ForeignKey("municipios.id"), nullable=False, index=True
    )
    nombre = Column(String(255), nullable=False)
    tipo = Column(String(50), nullable=False)
    url = Column(String(500), nullable=False)
    descripcion = Column(Text, nullable=True)
    tamano_original = Column(Integer, nullable=True)
    tamano_almacenado = Column(Integer, nullable=True)
    optimizada = Column(Boolean, default=False, nullable=False)
    subida_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)

    avance = relationship("AvanceProducto", backref="evidencias")

    def __repr__(self) -> str:
        return f"<Evidencia {self.nombre} avance={self.avance_id}>"
