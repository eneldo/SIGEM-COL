"""Audit service - Event logging for security and compliance"""
import json
from datetime import datetime, timezone
from typing import Optional
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
        municipio_id: Optional[UUID] = None,
        usuario_id: Optional[UUID] = None,
        actor_id: Optional[UUID] = None,
        recurso_tipo: Optional[str] = None,
        recurso_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[dict] = None,
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
            fecha_evento=datetime.now(timezone.utc),
        )
        self.db.add(event)
        await self.db.commit()
        return event

    async def get_events(
        self,
        municipio_id: UUID,
        limit: int = 100,
        offset: int = 0,
        usuario_id: Optional[UUID] = None,
        evento_tipo: Optional[str] = None,
        recurso_id: Optional[UUID] = None,
        recurso_tipo: Optional[str] = None,
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
