"""
Schemas para Cumplimiento de Metas - SIGEM Colombia
"""
from pydantic import BaseModel


class CumplimientoGeneral(BaseModel):
    total_productos: int
    con_meta_definida: int
    sin_meta_definida: int
    completados: int
    en_progreso: int
    sin_avance: int
    porcentaje_cumplimiento_general: float


class CumplimientoPorLinea(BaseModel):
    id: str
    codigo: str
    nombre: str
    total_productos: int
    con_meta_definida: int
    completados: int
    en_progreso: int
    sin_avance: int
    porcentaje_cumplimiento: float


class CumplimientoPorPrograma(BaseModel):
    id: str
    codigo: str
    nombre: str
    linea_nombre: str
    total_productos: int
    con_meta_definida: int
    completados: int
    en_progreso: int
    sin_avance: int
    porcentaje_cumplimiento: float


class DetalleProductoCumplimiento(BaseModel):
    id: str
    codigo: str
    nombre: str
    codigo_indicador: str | None
    indicador: str | None
    meta_redactada: str | None
    linea_base: int | None
    meta_cuatrienio: int | None
    programa_codigo: str
    programa_nombre: str
    linea_nombre: str
    porcentaje_avance: float
    estado_cumplimiento: str


class ItemCumplimientoProducto(BaseModel):
    id: str
    codigo: str
    nombre: str
    indicador: str | None
    linea_base: int | None
    meta_cuatrienio: int | None
    programa_nombre: str
    linea_nombre: str
    porcentaje_avance: float
    estado_cumplimiento: str
