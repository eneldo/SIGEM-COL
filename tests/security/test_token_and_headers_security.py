"""Pruebas de validacion de claims JWT, CORS efectivo y cabeceras de trazabilidad."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import jwt
import pytest
from fastapi.testclient import TestClient

from src.backend.core.config import settings
from src.backend.core.middleware import REQUEST_ID_PATTERN, RequestIDMiddleware
from src.backend.core.security import create_access_token, decode_token
from src.backend.main import app

ALLOWED_ORIGIN = "http://localhost:3000"


def _token(payload: dict, secret: str | None = None) -> str:
    data = {
        "sub": str(uuid.uuid4()),
        "municipio_id": str(uuid.uuid4()),
        "type": "access",
        "exp": datetime.now(UTC) + timedelta(minutes=15),
        **payload,
    }
    return jwt.encode(data, secret or settings.JWT_SECRET_KEY, algorithm="HS256")


class TestClaimsJWTDefensivos:
    def test_rechaza_sub_que_no_es_uuid(self) -> None:
        assert decode_token(_token({"sub": "no-es-uuid"})) is None

    def test_rechaza_municipio_ausente(self) -> None:
        token = jwt.encode(
            {"sub": str(uuid.uuid4()), "type": "access", "exp": 9999999999},
            settings.JWT_SECRET_KEY,
            algorithm="HS256",
        )

        assert decode_token(token) is None

    def test_rechaza_tipo_desconocido(self) -> None:
        assert decode_token(_token({"type": "administrador"})) is None

    def test_rechaza_token_firmado_con_otra_clave(self) -> None:
        assert decode_token(_token({}, secret="otra-clave-de-32-caracteres-minimo")) is None

    def test_rechaza_token_sin_exp(self) -> None:
        token = jwt.encode(
            {
                "sub": str(uuid.uuid4()),
                "municipio_id": str(uuid.uuid4()),
                "type": "access",
            },
            settings.JWT_SECRET_KEY,
            algorithm="HS256",
        )

        assert decode_token(token) is None

    def test_acepta_token_valido(self) -> None:
        payload = decode_token(
            create_access_token({"sub": str(uuid.uuid4()), "municipio_id": str(uuid.uuid4())})
        )

        assert payload is not None
        assert payload["type"] == "access"
        assert payload["jti"]

    @pytest.mark.parametrize(
        "claims",
        [
            {"sub": "no-es-uuid"},
            {"municipio_id": "no-es-uuid"},
            {"type": "refresh"},
            {"sid": "no-es-uuid"},
        ],
    )
    async def test_el_guard_rechaza_claims_invalidos_con_401(self, claims) -> None:
        from fastapi import HTTPException
        from starlette.requests import Request

        from src.backend.api.v1.auth import get_current_user_from_token

        token = jwt.encode(
            {
                "sub": str(uuid.uuid4()),
                "municipio_id": str(uuid.uuid4()),
                "type": "access",
                "exp": datetime.now(UTC) + timedelta(minutes=5),
                **claims,
            },
            settings.JWT_SECRET_KEY,
            algorithm="HS256",
        )
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/api/v1/auth/me",
                "headers": [
                    (b"authorization", f"Bearer {token}".encode()),
                ],
                "client": ("127.0.0.1", 1234),
                "query_string": b"",
                "scheme": "https",
                "server": ("testserver", 443),
            }
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_token(request, MagicMock())

        assert exc_info.value.status_code == 401


class TestCORSEfectivo:
    def test_preflight_de_origen_autorizado_es_aceptado(self) -> None:
        client = TestClient(app)

        response = client.options(
            "/api/v1/usuarios",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )

        assert response.status_code == 200
        assert response.headers["Access-Control-Allow-Origin"] == ALLOWED_ORIGIN
        assert response.headers["Access-Control-Allow-Credentials"] == "true"

    def test_origen_no_autorizado_no_recibe_permisos_cors(self) -> None:
        client = TestClient(app)

        response = client.options(
            "/api/v1/usuarios",
            headers={
                "Origin": "https://sitio-no-autorizado.example",
                "Access-Control-Request-Method": "GET",
            },
        )

        assert "Access-Control-Allow-Origin" not in response.headers

    def test_respuesta_incluye_vary_origin(self) -> None:
        client = TestClient(app)

        response = client.get("/health", headers={"Origin": ALLOWED_ORIGIN})

        assert response.headers.get("Vary", "").lower().find("origin") >= 0


class TestRequestIDRobusto:
    def _client(self):
        from fastapi import FastAPI

        inner = FastAPI()

        @inner.get("/ping")
        async def ping():
            return {"ok": True}

        return TestClient(RequestIDMiddleware(inner))

    @pytest.mark.parametrize(
        "supplied",
        [
            "x" * 500,
            "identificador con espacios",
            "identificador\ninyectado",
            "identificador;drop",
        ],
    )
    def test_rechaza_identificadores_invalidos(self, supplied: str) -> None:
        client = self._client()

        response = client.get("/ping", headers={"X-Request-ID": supplied})

        generated = response.headers["X-Request-ID"]
        assert REQUEST_ID_PATTERN.fullmatch(generated)
        assert generated != supplied

    def test_conserva_identificador_valido(self) -> None:
        client = self._client()

        response = client.get("/ping", headers={"X-Request-ID": "req-123_ABC.1"})

        assert response.headers["X-Request-ID"] == "req-123_ABC.1"


class TestMetricasProtegidas:
    def test_comparacion_del_token_es_segura(self) -> None:
        from src.backend import main as app_main

        original = app_main.settings.METRICS_TOKEN
        app_main.settings.METRICS_TOKEN = "token-de-metricas-largo-y-secreto"
        try:
            client = TestClient(app_main.app)
            assert (
                client.get("/metrics", headers={"Authorization": "Bearer incorrecto"}).status_code
                == 401
            )
            assert (
                client.get(
                    "/metrics",
                    headers={"Authorization": "Bearer token-de-metricas-largo-y-secreto"},
                ).status_code
                == 200
            )
        finally:
            app_main.settings.METRICS_TOKEN = original
