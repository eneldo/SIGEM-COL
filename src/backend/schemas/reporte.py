"""
Schemas para Reportes y Rendición de Cuentas - SIGEM Colombia
"""
from pydantic import BaseModel


class ResumenGeneral(BaseModel):
    total_lineas: int
    total_programas: int
    total_productos: int
    productos_activos: int
    productos_inactivos: int
    total_gestores: int


class ResumenPorLinea(BaseModel):
    id: str
    codigo: str
    nombre: str
    total_programas: int
    total_productos: int
    estado: str


class ResumenPorPrograma(BaseModel):
    id: str
    codigo: str
    nombre: str
    sector: str | None
    linea_nombre: str
    total_productos: int
    productos_activos: int
    estado: str


class ResumenPorDependencia(BaseModel):
    id: str
    codigo: str
    nombre: str
    total_productos: int
    total_gestores: int


class MetricasProductos(BaseModel):
    total_productos: int
    con_indicador: int
    sin_indicador: int
    con_meta_cuatrienio: int
    con_linea_base: int
    con_gestor_asignado: int
    sin_gestor_asignado: int
    porcentaje_cumplimiento_indicador: float
    porcentaje_cumplimiento_meta: float
    promedio_avance: float
