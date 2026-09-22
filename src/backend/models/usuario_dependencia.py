"""UsuarioDependencia model - Relación usuario-dependencia"""
import uuid
from sqlalchemy import Column, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


class UsuarioDependencia(Base):
    __tablename__ = "usuario_dependencias"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, index=True)
    dependencia_id = Column(UUID(as_uuid=True), ForeignKey("dependencias.id"), nullable=False, index=True)
    municipio_id = Column(UUID(as_uuid=True), ForeignKey("municipios.id"), nullable=False, index=True)
    es_principal = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<UsuarioDependencia usuario={self.usuario_id} dependencia={self.dependencia_id}>"
