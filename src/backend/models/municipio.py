"""Municipio model - Modelo para municipios"""
import uuid
from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel


class Municipio(BaseModel):
    __tablename__ = "municipios"

    codigo = Column(String(10), unique=True, nullable=False, index=True)
    nombre = Column(String(255), nullable=False)
    departamento = Column(String(255), nullable=False)
    region = Column(String(255), nullable=True)
    poblacion = Column(Integer, nullable=True)
    alcalde = Column(String(255), nullable=True)
    email_institucional = Column(String(255), nullable=True)
    telefono = Column(String(50), nullable=True)
    direccion = Column(String(500), nullable=True)
    activo = Column(Integer, default=1, nullable=False)

    def __repr__(self):
        return f"<Municipio {self.codigo} - {self.nombre}>"
