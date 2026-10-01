#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="infra/docker/docker-compose.prod.yml"
PROJECT="sigem-prod"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="$REPO_ROOT/infra/docker/.env.prod"

usage() {
    echo "usage: rollback.sh <previous-image-tag>" >&2
    echo "example: rollback.sh v1.2.2" >&2
    exit 1
}

fail() {
    echo "" >&2
    echo "ROLLBACK FAILED: $1" >&2
    echo "Inspect logs with: docker compose -f $COMPOSE_FILE -p $PROJECT logs --tail=100" >&2
    exit 1
}

if [ $# -ne 1 ]; then
    usage
fi

PREV_TAG="$1"
export SIGEM_IMAGE_TAG="$PREV_TAG"

cd "$REPO_ROOT"

compose() {
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT" "$@"
}

if [ ! -f "$ENV_FILE" ]; then
    fail "missing $ENV_FILE"
fi

echo "Rolling back to image tag: $PREV_TAG"
echo ""
echo "Rollback in SIGEM means redeploying the previous image tag."
echo "Automatic alembic downgrade is NOT performed, because downgrading the"
echo "database schema is destructive and can lose data."
echo "If the failed release already applied migrations, redeploying the old"
echo "image tag is not enough: restore the database from the most recent"
echo "backup first, then keep the old tag running:"
echo "  docker compose -f $COMPOSE_FILE -p $PROJECT exec backup ls -lt /backups"
echo "  docker compose -f $COMPOSE_FILE -p $PROJECT run --rm backup /backup/restore_db.sh /backups/<dump-file> --yes"
echo "  bash scripts/setup/rollback.sh $PREV_TAG"
echo ""

if ! docker image inspect "sigem-backend:$PREV_TAG" >/dev/null 2>&1; then
    compose pull backend >/dev/null 2>&1 || true
fi
if ! docker image inspect "sigem-backend:$PREV_TAG" >/dev/null 2>&1; then
    fail "image sigem-backend:$PREV_TAG not available locally and could not be pulled"
fi

if ! compose up -d --remove-orphans; then
    fail "compose up with tag $PREV_TAG failed"
fi

echo "waiting for stack health"
ATTEMPTS=0
MAX_ATTEMPTS=60
HEALTHY=0
while [ "$ATTEMPTS" -lt "$MAX_ATTEMPTS" ]; do
    if compose exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)" >/dev/null 2>&1; then
        if compose exec -T nginx wget -q --no-check-certificate -O /dev/null https://127.0.0.1/ >/dev/null 2>&1; then
            HEALTHY=1
            break
        fi
    fi
    ATTEMPTS=$(( ATTEMPTS + 1 ))
    sleep 5
done

if [ "$HEALTHY" -ne 1 ]; then
    compose ps >&2 || true
    fail "stack did not become healthy with tag $PREV_TAG"
fi

echo ""
echo "ROLLBACK OK: tag $PREV_TAG is running"
echo "Post-rollback: verify the application against the restored database before closing the incident."
compose ps
