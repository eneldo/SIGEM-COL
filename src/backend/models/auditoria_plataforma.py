"""AuditoriaPlataforma model - Eventos de auditoría sin municipio (plataforma).

Contraparte de `auditoria_eventos` para eventos que no pertenecen a ningún
municipio (bootstrap del sistema, jobs, registros de plataforma). La tabla no
tiene RLS porque no es multi-municipio; el rol de aplicación solo puede
INSERTAR (append-only) según la migración 022: UPDATE/DELETE quedan exclusivos
del rol de migración para conservar la cadena de custodia.
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class AuditoriaPlataforma(Base):
    __tablename__ = "auditoria_plataforma"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True, index=True)
    actor_id = Column(UUID(as_uuid=True), nullable=True)  # Quién realizó la acción
    evento_tipo = Column(String(100), nullable=False, index=True)
    recurso_tipo = Column(String(100), nullable=True)
    recurso_id = Column(UUID(as_uuid=True), nullable=True)
    resultado = Column(String(50), nullable=False)  # EXITOSO, FALLIDO
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    metadata_json = Column("metadata", Text, nullable=True)  # JSON seguro
    fecha_evento = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    def __repr__(self) -> str:
        return f"<AuditoriaPlataforma {self.evento_tipo} - {self.resultado}>"
