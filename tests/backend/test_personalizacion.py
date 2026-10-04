"""Tests del módulo de Personalizacion (branding por municipio)."""

import asyncio

import asyncpg
import pytest
from pydantic import ValidationError
from sqlalchemy import make_url

from src.backend.core.config import settings
from src.backend.schemas.personalizacion import (
    MAX_LOGO_B64_CHARS,
    PersonalizacionUpdate,
)
from tests.conftest import API_PREFIX, auth_header

PNG_DATA_URL = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
SVG_DATA_URL = "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4="


def _borrar_configuraciones() -> None:
    url = make_url(settings.DATABASE_URL)

    async def _run() -> None:
        conn = await asyncpg.connect(
            host=url.host or "localhost",
            port=url.port or 5432,
            user=url.username or "sigem",
            password=url.password or "",
            database=url.database or "sigem_db",
        )
        try:
            await conn.execute("DELETE FROM personalizaciones")
        finally:
            await conn.close()

    asyncio.run(_run())


@pytest.fixture(autouse=True)
def _configuracion_limpia():
    _borrar_configuraciones()
    yield
    _borrar_configuraciones()


def _payload(**overrides):
    payload = {
        "color_primario": "#0f3d3b",
        "color_secundario": "#b9852f",
        "nombre_sistema": "SIGEM Colombia",
        "logo_data_url": None,
    }
    payload.update(overrides)
    return payload


def _put(api, token, payload):
    return api.put(
        f"{API_PREFIX}/personalizacion",
        json=payload,
        headers=auth_header(token),
    )


class TestPersonalizacionAPI:
    def test_get_devuelve_valores_por_defecto(self, api, admin_token):
        resp = api.get(
            f"{API_PREFIX}/personalizacion", headers=auth_header(admin_token)
        )
        assert resp.status_code == 200, resp.text
        assert resp.json() == {
            "color_primario": "#0f3d3b",
            "color_secundario": "#b9852f",
            "nombre_sistema": "SIGEM Colombia",
            "logo_data_url": None,
        }

    def test_put_crea_la_configuracion(self, api, admin_token):
        resp = _put(api, admin_token, _payload(color_primario="#ABCDEF"))
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["color_primario"] == "#abcdef"
        assert data["color_secundario"] == "#b9852f"

    def test_get_devuelve_la_configuracion_guardada(self, api, admin_token):
        _put(api, admin_token, _payload(nombre_sistema="Municipio Demo"))
        resp = api.get(
            f"{API_PREFIX}/personalizacion", headers=auth_header(admin_token)
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["nombre_sistema"] == "Municipio Demo"

    def test_put_actualiza_la_configuracion_existente(self, api, admin_token):
        _put(api, admin_token, _payload(nombre_sistema="Primera versión"))
        resp = _put(api, admin_token, _payload(nombre_sistema="Segunda versión"))
        assert resp.status_code == 200, resp.text
        assert resp.json()["nombre_sistema"] == "Segunda versión"

        get_resp = api.get(
            f"{API_PREFIX}/personalizacion", headers=auth_header(admin_token)
        )
        assert get_resp.json()["nombre_sistema"] == "Segunda versión"

    def test_put_guarda_y_limpia_el_nombre(self, api, admin_token):
        resp = _put(api, admin_token, _payload(nombre_sistema="  Nombre recortado  "))
        assert resp.status_code == 200, resp.text
        assert resp.json()["nombre_sistema"] == "Nombre recortado"

    def test_put_con_logotipo_png(self, api, admin_token):
        resp = _put(api, admin_token, _payload(logo_data_url=PNG_DATA_URL))
        assert resp.status_code == 200, resp.text
        assert resp.json()["logo_data_url"] == PNG_DATA_URL

        get_resp = api.get(
            f"{API_PREFIX}/personalizacion", headers=auth_header(admin_token)
        )
        assert get_resp.json()["logo_data_url"] == PNG_DATA_URL

    def test_put_sin_logotipo_limpia_el_anterior(self, api, admin_token):
        _put(api, admin_token, _payload(logo_data_url=PNG_DATA_URL))
        resp = _put(api, admin_token, _payload(logo_data_url=None))
        assert resp.status_code == 200, resp.text
        assert resp.json()["logo_data_url"] is None

    def test_gestor_no_puede_guardar(self, api, gestor_token):
        resp = _put(api, gestor_token, _payload())
        assert resp.status_code == 403, resp.text

    def test_gestor_puede_leer(self, api, gestor_token):
        resp = api.get(
            f"{API_PREFIX}/personalizacion", headers=auth_header(gestor_token)
        )
        assert resp.status_code == 200, resp.text

    def test_get_sin_token_devuelve_401(self, api):
        resp = api.get(f"{API_PREFIX}/personalizacion")
        assert resp.status_code == 401

    def test_put_sin_token_devuelve_401(self, api):
        resp = api.put(f"{API_PREFIX}/personalizacion", json=_payload())
        assert resp.status_code == 401

    def test_put_con_color_invalido_devuelve_422(self, api, admin_token):
        resp = _put(api, admin_token, _payload(color_primario="#GGGGGG"))
        assert resp.status_code == 422, resp.text

    def test_put_con_logotipo_invalido_devuelve_422(self, api, admin_token):
        resp = _put(api, admin_token, _payload(logo_data_url="no-es-una-imagen"))
        assert resp.status_code == 422, resp.text


class TestPersonalizacionSchemas:
    def test_colores_validos_se_normalizan_a_minusculas(self):
        data = PersonalizacionUpdate(**_payload(color_primario="#ABCDEF"))
        assert data.color_primario == "#abcdef"

    def test_color_con_longitud_invalida(self):
        with pytest.raises(ValidationError):
            PersonalizacionUpdate(**_payload(color_primario="verde"))

    def test_color_no_hexadecimal(self):
        with pytest.raises(ValidationError):
            PersonalizacionUpdate(**_payload(color_primario="#GGGGGG"))

    def test_nombre_vacio(self):
        with pytest.raises(ValidationError):
            PersonalizacionUpdate(**_payload(nombre_sistema=""))

    def test_nombre_solo_espacios(self):
        with pytest.raises(ValidationError):
            PersonalizacionUpdate(**_payload(nombre_sistema="   "))

    def test_nombre_excede_longitud_maxima(self):
        with pytest.raises(ValidationError):
            PersonalizacionUpdate(**_payload(nombre_sistema="x" * 121))

    def test_logo_no_es_data_url(self):
        with pytest.raises(ValidationError):
            PersonalizacionUpdate(**_payload(logo_data_url="logo.png"))

    def test_logo_data_url_sin_base64(self):
        with pytest.raises(ValidationError):
            PersonalizacionUpdate(**_payload(logo_data_url="data:image/png,abc"))

    def test_logo_con_caracteres_invalidos(self):
        with pytest.raises(ValidationError):
            PersonalizacionUpdate(**_payload(logo_data_url="data:image/png;base64,***"))

    def test_logo_supera_el_tamano_maximo(self):
        payload_grande = "data:image/png;base64," + "A" * (MAX_LOGO_B64_CHARS + 1)
        with pytest.raises(ValidationError):
            PersonalizacionUpdate(**_payload(logo_data_url=payload_grande))

    def test_logo_svg_valido(self):
        data = PersonalizacionUpdate(**_payload(logo_data_url=SVG_DATA_URL))
        assert data.logo_data_url == SVG_DATA_URL

    def test_logo_nulo_es_valido(self):
        data = PersonalizacionUpdate(**_payload(logo_data_url=None))
        assert data.logo_data_url is None
