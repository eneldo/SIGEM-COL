#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TLS_DIR="$REPO_ROOT/infra/tls"

mkdir -p "$TLS_DIR"

if command -v docker >/dev/null 2>&1; then
    HOST_PATH="$TLS_DIR"
    if command -v cygpath >/dev/null 2>&1; then
        HOST_PATH="$(cygpath -m "$TLS_DIR")"
    fi
    MSYS_NO_PATHCONV=1 docker run --rm -v "$HOST_PATH:/certs" alpine/openssl req -x509 -nodes -newkey rsa:2048 -days 365 -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" -keyout /certs/privkey.pem -out /certs/fullchain.pem
elif command -v openssl >/dev/null 2>&1; then
    openssl req -x509 -nodes -newkey rsa:2048 -days 365 -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" -keyout "$TLS_DIR/privkey.pem" -out "$TLS_DIR/fullchain.pem"
else
    echo "error: neither docker nor openssl is available to generate certificates" >&2
    exit 1
fi

chmod 600 "$TLS_DIR/privkey.pem"
chmod 644 "$TLS_DIR/fullchain.pem"
echo "certificate written to $TLS_DIR/fullchain.pem and $TLS_DIR/privkey.pem"
