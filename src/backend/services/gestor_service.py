"""
Servicio de Gestión de Gestores Líderes - SIGEM Colombia
======================================================

Proporciona operaciones CRUD y de gestión para el módulo de Gestores Líderes,
incluyendo creación (con código, usuario y contraseña generados por el sistema),
listado, actualización, asignación de roles y dependencias (permisos),
activación/desactivación, bloqueo/desbloqueo, restablecimiento de contraseñas,
eliminación lógica y consulta de accesos/auditoría.

Autor: SIGEM Colombia
Versión: 1.1
Fecha: 2026-09-20
"""

import re
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.security import generate_temporary_password, get_password_hash
from ..models.dependencia import Dependencia
from ..models.gestor_lider import GestorLider
from ..models.intento_login import IntentoLogin
from ..models.rol import Rol
from ..models.usuario import Usuario
from ..models.usuario_dependencia import UsuarioDependencia
from ..models.usuario_rol import UsuarioRol
from ..services.audit_service import AuditService
from ..services.auth_service import AuthService

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

ROL_GESTOR_LIDER = "GESTOR_LIDER"
CODIGO_PREFIJO = "GES-"
CODIGO_LONGITUD_NUMERICA = 6
PASSWORD_LONGITUD = 24
PASSWORD_MIN_LENGTH = 15
ESTADO_ACTIVO = "ACTIVO"
ESTADO_INACTIVO = "INACTIVO"
ESTADO_BLOQUEADO = "BLOQUEADO"
USERNAME_RE = re.compile(r"^[a-zA-Z0-9._-]{3,50}$")
ROLES_NO_ASIGNABLES_POR_COORDINADOR = {
    "SUPERADMIN_PLATAFORMA",
    "ADMINISTRADOR_MUNICIPAL",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_gestor_usuario(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    gestor_id: uuid.UUID,
) -> tuple[GestorLider, Usuario] | tuple[None, None]:
    """Obtiene el gestor y su usuario asociado dentro del municipio."""
    stmt = (
        select(GestorLider, Usuario)
        .join(Usuario, GestorLider.usuario_id == Usuario.id)
        .where(
            and_(
                GestorLider.id == gestor_id,
                GestorLider.municipio_id == municipio_id,
                GestorLider.deleted_at.is_(None),
                Usuario.deleted_at.is_(None),
            )
        )
    )
    result = await db.execute(stmt)
    row = result.first()
    if row is None:
        return None, None
    return row[0], row[1]


async def _get_roles(db: AsyncSession, usuario_id: uuid.UUID) -> list[Rol]:
    stmt = (
        select(Rol)
        .join(UsuarioRol, UsuarioRol.rol_id == Rol.id)
        .where(UsuarioRol.usuario_id == usuario_id)
        .order_by(Rol.nivel.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _get_dependencias(
    db: AsyncSession, usuario_id: uuid.UUID
) -> list[tuple[uuid.UUID, str, str, bool]]:
    """Retorna (dependencia_id, nombre, codigo, es_principal) del usuario."""
    stmt = (
        select(
            Dependencia.id,
            Dependencia.nombre,
            Dependencia.codigo,
            UsuarioDependencia.es_principal,
        )
        .join(
            Dependencia,
            Dependencia.id == UsuarioDependencia.dependencia_id,
        )
        .where(UsuarioDependencia.usuario_id == usuario_id)
        .order_by(Dependencia.nombre.asc())
    )
    result = await db.execute(stmt)
    return list(result.all())  # type: ignore[arg-type]


async def _build_gestor_dict(
    db: AsyncSession,
    gestor: GestorLider,
    usuario: Usuario,
) -> dict[str, Any]:
    """Construye el diccionario de respuesta completo de un gestor."""
    roles = await _get_roles(db, usuario.id)  # type: ignore[arg-type]
    deps = await _get_dependencias(db, usuario.id)  # type: ignore[arg-type]
    rol = next((r for r in roles if r.codigo == ROL_GESTOR_LIDER), roles[0] if roles else None)
    principal = next((d for d in deps if d[3]), None)

    return {
        "id": gestor.id,
        "codigo": gestor.codigo,
        "username": usuario.username,
        "email": usuario.email,
        "telefono": usuario.telefono,
        "nombre_completo": usuario.nombre_completo,
        "cargo": gestor.cargo,
        "rol": rol.nombre if rol else None,
        "rol_id": rol.id if rol else None,
        "roles": [r.codigo for r in roles],
        "dependencia_principal_id": gestor.dependencia_principal_id,
        "dependencia_principal": principal[1] if principal else None,
        "dependencias": [{"id": d[0], "nombre": d[1], "es_principal": d[3]} for d in deps],
        "estado": gestor.estado,
        "mfa_activo": usuario.mfa_activo,
        "must_change_password": usuario.must_change_password,
        "ultimo_acceso": usuario.ultimo_acceso,
        "ip_ultimo_acceso": usuario.ip_ultimo_acceso,
        "intentos_fallidos": usuario.intentos_fallidos,
        "ultimo_cambio_password": usuario.ultimo_cambio_password,
        "created_at": gestor.created_at,
        "updated_at": gestor.updated_at,
    }


async def _validar_rol(db: AsyncSession, rol_id: uuid.UUID | None) -> Rol:
    """Valida el rol seleccionado o usa el default GESTOR_LIDER."""
    if rol_id:
        encontrado: Rol | None = await db.scalar(
            select(Rol).where(and_(Rol.id == rol_id, Rol.deleted_at.is_(None)))
        )
        if encontrado is None:
            raise ValueError("El rol seleccionado no existe.")
        return encontrado
    rol: Rol | None = await db.scalar(
        select(Rol).where(and_(Rol.codigo == ROL_GESTOR_LIDER, Rol.deleted_at.is_(None)))
    )
    if rol is None:
        raise ValueError(f"El rol {ROL_GESTOR_LIDER} no existe en el sistema.")
    return rol


async def _validar_dependencias(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    dep_ids: set[uuid.UUID],
) -> None:
    """Valida que las dependencias existan y pertenezcan al municipio."""
    dep_ids = {d for d in dep_ids if d is not None}
    if not dep_ids:
        return
    count = await db.scalar(
        select(func.count())
        .select_from(Dependencia)
        .where(
            and_(
                Dependencia.id.in_(list(dep_ids)),
                Dependencia.municipio_id == municipio_id,
                Dependencia.deleted_at.is_(None),
            )
        )
    )
    if count != len(dep_ids):
        raise ValueError("Una o más dependencias seleccionadas no existen en el municipio.")


# ---------------------------------------------------------------------------
# Generación de código secuencial
# ---------------------------------------------------------------------------


async def generate_gestor_code(db: AsyncSession, municipio_id: uuid.UUID) -> str:
    """
    Genera un código secuencial para el gestor líder dentro de un municipio.

    Formato: GES-000001, GES-000002, ...
    """
    stmt = (
        select(GestorLider.codigo)
        .where(GestorLider.municipio_id == municipio_id)
        .order_by(GestorLider.codigo.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    last_code = result.scalar_one_or_none()

    if last_code and last_code.startswith(CODIGO_PREFIJO):
        last_number = int(last_code[len(CODIGO_PREFIJO) :])
        next_number = last_number + 1
    else:
        next_number = 1

    return f"{CODIGO_PREFIJO}{next_number:0{CODIGO_LONGITUD_NUMERICA}d}"


# ---------------------------------------------------------------------------
# Generación de nombre de usuario
# ---------------------------------------------------------------------------


async def _username_existe(db: AsyncSession, username: str) -> bool:
    stmt = select(Usuario.id).where(
        and_(Usuario.username == username, Usuario.deleted_at.is_(None))
    )
    return (await db.scalar(stmt)) is not None


async def generate_username(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    nombre_completo: str,
) -> str:
    """
    Genera un nombre de usuario único a partir del nombre completo.

    Reglas:
      - Primera letra del primer nombre + apellido(s) completo(s) en
        minúsculas y sin espacios. Ej.: "Juan Carlos Pérez" -> "jperez".
      - Si ya existe, se agrega un número incremental.
    """
    partes = nombre_completo.strip().split()
    if len(partes) < 2:
        base = partes[0].lower() if partes else "usuario"
    else:
        base = (partes[0][0] + "".join(partes[1:])).lower()

    base = "".join(c for c in base if c.isalnum())

    username = base
    counter = 2

    while True:
        if not await _username_existe(db, username):
            return username
        username = f"{base}{counter}"
        counter += 1


# ---------------------------------------------------------------------------
# Creación de gestor líder
# ---------------------------------------------------------------------------


async def create_gestor(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    create_data: dict[str, Any],
    allowed_role_codes: set[str] | None = None,
) -> dict[str, Any]:
    """
    Crea un nuevo gestor líder o miembro del equipo.

    El código (GES-XXXXXX) siempre se autogenera. El usuario y la contraseña
    pueden definirse en create_data; si se omiten se generan automáticamente.
    La contraseña se retorna una sola vez.

    Campos aceptados: nombre_completo, email, telefono, cargo, rol_id,
    dependencia_principal_id, dependencias_adicionales, username, password.

    Si se recibe allowed_role_codes, el rol seleccionado debe estar en ese
    conjunto (usado para que un coordinador no asigne roles de administración).
    """
    nombre = (create_data.get("nombre_completo") or "").strip()
    email = create_data.get("email")
    cargo = create_data.get("cargo")
    telefono = create_data.get("telefono")
    rol_id = create_data.get("rol_id")
    principal_id = create_data.get("dependencia_principal_id")
    adicionales = create_data.get("dependencias_adicionales") or []
    custom_username = (create_data.get("username") or "").strip() or None
    custom_password = create_data.get("password") or None

    if not nombre:
        raise ValueError("El nombre completo es obligatorio.")
    if not email:
        raise ValueError("El correo electrónico es obligatorio.")
    if custom_password is not None and len(custom_password) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"La contraseña debe tener al menos {PASSWORD_MIN_LENGTH} caracteres.")
    if custom_username is not None and not USERNAME_RE.match(custom_username):
        raise ValueError(
            "El usuario debe tener de 3 a 50 caracteres y solo puede contener "
            "letras, números, punto, guion bajo o guion."
        )

    now = datetime.now(UTC)

    rol = await _validar_rol(db, rol_id)
    if allowed_role_codes is not None and rol.codigo not in allowed_role_codes:
        raise ValueError("No tiene permisos para asignar ese rol.")

    if rol.codigo in (ROL_GESTOR_LIDER, "GESTOR"):
        if not principal_id:
            raise ValueError(
                "La dependencia principal es obligatoria. "
                "El coordinador solo debe estar asociado a su dependencia."
            )
        adicionales = []

    if custom_username and await _username_existe(db, custom_username):
        raise ValueError(f"El usuario '{custom_username}' ya está en uso.")

    dep_ids = set(adicionales)
    if principal_id:
        dep_ids.add(principal_id)
    await _validar_dependencias(db, municipio_id, dep_ids)

    codigo = await generate_gestor_code(db, municipio_id)
    if custom_username:
        username = custom_username
    else:
        username = await generate_username(db, municipio_id, nombre)

    if custom_password:
        temp_password = custom_password
        must_change = False
    else:
        temp_password = generate_temporary_password(length=PASSWORD_LONGITUD)
        must_change = True

    usuario = Usuario(
        municipio_id=municipio_id,
        codigo=codigo,
        username=username,
        email=email,
        nombre_completo=nombre,
        telefono=telefono,
        cargo=cargo,
        password_hash=get_password_hash(temp_password),
        must_change_password=must_change,
        activo=1,
        estado=ESTADO_ACTIVO,
        created_at=now,
        updated_at=now,
    )
    db.add(usuario)
    await db.flush()

    gestor = GestorLider(
        usuario_id=usuario.id,
        municipio_id=municipio_id,
        codigo=codigo,
        nombre_completo=nombre,
        cargo=cargo,
        dependencia_principal_id=principal_id,
        estado=ESTADO_ACTIVO,
        created_at=now,
        updated_at=now,
    )
    db.add(gestor)
    await db.flush()

    db.add(UsuarioRol(usuario_id=usuario.id, rol_id=rol.id, municipio_id=municipio_id))

    if principal_id:
        db.add(
            UsuarioDependencia(
                usuario_id=usuario.id,
                dependencia_id=principal_id,
                municipio_id=municipio_id,
                es_principal=True,
            )
        )
    for dep_id in adicionales:
        if dep_id != principal_id:
            db.add(
                UsuarioDependencia(
                    usuario_id=usuario.id,
                    dependencia_id=dep_id,
                    municipio_id=municipio_id,
                    es_principal=False,
                )
            )

    await db.commit()

    audit = AuditService(db)
    await audit.log_event(
        evento_tipo="USER_CREATED",
        resultado="EXITOSO",
        municipio_id=municipio_id,
        usuario_id=usuario.id,  # type: ignore[arg-type]
        recurso_tipo="GestorLider",
        recurso_id=gestor.id,  # type: ignore[arg-type]
        metadata={
            "codigo": codigo,
            "rol": rol.codigo,
            "username_definido_por_usuario": bool(custom_username),
            "password_definido_por_usuario": bool(custom_password),
        },
    )

    return {
        "id": gestor.id,
        "codigo": codigo,
        "username": username,
        "nombre_completo": nombre,
        "temp_password": temp_password,
        "must_change_password": must_change,
    }


# ---------------------------------------------------------------------------
# Listado de gestores
# ---------------------------------------------------------------------------


async def list_gestores(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    filtros: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Lista gestores líderes con filtros y paginación.

    Filtros: search, estado, cargo, rol_id, page, page_size.
    """
    filtros = filtros or {}
    page = max(1, filtros.get("page", 1))
    page_size = min(100, max(1, filtros.get("page_size", 20)))
    offset = (page - 1) * page_size

    condiciones = [
        GestorLider.municipio_id == municipio_id,
        GestorLider.deleted_at.is_(None),
        Usuario.deleted_at.is_(None),
    ]

    search = filtros.get("search")
    if search:
        patron = f"%{search}%"
        condiciones.append(
            or_(
                Usuario.nombre_completo.ilike(patron),
                Usuario.username.ilike(patron),
                Usuario.email.ilike(patron),
                GestorLider.codigo.ilike(patron),
            )
        )

    estado = filtros.get("estado")
    if estado:
        condiciones.append(GestorLider.estado == estado)

    cargo = filtros.get("cargo")
    if cargo:
        condiciones.append(GestorLider.cargo.ilike(f"%{cargo}%"))

    rol_id = filtros.get("rol_id")

    join_rol = bool(rol_id)
    if join_rol:
        condiciones.append(UsuarioRol.rol_id == uuid.UUID(str(rol_id)))

    base = select(GestorLider.id).join(Usuario, GestorLider.usuario_id == Usuario.id)
    if join_rol:
        base = base.join(UsuarioRol, UsuarioRol.usuario_id == Usuario.id)
    base = base.where(*condiciones).distinct()

    total = await db.scalar(select(func.count()).select_from(base.subquery())) or 0

    query = select(GestorLider, Usuario).join(Usuario, GestorLider.usuario_id == Usuario.id)
    if join_rol:
        query = query.join(UsuarioRol, UsuarioRol.usuario_id == Usuario.id)
    query = (
        query.where(*condiciones)
        .order_by(GestorLider.updated_at.desc())
        .offset(offset)
        .limit(page_size)
        .distinct()
    )
    result = await db.execute(query)
    rows = result.all()

    gestores = []
    for gestor, usuario in rows:
        gestores.append(await _build_gestor_dict(db, gestor, usuario))

    return {
        "gestores": gestores,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


# ---------------------------------------------------------------------------
# Obtener gestor por ID
# ---------------------------------------------------------------------------


async def get_gestor(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    gestor_id: uuid.UUID,
) -> dict[str, Any] | None:
    """Obtiene un gestor líder por su ID dentro de un municipio."""
    gestor, usuario = await _get_gestor_usuario(db, municipio_id, gestor_id)
    if gestor is None or usuario is None:
        return None
    return await _build_gestor_dict(db, gestor, usuario)


# ---------------------------------------------------------------------------
# Actualizar gestor
# ---------------------------------------------------------------------------


async def update_gestor(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    gestor_id: uuid.UUID,
    update_data: dict[str, Any],
) -> dict[str, Any] | None:
    """
    Actualiza la información de un gestor líder.

    Campos actualizables: nombre_completo, email, telefono, cargo,
    dependencia_principal_id.
    """
    gestor, usuario = await _get_gestor_usuario(db, municipio_id, gestor_id)
    if gestor is None or usuario is None:
        return None

    now = datetime.now(UTC)

    if "nombre_completo" in update_data and update_data["nombre_completo"]:
        usuario.nombre_completo = update_data["nombre_completo"]
        gestor.nombre_completo = update_data["nombre_completo"]
    if "cargo" in update_data:
        gestor.cargo = update_data["cargo"]
        usuario.cargo = update_data["cargo"]
    if "email" in update_data:
        usuario.email = update_data["email"]
    if "telefono" in update_data:
        usuario.telefono = update_data["telefono"]
    if "dependencia_principal_id" in update_data:
        nuevo_principal = update_data["dependencia_principal_id"]
        gestor.dependencia_principal_id = nuevo_principal
        await _marcar_principal(db, usuario.id, municipio_id, nuevo_principal)  # type: ignore[arg-type]

    usuario.updated_at = now  # type: ignore[assignment]
    gestor.updated_at = now  # type: ignore[assignment]

    await db.commit()

    audit = AuditService(db)
    await audit.log_event(
        evento_tipo="USER_UPDATED",
        resultado="EXITOSO",
        municipio_id=municipio_id,
        usuario_id=usuario.id,  # type: ignore[arg-type]
        recurso_tipo="GestorLider",
        recurso_id=gestor.id,  # type: ignore[arg-type]
        metadata={"campos": list(update_data.keys())},
    )

    await db.refresh(gestor)
    await db.refresh(usuario)
    return await _build_gestor_dict(db, gestor, usuario)


async def _marcar_principal(
    db: AsyncSession,
    usuario_id: uuid.UUID,
    municipio_id: uuid.UUID,
    principal_id: uuid.UUID | None,
) -> None:
    """Marca la dependencia principal del usuario."""
    filas = list(
        (
            await db.execute(
                select(UsuarioDependencia).where(UsuarioDependencia.usuario_id == usuario_id)
            )
        )
        .scalars()
        .all()
    )
    for fila in filas:
        fila.es_principal = fila.dependencia_id == principal_id  # type: ignore[assignment]
    if principal_id and not any(f.dependencia_id == principal_id for f in filas):
        db.add(
            UsuarioDependencia(
                usuario_id=usuario_id,
                dependencia_id=principal_id,
                municipio_id=municipio_id,
                es_principal=True,
            )
        )


# ---------------------------------------------------------------------------
# Permisos del gestor (rol + dependencias)
# ---------------------------------------------------------------------------


async def update_gestor_permissions(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    gestor_id: uuid.UUID,
    permisos: dict[str, Any],
) -> dict[str, Any] | None:
    """
    Actualiza los permisos del gestor: rol asignado y dependencias asociadas.

    Si se omite rol_id o dependencias, esos aspectos se conservan.
    """
    gestor, usuario = await _get_gestor_usuario(db, municipio_id, gestor_id)
    if gestor is None or usuario is None:
        return None

    now = datetime.now(UTC)

    rol_id = permisos.get("rol_id")
    rol = None
    if rol_id:
        rol = await _validar_rol(db, rol_id)
        await db.execute(delete(UsuarioRol).where(UsuarioRol.usuario_id == usuario.id))
        db.add(UsuarioRol(usuario_id=usuario.id, rol_id=rol.id, municipio_id=municipio_id))

    tiene_cambio_dep = (
        "dependencia_principal_id" in permisos or "dependencias_adicionales" in permisos
    )
    if tiene_cambio_dep:
        principal_id = permisos.get("dependencia_principal_id")
        adicionales = permisos.get("dependencias_adicionales") or []

        roles_actuales = await _get_roles(db, usuario.id)  # type: ignore[arg-type]
        codigos = {r.codigo for r in roles_actuales}
        if rol is not None:
            codigos.add(rol.codigo)
        if codigos & {ROL_GESTOR_LIDER, "GESTOR"}:
            adicionales = []

        dep_ids = set(adicionales)
        if principal_id:
            dep_ids.add(principal_id)
        await _validar_dependencias(db, municipio_id, dep_ids)

        await db.execute(
            delete(UsuarioDependencia).where(UsuarioDependencia.usuario_id == usuario.id)
        )
        if principal_id:
            db.add(
                UsuarioDependencia(
                    usuario_id=usuario.id,
                    dependencia_id=principal_id,
                    municipio_id=municipio_id,
                    es_principal=True,
                )
            )
            gestor.dependencia_principal_id = principal_id
        else:
            gestor.dependencia_principal_id = None  # type: ignore[assignment]
        for dep_id in adicionales:
            if dep_id != principal_id:
                db.add(
                    UsuarioDependencia(
                        usuario_id=usuario.id,
                        dependencia_id=dep_id,
                        municipio_id=municipio_id,
                        es_principal=False,
                    )
                )

    gestor.updated_at = now  # type: ignore[assignment]
    await db.commit()

    audit = AuditService(db)
    await audit.log_event(
        evento_tipo="PERMISSIONS_UPDATED",
        resultado="EXITOSO",
        municipio_id=municipio_id,
        usuario_id=usuario.id,  # type: ignore[arg-type]
        recurso_tipo="GestorLider",
        recurso_id=gestor.id,  # type: ignore[arg-type]
        metadata={
            "permisos": {
                k: [str(x) if isinstance(x, uuid.UUID) else x for x in v]
                if isinstance(v, list)
                else (str(v) if isinstance(v, uuid.UUID) else v)
                for k, v in permisos.items()
            }
        },
    )

    await db.refresh(gestor)
    await db.refresh(usuario)
    return await _build_gestor_dict(db, gestor, usuario)


# ---------------------------------------------------------------------------
# Activar / Desactivar / Bloquear / Desbloquear
# ---------------------------------------------------------------------------


async def _change_gestor_status(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    gestor_id: uuid.UUID,
    new_status: str,
    evento: str,
    motivo: str | None = None,
) -> dict[str, Any] | None:
    """Cambia el estado de un gestor líder y su usuario."""
    gestor, usuario = await _get_gestor_usuario(db, municipio_id, gestor_id)
    if gestor is None or usuario is None:
        return None

    now = datetime.now(UTC)
    gestor.estado = new_status  # type: ignore[assignment]
    gestor.updated_at = now  # type: ignore[assignment]
    usuario.estado = new_status  # type: ignore[assignment]
    usuario.updated_at = now  # type: ignore[assignment]

    if new_status == ESTADO_BLOQUEADO:
        usuario.activo = 0  # type: ignore[assignment]
        usuario.fecha_bloqueo = now  # type: ignore[assignment]
        usuario.motivo_bloqueo = motivo or "BLOQUEO_ADMINISTRATIVO"  # type: ignore[assignment]
    elif new_status == ESTADO_ACTIVO:
        usuario.activo = 1  # type: ignore[assignment]
        usuario.fecha_bloqueo = None  # type: ignore[assignment]
        usuario.motivo_bloqueo = None  # type: ignore[assignment]
    elif new_status == ESTADO_INACTIVO:
        usuario.activo = 0  # type: ignore[assignment]

    if new_status in (ESTADO_BLOQUEADO, ESTADO_INACTIVO):
        await AuthService(db).revoke_all_sessions(uuid.UUID(str(usuario.id)), commit=False)

    await db.commit()

    audit = AuditService(db)
    await audit.log_event(
        evento_tipo=evento,
        resultado="EXITOSO",
        municipio_id=municipio_id,
        usuario_id=usuario.id,  # type: ignore[arg-type]
        recurso_tipo="GestorLider",
        recurso_id=gestor.id,  # type: ignore[arg-type]
        metadata={"motivo": motivo} if motivo else None,
    )

    await db.refresh(gestor)
    await db.refresh(usuario)
    return await _build_gestor_dict(db, gestor, usuario)


async def activate_gestor(
    db: AsyncSession, municipio_id: uuid.UUID, gestor_id: uuid.UUID
) -> dict[str, Any] | None:
    return await _change_gestor_status(db, municipio_id, gestor_id, ESTADO_ACTIVO, "USER_ACTIVATED")


async def deactivate_gestor(
    db: AsyncSession, municipio_id: uuid.UUID, gestor_id: uuid.UUID
) -> dict[str, Any] | None:
    return await _change_gestor_status(
        db, municipio_id, gestor_id, ESTADO_INACTIVO, "USER_DEACTIVATED"
    )


async def block_gestor(
    db: AsyncSession, municipio_id: uuid.UUID, gestor_id: uuid.UUID, motivo: str
) -> dict[str, Any] | None:
    if not motivo or not motivo.strip():
        raise ValueError("El motivo del bloqueo es obligatorio.")
    return await _change_gestor_status(
        db, municipio_id, gestor_id, ESTADO_BLOQUEADO, "USER_BLOCKED", motivo=motivo.strip()
    )


async def unblock_gestor(
    db: AsyncSession, municipio_id: uuid.UUID, gestor_id: uuid.UUID
) -> dict[str, Any] | None:
    return await _change_gestor_status(db, municipio_id, gestor_id, ESTADO_ACTIVO, "USER_UNBLOCKED")


# ---------------------------------------------------------------------------
# Restablecer contraseña
# ---------------------------------------------------------------------------


async def reset_password(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    gestor_id: uuid.UUID,
    nueva_password: str | None = None,
) -> dict[str, Any] | None:
    """
    Cambia la contraseña del gestor líder.

    - Si se envía nueva_password, se usa esa contraseña (no se fuerza cambio).
    - Si se omite, se genera una contraseña temporal de 24 caracteres
      (se fuerza cambio en el primer ingreso).
    En ambos casos la cuenta se reactiva. La contraseña se muestra una sola vez.
    """
    gestor, usuario = await _get_gestor_usuario(db, municipio_id, gestor_id)
    if gestor is None or usuario is None:
        return None

    if nueva_password is not None:
        if len(nueva_password) < PASSWORD_MIN_LENGTH:
            raise ValueError(f"La contraseña debe tener al menos {PASSWORD_MIN_LENGTH} caracteres.")
        temp_password = nueva_password
        must_change = False
    else:
        temp_password = generate_temporary_password(length=PASSWORD_LONGITUD)
        must_change = True

    now = datetime.now(UTC)
    usuario.password_hash = get_password_hash(temp_password)  # type: ignore[assignment]
    usuario.must_change_password = must_change  # type: ignore[assignment]
    usuario.fecha_bloqueo = None  # type: ignore[assignment]
    usuario.motivo_bloqueo = None  # type: ignore[assignment]
    usuario.activo = 1  # type: ignore[assignment]
    usuario.estado = ESTADO_ACTIVO  # type: ignore[assignment]
    usuario.updated_at = now  # type: ignore[assignment]
    gestor.estado = ESTADO_ACTIVO  # type: ignore[assignment]
    gestor.updated_at = now  # type: ignore[assignment]

    await db.commit()

    audit = AuditService(db)
    await audit.log_event(
        evento_tipo="USER_PASSWORD_RESET",
        resultado="EXITOSO",
        municipio_id=municipio_id,
        usuario_id=usuario.id,  # type: ignore[arg-type]
        recurso_tipo="GestorLider",
        recurso_id=gestor.id,  # type: ignore[arg-type]
        metadata={"password_personalizada": nueva_password is not None},
    )

    return {
        "id": gestor.id,
        "codigo": gestor.codigo,
        "username": usuario.username,
        "temp_password": temp_password,
        "must_change_password": must_change,
    }


# ---------------------------------------------------------------------------
# Eliminación lógica
# ---------------------------------------------------------------------------


async def soft_delete_gestor(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    gestor_id: uuid.UUID,
) -> dict[str, Any] | None:
    """
    Realiza la eliminación lógica de un gestor líder y su usuario.
    No se eliminan registros físicos de la base de datos.
    """
    gestor, usuario = await _get_gestor_usuario(db, municipio_id, gestor_id)
    if gestor is None or usuario is None:
        return None

    now = datetime.now(UTC)

    gestor.eliminado = True
    gestor.updated_at = now  # type: ignore[assignment]
    usuario.eliminado = True
    usuario.activo = 0  # type: ignore[assignment]
    usuario.updated_at = now  # type: ignore[assignment]

    # Desasociar roles y dependencias activos del usuario
    await db.execute(delete(UsuarioRol).where(UsuarioRol.usuario_id == usuario.id))
    await db.execute(delete(UsuarioDependencia).where(UsuarioDependencia.usuario_id == usuario.id))

    await db.commit()

    audit = AuditService(db)
    await audit.log_event(
        evento_tipo="USER_SOFT_DELETED",
        resultado="EXITOSO",
        municipio_id=municipio_id,
        usuario_id=usuario.id,  # type: ignore[arg-type]
        recurso_tipo="GestorLider",
        recurso_id=gestor.id,  # type: ignore[arg-type]
    )

    return {
        "id": gestor.id,
        "codigo": gestor.codigo,
        "eliminado": True,
        "deleted_at": now.isoformat(),
        "message": f"Gestor líder {gestor.codigo} eliminado exitosamente.",
    }


# ---------------------------------------------------------------------------
# Accesos y auditoría
# ---------------------------------------------------------------------------


async def list_gestor_accesos(
    db: AsyncSession,
    municipio_id: uuid.UUID,
    gestor_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]] | None:
    """
    Lista los intentos de acceso (exitosos y fallidos) de un gestor líder.
    """
    gestor, usuario = await _get_gestor_usuario(db, municipio_id, gestor_id)
    if gestor is None or usuario is None:
        return None

    stmt = (
        select(IntentoLogin)
        .where(IntentoLogin.usuario_id == usuario.id)
        .order_by(IntentoLogin.fecha_intento.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    rows = list(result.scalars().all())

    return [
        {
            "id": r.id,
            "exitoso": r.exitoso,
            "ip_address": r.ip_address,
            "user_agent": r.user_agent,
            "razon_fallo": r.razon_fallo,
            "fecha_intento": r.fecha_intento,
        }
        for r in rows
    ]
