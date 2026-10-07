"""Personalizacion model - Configuracion visual (branding) por municipio"""

from sqlalchemy import Column, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import BaseModel


class Personalizacion(BaseModel):
    __tablename__ = "personalizaciones"
    __table_args__ = (UniqueConstraint("municipio_id", name="uq_personalizaciones_municipio"),)

    municipio_id = Column(
        UUID(as_uuid=True), ForeignKey("municipios.id"), nullable=False, index=True
    )
    color_primario = Column(String(7), nullable=False, default="#0F3D3B")
    color_secundario = Column(String(7), nullable=False, default="#B9852F")
    nombre_sistema = Column(String(120), nullable=False, default="SIGEM Colombia")
    logo_data_url = Column(Text, nullable=True)

    municipio = relationship("Municipio", backref="personalizaciones")

    def __repr__(self) -> str:
        return f"<Personalizacion {self.nombre_sistema}>"
