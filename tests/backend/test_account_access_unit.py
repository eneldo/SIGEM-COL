"""Account/session regressions using real SQL on an isolated in-memory database.

SQLite verifies account predicates and session updates; it does not test PostgreSQL RLS.
"""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pyotp
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from src.backend.api.v1 import auth
from src.backend.core.database import get_db, get_db_with_rls
from src.backend.core.security import (
    create_access_token,
    create_mfa_token,
    create_refresh_token,
)
from src.backend.models.gestor_lider import GestorLider
from src.backend.models.intento_login import IntentoLogin
from src.backend.models.municipio import Municipio
from src.backend.models.rol import Permiso, Rol
from src.backend.models.sesion import Sesion
from src.backend.models.usuario import Usuario
from src.backend.models.usuario_rol import RolPermiso, UsuarioRol
from src.backend.services import auth_service, gestor_service, usuario_service


class AsyncTestSession:
    """Run service SQL on SQLite without an extra asynchronous driver dependency."""

    def __init__(self, session):
        self.session = session
        self.commits = 0

    async def execute(self, statement):
        return self.session.execute(statement)

    async def commit(self):
        self.session.commit()
        self.commits += 1

    async def refresh(self, instance):
        self.session.refresh(instance)

    def add(self, instance):
        self.session.add(instance)


@pytest.fixture
def account_api(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    models = (
        Municipio,
        Usuario,
        Sesion,
        Rol,
        Permiso,
        UsuarioRol,
        RolPermiso,
        GestorLider,
        IntentoLogin,
    )
    for model in models:
        model.__table__.create(engine)
    session = Session(engine, expire_on_commit=False)
    db = AsyncTestSession(session)
    municipio_id = uuid4()
    session.add(
        Municipio(
            id=municipio_id,
            codigo="00000",
            nombre="Municipio de prueba",
            departamento="Departamento de prueba",
        )
    )
    session.commit()

    def create_user(username):
        user = Usuario(
            id=uuid4(),
            municipio_id=municipio_id,
            codigo=username,
            username=username,
            email=f"{username}@example.com",
            nombre_completo="Usuario de prueba",
            password_hash="unused",
            must_change_password=False,
            activo=1,
            mfa_activo=False,
        )
        session.add(user)
        session.commit()
        return user

    user = create_user("reviewuser")
    other = create_user("otheruser")
    now = datetime.now(UTC)
    tokens = []
    for owner in (user, user, other):
        sid, jti = uuid4(), str(uuid4())
        claims = {
            "sub": str(owner.id),
            "municipio_id": str(municipio_id),
            "username": owner.username,
        }
        session.add(
            Sesion(
                id=sid,
                usuario_id=owner.id,
                municipio_id=municipio_id,
                token_jti=jti,
                fecha_creacion=now,
                fecha_expiracion=now + timedelta(days=1),
                activa=1,
            )
        )
        tokens.append(
            {
                "sid": sid,
                "access": create_access_token({**claims, "sid": str(sid)}),
                "refresh": create_refresh_token(claims, jti=jti),
            }
        )
    session.commit()

    # RLS itself is a PostgreSQL concern, separate from these account-state tests.
    monkeypatch.setattr(auth_service, "set_tenant_context", AsyncMock())
    app = FastAPI()
    app.include_router(auth.router, prefix="/api/v1/auth")
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_db_with_rls] = lambda: db
    try:
        with TestClient(app) as client:
            yield SimpleNamespace(
                client=client,
                db=db,
                session=session,
                user=user,
                other=other,
                municipio_id=municipio_id,
                tokens=tokens,
            )
    finally:
        session.close()
        engine.dispose()


def me(api, token):
    return api.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})


@pytest.mark.parametrize("change", ["inactive", "blocked", "deleted"])
def test_existing_tokens_cannot_authenticate_unavailable_accounts(account_api, change):
    api = account_api
    assert me(api, api.tokens[0]["access"]).status_code == 200
    secret = pyotp.random_base32()
    changes = {"mfa_activo": True, "mfa_secret": secret}
    if change == "inactive":
        changes["activo"] = 0
    elif change == "blocked":
        changes["fecha_bloqueo"] = datetime.now(UTC)
    else:
        changes["deleted_at"] = datetime.now(UTC)
    # Change state independently of the revocation hooks to verify defense in depth.
    api.session.execute(update(Usuario).where(Usuario.id == api.user.id).values(**changes))
    api.session.commit()

    assert me(api, api.tokens[0]["access"]).status_code == 401
    refresh = api.client.post(
        "/api/v1/auth/refresh", json={"refresh_token": api.tokens[0]["refresh"]}
    )
    assert refresh.status_code == 401, refresh.text
    mfa_token = create_mfa_token({"sub": str(api.user.id), "municipio_id": str(api.municipio_id)})
    mfa = api.client.post(
        "/api/v1/auth/mfa/login",
        json={"mfa_token": mfa_token, "code": pyotp.TOTP(secret).now()},
    )
    assert mfa.status_code == 401, mfa.text
    assert len(api.session.scalars(select(Sesion)).all()) == 3
    assert me(api, api.tokens[2]["access"]).status_code == 200


async def test_deactivation_revokes_all_user_sessions_without_reviving_on_reactivation(
    account_api,
):
    api = account_api
    await usuario_service.update_usuario(api.db, api.municipio_id, api.user.id, {"activo": 0})
    assert api.db.commits == 1
    assert [
        s.activa
        for s in api.session.scalars(select(Sesion).where(Sesion.usuario_id == api.user.id))
    ] == [0, 0]
    assert api.session.get(Sesion, api.tokens[2]["sid"]).activa == 1

    await usuario_service.update_usuario(api.db, api.municipio_id, api.user.id, {"activo": 1})
    for token in api.tokens[:2]:
        assert me(api, token["access"]).status_code == 401
        response = api.client.post("/api/v1/auth/refresh", json={"refresh_token": token["refresh"]})
        assert response.status_code == 401, response.text
    assert me(api, api.tokens[2]["access"]).status_code == 200


@pytest.mark.parametrize("action", ["deactivate", "block"])
async def test_gestor_status_changes_revoke_sessions(account_api, monkeypatch, action):
    api = account_api
    gestor = GestorLider(
        id=uuid4(),
        municipio_id=api.municipio_id,
        usuario_id=api.user.id,
        codigo="GES-TEST",
        nombre_completo="Gestor de prueba",
    )
    api.session.add(gestor)
    api.session.commit()
    monkeypatch.setattr(
        gestor_service,
        "_build_gestor_dict",
        AsyncMock(return_value={"id": str(gestor.id)}),
    )
    monkeypatch.setattr(
        gestor_service,
        "AuditService",
        lambda _db: SimpleNamespace(log_event=AsyncMock()),
    )
    if action == "block":
        await gestor_service.block_gestor(api.db, api.municipio_id, gestor.id, "Prueba de bloqueo")
    else:
        await gestor_service.deactivate_gestor(api.db, api.municipio_id, gestor.id)
    assert api.db.commits == 1
    assert [
        s.activa
        for s in api.session.scalars(select(Sesion).where(Sesion.usuario_id == api.user.id))
    ] == [0, 0]

    await gestor_service.activate_gestor(api.db, api.municipio_id, gestor.id)
    assert me(api, api.tokens[0]["access"]).status_code == 401
    assert me(api, api.tokens[1]["access"]).status_code == 401
    assert me(api, api.tokens[2]["access"]).status_code == 200


async def test_login_attempt_lock_revokes_existing_sessions(account_api, monkeypatch):
    api = account_api
    monkeypatch.setattr(auth_service.settings, "RATE_LIMIT_LOGIN_ATTEMPTS", 1)
    monkeypatch.setattr(auth_service, "verify_password", lambda *_: False)
    result = await auth_service.AuthService(api.db).authenticate_user(
        api.user.username, "wrong password", "00000"
    )
    assert result is None
    assert api.user.fecha_bloqueo is not None
    assert api.db.commits == 1
    assert [
        s.activa
        for s in api.session.scalars(select(Sesion).where(Sesion.usuario_id == api.user.id))
    ] == [0, 0]
    assert api.session.get(Sesion, api.tokens[2]["sid"]).activa == 1
    assert me(api, api.tokens[0]["access"]).status_code == 401
