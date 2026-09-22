"""UsuarioRol and RolPermiso models - Modelos de relación"""
import uuid
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


class UsuarioRol(Base):
    __tablename__ = "usuario_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, index=True)
    rol_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False, index=True)
    municipio_id = Column(UUID(as_uuid=True), ForeignKey("municipios.id"), nullable=False, index=True)

    def __repr__(self):
        return f"<UsuarioRol usuario={self.usuario_id} rol={self.rol_id}>"


class RolPermiso(Base):
    __tablename__ = "rol_permisos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rol_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False, index=True)
    permiso_id = Column(UUID(as_uuid=True), ForeignKey("permisos.id"), nullable=False, index=True)

    def __repr__(self):
        return f"<RolPermiso rol={self.rol_id} permiso={self.permiso_id}>"
