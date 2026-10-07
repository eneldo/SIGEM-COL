"""Audit service - Event logging for security and compliance"""

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.auditoria_evento import AuditoriaEvento


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(
        self,
        evento_tipo: str,
        resultado: str,
        municipio_id: UUID | None = None,
        usuario_id: UUID | None = None,
        actor_id: UUID | None = None,
        recurso_tipo: str | None = None,
        recurso_id: UUID | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditoriaEvento:
        event = AuditoriaEvento(
            municipio_id=municipio_id,
            usuario_id=usuario_id,
            actor_id=actor_id,
            evento_tipo=evento_tipo,
            recurso_tipo=recurso_tipo,
            recurso_id=recurso_id,
            resultado=resultado,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata_json=json.dumps(metadata) if metadata else None,
            fecha_evento=datetime.now(UTC),
        )
        self.db.add(event)
        await self.db.commit()
        return event

    async def get_events(
        self,
        municipio_id: UUID,
        limit: int = 100,
        offset: int = 0,
        usuario_id: UUID | None = None,
        evento_tipo: str | None = None,
        recurso_id: UUID | None = None,
        recurso_tipo: str | None = None,
    ) -> list[AuditoriaEvento]:
        query = select(AuditoriaEvento).where(AuditoriaEvento.municipio_id == municipio_id)

        if usuario_id:
            query = query.where(AuditoriaEvento.usuario_id == usuario_id)
        if evento_tipo:
            query = query.where(AuditoriaEvento.evento_tipo == evento_tipo)
        if recurso_id:
            query = query.where(AuditoriaEvento.recurso_id == recurso_id)
        if recurso_tipo:
            query = query.where(AuditoriaEvento.recurso_tipo == recurso_tipo)

        query = query.order_by(AuditoriaEvento.fecha_evento.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())
