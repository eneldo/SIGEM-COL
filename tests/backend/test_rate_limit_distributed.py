"""Pruebas del rate limiting distribuido y de las ventanas separadas por bucket."""

from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.backend.core import rate_limit as rate_limit_module
from src.backend.core.middleware import RateLimitMiddleware


class FakeRedis:
    def __init__(self, fail: bool = False) -> None:
        self.counters: dict[str, int] = {}
        self.expirations: dict[str, int] = {}
        self.fail = fail

    async def incr(self, key: str) -> int:
        if self.fail:
            raise ConnectionError("redis no disponible")
        self.counters[key] = self.counters.get(key, 0) + 1
        return self.counters[key]

    async def expire(self, key: str, seconds: int) -> bool:
        if self.fail:
            raise ConnectionError("redis no disponible")
        self.expirations[key] = seconds
        return True


def _app_client(limiter: RateLimitMiddleware) -> TestClient:
    return TestClient(limiter)


def _limiter(app: Any = None, **kwargs: Any) -> RateLimitMiddleware:
    defaults: dict[str, Any] = {
        "default_max_requests": 2,
        "login_max_requests": 1,
        "window_seconds": 60,
        "login_window_seconds": 900,
        "backend": rate_limit_module.InMemoryRateLimitBackend(),
    }
    defaults.update(kwargs)
    return RateLimitMiddleware(app if app is not None else FastAPI(), **defaults)


def _limited_app(**kwargs: Any) -> TestClient:
    inner = FastAPI()

    @inner.get("/ping")
    async def ping() -> dict[str, str]:
        return {"status": "pong"}

    @inner.post("/api/v1/auth/login")
    async def login() -> dict[str, str]:
        return {"status": "ok"}

    return TestClient(_limiter(inner, **kwargs))


@pytest.mark.asyncio
async def test_redis_backend_incrementa_y_expira_la_primera_vez() -> None:
    redis = FakeRedis()
    backend = rate_limit_module.RedisRateLimitBackend(redis)

    primera = await backend.hit("default:1.2.3.4", limit=2, window_seconds=60)
    segunda = await backend.hit("default:1.2.3.4", limit=2, window_seconds=60)
    tercera = await backend.hit("default:1.2.3.4", limit=2, window_seconds=60)

    assert primera.allowed is True
    assert segunda.allowed is True
    assert tercera.allowed is False
    assert redis.counters["default:1.2.3.4"] == 3
    assert redis.expirations["default:1.2.3.4"] == 60


@pytest.mark.asyncio
async def test_redis_backend_propaga_error_para_que_el_middleware_decida() -> None:
    backend = rate_limit_module.RedisRateLimitBackend(FakeRedis(fail=True))
    with pytest.raises(ConnectionError):
        await backend.hit("login:1.2.3.4", limit=5, window_seconds=900)


def test_middleware_limita_con_ventana_independiente_para_login() -> None:
    client = _limited_app(
        default_max_requests=100,
        login_max_requests=1,
        window_seconds=60,
        login_window_seconds=900,
    )

    assert client.post("/api/v1/auth/login").status_code == 200
    assert client.post("/api/v1/auth/login").status_code == 429
    assert client.get("/ping").status_code == 200
    assert client.get("/ping").status_code == 200


def test_middleware_falla_cerrado_en_login_si_redis_cae() -> None:
    client = _limited_app(
        backend=rate_limit_module.RedisRateLimitBackend(FakeRedis(fail=True)),
        fail_closed_login=True,
    )

    response = client.post("/api/v1/auth/login")

    assert response.status_code == 429
    assert response.json()["detail"].startswith("Demasiadas solicitudes")


def test_middleware_degrada_a_memoria_para_trafico_general() -> None:
    client = _limited_app(
        backend=rate_limit_module.RedisRateLimitBackend(FakeRedis(fail=True)),
        fail_closed_login=False,
        default_max_requests=2,
        login_max_requests=100,
    )

    assert client.get("/ping").status_code == 200
    assert client.get("/ping").status_code == 200
    assert client.get("/ping").status_code == 429
    assert client.post("/api/v1/auth/login").status_code == 200


def test_backend_por_defecto_usa_memoria_fuera_de_produccion() -> None:
    backend = rate_limit_module.build_rate_limit_backend(is_production=False)
    assert isinstance(backend, rate_limit_module.InMemoryRateLimitBackend)


def test_backend_por_defecto_usa_redis_en_produccion() -> None:
    backend = rate_limit_module.build_rate_limit_backend(is_production=True)
    assert isinstance(backend, rate_limit_module.RedisRateLimitBackend)
