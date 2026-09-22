"""Create or update the local SIGEM administrator from environment variables."""

import asyncio
import os
import uuid

from sqlalchemy import select

from src.backend.core.database import AsyncSessionLocal
from src.backend.core.security import get_password_hash
from src.backend.models.municipio import Municipio
from src.backend.models.rol import Rol
from src.backend.models.usuario import Usuario
from src.backend.models.usuario_rol import UsuarioRol


async def bootstrap_admin() -> None:
    password = os.environ.get("SIGEM_BOOTSTRAP_PASSWORD")
    if not password or len(password) < 15:
        raise ValueError("SIGEM_BOOTSTRAP_PASSWORD must contain at least 15 characters")

    username = os.environ.get("SIGEM_BOOTSTRAP_USERNAME", "admin")
    municipio_codigo = os.environ.get("SIGEM_BOOTSTRAP_MUNICIPIO", "00000")

    async with AsyncSessionLocal() as session:
        municipio = await session.scalar(
            select(Municipio).where(Municipio.codigo == municipio_codigo)
        )
        role = await session.scalar(
            select(Rol).where(Rol.codigo == "SUPERADMIN_PLATAFORMA")
        )
        if municipio is None or role is None:
            raise RuntimeError("Run Alembic migrations before bootstrapping the administrator")

        user = await session.scalar(
            select(Usuario).where(
                Usuario.municipio_id == municipio.id,
                Usuario.username == username,
            )
        )
        if user is None:
            user = Usuario(
                municipio_id=municipio.id,
                codigo="ADM-00000",
                username=username,
                email="admin@sigem.gov.co",
                nombre_completo="Administrador SIGEM",
                password_hash=get_password_hash(password),
                must_change_password=True,
                activo=1,
            )
            session.add(user)
            await session.flush()
        else:
            user.password_hash = get_password_hash(password)
            user.must_change_password = True
            user.activo = 1
            user.estado = "ACTIVO"
            user.fecha_bloqueo = None
            user.motivo_bloqueo = None
            user.intentos_fallidos = 0

        assignment = await session.scalar(
            select(UsuarioRol).where(
                UsuarioRol.usuario_id == user.id,
                UsuarioRol.rol_id == role.id,
            )
        )
        if assignment is None:
            session.add(
                UsuarioRol(
                    id=uuid.uuid4(),
                    usuario_id=user.id,
                    rol_id=role.id,
                    municipio_id=municipio.id,
                )
            )

        await session.commit()
        print(f"Administrator ready: {username} ({municipio_codigo})")


if __name__ == "__main__":
    asyncio.run(bootstrap_admin())
