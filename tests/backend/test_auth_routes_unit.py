import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from src.backend.api.v1 import auth
from src.backend.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    MFADisableRequest,
    MFALoginRequest,
    MFAVerifyRequest,
    RefreshTokenRequest,
)


def make_request(path="/api/v1/auth/me", headers=None, client=("127.0.0.1", 1234)):
    raw_headers = [
        (key.lower().encode(), value.encode()) for key, value in (headers or {}).items()
    ]
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": path,
            "headers": raw_headers,
            "client": client,
            "query_string": b"",
            "scheme": "http",
            "server": ("testserver", 80),
        }
    )


@pytest.fixture
def ids():
    return SimpleNamespace(
        user=uuid.uuid4(), municipio=uuid.uuid4(), session=uuid.uuid4()
    )


@pytest.fixture
def user(ids):
    return SimpleNamespace(
        id=ids.user,
        username="alice",
        email="alice@example.com",
        nombre_completo="Alice Test",
        municipio_id=ids.municipio,
        must_change_password=False,
        mfa_activo=True,
    )


@pytest.fixture
def current_user(user, ids):
    return {
        "user": user,
        "municipio_id": str(ids.municipio),
        "roles": ["GESTOR"],
        "permissions": ["usuarios.ver"],
        "sid": str(ids.session),
    }


@pytest.fixture
def services(monkeypatch):
    auth_service = MagicMock()
    audit_service = MagicMock()
    audit_service.log_event = AsyncMock()
    monkeypatch.setattr(auth, "AuthService", MagicMock(return_value=auth_service))
    monkeypatch.setattr(auth, "AuditService", MagicMock(return_value=audit_service))
    return auth_service, audit_service


def assert_http_error(exc_info, status_code, detail):
    assert exc_info.value.status_code == status_code
    assert exc_info.value.detail == detail


@pytest.mark.asyncio
@pytest.mark.parametrize("authorization", [None, "Basic abc"])
async def test_get_current_user_rejects_missing_or_malformed_bearer(authorization):
    headers = {} if authorization is None else {"Authorization": authorization}
    with pytest.raises(HTTPException) as exc_info:
        await auth.get_current_user_from_token(
            make_request(headers=headers), MagicMock()
        )
    assert_http_error(exc_info, 401, "Token de autenticación requerido")


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [None, {"type": "refresh"}])
async def test_get_current_user_rejects_invalid_token(monkeypatch, payload):
    monkeypatch.setattr(auth, "decode_token", MagicMock(return_value=payload))
    with pytest.raises(HTTPException) as exc_info:
        await auth.get_current_user_from_token(
            make_request(headers={"Authorization": "Bearer token"}), MagicMock()
        )
    assert_http_error(exc_info, 401, "Token inválido o expirado")


@pytest.mark.asyncio
async def test_get_current_user_rejects_revoked_session(monkeypatch, services, ids):
    service, _ = services
    service.get_active_session = AsyncMock(return_value=False)
    monkeypatch.setattr(
        auth,
        "decode_token",
        MagicMock(
            return_value={
                "type": "access",
                "sub": str(ids.user),
                "municipio_id": str(ids.municipio),
                "sid": str(ids.session),
            }
        ),
    )
    with pytest.raises(HTTPException) as exc_info:
        await auth.get_current_user_from_token(
            make_request(headers={"Authorization": "Bearer token"}), MagicMock()
        )
    assert_http_error(exc_info, 401, "Sesión revocada o expirada")


@pytest.mark.asyncio
async def test_get_current_user_rejects_unknown_user(monkeypatch, services, ids):
    service, _ = services
    service.get_active_session = AsyncMock(return_value=True)
    service.get_current_user = AsyncMock(return_value=None)
    monkeypatch.setattr(
        auth,
        "decode_token",
        lambda _: {
            "type": "access",
            "sub": str(ids.user),
            "municipio_id": str(ids.municipio),
            "sid": str(ids.session),
        },
    )
    with pytest.raises(HTTPException) as exc_info:
        await auth.get_current_user_from_token(
            make_request(headers={"Authorization": "Bearer token"}), MagicMock()
        )
    assert_http_error(exc_info, 401, "Usuario no encontrado")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "must_change_password", "mfa_activo", "roles", "detail"),
    [
        ("/api/v1/catalogos", True, True, ["GESTOR"], "PASSWORD_CHANGE_REQUIRED"),
        (
            "/api/v1/catalogos",
            False,
            False,
            ["ADMINISTRADOR_MUNICIPAL"],
            "MFA_SETUP_REQUIRED",
        ),
    ],
)
async def test_get_current_user_enforces_security_flags(
    monkeypatch,
    services,
    user,
    ids,
    path,
    must_change_password,
    mfa_activo,
    roles,
    detail,
):
    service, _ = services
    user.must_change_password = must_change_password
    user.mfa_activo = mfa_activo
    service.get_current_user = AsyncMock(return_value=user)
    service.get_user_roles = AsyncMock(return_value=roles)
    monkeypatch.setattr(
        auth,
        "decode_token",
        lambda _: {
            "type": "access",
            "sub": str(ids.user),
            "municipio_id": str(ids.municipio),
        },
    )
    with pytest.raises(HTTPException) as exc_info:
        await auth.get_current_user_from_token(
            make_request(path, {"Authorization": "Bearer token"}), MagicMock()
        )
    assert_http_error(exc_info, 403, detail)


@pytest.mark.asyncio
async def test_get_current_user_returns_context_on_allowed_path(
    monkeypatch, services, user, ids
):
    service, _ = services
    user.must_change_password = True
    user.mfa_activo = False
    service.get_current_user = AsyncMock(return_value=user)
    service.get_user_roles = AsyncMock(return_value=["ADMINISTRADOR_MUNICIPAL"])
    service.get_user_permissions = AsyncMock(return_value=["auth.me"])
    monkeypatch.setattr(
        auth,
        "decode_token",
        lambda _: {
            "type": "access",
            "sub": str(ids.user),
            "municipio_id": str(ids.municipio),
        },
    )
    result = await auth.get_current_user_from_token(
        make_request("/api/v1/auth/me", {"Authorization": "Bearer token"}), MagicMock()
    )
    assert result == {
        "user": user,
        "municipio_id": str(ids.municipio),
        "roles": ["ADMINISTRADOR_MUNICIPAL"],
        "permissions": ["auth.me"],
        "sid": None,
    }


@pytest.mark.asyncio
async def test_login_error_and_success(services, ids):
    service, audit = services
    service.authenticate_user = AsyncMock(
        side_effect=[None, {"user": {"id": ids.user, "municipio_id": ids.municipio}}]
    )
    request = make_request(headers={"User-Agent": "pytest"})
    data = LoginRequest(username="alice", password="secret")
    with pytest.raises(HTTPException) as exc_info:
        await auth.login(data, request, MagicMock())
    assert_http_error(exc_info, 401, "Credenciales inválidas")
    result = await auth.login(data, request, MagicMock())
    assert result["user"]["id"] == ids.user
    audit.log_event.assert_awaited_once()


async def test_get_current_user_response(current_user, user):
    result = await auth.get_current_user(current_user)
    assert result.id == user.id
    assert result.roles == ["GESTOR"]


@pytest.mark.asyncio
async def test_change_password_all_paths(services, current_user):
    service, audit = services
    mismatch = ChangePasswordRequest(
        current_password="old",
        new_password="NewPassword123!",
        confirm_password="different",
    )
    with pytest.raises(HTTPException) as exc_info:
        await auth.change_password(mismatch, current_user, MagicMock())
    assert_http_error(exc_info, 400, "Las contraseñas no coinciden")

    valid = ChangePasswordRequest(
        current_password="old",
        new_password="NewPassword123!",
        confirm_password="NewPassword123!",
    )
    service.change_password = AsyncMock(side_effect=[False, True])
    with pytest.raises(HTTPException) as exc_info:
        await auth.change_password(valid, current_user, MagicMock())
    assert_http_error(exc_info, 400, "Contraseña actual incorrecta")
    assert await auth.change_password(valid, current_user, MagicMock()) == {
        "message": "Contraseña cambiada exitosamente"
    }
    audit.log_event.assert_awaited_once()


@pytest.mark.asyncio
async def test_mfa_status(services, current_user):
    service, _ = services
    service.mfa_status = AsyncMock(return_value={"mfa_activo": True, "pending": False})
    result = await auth.mfa_status(current_user, MagicMock())
    assert result.mfa_activo is True


@pytest.mark.asyncio
async def test_mfa_setup_error_and_success(services, current_user):
    service, audit = services
    service.mfa_setup = AsyncMock(
        side_effect=[
            ValueError("already enabled"),
            {"secret": "secret", "qr_code_url": "otpauth://test"},
        ]
    )
    with pytest.raises(HTTPException) as exc_info:
        await auth.mfa_setup(current_user, MagicMock())
    assert_http_error(exc_info, 409, "already enabled")
    result = await auth.mfa_setup(current_user, MagicMock())
    assert result.secret == "secret"
    audit.log_event.assert_awaited_once()


@pytest.mark.asyncio
async def test_mfa_verify_all_paths(services, current_user):
    service, audit = services
    data = MFAVerifyRequest(code="123456")
    service.mfa_verify = AsyncMock(
        side_effect=[ValueError("not configured"), False, True]
    )
    with pytest.raises(HTTPException) as exc_info:
        await auth.mfa_verify(data, current_user, MagicMock())
    assert_http_error(exc_info, 400, "not configured")
    with pytest.raises(HTTPException) as exc_info:
        await auth.mfa_verify(data, current_user, MagicMock())
    assert_http_error(exc_info, 401, "Código MFA inválido.")
    assert await auth.mfa_verify(data, current_user, MagicMock()) == {
        "message": "MFA activado exitosamente",
        "mfa_activo": True,
    }
    audit.log_event.assert_awaited_once()


@pytest.mark.asyncio
async def test_mfa_login_error_and_success(services, ids):
    service, audit = services
    result = {"user": {"id": ids.user, "municipio_id": ids.municipio}}
    service.mfa_login = AsyncMock(side_effect=[None, result])
    data = MFALoginRequest(mfa_token="long-mfa-token", code="123456")
    request = make_request(headers={"User-Agent": "pytest"}, client=None)
    with pytest.raises(HTTPException) as exc_info:
        await auth.mfa_login(data, request, MagicMock())
    assert_http_error(exc_info, 401, "Código MFA inválido o token expirado.")
    assert await auth.mfa_login(data, request, MagicMock()) == result
    audit.log_event.assert_awaited_once()


@pytest.mark.asyncio
async def test_mfa_disable_all_paths(services, current_user):
    service, audit = services
    data = MFADisableRequest(password="password", code="123456")
    service.mfa_disable = AsyncMock(
        side_effect=[ValueError("not enabled"), False, True]
    )
    with pytest.raises(HTTPException) as exc_info:
        await auth.mfa_disable(data, current_user, MagicMock())
    assert_http_error(exc_info, 400, "not enabled")
    with pytest.raises(HTTPException) as exc_info:
        await auth.mfa_disable(data, current_user, MagicMock())
    assert_http_error(exc_info, 401, "Contraseña o código MFA inválido.")
    assert await auth.mfa_disable(data, current_user, MagicMock()) == {
        "message": "MFA desactivado exitosamente",
        "mfa_activo": False,
    }
    audit.log_event.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_error_and_success(services, ids):
    service, audit = services
    result = {"user": {"id": ids.user, "municipio_id": ids.municipio}}
    service.refresh_session = AsyncMock(side_effect=[None, result])
    data = RefreshTokenRequest(refresh_token="refresh")
    request = make_request(headers={"User-Agent": "pytest"}, client=None)
    with pytest.raises(HTTPException) as exc_info:
        await auth.refresh_tokens(data, request, MagicMock())
    assert_http_error(exc_info, 401, "Refresh token inválido o expirado.")
    assert await auth.refresh_tokens(data, request, MagicMock()) == result
    audit.log_event.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("with_sid", [True, False])
async def test_logout_revokes_expected_sessions(services, current_user, ids, with_sid):
    service, audit = services
    service.revoke_session = AsyncMock()
    service.revoke_all_sessions = AsyncMock()
    current_user["sid"] = str(ids.session) if with_sid else None
    assert await auth.logout(current_user, MagicMock()) == {
        "message": "Sesión cerrada exitosamente"
    }
    if with_sid:
        service.revoke_session.assert_awaited_once_with(
            ids.session, current_user["user"].id
        )
        service.revoke_all_sessions.assert_not_awaited()
    else:
        service.revoke_all_sessions.assert_awaited_once_with(current_user["user"].id)
        service.revoke_session.assert_not_awaited()
    audit.log_event.assert_awaited_once()
