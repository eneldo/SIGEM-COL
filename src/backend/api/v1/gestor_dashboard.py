"""
Rutas API - Dashboard del Gestor
================================
Endpoints para que los gestores líderes vean sus productos asignados,
registren avances y revisen avances de su equipo.

Autor: SIGEM Colombia
Versión: 1.0
Fecha: 2026-09-21
"""

import logging
from pathlib import PurePath
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.v1.auth import get_current_user_from_token
from ...core.database import get_db
from ...models.gestor_lider import GestorLider
from ...services.avance_service import (
    actualizar_avance,
    actualizar_descripcion_evidencia,
    agregar_evidencias,
    eliminar_avance,
    eliminar_evidencia,
    get_avances_para_revision,
    get_avances_producto,
    get_estadisticas_revision,
    get_mis_productos,
    get_resumen_avances,
    guardar_evidencia,
    listar_evidencias,
    obtener_archivo_evidencia,
    obtener_archivo_evidencia_por_id,
    registrar_avance,
    revisar_avance,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gestor/dashboard", tags=["Gestor Dashboard"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class AvanceCreate(BaseModel):
    avance_porcentaje: float = Field(..., ge=0, le=100, description="Porcentaje de avance (0-100)")
    avance_valor: int | None = Field(None, ge=0, description="Valor numérico del avance")
    observaciones: str | None = Field(None, max_length=1000, description="Observaciones del avance")
    evidencia_url: str | None = Field(None, max_length=500, description="URL de evidencia")
    indicador: str | None = Field(None, max_length=300, description="Indicador del producto")
    periodo: str | None = Field(None, max_length=50, description="Periodo del avance")
    estado_revision: str | None = Field("PENDIENTE", description="Estado de revisión")
    evidencia_nombre: str | None = Field(
        None, max_length=255, description="Nombre del archivo de evidencia"
    )
    evidencia_tipo: str | None = Field(None, max_length=50, description="Tipo MIME del archivo")


class AvanceUpdate(BaseModel):
    avance_porcentaje: float | None = Field(
        None, ge=0, le=100, description="Porcentaje de avance (0-100)"
    )
    avance_valor: int | None = Field(None, ge=0, description="Valor numérico del avance")
    observaciones: str | None = Field(None, max_length=1000, description="Observaciones del avance")
    indicador: str | None = Field(None, max_length=300, description="Indicador del producto")
    periodo: str | None = Field(None, max_length=50, description="Periodo del avance")
    estado_revision: str | None = Field(None, description="Estado de revisión")


class AvanceResponse(BaseModel):
    id: str
    producto_id: str
    avance_porcentaje: float
    avance_valor: int | None
    observaciones: str | None
    evidencia_url: str | None
    indicador: str | None
    periodo: str | None
    fecha_registro: str | None
    estado_revision: str
    evidencia_nombre: str | None
    evidencia_tipo: str | None
    observaciones_revision: str | None = None
    estado: str
    created_at: str | None


class ProductoAsignado(BaseModel):
    id: str
    codigo: str
    nombre: str
    indicador: str | None
    codigo_indicador: str | None
    meta_redactada: str | None
    linea_base: int | None
    meta_cuatrienio: int | None
    unidad_medida: str | None
    estado: str


class ResumenAvances(BaseModel):
    total_productos: int
    productos_con_avance: int
    avance_promedio: float
    productos_completados: int


class AvanceRevisionResponse(BaseModel):
    id: str
    producto_id: str
    producto_codigo: str
    producto_nombre: str
    codigo_indicador: str | None
    indicador: str | None
    gestor_id: str
    gestor_codigo: str
    gestor_nombre: str
    avance_porcentaje: float
    avance_valor: int | None
    periodo: str | None
    fecha_registro: str | None
    estado_revision: str
    evidencia_nombre: str | None
    evidencia_tipo: str | None
    evidencia_url: str | None
    observaciones: str | None
    observaciones_revision: str | None = None
    created_at: str | None


class EstadisticasRevision(BaseModel):
    pendientes: int
    aprobados_semana: int
    devueltos: int


class RevisionAvanceRequest(BaseModel):
    nuevo_estado: str = Field(..., description="APROBADO o RECHAZADO")
    observacion: str | None = Field(
        None, max_length=1000, description="Observación (obligatoria si se devuelve)"
    )


class EvidenciaResponse(BaseModel):
    id: str
    avance_id: str
    nombre: str
    tipo: str
    url: str
    descripcion: str | None = None
    tamano_original: int | None = None
    tamano_almacenado: int | None = None
    optimizada: bool = False
    created_at: str | None = None


class EvidenciaDescripcionUpdate(BaseModel):
    descripcion: str | None = Field(
        None, max_length=1000, description="Descripción de la evidencia"
    )


ALLOWED_EVIDENCE_TYPES = {
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
    "application/pdf": {".pdf"},
}
MAX_EVIDENCE_BYTES = 10 * 1024 * 1024  # 10 MB


def _valid_evidence_signature(content_type: str, content: bytes) -> bool:
    if content_type == "image/jpeg":
        return content.startswith(b"\xff\xd8\xff")
    if content_type == "image/png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "application/pdf":
        return content.startswith(b"%PDF-")
    return False


# ---------------------------------------------------------------------------
# Helper: obtener gestor_lider_id del usuario actual
# ---------------------------------------------------------------------------


async def _get_gestor_lider_id(db, user, municipio_id):
    gestor_stmt = select(GestorLider.id).where(
        and_(
            GestorLider.usuario_id == UUID(str(user.id)),
            GestorLider.municipio_id == municipio_id,
            GestorLider.deleted_at.is_(None),
        )
    )
    return await db.scalar(gestor_stmt)


async def _require_revision_access(db, current_user) -> UUID | None:
    """Only admins and gestor líderes may review avances.

    Returns the gestor_lider_id scope (None for admins, who see everything).
    """
    roles = current_user.get("roles", [])
    if "SUPERADMIN_PLATAFORMA" in roles or "ADMINISTRADOR_MUNICIPAL" in roles:
        return None

    if "GESTOR_LIDER" in roles:
        user = current_user.get("user")
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no autenticado",
            )
        gestor_lider_id = await _get_gestor_lider_id(db, user, UUID(current_user["municipio_id"]))
        if gestor_lider_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No existe un gestor líder asociado al usuario actual.",
            )
        return gestor_lider_id

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Permiso requerido: avance.revisar",
    )


# ---------------------------------------------------------------------------
# Static routes FIRST (before /avances/{producto_id})
# ---------------------------------------------------------------------------


@router.get(
    "/mis-productos",
    response_model=list[ProductoAsignado],
    summary="Obtener productos asignados al gestor",
)
async def obtener_mis_productos(
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user = current_user.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado"
        )

    productos = await get_mis_productos(
        db=db,
        usuario_id=UUID(str(user.id)),
        municipio_id=UUID(current_user["municipio_id"]),
    )
    return [ProductoAsignado(**p) for p in productos]


@router.get(
    "/resumen",
    response_model=ResumenAvances,
    summary="Resumen de avances del gestor",
)
async def obtener_resumen_avances(
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user = current_user.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado"
        )

    resumen = await get_resumen_avances(
        db=db,
        usuario_id=UUID(str(user.id)),
        municipio_id=UUID(current_user["municipio_id"]),
    )
    return ResumenAvances(**resumen)


# ---------------------------------------------------------------------------
# Revision routes (static, before /avances/{producto_id})
# ---------------------------------------------------------------------------


@router.get(
    "/revision/avances",
    response_model=list[AvanceRevisionResponse],
    summary="Obtener avances para revisión",
)
async def obtener_avances_revision(
    estado: str | None = None,
    search: str | None = None,
    periodo: str | None = None,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user = current_user.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado"
        )

    municipio_id = UUID(current_user["municipio_id"])
    gestor_lider_id = await _require_revision_access(db, current_user)

    avances = await get_avances_para_revision(
        db=db,
        municipio_id=municipio_id,
        gestor_lider_id=gestor_lider_id,
        estado_revision=estado,
        search=search,
    )

    if periodo:
        avances = [a for a in avances if a.get("periodo") == periodo]

    return [AvanceRevisionResponse(**a) for a in avances]


@router.get(
    "/revision/estadisticas",
    response_model=EstadisticasRevision,
    summary="Estadísticas de revisión de avances",
)
async def obtener_estadisticas_revision(
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user = current_user.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado"
        )

    municipio_id = UUID(current_user["municipio_id"])
    gestor_lider_id = await _require_revision_access(db, current_user)

    stats = await get_estadisticas_revision(
        db=db,
        municipio_id=municipio_id,
        gestor_lider_id=gestor_lider_id,
    )
    return EstadisticasRevision(**stats)


@router.patch(
    "/revision/{avance_id}",
    response_model=dict,
    summary="Revisar avance (aprobar o devolver)",
)
async def revisar_avance_endpoint(
    avance_id: UUID,
    data: RevisionAvanceRequest,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user = current_user.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado"
        )

    gestor_lider_id = await _require_revision_access(db, current_user)

    try:
        result = await revisar_avance(
            db=db,
            avance_id=avance_id,
            municipio_id=UUID(current_user["municipio_id"]),
            usuario_id=UUID(str(user.id)),
            gestor_lider_id=gestor_lider_id,
            nuevo_estado=data.nuevo_estado,
            observacion=data.observacion,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
    except Exception as exc:
        logger.exception("Error interno al revisar avance")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al revisar el avance",
        ) from exc

    return result


# ---------------------------------------------------------------------------
# POST /avances - Registrar avance (static, before /avances/{producto_id})
# ---------------------------------------------------------------------------


@router.post(
    "/avances",
    response_model=AvanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar avance en un producto",
)
async def crear_avance(
    avance_data: AvanceCreate,
    producto_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user = current_user.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado"
        )

    try:
        result = await registrar_avance(
            db=db,
            usuario_id=UUID(str(user.id)),
            municipio_id=UUID(current_user["municipio_id"]),
            producto_id=producto_id,
            avance_data=avance_data.model_dump(),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
    except Exception as exc:
        logger.exception("Error interno al registrar avance")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al registrar el avance",
        ) from exc

    return AvanceResponse(**result)


# ---------------------------------------------------------------------------
# Dynamic routes LAST
# ---------------------------------------------------------------------------


@router.put(
    "/avances/{avance_id}",
    response_model=AvanceResponse,
    summary="Actualizar un avance existente",
)
async def editar_avance(
    avance_id: UUID,
    avance_data: AvanceUpdate,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user = current_user.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado"
        )

    payload = avance_data.model_dump(exclude_unset=True)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No se enviaron campos para actualizar.",
        )

    try:
        result = await actualizar_avance(
            db=db,
            avance_id=avance_id,
            municipio_id=UUID(current_user["municipio_id"]),
            usuario_id=UUID(str(user.id)),
            avance_data=payload,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as exc:
        logger.exception("Error interno al actualizar avance")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al actualizar el avance",
        ) from exc

    return AvanceResponse(**result)


@router.delete(
    "/avances/{avance_id}",
    response_model=dict,
    summary="Eliminar un avance (soft delete)",
)
async def borrar_avance(
    avance_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user = current_user.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado"
        )

    try:
        result = await eliminar_avance(
            db=db,
            avance_id=avance_id,
            municipio_id=UUID(current_user["municipio_id"]),
            usuario_id=UUID(str(user.id)),
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as exc:
        logger.exception("Error interno al eliminar avance")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al eliminar el avance",
        ) from exc

    return result


@router.get(
    "/avances/{producto_id}",
    response_model=list[AvanceResponse],
    summary="Obtener avances de un producto",
)
async def obtener_avances_producto(
    producto_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user = current_user.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado"
        )

    avances = await get_avances_producto(
        db=db,
        producto_id=producto_id,
        municipio_id=UUID(current_user["municipio_id"]),
    )
    return [AvanceResponse(**a) for a in avances]


# ---------------------------------------------------------------------------
# Evidencia: subir y descargar archivo
# ---------------------------------------------------------------------------


@router.post(
    "/avances/{avance_id}/evidencia",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Subir evidencia de un avance",
)
async def subir_evidencia(
    avance_id: UUID,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user = current_user.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado"
        )

    content_type = file.content_type or ""
    if content_type not in ALLOWED_EVIDENCE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Solo se permiten archivos JPG, PNG o PDF.",
        )

    filename = (file.filename or "").replace("\\", "/")
    filename = PurePath(filename).name
    extension = PurePath(filename).suffix.lower()
    if not filename or extension not in ALLOWED_EVIDENCE_TYPES[content_type]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La extensión del archivo no corresponde a un formato permitido.",
        )

    content = await file.read(MAX_EVIDENCE_BYTES + 1)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El archivo está vacío.",
        )
    if len(content) > MAX_EVIDENCE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="El archivo no puede superar 10 MB.",
        )
    if not _valid_evidence_signature(content_type, content):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El contenido del archivo no corresponde al tipo declarado.",
        )

    try:
        result = await guardar_evidencia(
            db=db,
            avance_id=avance_id,
            municipio_id=UUID(current_user["municipio_id"]),
            usuario_id=UUID(str(user.id)),
            content=content,
            filename=filename,
            content_type=content_type,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
    except Exception as exc:
        logger.exception("Error al subir evidencia")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al subir la evidencia"
        ) from exc

    return result


@router.get(
    "/avances/{avance_id}/evidencia",
    summary="Descargar evidencia de un avance",
)
async def descargar_evidencia(
    avance_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user = current_user.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado"
        )

    roles = current_user.get("roles", [])
    try:
        path, filename, content_type = await obtener_archivo_evidencia(
            db=db,
            avance_id=avance_id,
            municipio_id=UUID(current_user["municipio_id"]),
            usuario_id=UUID(str(user.id)),
            roles=roles,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    return FileResponse(
        path=str(path),
        media_type=content_type,
        filename=filename,
    )


# ---------------------------------------------------------------------------
# Evidencias múltiples: subir, listar, descargar, editar, eliminar
# ---------------------------------------------------------------------------


def _validate_evidence_file(file: UploadFile) -> tuple[str, bytes]:
    content_type = file.content_type or ""
    if content_type not in ALLOWED_EVIDENCE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Solo se permiten archivos JPG, PNG o PDF.",
        )
    filename = (file.filename or "").replace("\\", "/")
    filename = PurePath(filename).name
    extension = PurePath(filename).suffix.lower()
    if not filename or extension not in ALLOWED_EVIDENCE_TYPES[content_type]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La extensión del archivo no corresponde a un formato permitido.",
        )
    content = file.file.read(MAX_EVIDENCE_BYTES + 1)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El archivo está vacío.",
        )
    if len(content) > MAX_EVIDENCE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="El archivo no puede superar 10 MB.",
        )
    if not _valid_evidence_signature(content_type, content):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El contenido del archivo no corresponde al tipo declarado.",
        )
    return filename, content


@router.post(
    "/avances/{avance_id}/evidencias",
    response_model=list[EvidenciaResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Subir una o más evidencias a un avance",
)
async def subir_evidencias(
    avance_id: UUID,
    files: list[UploadFile] = File(...),
    descripcion: str | None = Form(None),
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user = current_user.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado"
        )

    if len(files) > 4:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Se permiten máximo 4 evidencias por avance.",
        )

    archivos = []
    for file in files:
        filename, content = _validate_evidence_file(file)
        archivos.append(
            {
                "content": content,
                "filename": filename,
                "content_type": file.content_type or "",
                "descripcion": descripcion,
            }
        )

    try:
        results = await agregar_evidencias(
            db=db,
            avance_id=avance_id,
            municipio_id=UUID(current_user["municipio_id"]),
            usuario_id=UUID(str(user.id)),
            archivos=archivos,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
    except Exception as exc:
        logger.exception("Error al subir evidencias")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al subir las evidencias",
        ) from exc

    return [EvidenciaResponse(**r) for r in results]


@router.get(
    "/avances/{avance_id}/evidencias",
    response_model=list[EvidenciaResponse],
    summary="Listar evidencias de un avance",
)
async def obtener_evidencias(
    avance_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user = current_user.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado"
        )

    try:
        evidencias = await listar_evidencias(
            db=db,
            avance_id=avance_id,
            municipio_id=UUID(current_user["municipio_id"]),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    return [EvidenciaResponse(**e) for e in evidencias]


@router.get(
    "/avances/{avance_id}/evidencias/{evidencia_id}",
    summary="Descargar una evidencia específica",
)
async def descargar_evidencia_por_id(
    avance_id: UUID,
    evidencia_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user = current_user.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado"
        )

    roles = current_user.get("roles", [])
    try:
        path, filename, content_type = await obtener_archivo_evidencia_por_id(
            db=db,
            avance_id=avance_id,
            evidencia_id=evidencia_id,
            municipio_id=UUID(current_user["municipio_id"]),
            usuario_id=UUID(str(user.id)),
            roles=roles,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    return FileResponse(
        path=str(path),
        media_type=content_type,
        filename=filename,
    )


@router.put(
    "/avances/{avance_id}/evidencias/{evidencia_id}",
    response_model=dict,
    summary="Actualizar descripción de una evidencia",
)
async def actualizar_evidencia(
    avance_id: UUID,
    evidencia_id: UUID,
    data: EvidenciaDescripcionUpdate,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user = current_user.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado"
        )

    try:
        result = await actualizar_descripcion_evidencia(
            db=db,
            avance_id=avance_id,
            evidencia_id=evidencia_id,
            municipio_id=UUID(current_user["municipio_id"]),
            usuario_id=UUID(str(user.id)),
            descripcion=data.descripcion,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    return result


@router.delete(
    "/avances/{avance_id}/evidencias/{evidencia_id}",
    response_model=dict,
    summary="Eliminar una evidencia",
)
async def borrar_evidencia(
    avance_id: UUID,
    evidencia_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    user = current_user.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autenticado"
        )

    try:
        result = await eliminar_evidencia(
            db=db,
            avance_id=avance_id,
            evidencia_id=evidencia_id,
            municipio_id=UUID(current_user["municipio_id"]),
            usuario_id=UUID(str(user.id)),
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    return result
