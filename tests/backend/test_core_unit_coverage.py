import json
import logging
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response

from src.backend import main
from src.backend.core import database, metrics, middleware, rbac
from src.backend.core.logging import JsonFormatter, _AppStreamHandler, setup_logging


def make_request(path="/test", headers=None, client=("127.0.0.1", 1234), route=None):
    scope = {
        "type": "http",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [
            (key.lower().encode(), value.encode()) for key, value in (headers or {}).items()
        ],
        "client": client,
        "server": ("testserver", 80),
    }
    if route is not None:
        scope["route"] = route
    return Request(scope)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("header", "payload", "expected"),
    [
        (None, None, None),
        ("Basic value", None, None),
        ("Bearer token", {"type": "refresh", "municipio_id": "ignored"}, None),
        ("Bearer token", {"type": "access", "municipio_id": "tenant"}, "tenant"),
        ("Bearer token", RuntimeError("invalid"), None),
    ],
)
async def test_rls_middleware_extracts_only_valid_access_tenant(
    monkeypatch, header, payload, expected
):
    request = make_request(headers={"Authorization": header} if header else None)
    if isinstance(payload, Exception):
        monkeypatch.setattr("src.backend.core.security.decode_token", Mock(side_effect=payload))
    elif payload is not None:
        monkeypatch.setattr("src.backend.core.security.decode_token", Mock(return_value=payload))
    call_next = AsyncMock(return_value=Response())

    response = await database.RLSMiddleware(Mock()).dispatch(request, call_next)

    assert response.status_code == 200
    assert request.state.municipio_id == expected


@pytest.mark.asyncio
async def test_set_tenant_context_sets_and_clears_values():
    session = AsyncMock()

    await database.set_tenant_context(session, uuid4())
    await database.set_tenant_context(session, None)

    assert session.execute.await_count == 2
    assert session.execute.await_args_list[1].args[1] == {"value": ""}


@pytest.mark.asyncio
@pytest.mark.parametrize("dependency_name", ["get_db", "get_db_with_rls"])
async def test_database_dependency_commits_and_closes(monkeypatch, dependency_name):
    connection = object()

    @asynccontextmanager
    async def connect():
        yield connection

    session = AsyncMock()
    monkeypatch.setattr(database, "engine", SimpleNamespace(connect=connect))
    monkeypatch.setattr(database, "AsyncSession", Mock(return_value=session))
    request = make_request()
    request.state.municipio_id = "tenant"
    dependency = getattr(database, dependency_name)(request)

    assert await dependency.__anext__() is session
    with pytest.raises(StopAsyncIteration):
        await dependency.__anext__()

    session.commit.assert_awaited_once()
    session.close.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("dependency_name", ["get_db", "get_db_with_rls"])
async def test_database_dependency_rolls_back_and_closes(monkeypatch, dependency_name):
    @asynccontextmanager
    async def connect():
        yield object()

    session = AsyncMock()
    monkeypatch.setattr(database, "engine", SimpleNamespace(connect=connect))
    monkeypatch.setattr(database, "AsyncSession", Mock(return_value=session))
    dependency = getattr(database, dependency_name)(make_request())
    await dependency.__anext__()

    with pytest.raises(RuntimeError, match="boom"):
        await dependency.athrow(RuntimeError("boom"))

    session.rollback.assert_awaited_once()
    session.close.assert_awaited_once()


def test_json_formatter_includes_stack_and_safe_scalars():
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "message", (), None)
    record.stack_info = "stack details"
    record.values = [None, True, 1, 1.5, "text"]
    record._private = "hidden"

    payload = json.loads(JsonFormatter().format(record))

    assert payload["stack"] == "stack details"
    assert payload["values"] == [None, True, 1, 1.5, "text"]
    assert "_private" not in payload


def test_setup_logging_removes_forwarded_handlers_and_handles_invalid_level():
    forwarded = logging.getLogger("uvicorn")
    handler = logging.NullHandler()
    forwarded.addHandler(handler)
    root = logging.getLogger()
    original_handlers = list(root.handlers)
    original_level = root.level
    try:
        setup_logging("not-a-level", "text")
        assert handler not in forwarded.handlers
        assert root.level == logging.INFO
        assert any(isinstance(item, _AppStreamHandler) for item in root.handlers)
    finally:
        for item in list(root.handlers):
            root.removeHandler(item)
        for item in original_handlers:
            root.addHandler(item)
        root.setLevel(original_level)


def test_metrics_falls_back_to_normalized_request_path():
    request = make_request("/objects/123")

    assert metrics.path_template_for(request) == "/objects/{id}"


@pytest.mark.asyncio
async def test_request_id_middleware_uses_supplied_and_generated_ids():
    call_next = AsyncMock(side_effect=[Response(), Response()])
    supplied = make_request(headers={"X-Request-ID": "known"})
    generated = make_request()
    layer = middleware.RequestIDMiddleware(Mock())

    first = await layer.dispatch(supplied, call_next)
    second = await layer.dispatch(generated, call_next)

    assert first.headers["X-Request-ID"] == "known"
    assert second.headers["X-Request-ID"] == generated.state.request_id
    assert second.headers["X-Request-ID"]


def test_rate_limiter_cleanup_removes_expired_and_preserves_recent(monkeypatch):
    limiter = middleware.RateLimitMiddleware(Mock(), window_seconds=10)
    limiter._last_cleanup = 0
    limiter.counters["expired"] = [1]
    limiter.counters["recent"] = [95]
    monkeypatch.setattr(middleware.time, "time", Mock(return_value=100))

    limiter._cleanup()
    limiter._cleanup()

    assert "expired" not in limiter.counters
    assert limiter.counters["recent"] == [95]


@pytest.mark.asyncio
async def test_audit_middleware_logs_exception(monkeypatch):
    request = make_request()
    log = Mock()
    monkeypatch.setattr(middleware, "logger", log)

    async def fail(_request):
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await middleware.AuditMiddleware(Mock()).dispatch(request, fail)

    log.error.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status_code", "method"), [(200, "info"), (400, "warning"), (500, "error")]
)
async def test_audit_middleware_logs_response_level(monkeypatch, status_code, method):
    log = Mock()
    monkeypatch.setattr(middleware, "logger", log)
    response = await middleware.AuditMiddleware(Mock()).dispatch(
        make_request(), AsyncMock(return_value=Response(status_code=status_code))
    )

    assert response.status_code == status_code
    getattr(log, method).assert_called_once()


@pytest.mark.asyncio
async def test_rbac_queries_permissions_and_roles():
    permissions_result = Mock()
    permissions_result.scalars.return_value.all.return_value = ["users.read"]
    roles_result = Mock()
    roles_result.scalars.return_value.all.return_value = ["GESTOR"]
    db = AsyncMock()
    db.execute.side_effect = [permissions_result, roles_result]
    user_id = uuid4()

    assert await rbac.get_user_permissions(db, user_id) == ["users.read"]
    assert await rbac.get_user_role_codes(db, user_id) == ["GESTOR"]


@pytest.mark.asyncio
async def test_rbac_admin_permission_shortcut(monkeypatch):
    roles = AsyncMock(return_value=["ADMINISTRADOR_MUNICIPAL"])
    permissions = AsyncMock()
    monkeypatch.setattr(rbac, "get_user_role_codes", roles)
    monkeypatch.setattr(rbac, "get_user_permissions", permissions)

    assert await rbac.check_permission(AsyncMock(), uuid4(), "users.read")
    permissions.assert_not_awaited()


@pytest.mark.asyncio
async def test_rbac_normalizes_permissions_and_rejects_missing(monkeypatch):
    monkeypatch.setattr(rbac, "get_user_role_codes", AsyncMock(return_value=[]))
    monkeypatch.setattr(rbac, "get_user_permissions", AsyncMock(return_value=["users.read"]))
    user_id = uuid4()

    assert await rbac.check_permission(AsyncMock(), user_id, "USERS_READ")
    await rbac.require_permission(AsyncMock(), user_id, "users.read")
    with pytest.raises(HTTPException) as exc_info:
        await rbac.require_permission(AsyncMock(), user_id, "users.write")
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_main_lifespan_validates_and_disposes(monkeypatch):
    validate = Mock()
    dispose = AsyncMock()
    fake_settings = SimpleNamespace(validate_production=validate)
    fake_engine = SimpleNamespace(dispose=dispose)
    monkeypatch.setattr(main, "settings", fake_settings)
    monkeypatch.setattr(main, "engine", fake_engine)

    async with main.lifespan(main.app):
        validate.assert_called_once()

    dispose.assert_awaited_once()


@pytest.mark.asyncio
async def test_main_value_error_handler_and_root():
    response = await main.value_error_handler(make_request(), ValueError("invalid"))

    assert response.status_code == 422
    assert json.loads(response.body) == {"detail": "invalid"}
    assert (await main.root())["docs"] == "/docs"


@pytest.mark.asyncio
async def test_security_headers_adds_hsts_only_outside_debug(monkeypatch):
    call_next = AsyncMock(side_effect=[Response(), Response()])
    monkeypatch.setattr(main.settings, "DEBUG", False)
    production = await main.security_headers(make_request(), call_next)
    monkeypatch.setattr(main.settings, "DEBUG", True)
    development = await main.security_headers(make_request(), call_next)

    assert production.headers["X-Frame-Options"] == "DENY"
    assert "Strict-Transport-Security" in production.headers
    assert "Strict-Transport-Security" not in development.headers


@pytest.mark.asyncio
async def test_database_health_check_success_and_error(monkeypatch):
    session = AsyncMock()

    class SessionContext:
        async def __aenter__(self):
            return session

        async def __aexit__(self, *args):
            return None

    monkeypatch.setattr(main, "AsyncSessionLocal", Mock(return_value=SessionContext()))
    assert await main._check_database() == "ok"
    session.execute.side_effect = RuntimeError("down")
    assert await main._check_database() == "error"


@pytest.mark.asyncio
async def test_redis_health_check_success_closes_client(monkeypatch):
    client = AsyncMock()
    from_url = Mock(return_value=client)
    monkeypatch.setattr(main.redis_asyncio, "from_url", from_url)

    assert await main._check_redis() == "ok"
    client.ping.assert_awaited_once()
    client.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_redis_health_check_error_still_closes_client(monkeypatch):
    client = AsyncMock()
    client.ping.side_effect = RuntimeError("down")
    monkeypatch.setattr(main.redis_asyncio, "from_url", Mock(return_value=client))

    assert await main._check_redis() == "error"
    client.aclose.assert_awaited_once()


def test_redis_url_with_auth_branches(monkeypatch):
    monkeypatch.setattr(main.settings, "REDIS_URL", "redis://redis:6379/0")
    monkeypatch.setattr(main.settings, "REDIS_PASSWORD", "s3cret")
    assert main._redis_url_with_auth() == "redis://:s3cret@redis:6379/0"

    monkeypatch.setattr(main.settings, "REDIS_URL", "redis://user:pass@redis:6379/0")
    assert main._redis_url_with_auth() == "redis://user:pass@redis:6379/0"

    monkeypatch.setattr(main.settings, "REDIS_URL", "redis://redis:6379/0")
    monkeypatch.setattr(main.settings, "REDIS_PASSWORD", "")
    assert main._redis_url_with_auth() == "redis://redis:6379/0"

    monkeypatch.setattr(main.settings, "REDIS_PASSWORD", "s3cret")
    monkeypatch.setattr(main.settings, "REDIS_URL", "localhost:6379")
    assert main._redis_url_with_auth() == "localhost:6379"
