#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-${POSTGRES_USER:-sigem}}"
DB_NAME="${DB_NAME:-${POSTGRES_DB:-sigem_db}}"
DB_PASSWORD="${DB_PASSWORD:-${POSTGRES_PASSWORD:-}}"

export PGPASSWORD="$DB_PASSWORD"

mkdir -p "$BACKUP_DIR"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT="$BACKUP_DIR/db_${TIMESTAMP}.dump"

pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --no-password -Fc -f "$OUTPUT"

if [ ! -s "$OUTPUT" ]; then
    echo "error: pg_dump produced an empty file" >&2
    exit 1
fi

echo "$OUTPUT"
