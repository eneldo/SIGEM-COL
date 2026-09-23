"""Tests de seguridad - Inyección SQL, XSS, rate limiting, auth bypass."""
import time
import pytest
from tests.conftest import API_PREFIX, auth_header


class TestSQLInjection:
    """Pruebas de resistencia a inyección SQL."""

    SQL_PAYLOADS = [
        "' OR '1'='1",
        "'; DROP TABLE usuarios; --",
        "' UNION SELECT * FROM usuarios --",
        "admin'--",
        "1' AND SLEEP(5) --",
        "'; INSERT INTO usuarios (username) VALUES ('hacked'); --",
        "1' OR 1=1 LIMIT 1 --",
    ]

    @pytest.mark.parametrize("payload", SQL_PAYLOADS)
    def test_login_sql_injection(self, api, payload):
        resp = api.post(f"{API_PREFIX}/auth/login", json={
            "username": payload,
            "password": "anything_12345",
        })
        # Should NOT return 200 with a valid token
        # 429 = rate limited (acceptable)
        assert resp.status_code in (401, 422, 429)
        if resp.status_code == 200:
            assert "access_token" not in resp.json()

    @pytest.mark.parametrize("payload", SQL_PAYLOADS)
    def test_search_sql_injection(self, api, admin_token, payload):
        resp = api.get(
            f"{API_PREFIX}/usuarios?search={payload}",
            headers=auth_header(admin_token),
        )
        # 429 = rate limited (acceptable)
        assert resp.status_code in (200, 400, 422, 429)


class TestXSSProtection:
    """Pruebas de protección contra XSS."""

    XSS_PAYLOADS = [
        '<script>alert("XSS")</script>',
        '<img src="x" onerror="alert(1)">',
        '"><script>alert("xss")</script>',
        "javascript:alert(1)",
        '<svg onload="alert(1)">',
    ]

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_search_xss_in_usuarios(self, api, admin_token, payload):
        resp = api.get(
            f"{API_PREFIX}/usuarios?search={payload}",
            headers=auth_header(admin_token),
        )
        # 429 = rate limited (acceptable)
        assert resp.status_code in (200, 400, 422, 429)

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_create_user_xss_in_name(self, api, admin_token, payload):
        resp = api.post(f"{API_PREFIX}/usuarios", json={
            "codigo": f"XSS-{hash(payload) % 10000:04d}",
            "username": f"xss_test_{hash(payload) % 10000}",
            "email": f"xss{hash(payload) % 10000}@test.com",
            "nombre_completo": payload,
            "password": "TestPassword2026!!",
        }, headers=auth_header(admin_token))
        if resp.status_code == 201:
            data = resp.json()
            # Cleanup
            api.delete(f"{API_PREFIX}/usuarios/{data['id']}", headers=auth_header(admin_token))


class TestAuthBypass:
    """Pruebas de bypass de autenticación."""

    PROTECTED_ENDPOINTS = [
        "GET /usuarios",
        "GET /lineas-estrategicas",
        "GET /programas",
        "GET /productos",
    ]

    def test_no_token_bypass(self, api):
        resp = api.get(f"{API_PREFIX}/usuarios")
        assert resp.status_code == 401

    def test_fake_token_bypass(self, api):
        resp = api.get(
            f"{API_PREFIX}/usuarios",
            headers=auth_header("eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJoYWNrZXIifQ.fake"),
        )
        assert resp.status_code in (401, 403, 429)

    def test_malformed_bearer(self, api):
        resp = api.get(
            f"{API_PREFIX}/usuarios",
            headers={"Authorization": "Bearer invalid_token_value"},
        )
        assert resp.status_code in (401, 429)


class TestSecurityHeaders:
    """Pruebas de headers de seguridad HTTP."""

    def test_security_headers_present(self, api):
        resp = api.get("/health")
        headers = resp.headers
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("X-XSS-Protection") == "1; mode=block"
        assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


class TestInputValidation:
    """Pruebas de validación de entrada."""

    def test_login_username_too_short(self, api):
        resp = api.post(f"{API_PREFIX}/auth/login", json={
            "username": "ab",
            "password": "valid_password_123",
        })
        assert resp.status_code in (422, 429)

    def test_login_password_empty(self, api):
        resp = api.post(f"{API_PREFIX}/auth/login", json={
            "username": "admin",
            "password": "",
        })
        assert resp.status_code in (422, 429)

    def test_invalid_uuid_format(self, api, admin_token):
        resp = api.get(
            f"{API_PREFIX}/usuarios/not-a-uuid",
            headers=auth_header(admin_token),
        )
        assert resp.status_code in (400, 422, 404, 500)

    def test_negative_page(self, api, admin_token):
        resp = api.get(
            f"{API_PREFIX}/usuarios?page=-1",
            headers=auth_header(admin_token),
        )
        assert resp.status_code in (200, 422)
