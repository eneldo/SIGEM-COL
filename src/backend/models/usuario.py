"""Usuario model - Modelo para usuarios del sistema"""
import uuid
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Usuario(BaseModel):
    __tablename__ = "usuarios"

    municipio_id = Column(UUID(as_uuid=True), ForeignKey("municipios.id"), nullable=False, index=True)
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    username = Column(String(150), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    nombre_completo = Column(String(500), nullable=False)
    telefono = Column(String(50), nullable=True)
    cargo = Column(String(255), nullable=True)
    password_hash = Column(String(500), nullable=False)
    must_change_password = Column(Boolean, default=True, nullable=False)
    activo = Column(Integer, default=1, nullable=False)
    
    # Security fields
    ultimo_acceso = Column(DateTime(timezone=True), nullable=True)
    ip_ultimo_acceso = Column(String(45), nullable=True)
    user_agent_ultimo_acceso = Column(Text, nullable=True)
    intentos_fallidos = Column(Integer, default=0, nullable=False)
    ultimo_intento_fallido = Column(DateTime(timezone=True), nullable=True)
    ultimo_cambio_password = Column(DateTime(timezone=True), nullable=True)
    fecha_bloqueo = Column(DateTime(timezone=True), nullable=True)
    motivo_bloqueo = Column(Text, nullable=True)
    mfa_activo = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(500), nullable=True)
    
    # Relationships
    municipio = relationship("Municipio", backref="usuarios")
    roles = relationship("UsuarioRol", backref="usuario", cascade="all, delete-orphan")
    dependencias = relationship("UsuarioDependencia", backref="usuario", cascade="all, delete-orphan")
    sesiones = relationship("Sesion", backref="usuario", cascade="all, delete-orphan")
    gestor_lider = relationship("GestorLider", backref="usuario", uselist=False)

    # Unique constraint: username per municipality
    __table_args__ = (
        {"schema": None},
    )

    def __repr__(self):
        return f"<Usuario {self.username} - {self.nombre_completo}>"
