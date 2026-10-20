"""Pruebas del refresh token en cookie HttpOnly y su proteccion CSRF."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from src.backend.api.v1 import auth as auth_routes
from src.backend.core import session_cookies
from src.backend.core.config import settings
from src.backend.schemas.auth import RefreshTokenRequest

PROD_ORIGIN = "https://sigem.gov.co"


def make_request(
    headers=None, cookies=None, client=("127.0.0.1", 1234), path="/api/v1/auth/refresh"
):
    all_headers = dict(headers or {})
    if cookies:
        all_headers["Cookie"] = "; ".join(
            f"{key}={value}" for key, value in cookies.items()
        )
    raw_headers = [
        (key.lower().encode(), value.encode()) for key, value in all_headers.items()
    ]
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": path,
            "headers": raw_headers,
            "client": client,
            "query_string": b"",
            "scheme": "https",
            "server": ("testserver", 443),
        }
    )


class DummyResponse:
    def __init__(self) -> None:
        self.set_cookie_params: dict = {}
        self.delete_cookie_params: dict = {}

    def set_cookie(self, key: str, value: str = "", **kwargs) -> None:
        self.set_cookie_params = {"key": key, "value": value, **kwargs}

    def delete_cookie(self, key: str, **kwargs) -> None:
        self.delete_cookie_params = {"key": key, **kwargs}


@pytest.fixture
def prod_origins(monkeypatch):
    monkeypatch.setattr(settings, "CORS_ORIGINS", [PROD_ORIGIN])
    return PROD_ORIGIN


@pytest.fixture
def current_user():
    return {
        "user": SimpleNamespace(
            id="11111111-1111-1111-1111-111111111111",
            municipio_id="22222222-2222-2222-2222-222222222222",
        ),
        "municipio_id": "22222222-2222-2222-2222-222222222222",
        "sid": "33333333-3333-3333-3333-333333333333",
    }


@pytest.fixture
def service(monkeypatch):
    service = MagicMock()
    service.refresh_session = AsyncMock(
        return_value={
            "user": {"id": "u", "municipio_id": "m"},
            "access_token": "a",
            "refresh_token": "nuevo-refresh",
        }
    )
    monkeypatch.setattr(auth_routes, "AuthService", MagicMock(return_value=service))
    audit = MagicMock()
    audit.log_event = AsyncMock()
    monkeypatch.setattr(auth_routes, "AuditService", MagicMock(return_value=audit))
    return service


def test_cookie_de_refresh_es_httponly_y_restringida() -> None:
    response = DummyResponse()

    session_cookies.set_refresh_cookie(response, "token-refresco")

    params = response.set_cookie_params
    assert params["key"] == session_cookies.REFRESH_COOKIE_NAME
    assert params["value"] == "token-refresco"
    assert params["httponly"] is True
    assert params["secure"] is True
    assert params["samesite"] == "strict"
    assert params["path"] == "/api/v1/auth"


def test_cookie_se_borra_en_logout() -> None:
    response = DummyResponse()

    session_cookies.clear_refresh_cookie(response)

    assert response.delete_cookie_params["key"] == session_cookies.REFRESH_COOKIE_NAME
    assert response.delete_cookie_params["path"] == "/api/v1/auth"


@pytest.mark.asyncio
async def test_refresh_usa_el_token_de_la_cookie(service) -> None:
    request = make_request(
        cookies={session_cookies.REFRESH_COOKIE_NAME: "cookie-token"}
    )
    response = DummyResponse()

    result = await auth_routes.refresh_tokens(
        request, response, RefreshTokenRequest(), MagicMock()
    )

    assert result["access_token"] == "a"
    service.refresh_session.assert_awaited_once()
    assert service.refresh_session.await_args.args[0] == "cookie-token"
    assert response.set_cookie_params["key"] == session_cookies.REFRESH_COOKIE_NAME


@pytest.mark.asyncio
async def test_refresh_rechaza_origin_no_autorizado(service, prod_origins) -> None:
    request = make_request(
        headers={"Origin": "https://sitio-malicioso.example"},
        cookies={session_cookies.REFRESH_COOKIE_NAME: "cookie-token"},
    )
    response = DummyResponse()

    with pytest.raises(HTTPException) as exc_info:
        await auth_routes.refresh_tokens(
            request, response, RefreshTokenRequest(), MagicMock()
        )

    assert exc_info.value.status_code == 403
    service.refresh_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_refresh_acepta_origin_autorizado(service, prod_origins) -> None:
    request = make_request(
        headers={"Origin": PROD_ORIGIN},
        cookies={session_cookies.REFRESH_COOKIE_NAME: "cookie-token"},
    )
    response = DummyResponse()

    await auth_routes.refresh_tokens(
        request, response, RefreshTokenRequest(), MagicMock()
    )

    service.refresh_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_sin_cookie_ni_cuerpo_responde_401(service) -> None:
    request = make_request()
    response = DummyResponse()

    with pytest.raises(HTTPException) as exc_info:
        await auth_routes.refresh_tokens(
            request, response, RefreshTokenRequest(), MagicMock()
        )

    assert exc_info.value.status_code == 401
    service.refresh_session.assert_not_awaited()


@pytest.mark.asyncio
async def test_refresh_invalido_limpia_la_cookie(service) -> None:
    service.refresh_session = AsyncMock(return_value=None)
    request = make_request(
        cookies={session_cookies.REFRESH_COOKIE_NAME: "cookie-token"}
    )
    response = DummyResponse()

    with pytest.raises(HTTPException) as exc_info:
        await auth_routes.refresh_tokens(
            request, response, RefreshTokenRequest(), MagicMock()
        )

    assert exc_info.value.status_code == 401
    assert response.delete_cookie_params["key"] == session_cookies.REFRESH_COOKIE_NAME


@pytest.mark.asyncio
async def test_login_emite_cookie_de_refresco_y_lo_retira_del_cuerpo(service) -> None:
    service.authenticate_user = AsyncMock(
        return_value={
            "access_token": "a",
            "refresh_token": "r",
            "user": {"id": "u", "municipio_id": "m"},
        }
    )
    request = make_request(path="/api/v1/auth/login")
    response = DummyResponse()

    result = await auth_routes.login(
        SimpleNamespace(username="admin", password="secreto"),
        request,
        response,
        MagicMock(),
    )

    assert response.set_cookie_params["value"] == "r"
    assert response.set_cookie_params["httponly"] is True
    assert "refresh_token" not in result


@pytest.mark.asyncio
async def test_logout_borra_la_cookie(service, current_user) -> None:
    service.revoke_session = AsyncMock()
    service.revoke_all_sessions = AsyncMock()
    response = DummyResponse()

    await auth_routes.logout(response, current_user, MagicMock())

    assert response.delete_cookie_params["key"] == session_cookies.REFRESH_COOKIE_NAME
