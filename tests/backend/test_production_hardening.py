"""Pruebas unitarias del hardening de producción de SIGEM Colombia.

Cubre health checks, rate limiting, validación de configuración en producción,
logging JSON, métricas Prometheus e IP del cliente.
"""

import json
import logging
import sys
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from src.backend import main as app_main
from src.backend.core.config import (
    DEV_JWT_SECRET_PLACEHOLDER,
    DEV_SECRET_KEY_PLACEHOLDER,
    Settings,
    settings,
)
from src.backend.core.logging import (
    _FORWARDED_LOGGERS,
    JsonFormatter,
    _AppStreamHandler,
    setup_logging,
)
from src.backend.core.metrics import MetricsMiddleware, normalize_path, render_metrics
from src.backend.core.middleware import (
    LOGIN_RATE_LIMIT_PATHS,
    RateLimitMiddleware,
    get_client_ip,
)

PROD_SECRET = "P" * 40
PROD_JWT_SECRET = "J" * 40
PROD_DATABASE_URL = "postgresql+asyncpg://sigem_app:ProdPass_2026!@db:5432/sigem_db"


async def _check_ok() -> str:
    return "ok"


async def _check_error() -> str:
    return "error"


async def _check_boom() -> str:
    raise RuntimeError("sin conexion")


def _client() -> TestClient:
    return TestClient(app_main.app)


def _prod_settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "ENVIRONMENT": "production",
        "APP_ENV": "production",
        "DEBUG": False,
        "SECRET_KEY": PROD_SECRET,
        "JWT_SECRET_KEY": PROD_JWT_SECRET,
        "DATABASE_URL": PROD_DATABASE_URL,
        "REDIS_URL": "redis://:redis-production-secret@redis:6379/0",
        "REDIS_PASSWORD": "redis-production-secret",
        "FRONTEND_URL": "https://sigem.gov.co",
        "BACKEND_URL": "https://sigem.gov.co",
        "CORS_ORIGINS": ["https://sigem.gov.co"],
        "METRICS_TOKEN": "metrics-production-secret-with-32-characters",
    }
    values.update(overrides)
    return Settings(**values)


def _limiter_client(default_max: int, login_max: int, window: int = 60) -> TestClient:
    inner = FastAPI()

    @inner.get("/ping")
    async def ping() -> dict[str, str]:
        return {"status": "pong"}

    @inner.api_route("/api/v1/auth/login", methods=["GET", "POST"])
    async def login() -> dict[str, str]:
        return {"status": "ok"}

    limiter = RateLimitMiddleware(
        inner,
        default_max_requests=default_max,
        login_max_requests=login_max,
        window_seconds=window,
    )
    return TestClient(limiter)


def _make_request(
    headers: dict[str, str] | None = None,
    client: tuple[str, int] | None = ("203.0.113.5", 40000),
) -> Request:
    raw_headers = [(key.lower().encode(), value.encode()) for key, value in (headers or {}).items()]
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": raw_headers,
        "client": client,
        "server": ("testserver", 80),
    }

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": b"", "more_body": False}

    return Request(scope, receive=receive)


def test_health_live_responde_200():
    response = _client().get("/health/live")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "alive"
    assert body["service"] == settings.APP_NAME
    assert body["version"] == settings.APP_VERSION


def test_health_agregado_saludable(monkeypatch):
    monkeypatch.setattr(app_main, "_check_database", _check_ok)

    response = _client().get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["checks"] == {"database": "ok"}
    assert body["service"] == settings.APP_NAME


def test_health_agregado_degradado(monkeypatch):
    monkeypatch.setattr(app_main, "_check_database", _check_error)

    response = _client().get("/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"] == {"database": "error"}


def test_health_ready_listo(monkeypatch):
    monkeypatch.setattr(app_main, "_check_database", _check_ok)
    monkeypatch.setattr(app_main, "_check_redis", _check_ok)

    response = _client().get("/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["checks"] == {"database": "ok", "redis": "ok"}


def test_health_ready_con_redis_caido(monkeypatch):
    monkeypatch.setattr(app_main, "_check_database", _check_ok)
    monkeypatch.setattr(app_main, "_check_redis", _check_error)

    response = _client().get("/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["checks"] == {"database": "ok", "redis": "error"}


def test_health_ready_no_propaga_excepciones(monkeypatch):
    monkeypatch.setattr(app_main, "_check_database", _check_boom)
    monkeypatch.setattr(app_main, "_check_redis", _check_boom)

    response = _client().get("/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["checks"] == {"database": "error", "redis": "error"}


def test_health_ready_no_lanza_excepcion_si_gather_falla(monkeypatch):
    monkeypatch.setattr(app_main, "_check_database", _check_boom)
    monkeypatch.setattr(app_main, "_check_redis", _check_ok)

    response = _client().get("/health/ready")

    assert response.status_code == 503


def test_rate_limit_general_bloquea_con_429():
    client = _limiter_client(default_max=2, login_max=5)

    assert client.get("/ping").status_code == 200
    assert client.get("/ping").status_code == 200

    blocked = client.get("/ping")

    assert blocked.status_code == 429
    assert blocked.headers.get("Retry-After")
    assert "Demasiadas solicitudes" in blocked.json()["detail"]


def test_rate_limit_buckets_independientes():
    client = _limiter_client(default_max=1, login_max=2)

    assert client.get("/api/v1/auth/login").status_code == 200
    assert client.get("/api/v1/auth/login").status_code == 200
    assert client.get("/api/v1/auth/login").status_code == 429
    assert client.get("/ping").status_code == 200
    assert client.get("/ping").status_code == 429


def test_rate_limit_buckets_por_prefijo():
    limiter = RateLimitMiddleware(FastAPI(), default_max_requests=1, login_max_requests=3)

    assert limiter._bucket_for("/api/v1/auth/login", "1.1.1.1") == ("login:1.1.1.1", 3)
    assert limiter._bucket_for("/api/v1/auth/mfa/verify", "1.1.1.1") == (
        "login:1.1.1.1",
        3,
    )
    assert limiter._bucket_for("/api/v1/gestores", "1.1.1.1") == ("default:1.1.1.1", 1)


def test_rate_limit_prefijos_de_login_definidos():
    assert "/api/v1/auth/login" in LOGIN_RATE_LIMIT_PATHS
    assert "/api/v1/auth/mfa/" in LOGIN_RATE_LIMIT_PATHS


def test_get_client_ip_usa_cliente_por_defecto():
    request = _make_request()

    assert get_client_ip(request) == "203.0.113.5"
    assert get_client_ip(request, trust_proxy_headers=True) == "203.0.113.5"


def test_get_client_ip_sin_confianza_en_proxy():
    request = _make_request(headers={"X-Forwarded-For": "198.51.100.9, 10.0.0.1"})

    assert get_client_ip(request, trust_proxy_headers=False) == "203.0.113.5"


def test_get_client_ip_confia_en_proxy_cuando_se_configura():
    request = _make_request(headers={"X-Forwarded-For": "198.51.100.9, 10.0.0.1"})

    assert get_client_ip(request, trust_proxy_headers=True) == "198.51.100.9"


def test_get_client_ip_sin_cliente_conectado():
    request = _make_request(client=None)

    assert get_client_ip(request) == "unknown"


def test_metrics_exponer_formato_prometheus():
    _client().get("/health/live")

    content, media_type = render_metrics()
    body = content.decode()

    assert "http_requests_total" in body
    assert "http_request_duration_seconds" in body
    assert "text/plain" in media_type


def test_metrics_middleware_registra_plantilla_de_ruta():
    inner = FastAPI()

    @inner.get("/items/{item_id}")
    async def items(item_id: int) -> dict[str, int]:
        return {"item_id": item_id}

    client = TestClient(MetricsMiddleware(inner))

    assert client.get("/items/42").status_code == 200

    body = render_metrics()[0].decode()
    assert 'path_template="/items/{item_id}"' in body
    assert 'path_template="/metrics"' not in body


def test_metrics_no_registra_el_propio_endpoint():
    client = TestClient(MetricsMiddleware(FastAPI()))

    client.get("/metrics")

    body = render_metrics()[0].decode()
    assert 'path_template="/metrics"' not in body


def test_metrics_endpoint_disponible_sin_token(monkeypatch):
    monkeypatch.setattr(settings, "METRICS_TOKEN", None)

    response = _client().get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_metrics_endpoint_valida_token(monkeypatch):
    monkeypatch.setattr(settings, "METRICS_TOKEN", "token-secreto")
    client = _client()

    assert client.get("/metrics").status_code == 401
    assert client.get("/metrics", headers={"Authorization": "Bearer equivocado"}).status_code == 401
    assert (
        client.get("/metrics", headers={"Authorization": "Bearer token-secreto"}).status_code == 200
    )


def test_metrics_endpoint_deshabilitado_responde_404(monkeypatch):
    monkeypatch.setattr(settings, "METRICS_ENABLED", False)

    assert _client().get("/metrics").status_code == 404


@pytest.mark.parametrize(
    ("path", "esperado"),
    [
        (
            "/api/v1/gestores/6f9619ff-8b86-4d01-b42d-00cf4fc964ff",
            "/api/v1/gestores/{id}",
        ),
        ("/api/v1/reportes/123", "/api/v1/reportes/{id}"),
        (
            "/api/v1/archivos/deadbeefdeadbeef/descargar",
            "/api/v1/archivos/{id}/descargar",
        ),
        ("/api/v1/estados", "/api/v1/estados"),
    ],
)
def test_normalize_path(path: str, esperado: str):
    assert normalize_path(path) == esperado


def test_is_production_detecta_entorno():
    assert Settings(ENVIRONMENT="production").is_production
    assert Settings(APP_ENV="prod").is_production
    assert not Settings(ENVIRONMENT="staging", APP_ENV="staging").is_production
    assert not Settings(ENVIRONMENT="development", APP_ENV="development").is_production


def test_validate_production_no_valida_en_desarrollo():
    Settings(ENVIRONMENT="development", APP_ENV="development", DEBUG=True).validate_production()


def test_validate_production_acepta_configuracion_de_exito():
    _prod_settings().validate_production()


def test_validate_production_acepta_entorno_prod_alternativo():
    _prod_settings(ENVIRONMENT="development", APP_ENV="prod").validate_production()


def test_validate_production_mensaje_en_espanol():
    with pytest.raises(RuntimeError) as excinfo:
        _prod_settings(DEBUG=True).validate_production()

    assert "Configuración de producción inválida" in str(excinfo.value)


@pytest.mark.parametrize(
    ("overrides", "campo_esperado"),
    [
        ({"DEBUG": True}, "DEBUG"),
        ({"SECRET_KEY": "corto"}, "SECRET_KEY"),
        ({"SECRET_KEY": DEV_SECRET_KEY_PLACEHOLDER}, "SECRET_KEY"),
        ({"JWT_SECRET_KEY": DEV_JWT_SECRET_PLACEHOLDER}, "JWT_SECRET_KEY"),
        ({"JWT_SECRET_KEY": PROD_SECRET}, "JWT_SECRET_KEY"),
        ({"DATABASE_URL": ""}, "DATABASE_URL"),
        (
            {"DATABASE_URL": "postgresql+asyncpg://sigem:sigem_password@db:5432/sigem_db"},
            "DATABASE_URL",
        ),
        ({"CORS_ORIGINS": ["*"]}, "CORS_ORIGINS"),
        ({"SECRET_KEY": "CHANGE_ME_openssl_rand_base64_48"}, "SECRET_KEY"),
        (
            {"JWT_SECRET_KEY": "changeme-production-secret-that-is-long-enough"},
            "JWT_SECRET_KEY",
        ),
        (
            {"DATABASE_URL": "postgresql+asyncpg://sigem_app:CHANGE_ME@postgres:5432/sigem_db"},
            "DATABASE_URL",
        ),
        (
            {"DATABASE_URL": "postgresql+asyncpg://sigem:strong-password@postgres:5432/sigem_db"},
            "DATABASE_URL",
        ),
        ({"REDIS_URL": "redis://redis:6379/0"}, "REDIS_URL"),
        ({"REDIS_PASSWORD": "CHANGE_ME_openssl_rand_base64_48"}, "REDIS_PASSWORD"),
        ({"FRONTEND_URL": "https://CHANGE_ME.example"}, "FRONTEND_URL"),
        ({"BACKEND_URL": "http://sigem.gov.co"}, "BACKEND_URL"),
        ({"CORS_ORIGINS": ["http://sigem.gov.co"]}, "CORS_ORIGINS"),
        ({"METRICS_TOKEN": "CHANGE_ME_openssl_rand_base64_48"}, "METRICS_TOKEN"),
        ({"MFA_ENABLED": False}, "MFA_ENABLED"),
        ({"RATE_LIMIT_ENABLED": False}, "RATE_LIMIT_ENABLED"),
    ],
)
def test_validate_production_rechaza_configuracion_debil(overrides: dict, campo_esperado: str):
    with pytest.raises(RuntimeError, match=campo_esperado):
        _prod_settings(**overrides).validate_production()


def test_json_formatter_genera_estructura_base():
    record = logging.LogRecord(
        name="sigem.test",
        level=logging.WARNING,
        pathname=__file__,
        lineno=10,
        msg="fallo en %s",
        args=("ejecucion",),
        exc_info=None,
    )
    record.request_id = "req-123"

    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "WARNING"
    assert payload["logger"] == "sigem.test"
    assert payload["message"] == "fallo en ejecucion"
    assert payload["request_id"] == "req-123"
    assert payload["timestamp"].endswith("+00:00")


def test_json_formatter_convierte_valores_no_serializables():
    record = logging.LogRecord(
        name="sigem.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=20,
        msg="detalle",
        args=None,
        exc_info=None,
    )
    record.detalle = {"objeto": object(), "lista": (1, 2)}

    payload = json.loads(JsonFormatter().format(record))

    assert payload["detalle"]["objeto"].startswith("<object")
    assert payload["detalle"]["lista"] == [1, 2]


def test_json_formatter_incluye_excepcion():
    try:
        raise ValueError("boom")
    except ValueError:
        record = logging.LogRecord(
            name="sigem.test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=30,
            msg="error controlado",
            args=None,
            exc_info=sys.exc_info(),
        )

    payload = json.loads(JsonFormatter().format(record))

    assert "ValueError: boom" in payload["exception"]


def test_setup_logging_installa_handler_unico():
    root = logging.getLogger()
    originales = list(root.handlers)
    nivel_original = root.level
    niveles_originales = {name: logging.getLogger(name).level for name in _FORWARDED_LOGGERS}
    try:
        setup_logging("INFO", "json")
        setup_logging("DEBUG", "json")

        handlers = [handler for handler in root.handlers if isinstance(handler, _AppStreamHandler)]
        assert len(handlers) == 1
        assert root.level == logging.DEBUG
        assert isinstance(handlers[0].formatter, JsonFormatter)
    finally:
        for handler in list(root.handlers):
            root.removeHandler(handler)
        for handler in originales:
            root.addHandler(handler)
        root.setLevel(nivel_original)
        for name, level in niveles_originales.items():
            logging.getLogger(name).setLevel(level)


def test_setup_logging_reenvia_loggers_de_infraestructura():
    root = logging.getLogger()
    originales = list(root.handlers)
    nivel_original = root.level
    try:
        setup_logging("INFO", "json")

        for name in ("uvicorn.access", "sqlalchemy.engine.Engine"):
            forwarded = logging.getLogger(name)
            assert forwarded.propagate is True
            assert forwarded.handlers == []
            assert forwarded.level == logging.INFO
    finally:
        for handler in list(root.handlers):
            root.removeHandler(handler)
        for handler in originales:
            root.addHandler(handler)
        root.setLevel(nivel_original)
        for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "uvicorn.lifespan"):
            logging.getLogger(name).setLevel(logging.NOTSET)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.NOTSET)
        logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.NOTSET)


def test_setup_logging_formato_texto_alternativo():
    root = logging.getLogger()
    originales = list(root.handlers)
    nivel_original = root.level
    try:
        setup_logging("WARNING", "texto")

        handlers = [handler for handler in root.handlers if isinstance(handler, _AppStreamHandler)]
        assert len(handlers) == 1
        assert root.level == logging.WARNING
        assert not isinstance(handlers[0].formatter, JsonFormatter)
    finally:
        for handler in list(root.handlers):
            root.removeHandler(handler)
        for handler in originales:
            root.addHandler(handler)
        root.setLevel(nivel_original)
