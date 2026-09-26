"""
Servicio de Avances de Productos - SIGEM Colombia
=================================================

Permite a los gestores líderes registrar avances en sus productos asignados.

Autor: SIGEM Colombia
Versión: 1.0
Fecha: 2026-09-21
"""

import asyncio
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..models.avance_producto import AvanceProducto
from ..models.evidencia import Evidencia
from ..models.gestor_lider import GestorLider
from ..models.producto import Producto
from ..services.audit_service import AuditService
from ..services.evidence_optimizer import optimize_evidence


async def get_mis_productos(
    db: AsyncSession,
    usuario_id: uuid.UUID,
    municipio_id: uuid.UUID,
) -> list[dict]:
    """
    Obtiene los productos asignados al gestor actual.
    """
    gestor_stmt = (
        select(GestorLider.id)
        .where(
            and_(
                GestorLider.usuario_id == usuario_id,
                GestorLider.municipio_id == municipio_id,
                GestorLider.deleted_at.is_(None),
            )
        )
    )
    gestor_id = await db.scalar(gestor_stmt)
    if not gestor_id:
        return []

    stmt = (
        select(Producto)
        .where(
            and_(
                Producto.gestor_lider_id == gestor_id,
                Producto.municipio_id == municipio_id,
                Producto.deleted_at.is_(None),
            )
        )
        .order_by(Producto.codigo.asc())
    )
    result = await db.execute(stmt)
    productos = list(result.scalars().all())

    return [
        {
            "id": str(p.id),
            "codigo": p.codigo,
            "nombre": p.nombre,
            "indicador": p.indicador,
            "codigo_indicador": p.codigo_indicador,
            "meta_redactada": p.meta_redactada,
            "linea_base": p.linea_base,
            "meta_cuatrienio": p.meta_cuatrienio,
            "unidad_medida": p.unidad_medida,
            "estado": p.estado,
        }
        for p in productos
    ]


async def get_avances_producto(
    db: AsyncSession,
    producto_id: uuid.UUID,
    municipio_id: uuid.UUID,
) -> list[dict]:
    """
    Obtiene los avances registrados para un producto específico.
    """
    stmt = (
        select(AvanceProducto)
        .where(
            and_(
                AvanceProducto.producto_id == producto_id,
                AvanceProducto.municipio_id == municipio_id,
                AvanceProducto.deleted_at.is_(None),
            )
        )
        .order_by(AvanceProducto.created_at.desc())
    )
    result = await db.execute(stmt)
    avances = list(result.scalars().all())

    return [
        {
            "id": str(a.id),
            "producto_id": str(a.producto_id),
            "avance_porcentaje": a.avance_porcentaje,
            "avance_valor": a.avance_valor,
            "observaciones": a.observaciones,
            "evidencia_url": a.evidencia_url,
            "indicador": a.indicador,
            "periodo": a.periodo,
            "fecha_registro": a.fecha_registro.isoformat() if a.fecha_registro else None,
            "estado_revision": a.estado_revision,
            "evidencia_nombre": a.evidencia_nombre,
            "evidencia_tipo": a.evidencia_tipo,
            "observaciones_revision": a.observaciones_revision,
            "estado": a.estado,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in avances
    ]


async def registrar_avance(
    db: AsyncSession,
    usuario_id: uuid.UUID,
    municipio_id: uuid.UUID,
    producto_id: uuid.UUID,
    avance_data: dict,
) -> dict:
    """
    Registra un nuevo avance para un producto.
    """
    gestor_stmt = (
        select(GestorLider.id)
        .where(
            and_(
                GestorLider.usuario_id == usuario_id,
                GestorLider.municipio_id == municipio_id,
                GestorLider.deleted_at.is_(None),
            )
        )
    )
    gestor_id = await db.scalar(gestor_stmt)
    if not gestor_id:
        raise ValueError("No se encontró un gestor líder asociado al usuario actual.")

    producto_stmt = (
        select(Producto)
        .where(
            and_(
                Producto.id == producto_id,
                Producto.municipio_id == municipio_id,
                Producto.gestor_lider_id == gestor_id,
                Producto.deleted_at.is_(None),
            )
        )
    )
    producto = await db.scalar(producto_stmt)
    if not producto:
        raise ValueError("El producto no existe o no está asignado a este gestor.")

    now = datetime.now(UTC)
    avance = AvanceProducto(
        municipio_id=municipio_id,
        producto_id=producto_id,
        gestor_lider_id=gestor_id,
        avance_porcentaje=avance_data.get("avance_porcentaje", 0.0),
        avance_valor=avance_data.get("avance_valor"),
        observaciones=avance_data.get("observaciones"),
        evidencia_url=avance_data.get("evidencia_url"),
        indicador=avance_data.get("indicador"),
        periodo=avance_data.get("periodo"),
        fecha_registro=now,
        estado_revision=avance_data.get("estado_revision", "PENDIENTE"),
        evidencia_nombre=avance_data.get("evidencia_nombre"),
        evidencia_tipo=avance_data.get("evidencia_tipo"),
        estado="REGISTRADO",
        registrado_por=usuario_id,
        created_at=now,
        updated_at=now,
    )
    db.add(avance)
    await db.flush()

    audit = AuditService(db)
    await audit.log_event(
        evento_tipo="AVANCE_REGISTRADO",
        resultado="EXITOSO",
        municipio_id=municipio_id,
        usuario_id=usuario_id,
        recurso_tipo="AvanceProducto",
        recurso_id=avance.id,
        metadata={
            "producto_id": str(producto_id),
            "avance_porcentaje": avance.avance_porcentaje,
        },
    )

    await db.commit()
    await db.refresh(avance)

    return {
        "id": str(avance.id),
        "producto_id": str(avance.producto_id),
        "avance_porcentaje": avance.avance_porcentaje,
        "avance_valor": avance.avance_valor,
        "observaciones": avance.observaciones,
        "evidencia_url": avance.evidencia_url,
        "indicador": avance.indicador,
        "periodo": avance.periodo,
        "fecha_registro": avance.fecha_registro.isoformat() if avance.fecha_registro else None,
        "estado_revision": avance.estado_revision,
        "evidencia_nombre": avance.evidencia_nombre,
        "evidencia_tipo": avance.evidencia_tipo,
        "observaciones_revision": avance.observaciones_revision,
        "estado": avance.estado,
        "created_at": avance.created_at.isoformat() if avance.created_at else None,
    }


async def actualizar_avance(
    db: AsyncSession,
    avance_id: uuid.UUID,
    municipio_id: uuid.UUID,
    usuario_id: uuid.UUID,
    avance_data: dict,
) -> dict:
    """
    Actualiza los campos editables de un avance existente.
    No permite editar avances ya aprobados.
    """
    avance = await _get_avance_or_404(db, avance_id, municipio_id)
    await _check_evidence_permission(db, avance, usuario_id, municipio_id)

    if avance.estado_revision == "APROBADO":
        raise PermissionError("No se puede editar un avance ya aprobado.")

    editable = {"avance_porcentaje", "avance_valor", "observaciones", "indicador", "periodo", "estado_revision"}
    changed = False
    for key in editable:
        if key in avance_data and avance_data[key] is not None:
            setattr(avance, key, avance_data[key])
            changed = True

    if not changed:
        raise ValueError("No se enviaron campos para actualizar.")

    avance.updated_at = datetime.now(UTC)
    await db.flush()

    audit = AuditService(db)
    await audit.log_event(
        evento_tipo="AVANCE_ACTUALIZADO",
        resultado="EXITOSO",
        municipio_id=municipio_id,
        usuario_id=usuario_id,
        recurso_tipo="AvanceProducto",
        recurso_id=avance.id,
        metadata={"campos": sorted(k for k in editable if k in avance_data and avance_data[k] is not None)},
    )

    await db.commit()
    await db.refresh(avance)

    return {
        "id": str(avance.id),
        "producto_id": str(avance.producto_id),
        "avance_porcentaje": avance.avance_porcentaje,
        "avance_valor": avance.avance_valor,
        "observaciones": avance.observaciones,
        "evidencia_url": avance.evidencia_url,
        "indicador": avance.indicador,
        "periodo": avance.periodo,
        "fecha_registro": avance.fecha_registro.isoformat() if avance.fecha_registro else None,
        "estado_revision": avance.estado_revision,
        "evidencia_nombre": avance.evidencia_nombre,
        "evidencia_tipo": avance.evidencia_tipo,
        "observaciones_revision": avance.observaciones_revision,
        "estado": avance.estado,
        "created_at": avance.created_at.isoformat() if avance.created_at else None,
    }


async def eliminar_avance(
    db: AsyncSession,
    avance_id: uuid.UUID,
    municipio_id: uuid.UUID,
    usuario_id: uuid.UUID,
) -> dict:
    """
    Elimina lógicamente un avance y sus evidencias.
    No permite eliminar avances ya aprobados.
    """
    avance = await _get_avance_or_404(db, avance_id, municipio_id)
    await _check_evidence_permission(db, avance, usuario_id, municipio_id)

    if avance.estado_revision == "APROBADO":
        raise PermissionError("No se puede eliminar un avance ya aprobado.")

    evidencias_stmt = select(Evidencia).where(
        and_(
            Evidencia.avance_id == avance.id,
            Evidencia.deleted_at.is_(None),
        )
    )
    result = await db.execute(evidencias_stmt)
    for ev in result.scalars().all():
        ev.soft_delete(usuario_id)

    avance.soft_delete(usuario_id)
    avance.updated_at = datetime.now(UTC)

    audit = AuditService(db)
    await audit.log_event(
        evento_tipo="AVANCE_ELIMINADO",
        resultado="EXITOSO",
        municipio_id=municipio_id,
        usuario_id=usuario_id,
        recurso_tipo="AvanceProducto",
        recurso_id=avance.id,
        metadata={
            "producto_id": str(avance.producto_id),
            "avance_porcentaje": avance.avance_porcentaje,
            "estado_revision": avance.estado_revision,
        },
    )

    await db.commit()

    return {"id": str(avance.id), "eliminado": True}


async def get_resumen_avances(
    db: AsyncSession,
    usuario_id: uuid.UUID,
    municipio_id: uuid.UUID,
) -> dict:
    """
    Resumen de avances del gestor actual.
    """
    gestor_stmt = (
        select(GestorLider.id)
        .where(
            and_(
                GestorLider.usuario_id == usuario_id,
                GestorLider.municipio_id == municipio_id,
                GestorLider.deleted_at.is_(None),
            )
        )
    )
    gestor_id = await db.scalar(gestor_stmt)
    if not gestor_id:
        return {
            "total_productos": 0,
            "productos_con_avance": 0,
            "avance_promedio": 0.0,
            "productos_completados": 0,
        }

    productos_stmt = (
        select(Producto)
        .where(
            and_(
                Producto.gestor_lider_id == gestor_id,
                Producto.municipio_id == municipio_id,
                Producto.deleted_at.is_(None),
            )
        )
    )
    productos_result = await db.execute(productos_stmt)
    productos = list(productos_result.scalars().all())
    total_productos = len(productos)

    avances_stmt = (
        select(
            AvanceProducto.producto_id,
            func.max(AvanceProducto.avance_porcentaje).label("max_avance"),
        )
        .where(
            and_(
                AvanceProducto.gestor_lider_id == gestor_id,
                AvanceProducto.municipio_id == municipio_id,
                AvanceProducto.deleted_at.is_(None),
            )
        )
        .group_by(AvanceProducto.producto_id)
    )
    avances_result = await db.execute(avances_stmt)
    avances_map = {row[0]: row[1] for row in avances_result.all()}

    productos_con_avance = len(avances_map)
    avances_values = list(avances_map.values())
    avance_promedio = sum(avances_values) / len(avances_values) if avances_values else 0.0
    productos_completados = sum(1 for v in avances_values if v >= 100.0)

    return {
        "total_productos": total_productos,
        "productos_con_avance": productos_con_avance,
        "avance_promedio": round(avance_promedio, 1),
        "productos_completados": productos_completados,
    }


async def get_avances_para_revision(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    gestor_lider_id: uuid.UUID | None = None,
    estado_revision: str | None = None,
    search: str | None = None,
) -> list[dict]:
    """
    Obtiene avances para revisión con datos del gestor y producto.
    Si se proporciona gestor_lider_id, filtra solo los avances de ese gestor (para gestor líder).
    Si no, retorna todos los avances del municipio (para admin).
    """
    conditions = [
        AvanceProducto.municipio_id == municipio_id,
        AvanceProducto.deleted_at.is_(None),
    ]

    if gestor_lider_id:
        conditions.append(AvanceProducto.gestor_lider_id == gestor_lider_id)

    if estado_revision:
        conditions.append(AvanceProducto.estado_revision == estado_revision)

    if search:
        search_filter = f"%{search}%"
        conditions.append(
            GestorLider.codigo.ilike(search_filter)
            | GestorLider.nombre_completo.ilike(search_filter)
            | Producto.codigo_indicador.ilike(search_filter)
            | Producto.indicador.ilike(search_filter)
        )

    stmt = (
        select(AvanceProducto, GestorLider, Producto)
        .join(GestorLider, AvanceProducto.gestor_lider_id == GestorLider.id)
        .join(Producto, AvanceProducto.producto_id == Producto.id)
        .where(and_(*conditions))
        .order_by(AvanceProducto.created_at.desc())
    )

    result = await db.execute(stmt)
    rows = list(result.all())

    return [
        {
            "id": str(avance.id),
            "producto_id": str(avance.producto_id),
            "producto_codigo": producto.codigo,
            "producto_nombre": producto.nombre,
            "codigo_indicador": producto.codigo_indicador,
            "indicador": avance.indicador or producto.indicador,
            "gestor_id": str(gestor.id),
            "gestor_codigo": gestor.codigo,
            "gestor_nombre": gestor.nombre_completo,
            "avance_porcentaje": avance.avance_porcentaje,
            "avance_valor": avance.avance_valor,
            "periodo": avance.periodo,
            "fecha_registro": avance.fecha_registro.isoformat() if avance.fecha_registro else None,
            "estado_revision": avance.estado_revision,
            "evidencia_nombre": avance.evidencia_nombre,
            "evidencia_tipo": avance.evidencia_tipo,
            "evidencia_url": avance.evidencia_url,
            "observaciones": avance.observaciones,
            "observaciones_revision": avance.observaciones_revision,
            "created_at": avance.created_at.isoformat() if avance.created_at else None,
        }
        for avance, gestor, producto in rows
    ]


async def get_estadisticas_revision(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    gestor_lider_id: uuid.UUID | None = None,
) -> dict:
    """
    Estadísticas para el dashboard de revisión.
    """
    from datetime import timedelta

    now = datetime.now(UTC)
    week_ago = now - timedelta(days=7)

    base_conditions = [
        AvanceProducto.municipio_id == municipio_id,
        AvanceProducto.deleted_at.is_(None),
    ]
    if gestor_lider_id:
        base_conditions.append(AvanceProducto.gestor_lider_id == gestor_lider_id)

    pendientes = await db.scalar(
        select(func.count()).select_from(AvanceProducto).where(
            and_(*base_conditions, AvanceProducto.estado_revision == "PENDIENTE")
        )
    )
    aprobados_semana = await db.scalar(
        select(func.count()).select_from(AvanceProducto).where(
            and_(
                *base_conditions,
                AvanceProducto.estado_revision == "APROBADO",
                AvanceProducto.updated_at >= week_ago,
            )
        )
    )
    devueltos = await db.scalar(
        select(func.count()).select_from(AvanceProducto).where(
            and_(*base_conditions, AvanceProducto.estado_revision == "RECHAZADO")
        )
    )

    return {
        "pendientes": pendientes or 0,
        "aprobados_semana": aprobados_semana or 0,
        "devueltos": devueltos or 0,
    }


async def revisar_avance(
    db: AsyncSession,
    avance_id: uuid.UUID,
    municipio_id: uuid.UUID,
    usuario_id: uuid.UUID,
    nuevo_estado: str,
    observacion: str | None = None,
) -> dict:
    """
    Aprueba o rechaza un avance.
    """
    stmt = select(AvanceProducto).where(
        and_(
            AvanceProducto.id == avance_id,
            AvanceProducto.municipio_id == municipio_id,
            AvanceProducto.deleted_at.is_(None),
        )
    )
    avance = await db.scalar(stmt)
    if not avance:
        raise ValueError("Avance no encontrado.")

    if nuevo_estado not in ("APROBADO", "RECHAZADO"):
        raise ValueError("Estado inválido. Debe ser APROBADO o RECHAZADO.")

    if nuevo_estado == "RECHAZADO" and not observacion:
        raise ValueError("La observación es obligatoria al devolver un avance.")

    avance.estado_revision = nuevo_estado
    if observacion:
        avance.observaciones_revision = observacion
    avance.updated_at = datetime.now(UTC)

    audit = AuditService(db)
    await audit.log_event(
        evento_tipo="AVANCE_REVISADO",
        resultado="EXITOSO",
        municipio_id=municipio_id,
        usuario_id=usuario_id,
        recurso_tipo="AvanceProducto",
        recurso_id=avance.id,
        metadata={
            "nuevo_estado": nuevo_estado,
            "observacion": observacion,
        },
    )

    await db.commit()
    await db.refresh(avance)

    return {
        "id": str(avance.id),
        "estado_revision": avance.estado_revision,
        "observaciones": avance.observaciones,
        "observaciones_revision": avance.observaciones_revision,
    }


async def guardar_evidencia(
    db: AsyncSession,
    avance_id: uuid.UUID,
    municipio_id: uuid.UUID,
    usuario_id: uuid.UUID,
    content: bytes,
    filename: str,
    content_type: str,
) -> dict:
    """
    Guarda el archivo de evidencia en disco y actualiza el avance.
    """
    stmt = select(AvanceProducto).where(
        and_(
            AvanceProducto.id == avance_id,
            AvanceProducto.municipio_id == municipio_id,
            AvanceProducto.deleted_at.is_(None),
        )
    )
    avance = await db.scalar(stmt)
    if not avance:
        raise ValueError("Avance no encontrado.")

    gestor_stmt = select(GestorLider.id).where(
        and_(
            GestorLider.usuario_id == usuario_id,
            GestorLider.municipio_id == municipio_id,
            GestorLider.deleted_at.is_(None),
        )
    )
    gestor_id = await db.scalar(gestor_stmt)
    if avance.registrado_por != usuario_id and avance.gestor_lider_id != gestor_id:
        raise PermissionError("No tiene permiso para adjuntar evidencia a este avance.")

    optimization = await asyncio.to_thread(optimize_evidence, content, content_type)

    storage_root = Path(settings.STORAGE_PATH)
    storage = storage_root / str(municipio_id) / str(avance_id)
    await asyncio.to_thread(storage.mkdir, parents=True, exist_ok=True)

    old_file_path = storage_root / avance.evidencia_url if avance.evidencia_url else None
    safe_name = f"{uuid.uuid4().hex}_{filename}"
    file_path = storage / safe_name
    temporary_path = storage / f".{safe_name}.tmp"

    def write_atomically() -> None:
        try:
            temporary_path.write_bytes(optimization.content)
            temporary_path.replace(file_path)
        finally:
            temporary_path.unlink(missing_ok=True)

    await asyncio.to_thread(write_atomically)

    rel_path = f"{municipio_id}/{avance_id}/{safe_name}"
    avance.evidencia_url = rel_path
    avance.evidencia_nombre = filename
    avance.evidencia_tipo = content_type
    avance.updated_at = datetime.now(UTC)

    try:
        audit = AuditService(db)
        await audit.log_event(
            evento_tipo="EVIDENCIA_SUBIDA",
            resultado="EXITOSO",
            municipio_id=municipio_id,
            usuario_id=usuario_id,
            recurso_tipo="AvanceProducto",
            recurso_id=avance.id,
            metadata={
                "evidencia_nombre": filename,
                "evidencia_tipo": content_type,
                "tamano_original": optimization.original_size,
                "tamano_almacenado": optimization.stored_size,
                "bytes_ahorrados": optimization.saved_bytes,
                "reduccion_porcentaje": optimization.reduction_percent,
                "optimizada": optimization.optimized,
                "metodo": optimization.method,
            },
        )
        await db.refresh(avance)
    except Exception:
        await db.rollback()
        await asyncio.to_thread(file_path.unlink, missing_ok=True)
        raise

    if old_file_path and old_file_path != file_path:
        try:
            resolved_old_path = old_file_path.resolve()
            if resolved_old_path.is_relative_to(storage_root.resolve()):
                await asyncio.to_thread(resolved_old_path.unlink, missing_ok=True)
        except OSError:
            pass

    return {
        "id": str(avance.id),
        "evidencia_url": avance.evidencia_url,
        "evidencia_nombre": avance.evidencia_nombre,
        "evidencia_tipo": avance.evidencia_tipo,
        "tamano_original": optimization.original_size,
        "tamano_almacenado": optimization.stored_size,
        "bytes_ahorrados": optimization.saved_bytes,
        "reduccion_porcentaje": optimization.reduction_percent,
        "optimizada": optimization.optimized,
    }


async def obtener_archivo_evidencia(
    db: AsyncSession,
    avance_id: uuid.UUID,
    municipio_id: uuid.UUID,
    usuario_id: uuid.UUID,
    roles: list[str],
) -> tuple[Path, str, str]:
    """
    Resuelve la ruta del archivo de evidencia y valida acceso.
    Retorna (path, filename, content_type).
    """
    stmt = select(AvanceProducto).where(
        and_(
            AvanceProducto.id == avance_id,
            AvanceProducto.municipio_id == municipio_id,
            AvanceProducto.deleted_at.is_(None),
        )
    )
    avance = await db.scalar(stmt)
    if not avance or not avance.evidencia_url:
        raise ValueError("Evidencia no encontrada.")

    admin_roles = ("SUPERADMIN_PLATAFORMA", "ADMINISTRADOR_MUNICIPAL", "GESTOR_LIDER")
    is_admin = any(r in roles for r in admin_roles)
    if not is_admin and avance.registrado_por != usuario_id:
        gestor_stmt = select(GestorLider.id).where(
            and_(
                GestorLider.usuario_id == usuario_id,
                GestorLider.municipio_id == municipio_id,
                GestorLider.deleted_at.is_(None),
            )
        )
        gestor_id = await db.scalar(gestor_stmt)
        if gestor_id != avance.gestor_lider_id:
            raise ValueError("No tiene permiso para ver esta evidencia.")

    file_path = Path(settings.STORAGE_PATH) / avance.evidencia_url
    if not file_path.is_file():
        raise ValueError("El archivo de evidencia no existe en el almacenamiento.")

    filename = avance.evidencia_nombre or file_path.name
    content_type = avance.evidencia_tipo or "application/octet-stream"
    return file_path, filename, content_type


async def _check_evidence_permission(
    db: AsyncSession,
    avance: AvanceProducto,
    usuario_id: uuid.UUID,
    municipio_id: uuid.UUID,
) -> None:
    gestor_stmt = select(GestorLider.id).where(
        and_(
            GestorLider.usuario_id == usuario_id,
            GestorLider.municipio_id == municipio_id,
            GestorLider.deleted_at.is_(None),
        )
    )
    gestor_id = await db.scalar(gestor_stmt)
    if avance.registrado_por != usuario_id and avance.gestor_lider_id != gestor_id:
        raise PermissionError("No tiene permiso para gestionar evidencias de este avance.")


async def _get_avance_or_404(
    db: AsyncSession,
    avance_id: uuid.UUID,
    municipio_id: uuid.UUID,
) -> AvanceProducto:
    stmt = select(AvanceProducto).where(
        and_(
            AvanceProducto.id == avance_id,
            AvanceProducto.municipio_id == municipio_id,
            AvanceProducto.deleted_at.is_(None),
        )
    )
    avance = await db.scalar(stmt)
    if not avance:
        raise ValueError("Avance no encontrado.")
    return avance


async def agregar_evidencias(
    db: AsyncSession,
    avance_id: uuid.UUID,
    municipio_id: uuid.UUID,
    usuario_id: uuid.UUID,
    archivos: list[dict],
) -> list[dict]:
    """
    Agrega una o más evidencias a un avance sin borrar las existentes.
    archivos: [{content: bytes, filename: str, content_type: str, descripcion: str|None}]
    """
    if not archivos:
        raise ValueError("Debe adjuntar al menos una evidencia.")

    avance = await _get_avance_or_404(db, avance_id, municipio_id)
    await _check_evidence_permission(db, avance, usuario_id, municipio_id)

    existing_count = await db.scalar(
        select(func.count(Evidencia.id)).where(
            and_(
                Evidencia.avance_id == avance.id,
                Evidencia.deleted_at.is_(None),
            )
        )
    )
    evidence_count = int(existing_count or 0)
    if evidence_count + len(archivos) > 4:
        raise ValueError(
            f"El avance admite máximo 4 evidencias; actualmente tiene {evidence_count}."
        )

    storage_root = Path(settings.STORAGE_PATH)
    storage = storage_root / str(municipio_id) / str(avance_id)
    await asyncio.to_thread(storage.mkdir, parents=True, exist_ok=True)

    results = []
    for item in archivos:
        content = item["content"]
        filename = item["filename"]
        content_type = item["content_type"]
        descripcion = item.get("descripcion")

        optimization = await asyncio.to_thread(optimize_evidence, content, content_type)

        safe_name = f"{uuid.uuid4().hex}_{filename}"
        file_path = storage / safe_name
        temporary_path = storage / f".{safe_name}.tmp"

        def write_atomically(
            tmp_path: Path = temporary_path,
            dest_path: Path = file_path,
            payload: bytes = optimization.content,
        ) -> None:
            try:
                tmp_path.write_bytes(payload)
                tmp_path.replace(dest_path)
            finally:
                tmp_path.unlink(missing_ok=True)

        await asyncio.to_thread(write_atomically)

        rel_path = f"{municipio_id}/{avance_id}/{safe_name}"

        evidencia = Evidencia(
            avance_id=avance.id,
            municipio_id=municipio_id,
            nombre=filename,
            tipo=content_type,
            url=rel_path,
            descripcion=descripcion,
            tamano_original=optimization.original_size,
            tamano_almacenado=optimization.stored_size,
            optimizada=optimization.optimized,
            subida_por=usuario_id,
        )
        db.add(evidencia)
        await db.flush()

        results.append(evidencia)

    # Actualizar denormalizado en avance (última evidencia)
    last = results[-1]
    avance.evidencia_url = last.url
    avance.evidencia_nombre = last.nombre
    avance.evidencia_tipo = last.tipo
    avance.updated_at = datetime.now(UTC)

    try:
        audit = AuditService(db)
        for ev in results:
            await audit.log_event(
                evento_tipo="EVIDENCIA_SUBIDA",
                resultado="EXITOSO",
                municipio_id=municipio_id,
                usuario_id=usuario_id,
                recurso_tipo="AvanceProducto",
                recurso_id=avance.id,
                metadata={
                    "evidencia_id": str(ev.id),
                    "evidencia_nombre": ev.nombre,
                    "evidencia_tipo": ev.tipo,
                    "descripcion": ev.descripcion,
                    "tamano_original": ev.tamano_original,
                    "tamano_almacenado": ev.tamano_almacenado,
                    "optimizada": ev.optimizada,
                },
            )
        await db.refresh(avance)
    except Exception:
        await db.rollback()
        for ev in results:
            fp = storage_root / ev.url
            await asyncio.to_thread(fp.unlink, missing_ok=True)
        raise

    return [
        {
            "id": str(ev.id),
            "avance_id": str(ev.avance_id),
            "nombre": ev.nombre,
            "tipo": ev.tipo,
            "url": ev.url,
            "descripcion": ev.descripcion,
            "tamano_original": ev.tamano_original,
            "tamano_almacenado": ev.tamano_almacenado,
            "optimizada": ev.optimizada,
            "created_at": ev.created_at.isoformat() if ev.created_at else None,
        }
        for ev in results
    ]


async def listar_evidencias(
    db: AsyncSession,
    avance_id: uuid.UUID,
    municipio_id: uuid.UUID,
) -> list[dict]:
    """Lista todas las evidencias (no eliminadas) de un avance."""
    avance = await _get_avance_or_404(db, avance_id, municipio_id)

    stmt = (
        select(Evidencia)
        .where(
            and_(
                Evidencia.avance_id == avance.id,
                Evidencia.deleted_at.is_(None),
            )
        )
        .order_by(Evidencia.created_at.asc())
    )
    result = await db.execute(stmt)
    evidencias = list(result.scalars().all())

    return [
        {
            "id": str(ev.id),
            "avance_id": str(ev.avance_id),
            "nombre": ev.nombre,
            "tipo": ev.tipo,
            "url": ev.url,
            "descripcion": ev.descripcion,
            "tamano_original": ev.tamano_original,
            "tamano_almacenado": ev.tamano_almacenado,
            "optimizada": ev.optimizada,
            "created_at": ev.created_at.isoformat() if ev.created_at else None,
        }
        for ev in evidencias
    ]


async def obtener_archivo_evidencia_por_id(
    db: AsyncSession,
    avance_id: uuid.UUID,
    evidencia_id: uuid.UUID,
    municipio_id: uuid.UUID,
    usuario_id: uuid.UUID,
    roles: list[str],
) -> tuple[Path, str, str]:
    """Resuelve la ruta de una evidencia específica por su id."""
    avance = await _get_avance_or_404(db, avance_id, municipio_id)

    stmt = select(Evidencia).where(
        and_(
            Evidencia.id == evidencia_id,
            Evidencia.avance_id == avance.id,
            Evidencia.deleted_at.is_(None),
        )
    )
    evidencia = await db.scalar(stmt)
    if not evidencia:
        raise ValueError("Evidencia no encontrada.")

    admin_roles = ("SUPERADMIN_PLATAFORMA", "ADMINISTRADOR_MUNICIPAL", "GESTOR_LIDER")
    is_admin = any(r in roles for r in admin_roles)
    if not is_admin and avance.registrado_por != usuario_id:
        gestor_stmt = select(GestorLider.id).where(
            and_(
                GestorLider.usuario_id == usuario_id,
                GestorLider.municipio_id == municipio_id,
                GestorLider.deleted_at.is_(None),
            )
        )
        gestor_id = await db.scalar(gestor_stmt)
        if gestor_id != avance.gestor_lider_id:
            raise PermissionError("No tiene permiso para ver esta evidencia.")

    file_path = Path(settings.STORAGE_PATH) / evidencia.url
    if not file_path.is_file():
        raise ValueError("El archivo de evidencia no existe en el almacenamiento.")

    filename = evidencia.nombre or file_path.name
    content_type = evidencia.tipo or "application/octet-stream"
    return file_path, filename, content_type


async def actualizar_descripcion_evidencia(
    db: AsyncSession,
    avance_id: uuid.UUID,
    evidencia_id: uuid.UUID,
    municipio_id: uuid.UUID,
    usuario_id: uuid.UUID,
    descripcion: str | None,
) -> dict:
    """Actualiza la descripción de una evidencia."""
    avance = await _get_avance_or_404(db, avance_id, municipio_id)
    await _check_evidence_permission(db, avance, usuario_id, municipio_id)

    stmt = select(Evidencia).where(
        and_(
            Evidencia.id == evidencia_id,
            Evidencia.avance_id == avance.id,
            Evidencia.deleted_at.is_(None),
        )
    )
    evidencia = await db.scalar(stmt)
    if not evidencia:
        raise ValueError("Evidencia no encontrada.")

    evidencia.descripcion = descripcion
    evidencia.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(evidencia)

    return {
        "id": str(evidencia.id),
        "descripcion": evidencia.descripcion,
    }


async def eliminar_evidencia(
    db: AsyncSession,
    avance_id: uuid.UUID,
    evidencia_id: uuid.UUID,
    municipio_id: uuid.UUID,
    usuario_id: uuid.UUID,
) -> dict:
    """Elimina lógicamente una evidencia y borra el archivo del disco."""
    avance = await _get_avance_or_404(db, avance_id, municipio_id)
    await _check_evidence_permission(db, avance, usuario_id, municipio_id)

    stmt = select(Evidencia).where(
        and_(
            Evidencia.id == evidencia_id,
            Evidencia.avance_id == avance.id,
            Evidencia.deleted_at.is_(None),
        )
    )
    evidencia = await db.scalar(stmt)
    if not evidencia:
        raise ValueError("Evidencia no encontrada.")

    # Borrar archivo del disco
    storage_root = Path(settings.STORAGE_PATH)
    file_path = storage_root / evidencia.url
    try:
        resolved = file_path.resolve()
        if resolved.is_relative_to(storage_root.resolve()):
            await asyncio.to_thread(resolved.unlink, missing_ok=True)
    except OSError:
        pass

    evidencia.soft_delete(usuario_id)

    # Si la evidencia denormalizada del avance era esta, actualizar
    if avance.evidencia_url == evidencia.url:
        remaining_stmt = (
            select(Evidencia)
            .where(
                and_(
                    Evidencia.avance_id == avance.id,
                    Evidencia.deleted_at.is_(None),
                )
            )
            .order_by(Evidencia.created_at.desc())
            .limit(1)
        )
        remaining = await db.scalar(remaining_stmt)
        if remaining:
            avance.evidencia_url = remaining.url
            avance.evidencia_nombre = remaining.nombre
            avance.evidencia_tipo = remaining.tipo
        else:
            avance.evidencia_url = None
            avance.evidencia_nombre = None
            avance.evidencia_tipo = None

    avance.updated_at = datetime.now(UTC)

    audit = AuditService(db)
    await audit.log_event(
        evento_tipo="EVIDENCIA_ELIMINADA",
        resultado="EXITOSO",
        municipio_id=municipio_id,
        usuario_id=usuario_id,
        recurso_tipo="AvanceProducto",
        recurso_id=avance.id,
        metadata={"evidencia_id": str(evidencia.id), "evidencia_nombre": evidencia.nombre},
    )

    await db.commit()

    return {"id": str(evidencia.id), "eliminada": True}
