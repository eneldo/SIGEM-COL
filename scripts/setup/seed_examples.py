"""Seed example users and gestor leaders for local testing."""

import asyncio
import os
import uuid

from sqlalchemy import select, text

from src.backend.core.database import AsyncSessionLocal, release_tenant_context
from src.backend.core.security import get_password_hash
from src.backend.models.dependencia import Dependencia
from src.backend.models.gestor_lider import GestorLider
from src.backend.models.municipio import Municipio
from src.backend.models.producto import Producto
from src.backend.models.rol import Rol
from src.backend.models.usuario import Usuario
from src.backend.models.usuario_dependencia import UsuarioDependencia
from src.backend.models.usuario_rol import UsuarioRol


PASSWORD = "SigemAdmin2026!"


async def main() -> None:
    async with AsyncSessionLocal() as session:
        municipio = await session.scalar(select(Municipio).where(Municipio.codigo == "00000"))
        if municipio is None:
            raise RuntimeError("Municipio 00000 not found")

        await session.execute(
            text("SELECT set_config('app.current_municipio_id', :value, false)"),
            {"value": str(municipio.id)},
        )

        roles = {}
        for code in ("GESTOR_LIDER", "ADMINISTRADOR_MUNICIPAL", "GESTOR"):
            r = await session.scalar(select(Rol).where(Rol.codigo == code))
            if r is None:
                raise RuntimeError(f"Role {code} not found")
            roles[code] = r

        dependencias = (await session.execute(select(Dependencia).where(Dependencia.municipio_id == municipio.id))).scalars().all()
        if not dependencias:
            raise RuntimeError("No dependencias found")

        # 3 gestores lideres
        gestores_lideres = []
        for i in range(1, 4):
            username = f"gestorlider{i}"
            user = await session.scalar(
                select(Usuario).where(Usuario.municipio_id == municipio.id, Usuario.username == username)
            )
            if user is None:
                user = Usuario(
                    municipio_id=municipio.id,
                    codigo=f"GL-00{i}",
                    username=username,
                    email=f"gestorlider{i}@sigem.gov.co",
                    nombre_completo=f"Gestor Lider {i}",
                    cargo="Gestor Lider",
                    password_hash=get_password_hash(PASSWORD),
                    must_change_password=False,
                    activo=1,
                )
                session.add(user)
                await session.flush()
            # role
            if not await session.scalar(select(UsuarioRol).where(UsuarioRol.usuario_id == user.id, UsuarioRol.rol_id == roles["GESTOR_LIDER"].id)):
                session.add(UsuarioRol(id=uuid.uuid4(), usuario_id=user.id, rol_id=roles["GESTOR_LIDER"].id, municipio_id=municipio.id))
            # dependencia
            dep = dependencias[(i - 1) % len(dependencias)]
            if not await session.scalar(select(UsuarioDependencia).where(UsuarioDependencia.usuario_id == user.id, UsuarioDependencia.dependencia_id == dep.id)):
                session.add(UsuarioDependencia(id=uuid.uuid4(), usuario_id=user.id, dependencia_id=dep.id, municipio_id=municipio.id, es_principal=True))
            # gestor lider record
            gl = await session.scalar(select(GestorLider).where(GestorLider.usuario_id == user.id))
            if gl is None:
                gl = GestorLider(
                    municipio_id=municipio.id,
                    usuario_id=user.id,
                    codigo=f"GL-00{i}",
                    nombre_completo=f"Gestor Lider {i}",
                    cargo="Gestor Lider",
                    dependencia_principal_id=dep.id,
                    estado="ACTIVO",
                )
                session.add(gl)
                await session.flush()
            gestores_lideres.append(gl)

        await session.flush()

        # assign existing products to gestores lideres (round-robin)
        productos = (await session.execute(select(Producto).where(Producto.municipio_id == municipio.id))).scalars().all()
        for idx, prod in enumerate(productos):
            gl = gestores_lideres[idx % len(gestores_lideres)]
            prod.gestor_lider_id = gl.id
            if prod.dependencia_responsable_id is None:
                prod.dependencia_responsable_id = gestores_lideres[idx % len(gestores_lideres)].dependencia_principal_id

        # 2 coordinadores
        for i in range(1, 3):
            username = f"coordinador{i}"
            user = await session.scalar(select(Usuario).where(Usuario.municipio_id == municipio.id, Usuario.username == username))
            if user is None:
                user = Usuario(
                    municipio_id=municipio.id,
                    codigo=f"COORD-00{i}",
                    username=username,
                    email=f"coordinador{i}@sigem.gov.co",
                    nombre_completo=f"Coordinador {i}",
                    cargo="Coordinador",
                    password_hash=get_password_hash(PASSWORD),
                    must_change_password=False,
                    activo=1,
                )
                session.add(user)
                await session.flush()
            if not await session.scalar(select(UsuarioRol).where(UsuarioRol.usuario_id == user.id, UsuarioRol.rol_id == roles["ADMINISTRADOR_MUNICIPAL"].id)):
                session.add(UsuarioRol(id=uuid.uuid4(), usuario_id=user.id, rol_id=roles["ADMINISTRADOR_MUNICIPAL"].id, municipio_id=municipio.id))

        # 3 gestores
        for i in range(1, 4):
            username = f"gestor{i}"
            user = await session.scalar(select(Usuario).where(Usuario.municipio_id == municipio.id, Usuario.username == username))
            if user is None:
                user = Usuario(
                    municipio_id=municipio.id,
                    codigo=f"GEST-00{i}",
                    username=username,
                    email=f"gestor{i}@sigem.gov.co",
                    nombre_completo=f"Gestor {i}",
                    cargo="Gestor",
                    password_hash=get_password_hash(PASSWORD),
                    must_change_password=False,
                    activo=1,
                )
                session.add(user)
                await session.flush()
            if not await session.scalar(select(UsuarioRol).where(UsuarioRol.usuario_id == user.id, UsuarioRol.rol_id == roles["GESTOR"].id)):
                session.add(UsuarioRol(id=uuid.uuid4(), usuario_id=user.id, rol_id=roles["GESTOR"].id, municipio_id=municipio.id))
            dep = dependencias[(i - 1) % len(dependencias)]
            if not await session.scalar(select(UsuarioDependencia).where(UsuarioDependencia.usuario_id == user.id, UsuarioDependencia.dependencia_id == dep.id)):
                session.add(UsuarioDependencia(id=uuid.uuid4(), usuario_id=user.id, dependencia_id=dep.id, municipio_id=municipio.id, es_principal=True))

        await session.commit()
        await release_tenant_context(session.connection())
        print("Seed examples ready. Password for all new users:", PASSWORD)


if __name__ == "__main__":
    asyncio.run(main())
