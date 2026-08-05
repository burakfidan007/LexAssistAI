#!/usr/bin/env bash
# MongoDB restore — restores a gzip archive produced by backup-mongo.sh
# into the running mongo container.
#
# Usage:  ./scripts/restore-mongo.sh ./backups/lexassist-YYYYmmdd-HHMMSS.archive.gz
#
# WARNING: --drop replaces the current lexassist database. Take a fresh
# backup first if the current data matters.
set -euo pipefail

cd "$(dirname "$0")/.."

ARCHIVE="${1:-}"
if [[ -z "$ARCHIVE" || ! -f "$ARCHIVE" ]]; then
    echo "Usage: $0 <path-to-archive.gz>"
    echo "Available backups:"
    ls -1t ./backups/lexassist-*.archive.gz 2>/dev/null || echo "  (none found)"
    exit 1
fi

set -a; . ./.env; set +a

read -r -p "This will REPLACE the current 'lexassist' database with ${ARCHIVE}. Continue? [y/N] " confirm
[[ "$confirm" == "y" || "$confirm" == "Y" ]] || { echo "Aborted."; exit 0; }

echo "[$(date)] Restoring from ${ARCHIVE} ..."
docker exec -i lexassist-mongo mongorestore \
    --username "${MONGO_INITDB_ROOT_USERNAME}" \
    --password "${MONGO_INITDB_ROOT_PASSWORD}" \
    --authenticationDatabase admin \
    --nsInclude 'lexassist.*' \
    --drop --archive --gzip < "$ARCHIVE"

echo "[$(date)] Restore complete."
