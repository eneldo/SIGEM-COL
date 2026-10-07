import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.backend.services import auth_service as auth_module
from src.backend.services.auth_service import AuthService


class ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class ScalarsResult:
    def __init__(self, values):
        self.values = values

    def scalars(self):
        return self

    def all(self):
        return self.values


@pytest.fixture
def db():
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def service(db):
    return AuthService(db)


@pytest.fixture
def ids():
    return SimpleNamespace(
        user=uuid.uuid4(), municipio=uuid.uuid4(), session=uuid.uuid4()
    )


@pytest.fixture
def user(ids):
    return SimpleNamespace(
        id=ids.user,
        municipio_id=ids.municipio,
        username="alice",
        email="alice@example.com",
        nombre_completo="Alice Test",
        password_hash="hashed",
        must_change_password=True,
        activo=1,
        estado="ACTIVO",
        deleted_at=None,
        fecha_bloqueo=None,
        motivo_bloqueo=None,
        intentos_fallidos=0,
        ultimo_intento_fallido=None,
        ultimo_acceso=None,
        ip_ultimo_acceso=None,
        user_agent_ultimo_acceso=None,
        ultimo_cambio_password=None,
        mfa_activo=False,
        mfa_secret=None,
    )


@pytest.fixture
def municipio(ids):
    return SimpleNamespace(id=ids.municipio, codigo="00001", estado="ACTIVO")


@pytest.mark.asyncio
async def test_authenticate_requires_municipio(service, db):
    assert await service.authenticate_user("alice", "password") is None
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_authenticate_rejects_unknown_municipio(service, db):
    db.execute.return_value = ScalarResult(None)
    assert await service.authenticate_user("alice", "password", "99999") is None
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_authenticate_records_unknown_user(service, db, municipio, monkeypatch):
    db.execute.side_effect = [ScalarResult(municipio), ScalarResult(None)]
    tenant = AsyncMock()
    monkeypatch.setattr(auth_module, "set_tenant_context", tenant)

    result = await service.authenticate_user(
        "missing", "password", municipio.codigo, "127.0.0.1", "agent"
    )

    assert result is None
    attempt = db.add.call_args.args[0]
    assert attempt.usuario_id is None
    assert attempt.username_intentado == "missing"
    assert attempt.razon_fallo == "USER_NOT_FOUND"
    assert attempt.exitoso is False
    tenant.assert_awaited_once_with(db, municipio.id)
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"fecha_bloqueo": datetime.now(UTC)}, "ACCOUNT_LOCKED"),
        ({"activo": 0}, "ACCOUNT_INACTIVE"),
        ({"estado": "ELIMINADO_LOGICAMENTE"}, "ACCOUNT_INACTIVE"),
    ],
)
async def test_authenticate_rejects_unavailable_accounts(
    service, db, municipio, user, monkeypatch, changes, reason
):
    for name, value in changes.items():
        setattr(user, name, value)
    db.execute.side_effect = [ScalarResult(municipio), ScalarResult(user)]
    monkeypatch.setattr(auth_module, "set_tenant_context", AsyncMock())

    assert (
        await service.authenticate_user("alice", "password", municipio.codigo) is None
    )
    attempt = db.add.call_args.args[0]
    assert attempt.razon_fallo == reason
    assert attempt.exitoso is False
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("starting_attempts,locked", [(0, False), (2, True)])
async def test_authenticate_invalid_password_tracks_and_may_lock(
    service, db, municipio, user, monkeypatch, starting_attempts, locked
):
    user.intentos_fallidos = starting_attempts
    db.execute.side_effect = [ScalarResult(municipio), ScalarResult(user)]
    if locked:
        db.execute.side_effect = [
            ScalarResult(municipio),
            ScalarResult(user),
            SimpleNamespace(rowcount=2),
        ]
    monkeypatch.setattr(auth_module, "set_tenant_context", AsyncMock())
    monkeypatch.setattr(auth_module, "verify_password", lambda *_: False)
    monkeypatch.setattr(auth_module.settings, "RATE_LIMIT_LOGIN_ATTEMPTS", 3)

    assert await service.authenticate_user("alice", "bad", municipio.codigo) is None
    assert user.intentos_fallidos == starting_attempts + 1
    assert user.ultimo_intento_fallido is not None
    assert (user.fecha_bloqueo is not None) is locked
    assert (user.motivo_bloqueo == "MAX_LOGIN_ATTEMPTS") is locked
    attempt = db.add.call_args.args[0]
    assert attempt.usuario_id == user.id
    assert attempt.razon_fallo == "INVALID_PASSWORD"


@pytest.mark.asyncio
async def test_authenticate_success_issues_tokens(
    service, db, municipio, user, monkeypatch
):
    db.execute.side_effect = [ScalarResult(municipio), ScalarResult(user)]
    monkeypatch.setattr(auth_module, "set_tenant_context", AsyncMock())
    monkeypatch.setattr(auth_module, "verify_password", lambda *_: True)
    service.get_user_roles = AsyncMock(return_value=["GESTOR"])
    service._issue_tokens = AsyncMock(return_value={"access_token": "access"})

    result = await service.authenticate_user(
        "alice", "password", municipio.codigo, "127.0.0.1", "agent"
    )

    assert result == {"access_token": "access"}
    assert user.intentos_fallidos == 0
    assert user.ultimo_intento_fallido is None
    assert user.ultimo_acceso is not None
    assert user.ip_ultimo_acceso == "127.0.0.1"
    assert user.user_agent_ultimo_acceso == "agent"
    assert db.add.call_args.args[0].exitoso is True
    service._issue_tokens.assert_awaited_once()


@pytest.mark.asyncio
async def test_authenticate_success_requires_mfa(
    service, db, municipio, user, monkeypatch
):
    user.mfa_activo = True
    db.execute.side_effect = [ScalarResult(municipio), ScalarResult(user)]
    monkeypatch.setattr(auth_module, "set_tenant_context", AsyncMock())
    monkeypatch.setattr(auth_module, "verify_password", lambda *_: True)
    monkeypatch.setattr(
        auth_module, "create_mfa_token", lambda data: f"mfa:{data['sub']}"
    )
    service.get_user_roles = AsyncMock(return_value=["ADMIN"])

    result = await service.authenticate_user("alice", "password", municipio.codigo)

    assert result["mfa_required"] is True
    assert result["mfa_token"] == f"mfa:{user.id}"
    assert result["user"]["roles"] == ["ADMIN"]
    assert result["must_change_password"] is True
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_issue_tokens_persists_session_and_builds_payload(
    service, db, user, ids, monkeypatch
):
    monkeypatch.setattr(auth_module, "create_refresh_token", lambda _: "refresh")
    monkeypatch.setattr(auth_module, "decode_token", lambda _: {"jti": "refresh-jti"})
    monkeypatch.setattr(
        auth_module, "create_access_token", lambda data: f"access:{data['sid']}"
    )

    result = await service._issue_tokens(
        user,
        ids.municipio,
        ["GESTOR"],
        {"sub": str(ids.user)},
        "10.0.0.1",
        "browser",
    )

    session = db.add.call_args.args[0]
    assert session.usuario_id == ids.user
    assert session.municipio_id == ids.municipio
    assert session.token_jti == "refresh-jti"
    assert session.ip_address == "10.0.0.1"
    assert session.user_agent == "browser"
    assert result["refresh_token"] == "refresh"
    assert result["access_token"].startswith("access:")
    assert result["mfa_required"] is False
    assert result["user"]["roles"] == ["GESTOR"]
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [None, {}])
async def test_issue_tokens_rejects_invalid_refresh_payload(
    service, user, ids, monkeypatch, payload
):
    monkeypatch.setattr(auth_module, "create_refresh_token", lambda _: "refresh")
    monkeypatch.setattr(auth_module, "decode_token", lambda _: payload)
    with pytest.raises(ValueError, match="Token de refresco inválido"):
        await service._issue_tokens(user, ids.municipio, [], {}, None, None)


@pytest.mark.asyncio
async def test_get_active_session_rejects_bad_uuid(service, db):
    assert await service.get_active_session("bad-uuid") is False
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("value,expected", [(uuid.uuid4(), True), (None, False)])
async def test_get_active_session_queries_database(service, db, value, expected):
    db.execute.return_value = ScalarResult(value)
    assert await service.get_active_session(str(uuid.uuid4())) is expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [None, {}, {"type": "access", "jti": "x"}, {"type": "refresh"}],
)
async def test_refresh_rejects_invalid_token(service, db, monkeypatch, payload):
    monkeypatch.setattr(auth_module, "decode_token", lambda _: payload)
    assert await service.refresh_session("token") is None
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_refresh_rejects_missing_session(service, db, ids, monkeypatch):
    payload = {
        "type": "refresh",
        "jti": "old",
        "sub": str(ids.user),
        "municipio_id": str(ids.municipio),
    }
    monkeypatch.setattr(auth_module, "decode_token", lambda _: payload)
    monkeypatch.setattr(auth_module, "set_tenant_context", AsyncMock())
    db.execute.return_value = ScalarResult(None)
    assert await service.refresh_session("token") is None


@pytest.mark.asyncio
async def test_refresh_rejects_missing_user(service, db, ids, monkeypatch):
    payload = {
        "type": "refresh",
        "jti": "old",
        "sub": str(ids.user),
        "municipio_id": str(ids.municipio),
    }
    monkeypatch.setattr(auth_module, "decode_token", lambda _: payload)
    monkeypatch.setattr(auth_module, "set_tenant_context", AsyncMock())
    db.execute.return_value = ScalarResult(SimpleNamespace())
    service.get_current_user = AsyncMock(return_value=None)
    assert await service.refresh_session("token") is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("active", "expires"),
    [(0, timedelta(hours=1)), (1, timedelta(seconds=-1))],
)
async def test_refresh_revokes_inactive_or_expired_session(
    service, db, user, ids, monkeypatch, active, expires
):
    payload = {
        "type": "refresh",
        "jti": "old",
        "sub": str(ids.user),
        "municipio_id": str(ids.municipio),
    }
    session = SimpleNamespace(
        id=ids.session,
        activa=active,
        fecha_expiracion=datetime.now(UTC) + expires,
    )
    monkeypatch.setattr(auth_module, "decode_token", lambda _: payload)
    monkeypatch.setattr(auth_module, "set_tenant_context", AsyncMock())
    db.execute.return_value = ScalarResult(session)
    service.get_current_user = AsyncMock(return_value=user)
    service.revoke_session = AsyncMock(return_value=True)

    assert await service.refresh_session("token") is None
    service.revoke_session.assert_awaited_once_with(ids.session, ids.user)


@pytest.mark.asyncio
async def test_refresh_rotates_session(service, db, user, ids, monkeypatch):
    old_session = SimpleNamespace(
        id=ids.session,
        activa=1,
        fecha_expiracion=datetime.now(UTC) + timedelta(days=1),
        municipio_id=ids.municipio,
        ip_address="old-ip",
        user_agent="old-agent",
    )
    old_payload = {
        "type": "refresh",
        "jti": "old-jti",
        "sub": str(ids.user),
        "municipio_id": str(ids.municipio),
    }
    decode = MagicMock(side_effect=[old_payload, {"jti": "new-jti"}])
    monkeypatch.setattr(auth_module, "decode_token", decode)
    monkeypatch.setattr(auth_module, "create_refresh_token", lambda _: "new-refresh")
    monkeypatch.setattr(
        auth_module, "create_access_token", lambda data: f"access:{data['sid']}"
    )
    monkeypatch.setattr(auth_module, "set_tenant_context", AsyncMock())
    db.execute.return_value = ScalarResult(old_session)
    service.get_current_user = AsyncMock(return_value=user)
    service.get_user_roles = AsyncMock(return_value=["GESTOR"])

    result = await service.refresh_session("old", user_agent="new-agent")

    new_session = db.add.call_args.args[0]
    assert old_session.activa == 0
    assert new_session.token_jti == "new-jti"
    assert new_session.ip_address == "old-ip"
    assert new_session.user_agent == "new-agent"
    assert result["refresh_token"] == "new-refresh"
    assert result["user"]["roles"] == ["GESTOR"]
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_rejects_invalid_rotated_token(
    service, db, user, ids, monkeypatch
):
    old_session = SimpleNamespace(
        id=ids.session,
        activa=1,
        fecha_expiracion=datetime.now(UTC) + timedelta(days=1),
        municipio_id=ids.municipio,
        ip_address=None,
        user_agent=None,
    )
    old_payload = {
        "type": "refresh",
        "jti": "old-jti",
        "sub": str(ids.user),
        "municipio_id": str(ids.municipio),
    }
    monkeypatch.setattr(
        auth_module, "decode_token", MagicMock(side_effect=[old_payload, None])
    )
    monkeypatch.setattr(
        auth_module, "create_refresh_token", lambda _: "invalid-refresh"
    )
    monkeypatch.setattr(auth_module, "set_tenant_context", AsyncMock())
    db.execute.return_value = ScalarResult(old_session)
    service.get_current_user = AsyncMock(return_value=user)
    service.get_user_roles = AsyncMock(return_value=[])

    with pytest.raises(ValueError, match="Token de refresco inválido"):
        await service.refresh_session("old")


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [None, {}, {"type": "access"}])
async def test_mfa_login_rejects_invalid_token(service, db, monkeypatch, payload):
    monkeypatch.setattr(auth_module, "decode_token", lambda _: payload)
    assert await service.mfa_login("token", "123456") is None
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_value",
    [
        None,
        SimpleNamespace(mfa_activo=False, mfa_secret="secret"),
        SimpleNamespace(mfa_activo=True, mfa_secret=None),
    ],
)
async def test_mfa_login_rejects_unavailable_mfa(service, ids, monkeypatch, user_value):
    payload = {"type": "mfa", "sub": str(ids.user), "municipio_id": str(ids.municipio)}
    monkeypatch.setattr(auth_module, "decode_token", lambda _: payload)
    monkeypatch.setattr(auth_module, "set_tenant_context", AsyncMock())
    service.get_current_user = AsyncMock(return_value=user_value)
    assert await service.mfa_login("token", "123456") is None


@pytest.mark.asyncio
async def test_mfa_login_rejects_wrong_code(service, user, ids, monkeypatch):
    user.mfa_activo = True
    user.mfa_secret = "secret"
    payload = {"type": "mfa", "sub": str(ids.user), "municipio_id": str(ids.municipio)}
    monkeypatch.setattr(auth_module, "decode_token", lambda _: payload)
    monkeypatch.setattr(auth_module, "set_tenant_context", AsyncMock())
    monkeypatch.setattr(
        auth_module.pyotp,
        "TOTP",
        lambda _: SimpleNamespace(verify=lambda *_a, **_k: False),
    )
    service.get_current_user = AsyncMock(return_value=user)
    assert await service.mfa_login("token", "bad") is None


@pytest.mark.asyncio
async def test_mfa_login_issues_tokens(service, user, ids, monkeypatch):
    user.mfa_activo = True
    user.mfa_secret = "secret"
    payload = {"type": "mfa", "sub": str(ids.user), "municipio_id": str(ids.municipio)}
    monkeypatch.setattr(auth_module, "decode_token", lambda _: payload)
    monkeypatch.setattr(auth_module, "set_tenant_context", AsyncMock())
    monkeypatch.setattr(
        auth_module.pyotp,
        "TOTP",
        lambda _: SimpleNamespace(verify=lambda *_a, **_k: True),
    )
    service.get_current_user = AsyncMock(return_value=user)
    service.get_user_roles = AsyncMock(return_value=["ADMIN"])
    service._issue_tokens = AsyncMock(return_value={"access_token": "access"})

    assert await service.mfa_login("token", "123456", "ip", "ua") == {
        "access_token": "access"
    }
    service._issue_tokens.assert_awaited_once()


@pytest.mark.asyncio
async def test_mfa_status_variants(service, user, monkeypatch):
    user.mfa_activo = True
    assert await service.mfa_status(user) == {"mfa_activo": True, "pending": False}

    totp = MagicMock()
    totp.provisioning_uri.return_value = "otpauth://test"
    monkeypatch.setattr(auth_module.pyotp, "TOTP", lambda _: totp)
    user.mfa_activo = False
    user.mfa_secret = "secret"
    pending = await service.mfa_status(user)
    assert pending == {
        "mfa_activo": False,
        "pending": True,
        "secret": "secret",
        "qr_code_url": "otpauth://test",
    }

    user.mfa_secret = None
    assert await service.mfa_status(user) == {"mfa_activo": False, "pending": False}


@pytest.mark.asyncio
async def test_mfa_setup_rejects_active(service, user):
    user.mfa_activo = True
    with pytest.raises(ValueError, match="MFA ya está activo"):
        await service.mfa_setup(user)


@pytest.mark.asyncio
async def test_mfa_setup_creates_pending_secret(service, db, user, monkeypatch):
    totp = MagicMock()
    totp.provisioning_uri.return_value = "otpauth://setup"
    monkeypatch.setattr(auth_module.pyotp, "random_base32", lambda: "NEWSECRET")
    monkeypatch.setattr(auth_module.pyotp, "TOTP", lambda _: totp)

    assert await service.mfa_setup(user) == {
        "secret": "NEWSECRET",
        "qr_code_url": "otpauth://setup",
    }
    assert user.mfa_secret == "NEWSECRET"
    assert user.mfa_activo is False
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_mfa_verify_requires_secret(service, user):
    with pytest.raises(ValueError, match="No hay un secreto MFA pendiente"):
        await service.mfa_verify(user, "123456")


@pytest.mark.asyncio
@pytest.mark.parametrize("valid", [False, True])
async def test_mfa_verify_code(service, db, user, monkeypatch, valid):
    user.mfa_secret = "secret"
    monkeypatch.setattr(
        auth_module.pyotp,
        "TOTP",
        lambda _: SimpleNamespace(verify=lambda *_a, **_k: valid),
    )
    assert await service.mfa_verify(user, "123456") is valid
    assert user.mfa_activo is valid
    assert db.commit.await_count == int(valid)


@pytest.mark.asyncio
async def test_mfa_disable_requires_active(service, user):
    with pytest.raises(ValueError, match="MFA no está activo"):
        await service.mfa_disable(user, "password", "123456")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("password_ok", "code_ok", "expected"),
    [(False, True, False), (True, False, False), (True, True, True)],
)
async def test_mfa_disable_validates_credentials(
    service, db, user, monkeypatch, password_ok, code_ok, expected
):
    user.mfa_activo = True
    user.mfa_secret = "secret"
    monkeypatch.setattr(auth_module, "verify_password", lambda *_: password_ok)
    monkeypatch.setattr(
        auth_module.pyotp,
        "TOTP",
        lambda _: SimpleNamespace(verify=lambda *_a, **_k: code_ok),
    )

    assert await service.mfa_disable(user, "password", "123456") is expected
    if expected:
        assert user.mfa_activo is False
        assert user.mfa_secret is None
        db.commit.assert_awaited_once()
    else:
        db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_user_role_and_permission_queries(service, db, ids):
    db.execute.side_effect = [
        ScalarResult("user"),
        ScalarsResult(["ADMIN", "GESTOR"]),
        ScalarsResult(["usuarios.ver", "usuarios.editar"]),
    ]
    assert await service.get_current_user(str(ids.user), str(ids.municipio)) == "user"
    assert await service.get_user_roles(ids.user) == ["ADMIN", "GESTOR"]
    assert await service.get_user_permissions(ids.user) == [
        "usuarios.ver",
        "usuarios.editar",
    ]


@pytest.mark.asyncio
async def test_change_password_rejects_missing_user(service, db):
    service.get_current_user = AsyncMock(return_value=None)
    assert (
        await service.change_password(
            str(uuid.uuid4()), str(uuid.uuid4()), "old", "new"
        )
        is False
    )
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_change_password_rejects_wrong_password(service, db, user, monkeypatch):
    service.get_current_user = AsyncMock(return_value=user)
    monkeypatch.setattr(auth_module, "verify_password", lambda *_: False)
    assert (
        await service.change_password(
            str(user.id), str(user.municipio_id), "bad", "new"
        )
        is False
    )
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_change_password_updates_hash(service, db, user, monkeypatch):
    service.get_current_user = AsyncMock(return_value=user)
    monkeypatch.setattr(auth_module, "verify_password", lambda *_: True)
    monkeypatch.setattr(auth_module, "get_password_hash", lambda value: f"hash:{value}")

    assert (
        await service.change_password(
            str(user.id), str(user.municipio_id), "old", "new"
        )
        is True
    )
    assert user.password_hash == "hash:new"
    assert user.must_change_password is False
    assert user.ultimo_cambio_password is not None
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_temp_password(service, monkeypatch):
    generate = MagicMock(return_value="temporary-password")
    monkeypatch.setattr(auth_module, "generate_temporary_password", generate)
    assert await service.generate_temp_password() == "temporary-password"
    generate.assert_called_once_with(24)


@pytest.mark.asyncio
async def test_revoke_session_missing(service, db, ids):
    db.execute.return_value = ScalarResult(None)
    assert await service.revoke_session(ids.session, ids.user) is False
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_revoke_session_success(service, db, ids):
    session = SimpleNamespace(activa=1)
    db.execute.return_value = ScalarResult(session)
    assert await service.revoke_session(ids.session, ids.user) is True
    assert session.activa == 0
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_revoke_all_sessions(service, db, ids):
    db.execute.return_value = SimpleNamespace(rowcount=4)
    assert await service.revoke_all_sessions(ids.user) == 4
    db.commit.assert_awaited_once()
