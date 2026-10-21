"""
Servicio de Personalizacion (branding) por municipio - SIGEM Colombia
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.personalizacion import Personalizacion

DEFAULT_COLOR_PRIMARIO = "#0f3d3b"
DEFAULT_COLOR_SECUNDARIO = "#b9852f"
DEFAULT_NOMBRE_SISTEMA = "SIGEM Colombia"


def default_configuracion() -> dict[str, Any]:
    """Configuracion visual por defecto cuando el municipio no tiene fila."""
    return {
        "color_primario": DEFAULT_COLOR_PRIMARIO,
        "color_secundario": DEFAULT_COLOR_SECUNDARIO,
        "nombre_sistema": DEFAULT_NOMBRE_SISTEMA,
        "logo_data_url": None,
    }


def _to_dict(row: Personalizacion) -> dict[str, Any]:
    return {
        "color_primario": row.color_primario,
        "color_secundario": row.color_secundario,
        "nombre_sistema": row.nombre_sistema,
        "logo_data_url": row.logo_data_url,
    }


async def get_personalizacion(
    db: AsyncSession,
    municipio_id: uuid.UUID,
) -> dict[str, Any]:
    """Obtener la configuracion visual del municipio (o los valores por defecto)."""
    stmt = select(Personalizacion).where(
        Personalizacion.municipio_id == municipio_id,
        Personalizacion.deleted_at.is_(None),
    )
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        return default_configuracion()
    return _to_dict(row)


async def save_personalizacion(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Crear o actualizar la configuracion visual del municipio."""
    stmt = select(Personalizacion).where(
        Personalizacion.municipio_id == municipio_id,
        Personalizacion.deleted_at.is_(None),
    )
    row = (await db.execute(stmt)).scalar_one_or_none()

    if row is None:
        row = Personalizacion(
            municipio_id=municipio_id,
            color_primario=data["color_primario"],
            color_secundario=data["color_secundario"],
            nombre_sistema=data["nombre_sistema"],
            logo_data_url=data["logo_data_url"],
        )
        db.add(row)
    else:
        row.color_primario = data["color_primario"]
        row.color_secundario = data["color_secundario"]
        row.nombre_sistema = data["nombre_sistema"]
        row.logo_data_url = data["logo_data_url"]

    await db.commit()
    await db.refresh(row)
    return _to_dict(row)
