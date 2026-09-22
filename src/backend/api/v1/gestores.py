"""
Rutas API - Gestores Líderes
============================
Endpoints para la gestión completa del módulo de Gestores Líderes de SIGEM Colombia.

Incluye operaciones CRUD, asignación de rol y dependencias (permisos),
activación/desactivación, bloqueo/desbloqueo, restablecimiento de contraseñas,
eliminación lógica y consulta de accesos/auditoría.

Autor: SIGEM Colombia
Versión: 1.1
Fecha: 2026-09-20
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from ...core.database import get_db
from ...core.rbac import require_permission
from ...api.v1.auth import get_current_user_from_token
from ...services.gestor_service import (
    create_gestor as svc_create,
    list_gestores as svc_list,
    get_gestor as svc_get,
    update_gestor as svc_update,
    update_gestor_permissions as svc_update_permissions,
    activate_gestor as svc_activate,
    deactivate_gestor as svc_deactivate,
    block_gestor as svc_block,
    unblock_gestor as svc_unblock,
    reset_password as svc_reset_password,
    soft_delete_gestor as svc_soft_delete,
    list_gestor_accesos as svc_list_accesos,
)
from ...services.audit_service import AuditService
from ...schemas.gestor import (
    GestorCreate,
    GestorUpdate,
    GestorPermisosUpdate,
    GestorAccion,
    GestorResponse,
    GestorListResponse,
    GestorPasswordReset,
    GestorAccesoResponse,
)

router = APIRouter(prefix="/gestores", tags=["Gestores"])


# ---------------------------------------------------------------------------
# POST /gestores - Crear gestor
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=GestorPasswordReset,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo gestor líder",
    description=(
        "Crea un nuevo gestor líder. El ID, el usuario y la contraseña temporal "
        "se generan automáticamente. La contraseña se retorna una sola vez."
    ),
)
async def create_gestor(
    gestor_data: GestorCreate,
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "gestor.crear")

    user = current_user["user"]
    municipio_id = current_user["municipio_id"]

    try:
        result = await svc_create(
            db=db,
            municipio_id=UUID(municipio_id),
            create_data=gestor_data.model_dump(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al crear el gestor líder",
        )

    return GestorPasswordReset(
        nueva_password_temporal=result["temp_password"],
        id=result["id"],
        codigo=result["codigo"],
        username=result["username"],
    )


# ---------------------------------------------------------------------------
# GET /gestores - Listar gestores con filtros
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=GestorListResponse,
    summary="Listar gestores líderes",
    description=(
        "Retorna una lista paginada de gestores líderes con filtros opcionales "
        "por búsqueda, estado, cargo y rol."
    ),
)
async def list_gestores(
    search: Optional[str] = Query(None, description="Búsqueda por nombre, username, email o código"),
    cargo: Optional[str] = Query(None, description="Filtrar por cargo"),
    rol_id: Optional[UUID] = Query(None, description="Filtrar por rol"),
    estado: Optional[str] = Query(None, description="Filtrar por estado (ACTIVO, INACTIVO, BLOQUEADO)"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(20, ge=1, le=100, description="Elementos por página"),
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "gestor.ver")

    municipio_id = current_user["municipio_id"]

    result = await svc_list(
        db=db,
        municipio_id=UUID(municipio_id),
        filtros={
            "search": search,
            "cargo": cargo,
            "rol_id": str(rol_id) if rol_id else None,
            "estado": estado,
            "page": page,
            "page_size": page_size,
        },
    )

    return GestorListResponse(
        items=result["gestores"],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
    )


# ---------------------------------------------------------------------------
# GET /gestores/{gestor_id} - Obtener detalle de gestor
# ---------------------------------------------------------------------------

@router.get(
    "/{gestor_id}",
    response_model=GestorResponse,
    summary="Obtener detalle de un gestor líder",
)
async def get_gestor(
    gestor_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "gestor.ver")

    municipio_id = current_user["municipio_id"]

    result = await svc_get(
        db=db,
        municipio_id=UUID(municipio_id),
        gestor_id=gestor_id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gestor líder no encontrado",
        )

    return GestorResponse(**result)


# ---------------------------------------------------------------------------
# PUT /gestores/{gestor_id} - Actualizar gestor
# ---------------------------------------------------------------------------

@router.put(
    "/{gestor_id}",
    response_model=GestorResponse,
    summary="Actualizar gestor líder",
)
async def update_gestor(
    gestor_id: UUID,
    gestor_data: GestorUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "gestor.editar")

    municipio_id = current_user["municipio_id"]

    result = await svc_update(
        db=db,
        municipio_id=UUID(municipio_id),
        gestor_id=gestor_id,
        update_data=gestor_data.model_dump(exclude_unset=True),
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gestor líder no encontrado",
        )

    return GestorResponse(**result)


# ---------------------------------------------------------------------------
# POST /gestores/{gestor_id}/permisos - Asignar rol y dependencias
# ---------------------------------------------------------------------------

@router.post(
    "/{gestor_id}/permisos",
    response_model=GestorResponse,
    summary="Asignar rol y dependencias al gestor líder",
    description=(
        "Actualiza el rol y las dependencias asociadas (principal y adicionales) "
        "de un gestor líder. Permiso requerido: gestor.permisos."
    ),
)
async def update_gestor_permissions(
    gestor_id: UUID,
    permisos_data: GestorPermisosUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "gestor.permisos")

    municipio_id = current_user["municipio_id"]

    try:
        result = await svc_update_permissions(
            db=db,
            municipio_id=UUID(municipio_id),
            gestor_id=gestor_id,
            permisos=permisos_data.model_dump(exclude_unset=True),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gestor líder no encontrado",
        )

    return GestorResponse(**result)


# ---------------------------------------------------------------------------
# POST /gestores/{gestor_id}/activate - Activar gestor
# ---------------------------------------------------------------------------

@router.post(
    "/{gestor_id}/activate",
    response_model=GestorResponse,
    summary="Activar gestor líder",
)
async def activate_gestor(
    gestor_id: UUID,
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "gestor.activar")

    municipio_id = current_user["municipio_id"]

    result = await svc_activate(
        db=db,
        municipio_id=UUID(municipio_id),
        gestor_id=gestor_id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gestor líder no encontrado",
        )

    return GestorResponse(**result)


# ---------------------------------------------------------------------------
# POST /gestores/{gestor_id}/deactivate - Desactivar gestor
# ---------------------------------------------------------------------------

@router.post(
    "/{gestor_id}/deactivate",
    response_model=GestorResponse,
    summary="Desactivar gestor líder",
)
async def deactivate_gestor(
    gestor_id: UUID,
    accion_data: Optional[GestorAccion] = None,
    request: Request = None,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "gestor.desactivar")

    municipio_id = current_user["municipio_id"]

    result = await svc_deactivate(
        db=db,
        municipio_id=UUID(municipio_id),
        gestor_id=gestor_id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gestor líder no encontrado",
        )

    return GestorResponse(**result)


# ---------------------------------------------------------------------------
# POST /gestores/{gestor_id}/block - Bloquear gestor
# ---------------------------------------------------------------------------

@router.post(
    "/{gestor_id}/block",
    response_model=GestorResponse,
    summary="Bloquear gestor líder",
    description="Bloquea un gestor líder. El motivo es obligatorio.",
)
async def block_gestor(
    gestor_id: UUID,
    accion_data: GestorAccion,
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "gestor.bloquear")

    if not accion_data.motivo or not accion_data.motivo.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El motivo del bloqueo es obligatorio",
        )

    municipio_id = current_user["municipio_id"]

    try:
        result = await svc_block(
            db=db,
            municipio_id=UUID(municipio_id),
            gestor_id=gestor_id,
            motivo=accion_data.motivo.strip(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gestor líder no encontrado",
        )

    return GestorResponse(**result)


# ---------------------------------------------------------------------------
# POST /gestores/{gestor_id}/unblock - Desbloquear gestor
# ---------------------------------------------------------------------------

@router.post(
    "/{gestor_id}/unblock",
    response_model=GestorResponse,
    summary="Desbloquear gestor líder",
)
async def unblock_gestor(
    gestor_id: UUID,
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "gestor.desbloquear")

    municipio_id = current_user["municipio_id"]

    result = await svc_unblock(
        db=db,
        municipio_id=UUID(municipio_id),
        gestor_id=gestor_id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gestor líder no encontrado",
        )

    return GestorResponse(**result)


# ---------------------------------------------------------------------------
# POST /gestores/{gestor_id}/reset-password - Restablecer contraseña
# ---------------------------------------------------------------------------

@router.post(
    "/{gestor_id}/reset-password",
    response_model=GestorPasswordReset,
    summary="Restablecer contraseña del gestor",
    description=(
        "Genera una nueva contraseña temporal. La contraseña se muestra una sola vez."
    ),
)
async def reset_password(
    gestor_id: UUID,
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "gestor.permisos")

    municipio_id = current_user["municipio_id"]

    result = await svc_reset_password(
        db=db,
        municipio_id=UUID(municipio_id),
        gestor_id=gestor_id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gestor líder no encontrado",
        )

    return GestorPasswordReset(
        nueva_password_temporal=result["temp_password"],
    )


# ---------------------------------------------------------------------------
# DELETE /gestores/{gestor_id} - Eliminación lógica
# ---------------------------------------------------------------------------

@router.delete(
    "/{gestor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar gestor líder (lógicamente)",
    description="Realiza la eliminación lógica de un gestor líder.",
)
async def delete_gestor(
    gestor_id: UUID,
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "gestor.eliminar")

    municipio_id = current_user["municipio_id"]

    result = await svc_soft_delete(
        db=db,
        municipio_id=UUID(municipio_id),
        gestor_id=gestor_id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gestor líder no encontrado",
        )

    return None


# ---------------------------------------------------------------------------
# GET /gestores/{gestor_id}/accesos - Historial de accesos del gestor
# ---------------------------------------------------------------------------

@router.get(
    "/{gestor_id}/accesos",
    response_model=List[GestorAccesoResponse],
    summary="Historial de accesos del gestor",
    description=(
        "Retorna los intentos de acceso (exitosos y fallidos) de un gestor líder "
        "con fecha/hora, IP, agente y razón del fallo."
    ),
)
async def get_gestor_accesos(
    gestor_id: UUID,
    limit: int = Query(50, ge=1, le=200, description="Número máximo de accesos"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación"),
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "auditoria.ver")

    municipio_id = current_user["municipio_id"]

    result = await svc_list_accesos(
        db=db,
        municipio_id=UUID(municipio_id),
        gestor_id=gestor_id,
        limit=limit,
        offset=offset,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gestor líder no encontrado",
        )

    return [GestorAccesoResponse(**item) for item in result]


# ---------------------------------------------------------------------------
# GET /gestores/{gestor_id}/audit - Eventos de auditoría del gestor
# ---------------------------------------------------------------------------

@router.get(
    "/{gestor_id}/audit",
    summary="Obtener eventos de auditoría del gestor",
    description="Retorna la lista de eventos de auditoría asociados a un gestor líder.",
)
async def get_gestor_audit_events(
    gestor_id: UUID,
    limit: int = Query(100, ge=1, le=500, description="Número máximo de eventos"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación"),
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "auditoria.ver")

    municipio_id = current_user["municipio_id"]

    audit_service = AuditService(db)
    events = await audit_service.get_events(
        municipio_id=UUID(municipio_id),
        limit=limit,
        offset=offset,
        recurso_id=gestor_id,
        recurso_tipo="GestorLider",
    )

    return [
        {
            "id": str(event.id),
            "evento_tipo": event.evento_tipo,
            "resultado": event.resultado,
            "recurso_tipo": event.recurso_tipo,
            "recurso_id": str(event.recurso_id) if event.recurso_id else None,
            "ip_address": event.ip_address,
            "user_agent": event.user_agent,
            "metadata": event.metadata_json,
            "fecha_evento": event.fecha_evento.isoformat() if event.fecha_evento else None,
        }
        for event in events
    ]
