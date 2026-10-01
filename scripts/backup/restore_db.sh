#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-${POSTGRES_USER:-sigem}}"
DB_NAME="${DB_NAME:-${POSTGRES_DB:-sigem_db}}"
DB_PASSWORD="${DB_PASSWORD:-${POSTGRES_PASSWORD:-}}"

export PGPASSWORD="$DB_PASSWORD"

DUMP_FILE=""
ASSUME_YES=0
FORCE=0
CLEAN=0

usage() {
    echo "usage: restore_db.sh <dump-file> --yes [--force] [--clean]" >&2
    echo "  --yes     required confirmation, restore will not run without it" >&2
    echo "  --force   restore even if the target database has active connections" >&2
    echo "  --clean   drop existing objects before restoring (pg_restore --clean --if-exists)" >&2
    exit 1
}

while [ $# -gt 0 ]; do
    case "$1" in
        --yes) ASSUME_YES=1 ;;
        --force) FORCE=1 ;;
        --clean) CLEAN=1 ;;
        -h|--help) usage ;;
        *)
            if [ -n "$DUMP_FILE" ]; then
                usage
            fi
            DUMP_FILE="$1"
            ;;
    esac
    shift
done

if [ -z "$DUMP_FILE" ]; then
    usage
fi

if [ ! -f "$DUMP_FILE" ]; then
    echo "error: dump file not found: $DUMP_FILE" >&2
    exit 1
fi

if [ ! -s "$DUMP_FILE" ]; then
    echo "error: dump file is empty: $DUMP_FILE" >&2
    exit 1
fi

if [ "$ASSUME_YES" -ne 1 ]; then
    echo "error: refusing to restore without explicit --yes" >&2
    exit 1
fi

ACTIVE="$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --no-password -tAc "SELECT count(*) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();")"

ACTIVE="$(printf '%s' "$ACTIVE" | tr -d '[:space:]')"

if [ "$ACTIVE" != "0" ]; then
    if [ "$FORCE" -eq 0 ]; then
        echo "error: target database '$DB_NAME' has $ACTIVE active connection(s) other than this session" >&2
        echo "stop the application stack or rerun with --force" >&2
        exit 1
    fi
    echo "warning: proceeding with --force despite $ACTIVE active connection(s)" >&2
fi

RESTORE_ARGS=(-h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --no-password)

if [ "$CLEAN" -eq 1 ]; then
    RESTORE_ARGS+=(--clean --if-exists)
fi

echo "restoring $DUMP_FILE into $DB_NAME@$DB_HOST"

pg_restore "${RESTORE_ARGS[@]}" "$DUMP_FILE"

echo "restore completed"
echo "if the dump predates a schema migration, redeploy the matching image tag or apply alembic migrations before serving traffic"
