#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
EVIDENCIAS_DIR="${EVIDENCIAS_DIR:-/data/evidencias}"

mkdir -p "$BACKUP_DIR"

if [ ! -d "$EVIDENCIAS_DIR" ]; then
    echo "error: evidencias directory not found: $EVIDENCIAS_DIR" >&2
    exit 1
fi

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT="$BACKUP_DIR/evidencias_${TIMESTAMP}.tar.gz"

tar -czf "$OUTPUT" -C "$(dirname "$EVIDENCIAS_DIR")" "$(basename "$EVIDENCIAS_DIR")"

if [ ! -s "$OUTPUT" ]; then
    echo "error: tar produced an empty archive" >&2
    exit 1
fi

echo "$OUTPUT"
