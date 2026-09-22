"""AuditoriaEvento model - Modelo para eventos de auditoría"""
import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


class AuditoriaEvento(Base):
    __tablename__ = "auditoria_eventos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    municipio_id = Column(UUID(as_uuid=True), ForeignKey("municipios.id"), nullable=True, index=True)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True, index=True)
    actor_id = Column(UUID(as_uuid=True), nullable=True)  # Quién realizó la acción
    evento_tipo = Column(String(50), nullable=False, index=True)
    recurso_tipo = Column(String(50), nullable=True)
    recurso_id = Column(UUID(as_uuid=True), nullable=True)
    resultado = Column(String(50), nullable=False)  # EXITOSO, FALLIDO
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    metadata_json = Column("metadata", Text, nullable=True)  # JSON seguro
    fecha_evento = Column(DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return f"<AuditoriaEvento {self.evento_tipo} - {self.resultado}>"
