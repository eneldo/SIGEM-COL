"""
Schemas Pydantic para Personalizacion (branding) - SIGEM Colombia
"""

import re

from pydantic import BaseModel, Field, field_validator

HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
LOGO_DATA_URL_RE = re.compile(r"^data:image/(?:png|svg\+xml);base64,[A-Za-z0-9+/]+={0,2}$")
MAX_LOGO_BYTES = 2 * 1024 * 1024
MAX_LOGO_B64_CHARS = ((MAX_LOGO_BYTES + 2) // 3) * 4


class PersonalizacionResponse(BaseModel):
    color_primario: str
    color_secundario: str
    nombre_sistema: str
    logo_data_url: str | None = None


class PersonalizacionUpdate(BaseModel):
    color_primario: str = Field(..., min_length=7, max_length=7)
    color_secundario: str = Field(..., min_length=7, max_length=7)
    nombre_sistema: str = Field(..., min_length=1, max_length=120)
    logo_data_url: str | None = Field(None)

    @field_validator("color_primario", "color_secundario")
    @classmethod
    def validar_color(cls, v: str) -> str:
        if not HEX_COLOR_RE.match(v):
            raise ValueError("El color debe ser un valor hexadecimal con formato #RRGGBB")
        return v.lower()

    @field_validator("nombre_sistema")
    @classmethod
    def validar_nombre(cls, v: str) -> str:
        nombre = v.strip()
        if not nombre:
            raise ValueError("El nombre del sistema no puede estar vacío")
        return nombre

    @field_validator("logo_data_url")
    @classmethod
    def validar_logo(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not v.startswith("data:image/") or ";base64," not in v:
            raise ValueError("El logotipo debe ser una imagen PNG o SVG en base64")
        if not LOGO_DATA_URL_RE.match(v):
            raise ValueError("El logotipo no es una imagen PNG o SVG válida")
        payload = v.partition(",")[2]
        if len(payload) > MAX_LOGO_B64_CHARS:
            raise ValueError("El logotipo supera el tamaño máximo de 2MB")
        return v
