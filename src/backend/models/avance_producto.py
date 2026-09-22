"""AvanceProducto model - Registro de avances de productos por gestores"""
import uuid
from sqlalchemy import Column, String, ForeignKey, Text, Integer, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class AvanceProducto(BaseModel):
    __tablename__ = "avances_producto"

    municipio_id = Column(UUID(as_uuid=True), ForeignKey("municipios.id"), nullable=False, index=True)
    producto_id = Column(UUID(as_uuid=True), ForeignKey("productos.id"), nullable=False, index=True)
    gestor_lider_id = Column(UUID(as_uuid=True), ForeignKey("gestores_lideres.id"), nullable=False, index=True)
    avance_porcentaje = Column(Float, default=0.0, nullable=False)
    avance_valor = Column(Integer, default=0, nullable=True)
    observaciones = Column(Text, nullable=True)
    evidencia_url = Column(String(500), nullable=True)
    estado = Column(String(50), default="REGISTRADO", nullable=False)
    registrado_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)

    # Campos nuevos para registro de avance
    indicador = Column(String(300), nullable=True)
    periodo = Column(String(50), nullable=True)
    fecha_registro = Column(DateTime(timezone=True), nullable=True)
    estado_revision = Column(String(50), default="PENDIENTE", nullable=False)
    evidencia_nombre = Column(String(255), nullable=True)
    evidencia_tipo = Column(String(50), nullable=True)

    # Relationships
    municipio = relationship("Municipio", backref="avances_producto")
    producto = relationship("Producto", backref="avances")
    gestor_lider = relationship("GestorLider", backref="avances")
    usuario = relationship("Usuario", backref="avances_registrados")

    def __repr__(self):
        return f"<AvanceProducto {self.producto_id} - {self.avance_porcentaje}%>"
