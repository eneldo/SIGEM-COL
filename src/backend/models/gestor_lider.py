"""GestorLider model - Modelo para gestores líderes"""
import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class GestorLider(BaseModel):
    __tablename__ = "gestores_lideres"

    municipio_id = Column(UUID(as_uuid=True), ForeignKey("municipios.id"), nullable=False, index=True)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), unique=True, nullable=False, index=True)
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    nombre_completo = Column(String(500), nullable=False)
    cargo = Column(String(255), nullable=True)
    dependencia_principal_id = Column(UUID(as_uuid=True), ForeignKey("dependencias.id"), nullable=True)
    estado = Column(String(50), default="ACTIVO", nullable=False)

    # Relationships
    municipio = relationship("Municipio", backref="gestores_lideres")
    dependencia_principal = relationship("Dependencia", backref="gestores_lideres")
    productos = relationship("Producto", backref="gestor_lider")

    def __repr__(self):
        return f"<GestorLider {self.codigo} - {self.nombre_completo}>"
