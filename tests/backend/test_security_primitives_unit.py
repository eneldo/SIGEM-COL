"""Pruebas unitarias de tokens, cifrado de secretos MFA y cabeceras residuales."""

import uuid

import pytest
from fastapi.testclient import TestClient

from src.backend import main as app_main
from src.backend.core.config import settings
from src.backend.core.security import (
    create_access_token,
    create_mfa_token,
    create_refresh_token,
    decode_token,
    decrypt_totp_secret,
    encrypt_totp_secret,
    generate_temporary_password,
    get_password_hash,
    verify_password,
)


def _claims() -> dict:
    return {"sub": str(uuid.uuid4()), "municipio_id": str(uuid.uuid4())}


class TestEmisionDeTokens:
    def test_access_token_lleva_jti_y_tipo(self) -> None:
        token = create_access_token(_claims())

        payload = decode_token(token)

        assert payload is not None
        assert payload["type"] == "access"
        assert payload["jti"]

    def test_refresh_token_conserva_el_jti_recibido(self) -> None:
        jti = str(uuid.uuid4())

        payload = decode_token(create_refresh_token(_claims(), jti=jti))

        assert payload is not None
        assert payload["type"] == "refresh"
        assert payload["jti"] == jti

    def test_refresh_token_genera_jti_cuando_no_se_recibe(self) -> None:
        payload = decode_token(create_refresh_token(_claims()))

        assert payload is not None
        assert payload["jti"]

    def test_mfa_token_no_es_un_access_token(self) -> None:
        payload = decode_token(create_mfa_token(_claims()))

        assert payload is not None
        assert payload["type"] == "mfa"


class TestCifradoDeSecretosMFA:
    def test_el_secreto_cifrado_no_aparece_en_claro(self) -> None:
        secreto = "JBSWY3DPEHPK3PXP"

        cifrado = encrypt_totp_secret(secreto)

        assert cifrado.startswith("enc:v1:")
        assert secreto not in cifrado

    def test_cifrado_y_descifrado_conservan_el_secreto(self) -> None:
        assert decrypt_totp_secret(encrypt_totp_secret("JBSWY3DPEHPK3PXP")) == ("JBSWY3DPEHPK3PXP")

    def test_cada_cifrado_usa_un_nonce_distinto(self) -> None:
        assert encrypt_totp_secret("secreto") != encrypt_totp_secret("secreto")

    def test_un_secreto_heredado_en_claro_se_acepta(self) -> None:
        assert decrypt_totp_secret("JBSWY3DPEHPK3PXP") == "JBSWY3DPEHPK3PXP"

    def test_un_texto_cifrado_corrupto_falla(self) -> None:
        with pytest.raises(ValueError):
            decrypt_totp_secret("enc:v1:no-es-un-cifrado-valido")


class TestContrasenas:
    def test_hash_y_verificacion_de_contrasena(self) -> None:
        hash_ = get_password_hash("Contrasena-Fuerte-2026!")

        assert verify_password("Contrasena-Fuerte-2026!", hash_)
        assert not verify_password("otra-contrasena", hash_)

    def test_contrasena_temporal_cumple_complejidad(self) -> None:
        password = generate_temporary_password()

        assert len(password) >= 24
        assert any(c.islower() for c in password)
        assert any(c.isupper() for c in password)
        assert any(c.isdigit() for c in password)

    def test_contrasena_temporal_respeta_la_longitud(self) -> None:
        assert len(generate_temporary_password(32)) == 32


def test_se_retira_la_cabecera_xss_protection_heredada() -> None:
    original_debug = app_main.settings.DEBUG
    app_main.settings.DEBUG = False
    try:
        client = TestClient(app_main.app)
        response = client.get("/health")
    finally:
        app_main.settings.DEBUG = original_debug

    assert "X-XSS-Protection" not in response.headers
    assert response.headers["Strict-Transport-Security"]


@pytest.mark.asyncio
async def test_el_middleware_de_cabeceras_retira_xss_protection() -> None:
    from starlette.responses import Response

    async def call_next(_request):
        return Response("ok", headers={"X-XSS-Protection": "1; mode=block"})

    response = await app_main.security_headers(_MagicRequest(), call_next)

    assert "X-XSS-Protection" not in response.headers
    assert response.headers["Content-Security-Policy"]
    assert response.headers["Permissions-Policy"]


def _MagicRequest():  # noqa: N802
    from starlette.requests import Request

    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/health",
            "headers": [],
            "client": ("127.0.0.1", 1234),
            "query_string": b"",
            "scheme": "https",
            "server": ("testserver", 443),
        }
    )


def test_producto_serializa_decimales_nulos() -> None:
    from datetime import UTC, datetime

    from src.backend.schemas.producto import ProductoResponse

    ahora = datetime.now(UTC)
    producto = ProductoResponse(
        id=uuid.uuid4(),
        codigo="P1",
        nombre="Producto",
        meta_cuatrienio=None,
        linea_base=None,
        estado="ACTIVO",
        municipio_id=uuid.uuid4(),
        programa_id=uuid.uuid4(),
        created_at=ahora,
        updated_at=ahora,
    )

    datos = producto.model_dump()

    assert datos["meta_cuatrienio"] is None
    assert datos["linea_base"] is None


def test_redis_url_agrega_la_contrasena_configurada() -> None:
    original = settings.REDIS_URL
    settings.REDIS_URL = "redis://redis:6379/0"
    try:
        url = app_main._redis_url_with_auth()
    finally:
        settings.REDIS_URL = original

    assert url.startswith("redis://:")
    assert "@redis:6379/0" in url
