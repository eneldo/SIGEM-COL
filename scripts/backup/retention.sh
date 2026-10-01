#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"

if [ ! -d "$BACKUP_DIR" ]; then
    exit 0
fi

find "$BACKUP_DIR" -maxdepth 1 -type f -name 'db_*.dump' -mtime +"$RETENTION_DAYS" -delete
find "$BACKUP_DIR" -maxdepth 1 -type f -name 'evidencias_*.tar.gz' -mtime +"$RETENTION_DAYS" -delete
find "$BACKUP_DIR" -maxdepth 1 -type f -name 'manifest_*.json' -mtime +"$RETENTION_DAYS" -delete
