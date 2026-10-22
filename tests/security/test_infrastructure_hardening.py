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
    assert "sigem-backend:${SIGEM_IMAGE_TAG:?SIGEM_IMAGE_TAG must be an immutable tag}" in compose


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


def test_nginx_rejects_unknown_host_and_sni_and_serves_only_sigem_domain():
    compose = PROD_COMPOSE.read_text(encoding="utf-8")
    nginx = NGINX_CONFIG.read_text(encoding="utf-8")

    # Vhost default de descarte: Host/SNI desconocidos no reciben respuesta.
    assert "listen 80 default_server" in nginx
    assert "listen 443 ssl default_server" in nginx
    assert "ssl_reject_handshake on" in nginx
    assert "return 444;" in nginx
    # Solo el dominio declarado en el entorno sirve trafico real.
    assert "server_name ${SIGEM_DOMAIN};" in nginx
    assert "SIGEM_DOMAIN: ${SIGEM_DOMAIN:?SIGEM_DOMAIN must be the public hostname" in compose
    assert "NGINX_ENVSUBST_OUTPUT_DIR: /etc/nginx" in compose
    assert "templates/nginx.conf.template" in compose


def test_dev_and_local_composes_bind_management_ports_to_loopback():
    repo = ROOT / "infra/docker"
    for name, ports in (
        ("docker-compose.yml", ["5433", "8001", "3001"]),
        ("docker-compose.local.yml", ["8080", "8443"]),
    ):
        compose = (repo / name).read_text(encoding="utf-8")
        ports_block = "\n".join(
            line
            for line in compose.splitlines()
            if "ports:" in line or line.strip().startswith('- "')
        )
        for port in ports:
            assert f'"127.0.0.1:{port}:' in ports_block, (
                f"{name}: port {port} not bound to loopback"
            )


def test_prometheus_uses_metrics_token_and_alerts_have_live_targets():
    repo = ROOT / "infra/monitoring"
    prometheus = (repo / "prometheus.yml").read_text(encoding="utf-8")
    alerts = (repo / "alerts.yml").read_text(encoding="utf-8")

    # El backend exige Bearer cuando METRICS_TOKEN esta configurado; el scrape
    # lo lee desde archivo generado por el entrypoint del contenedor.
    assert "bearer_token_file: /etc/prometheus/metrics_token" in prometheus
    assert "sigem-backend" in prometheus
    # Alertado por Alertmanager en el stack.
    assert "alertmanager:9093" in prometheus
    # Las alertas muertas (sin exporter asociado) no deben volver.
    assert "pg_stat_activity_count" not in alerts
    assert "node_filesystem_avail_bytes" not in alerts
    # Alertas con metricas reales del backend.
    assert "http_requests_total" in alerts
    assert "alertmanager.yml" in (Path(ROOT) / "infra/docker/docker-compose.prod.yml").read_text()


def test_dashboard_metrics_token_env_written_before_prometheus_start():
    compose = (ROOT / "infra/docker/docker-compose.prod.yml").read_text(encoding="utf-8")
    assert "printf '%s' \"$$METRICS_TOKEN\" > /etc/prometheus/metrics_token" in compose
    assert "prom/alertmanager" in compose


def test_backup_pipeline_supports_encryption_and_offsite_gate():
    backup = "scripts/backup"
    run_backup = (ROOT / backup / "run_backup.sh").read_text(encoding="utf-8")
    backup_db = (ROOT / backup / "backup_db.sh").read_text(encoding="utf-8")
    verify = (ROOT / backup / "verify_backup.sh").read_text(encoding="utf-8")
    restore = (ROOT / backup / "restore_db.sh").read_text(encoding="utf-8")

    # Offsite: advertencia explícita siempre, error si se exige offsite.
    assert "BACKUP_REQUIRE_OFFSITE" in run_backup
    assert "no off-site copy was made" in run_backup
    # Cifrado at-rest opcional y passphrase SOLO por entorno.
    assert "openssl enc -aes-256-cbc -pbkdf2" in backup_db
    assert "-pass env:BACKUP_ENCRYPTION_PASSPHRASE" in backup_db
    # Restaurar soporta dumps cifrados y descifra a temporal.
    assert "*.enc" in restore
    assert "BACKUP_ENCRYPTION_PASSPHRASE" in restore
    # pg_restore --list se salta dumps cifrados.
    assert "*.dump.enc" in verify
