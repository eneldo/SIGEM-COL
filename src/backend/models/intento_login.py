"""IntentoLogin model - Modelo para registrar intentos de login"""
import uuid
from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


class IntentoLogin(Base):
    __tablename__ = "intentos_login"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True, index=True)
    username_intentado = Column(String(150), nullable=False, index=True)
    municipio_id = Column(UUID(as_uuid=True), ForeignKey("municipios.id"), nullable=True, index=True)
    exitoso = Column(Boolean, default=False, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    fecha_intento = Column(DateTime(timezone=True), nullable=False)
    razon_fallo = Column(Text, nullable=True)

    def __repr__(self):
        return f"<IntentoLogin {self.username_intentado} - {'OK' if self.exitoso else 'FAIL'}>"
