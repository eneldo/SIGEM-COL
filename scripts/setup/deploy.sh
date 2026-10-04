#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="infra/docker/docker-compose.prod.yml"
PROJECT="sigem-prod"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="$REPO_ROOT/infra/docker/.env.prod"
TLS_DIR="$REPO_ROOT/infra/tls"
BACKEND_IMAGE="sigem-backend"
FRONTEND_IMAGE="sigem-frontend"
BACKUP_IMAGE="sigem-backup"

usage() {
    echo "usage: deploy.sh <image-tag>" >&2
    echo "example: deploy.sh v1.2.3" >&2
    exit 1
}

fail() {
    echo "" >&2
    echo "DEPLOY FAILED: $1" >&2
    echo "" >&2
    echo "Rollback instructions:" >&2
    echo "  1. Redeploy the previous known-good tag:" >&2
    echo "       bash scripts/setup/rollback.sh <previous-tag>" >&2
    echo "  2. If the migrate service already applied new migrations, redeploying the" >&2
    echo "     previous image tag is NOT enough. Restore the database from the most" >&2
    echo "     recent backup and then redeploy the previous tag:" >&2
    echo "       docker compose -f $COMPOSE_FILE -p $PROJECT exec backup ls -lt /backups" >&2
    echo "       docker compose -f $COMPOSE_FILE -p $PROJECT run --rm backup /backup/restore_db.sh /backups/<dump-file> --yes" >&2
    echo "       bash scripts/setup/rollback.sh <previous-tag>" >&2
    exit 1
}

if [ $# -ne 1 ]; then
    usage
fi

TAG="$1"
if [[ ! "$TAG" =~ ^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$ ]]; then
    fail "invalid immutable image tag"
fi
export SIGEM_IMAGE_TAG="$TAG"

cd "$REPO_ROOT"

compose() {
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT" "$@"
}

if [ ! -f "$ENV_FILE" ]; then
    fail "missing $ENV_FILE (copy infra/docker/.env.prod.example and fill in real values)"
fi

if [ ! -f "$TLS_DIR/fullchain.pem" ] || [ ! -f "$TLS_DIR/privkey.pem" ]; then
    fail "missing trusted TLS certificates in infra/tls (follow docs/operations/tls.md)"
fi

if grep -Eqi 'CHANGE_ME|CHANGEME|\.example' "$ENV_FILE"; then
    fail "production environment still contains placeholder values"
fi

if ! openssl x509 -in "$TLS_DIR/fullchain.pem" -noout -checkend 2592000 >/dev/null 2>&1; then
    fail "TLS certificate is invalid or expires in less than 30 days"
fi

CERT_PUBKEY="$(openssl x509 -in "$TLS_DIR/fullchain.pem" -pubkey -noout 2>/dev/null | openssl pkey -pubin -outform pem 2>/dev/null)"
KEY_PUBKEY="$(openssl pkey -in "$TLS_DIR/privkey.pem" -pubout -outform pem 2>/dev/null)"
if [ -z "$CERT_PUBKEY" ] || [ "$CERT_PUBKEY" != "$KEY_PUBKEY" ]; then
    fail "TLS certificate and private key do not match"
fi

echo "deploying SIGEM Colombia with tag: $TAG"

missing_services=""
for pair in "$BACKEND_IMAGE:backend" "$FRONTEND_IMAGE:frontend" "$BACKUP_IMAGE:backup"; do
    image="${pair%%:*}"
    service="${pair##*:}"
    if ! docker image inspect "$image:$TAG" >/dev/null 2>&1; then
        missing_services="$missing_services $service"
    fi
done

if [ -n "$missing_services" ]; then
    echo "images not present locally for tag $TAG, pulling:$missing_services"
    for service in $missing_services; do
        compose pull "$service" || fail "unable to pull immutable image for $service"
    done
fi

for pair in "$BACKEND_IMAGE:backend" "$FRONTEND_IMAGE:frontend" "$BACKUP_IMAGE:backup"; do
    image="${pair%%:*}"
    if ! docker image inspect "$image:$TAG" >/dev/null 2>&1; then
        fail "required image $image:$TAG is unavailable"
    fi
done

if ! compose up -d --remove-orphans --no-build; then
    fail "docker compose up failed (check the migrate service logs: compose logs migrate)"
fi

echo "waiting for stack health"
ATTEMPTS=0
MAX_ATTEMPTS=60
HEALTHY=0
while [ "$ATTEMPTS" -lt "$MAX_ATTEMPTS" ]; do
    if compose exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)" >/dev/null 2>&1; then
        if compose exec -T frontend wget -q -O /dev/null http://127.0.0.1:3000/ >/dev/null 2>&1; then
            HEALTHY=1
            break
        fi
    fi
    ATTEMPTS=$(( ATTEMPTS + 1 ))
    sleep 5
done

if [ "$HEALTHY" -ne 1 ]; then
    compose ps >&2 || true
    fail "stack did not become healthy within $(( MAX_ATTEMPTS * 5 ))s"
fi

echo "running smoke checks"

if ! compose exec -T backend python -c "import urllib.request, sys; r = urllib.request.urlopen('http://localhost:8000/api/v1/health/', timeout=5); sys.exit(0 if r.status == 200 else 1)" >/dev/null; then
    fail "API smoke check failed (/api/v1/health/ inside the internal network)"
fi

if ! compose exec -T nginx wget -q --no-check-certificate -O /dev/null https://127.0.0.1/; then
    fail "frontend smoke check failed through nginx TLS (https://.../)"
fi

if ! compose exec -T nginx wget -q --no-check-certificate -O - https://127.0.0.1/api/v1/health/ | grep -q healthy; then
    fail "API smoke check failed through nginx TLS (https://.../api/v1/health/)"
fi

if ! compose exec -T nginx wget -q --no-check-certificate -O - https://127.0.0.1/health | grep -q healthy; then
    fail "backend health check failed through nginx TLS (https://.../health)"
fi

echo ""
echo "DEPLOY OK: tag $TAG is live"
compose ps
