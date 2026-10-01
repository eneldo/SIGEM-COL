#!/usr/bin/env bash
set -euo pipefail

BACKUP_TIME="${BACKUP_TIME:-03:00}"
export TZ="${TZ:-America/Bogota}"
RUN_SCRIPT="${RUN_SCRIPT:-/backup/run_backup.sh}"

log() {
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [backup-scheduler] $*"
}

next_run_epoch() {
    local target now
    target="$(date -d "today $BACKUP_TIME" +%s)"
    now="$(date +%s)"
    if [ "$target" -le "$now" ]; then
        date -d "tomorrow $BACKUP_TIME" +%s
    else
        printf '%s' "$target"
    fi
}

log "scheduler started: daily backup at $BACKUP_TIME in $TZ"

while true; do
    TARGET_EPOCH="$(next_run_epoch)"
    NOW_EPOCH="$(date +%s)"
    SLEEP_SECONDS=$(( TARGET_EPOCH - NOW_EPOCH ))
    log "next backup in ${SLEEP_SECONDS}s"
    sleep "$SLEEP_SECONDS"
    log "starting scheduled backup"
    if "$RUN_SCRIPT"; then
        log "scheduled backup completed"
    else
        log "scheduled backup failed with exit code $?"
    fi
done
