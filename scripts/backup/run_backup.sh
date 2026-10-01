#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
BACKUP_RSYNC_TARGET="${BACKUP_RSYNC_TARGET:-}"
SIGEM_VERSION="${SIGEM_VERSION:-${APP_VERSION:-unknown}}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$BACKUP_DIR"

DB_FILE="$("$SCRIPT_DIR/backup_db.sh")"
EV_FILE="$("$SCRIPT_DIR/backup_evidencias.sh")"

"$SCRIPT_DIR/retention.sh"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
CREATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
DB_NAME_BASE="$(basename "$DB_FILE")"
EV_NAME_BASE="$(basename "$EV_FILE")"
DB_SHA="$(sha256sum "$DB_FILE" | cut -d' ' -f1)"
EV_SHA="$(sha256sum "$EV_FILE" | cut -d' ' -f1)"
DB_SIZE="$(stat -c %s "$DB_FILE")"
EV_SIZE="$(stat -c %s "$EV_FILE")"
MANIFEST="$BACKUP_DIR/manifest_${TIMESTAMP}.json"

cat > "$MANIFEST" <<EOF
{
  "version": "$SIGEM_VERSION",
  "timestamp": "$CREATED_AT",
  "files": [
    {"name":"$DB_NAME_BASE","type":"database","sha256":"$DB_SHA","size":$DB_SIZE},
    {"name":"$EV_NAME_BASE","type":"evidencias","sha256":"$EV_SHA","size":$EV_SIZE}
  ]
}
EOF

cp "$MANIFEST" "$BACKUP_DIR/manifest.json"

if [ -n "$BACKUP_RSYNC_TARGET" ]; then
    rsync -a "$DB_FILE" "$EV_FILE" "$MANIFEST" "$BACKUP_RSYNC_TARGET"
fi

echo "backup completed"
echo "database: $DB_FILE (sha256=$DB_SHA)"
echo "evidencias: $EV_FILE (sha256=$EV_SHA)"
echo "manifest: $MANIFEST"
