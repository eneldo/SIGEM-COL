#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
TARGET="${1:-}"

resolve_manifest() {
    if [ -f "$BACKUP_DIR/manifest.json" ]; then
        printf '%s' "$BACKUP_DIR/manifest.json"
        return 0
    fi
    ls -1t "$BACKUP_DIR"/manifest_*.json 2>/dev/null | head -n 1 || true
}

manifest_for_name() {
    local name="$1"
    local candidate
    for candidate in "$BACKUP_DIR/manifest.json" $(ls -1 "$BACKUP_DIR"/manifest_*.json 2>/dev/null | sort -r); do
        if [ -f "$candidate" ] && grep -q "\"name\":\"$name\"" "$candidate"; then
            printf '%s' "$candidate"
            return 0
        fi
    done
    return 1
}

extract_field() {
    local entry="$1"
    local field="$2"
    printf '%s' "$entry" | sed -n "s/.*\"$field\":\"\([^\"]*\)\".*/\1/p"
}

verify_entry() {
    local entry="$1"
    local name sha file actual
    name="$(extract_field "$entry" name)"
    sha="$(extract_field "$entry" sha256)"
    file="$BACKUP_DIR/$name"
    if [ -z "$name" ] || [ -z "$sha" ]; then
        echo "error: malformed manifest entry: $entry" >&2
        return 1
    fi
    if [ ! -f "$file" ]; then
        echo "missing: $name" >&2
        return 1
    fi
    actual="$(sha256sum "$file" | cut -d' ' -f1)"
    if [ "$actual" != "$sha" ]; then
        echo "checksum mismatch: $name" >&2
        return 1
    fi
    echo "checksum ok: $name"
    case "$name" in
        *.dump)
            if pg_restore --list "$file" >/dev/null 2>&1; then
                echo "pg_restore --list ok: $name"
            else
                echo "pg_restore --list failed: $name" >&2
                return 1
            fi
            ;;
    esac
    return 0
}

SINGLE_ENTRY=""

if [ -z "$TARGET" ]; then
    TARGET="$(resolve_manifest)"
elif [ -f "$TARGET" ]; then
    case "$TARGET" in
        *.dump)
            DUMP_BASE="$(basename "$TARGET")"
            MANIFEST_FOR_DUMP="$(manifest_for_name "$DUMP_BASE")" || {
                echo "error: no manifest in $BACKUP_DIR references $DUMP_BASE" >&2
                exit 1
            }
            SINGLE_ENTRY="$(grep -o "{\"name\":\"$DUMP_BASE\"[^}]*}" "$MANIFEST_FOR_DUMP")"
            if [ -z "$SINGLE_ENTRY" ]; then
                echo "error: manifest $MANIFEST_FOR_DUMP has no entry for $DUMP_BASE" >&2
                exit 1
            fi
            TARGET="$MANIFEST_FOR_DUMP"
            ;;
    esac
fi

if [ -z "$TARGET" ] || [ ! -f "$TARGET" ]; then
    echo "error: no manifest found in $BACKUP_DIR" >&2
    exit 1
fi

FAILED=0

if [ -n "$SINGLE_ENTRY" ]; then
    if ! verify_entry "$SINGLE_ENTRY"; then
        FAILED=1
    fi
else
    ENTRIES="$(grep -o '{"name":"[^}]*}' "$TARGET" || true)"
    if [ -z "$ENTRIES" ]; then
        echo "error: no file entries in manifest: $TARGET" >&2
        exit 1
    fi
    while IFS= read -r ENTRY; do
        [ -n "$ENTRY" ] || continue
        if ! verify_entry "$ENTRY"; then
            FAILED=1
        fi
    done <<< "$ENTRIES"
fi

if [ "$FAILED" -ne 0 ]; then
    echo "verification FAILED for $TARGET" >&2
    exit 1
fi

echo "verification passed for $TARGET"
