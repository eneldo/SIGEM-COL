"""MFAFactor model - Modelo para factores MFA"""
import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


class MFAFactor(Base):
    __tablename__ = "mfa_factors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, index=True)
    municipio_id = Column(UUID(as_uuid=True), ForeignKey("municipios.id"), nullable=False, index=True)
    tipo = Column(String(50), nullable=False)  # TOTP, WEBAUTHN
    nombre = Column(String(255), nullable=False)
    secret_encrypted = Column(Text, nullable=True)
    public_key = Column(Text, nullable=True)
    activo = Column(Boolean, default=True, nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), nullable=False)
    ultimo_uso = Column(DateTime(timezone=True), nullable=True)
    revocado = Column(Boolean, default=False, nullable=False)
    fecha_revocacion = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<MFAFactor {self.tipo} - {self.nombre}>"
