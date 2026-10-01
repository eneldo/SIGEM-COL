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

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.v1.auth import get_current_user_from_token
from ...core.database import get_db
from ...core.rbac import require_permission
from ...schemas.gestor import (
    GestorAccesoResponse,
    GestorAccion,
    GestorCreate,
    GestorListResponse,
    GestorPasswordReset,
    GestorPasswordUpdate,
    GestorPermisosUpdate,
    GestorResponse,
    GestorUpdate,
)
from ...services.audit_service import AuditService
from ...services.gestor_service import (
    activate_gestor as svc_activate,
)
from ...services.gestor_service import (
    block_gestor as svc_block,
)
from ...services.gestor_service import (
    create_gestor as svc_create,
)
from ...services.gestor_service import (
    deactivate_gestor as svc_deactivate,
)
from ...services.gestor_service import (
    get_gestor as svc_get,
)
from ...services.gestor_service import (
    list_gestor_accesos as svc_list_accesos,
)
from ...services.gestor_service import (
    list_gestores as svc_list,
)
from ...services.gestor_service import (
    reset_password as svc_reset_password,
)
from ...services.gestor_service import (
    soft_delete_gestor as svc_soft_delete,
)
from ...services.gestor_service import (
    unblock_gestor as svc_unblock,
)
from ...services.gestor_service import (
    update_gestor as svc_update,
)
from ...services.gestor_service import (
    update_gestor_permissions as svc_update_permissions,
)

router = APIRouter(prefix="/gestores", tags=["Gestores"])

ADMIN_ROLE_CODES = {"SUPERADMIN_PLATAFORMA", "ADMINISTRADOR_MUNICIPAL"}


def _allowed_role_codes(current_user: dict) -> set[str] | None:
    """Administradores: cualquier rol. Coordinadores al crear: solo GESTOR."""
    role_codes = set(current_user.get("roles") or [])
    if role_codes & ADMIN_ROLE_CODES:
        return None
    return {"GESTOR"}


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

    municipio_id = current_user["municipio_id"]

    try:
        result = await svc_create(
            db=db,
            municipio_id=UUID(municipio_id),
            create_data=gestor_data.model_dump(),
            allowed_role_codes=_allowed_role_codes(current_user),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al crear el gestor líder",
        ) from exc

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
    search: str | None = Query(None, description="Búsqueda por nombre, username, email o código"),
    cargo: str | None = Query(None, description="Filtrar por cargo"),
    rol_id: UUID | None = Query(None, description="Filtrar por rol"),
    estado: str | None = Query(
        None, description="Filtrar por estado (ACTIVO, INACTIVO, BLOQUEADO)"
    ),
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
        ) from e

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
    request: Request,
    accion_data: GestorAccion | None = None,
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
        ) from e

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
    summary="Cambiar/restablecer contraseña del gestor",
    description=(
        "Si se envía `nueva_password` se establece esa contraseña; "
        "si se omite se genera una contraseña temporal. "
        "En ambos casos la contraseña se retorna una sola vez."
    ),
)
async def reset_password(
    gestor_id: UUID,
    request: Request,
    body: GestorPasswordUpdate | None = None,
    current_user: dict = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    await require_permission(db, current_user["user"].id, "gestor.permisos")

    municipio_id = current_user["municipio_id"]

    try:
        result = await svc_reset_password(
            db=db,
            municipio_id=UUID(municipio_id),
            gestor_id=gestor_id,
            nueva_password=body.nueva_password if body else None,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gestor líder no encontrado",
        )

    return GestorPasswordReset(
        nueva_password_temporal=result["temp_password"],
        id=result.get("id"),
        codigo=result.get("codigo"),
        username=result.get("username"),
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
    response_model=list[GestorAccesoResponse],
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
