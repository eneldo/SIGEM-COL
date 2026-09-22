"""Base model - Modelo base para todas las entidades"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class BaseModel(Base):
    """Modelo base con campos transversales"""
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    estado = Column(String(50), default="ACTIVO", nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)

    def soft_delete(self, user_id: uuid.UUID):
        """Eliminación lógica"""
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = user_id
        self.estado = "ELIMINADO_LOGICAMENTE"

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @hybrid_property
    def eliminado(self) -> bool:
        return self.deleted_at is not None

    @eliminado.inplace.expression
    @classmethod
    def _eliminado_expression(cls):
        return cls.deleted_at.is_not(None)

    @eliminado.inplace.setter
    def _eliminado_setter(self, value: bool) -> None:
        self.deleted_at = datetime.now(timezone.utc) if value else None
        if value:
            self.estado = "ELIMINADO_LOGICAMENTE"
