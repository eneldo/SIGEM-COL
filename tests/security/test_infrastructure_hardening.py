from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROD_COMPOSE = ROOT / "infra/docker/docker-compose.prod.yml"
APP_ROLE = ROOT / "infra/postgres/init/01-app-role.sh"
BACKEND_DOCKERFILE = ROOT / "infra/docker/backend/Dockerfile"
NGINX_CONFIG = ROOT / "infra/nginx/nginx.prod.conf"


def test_production_images_are_pinned_and_require_release_tag():
    compose = PROD_COMPOSE.read_text(encoding="utf-8")

    assert ":latest" not in compose
    assert "image: nginx:alpine" not in compose
    assert "image: postgres:17-alpine" not in compose
    assert "image: redis:7-alpine" not in compose
    assert (
        "sigem-backend:${SIGEM_IMAGE_TAG:?SIGEM_IMAGE_TAG must be an immutable tag}"
        in compose
    )


def test_runtime_database_role_has_no_schema_or_database_ownership_privileges():
    script = APP_ROLE.read_text(encoding="utf-8")

    assert "NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS" in script
    assert "GRANT CONNECT ON DATABASE" in script
    assert "GRANT USAGE ON SCHEMA public" in script
    assert "GRANT USAGE, CREATE ON SCHEMA public" not in script
    assert "GRANT ALL PRIVILEGES ON DATABASE" not in script
    assert "GRANT ALL ON TABLE" not in script


def test_backend_image_uses_frozen_runtime_dependencies_only():
    dockerfile = BACKEND_DOCKERFILE.read_text(encoding="utf-8")

    assert "uv sync --frozen --no-dev" in dockerfile
    assert ".[dev]" not in dockerfile
    assert "src/backend/uv.lock" in dockerfile


def test_nginx_tls_healthcheck_verifies_certificate_and_auth_limits_are_scoped():
    compose = PROD_COMPOSE.read_text(encoding="utf-8")
    nginx = NGINX_CONFIG.read_text(encoding="utf-8")

    assert "--no-check-certificate" not in compose
    assert "--ca-certificate=/etc/nginx/tls/fullchain.pem" in compose
    assert "location = /api/v1/auth/login" in nginx
    assert "limit_req zone=auth_login burst=5 nodelay" in nginx
    assert "location = /health {\n            access_log off;" in nginx
