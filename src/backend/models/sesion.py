"""Sesion model - Modelo para sesiones de usuario"""
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base


class Sesion(Base):
    __tablename__ = "sesiones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, index=True)
    municipio_id = Column(UUID(as_uuid=True), ForeignKey("municipios.id"), nullable=False, index=True)
    token_jti = Column(String(36), unique=True, nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    activa = Column(Integer, default=1, nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), nullable=False)
    ultima_actividad = Column(DateTime(timezone=True), nullable=True)
    fecha_expiracion = Column(DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return f"<Sesion {self.token_jti[:20]}...>"
