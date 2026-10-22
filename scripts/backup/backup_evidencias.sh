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

# Cifrado opcional en reposo (mismo esquema que backup_db.sh): AES-256-CBC con
# PBKDF2, passphrase solo por entorno, salida evidencias_<ts>.tar.gz.enc.
if [ -n "${BACKUP_ENCRYPTION_PASSPHRASE:-}" ]; then
    openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt \
        -pass env:BACKUP_ENCRYPTION_PASSPHRASE \
        -in "$OUTPUT" -out "$OUTPUT.enc"
    if [ "${BACKUP_KEEP_PLAINTEXT:-false}" != "true" ]; then
        rm -f "$OUTPUT"
        OUTPUT="$OUTPUT.enc"
    else
        OUTPUT="$OUTPUT.enc"
        echo "warning: BACKUP_KEEP_PLAINTEXT=true keeps an unencrypted archive on disk" >&2
    fi
fi

echo "$OUTPUT"
