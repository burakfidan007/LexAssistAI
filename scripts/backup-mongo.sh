#!/usr/bin/env bash
# MongoDB backup — dumps the lexassist database from the running mongo
# container into ./backups/lexassist-YYYYmmdd-HHMMSS.archive.gz
#
# Usage:  ./scripts/backup-mongo.sh
# Cron :  0 3 * * *  cd /opt/lexassist-ai && ./scripts/backup-mongo.sh >> /var/log/lexassist-backup.log 2>&1
set -euo pipefail

cd "$(dirname "$0")/.."

# Load Mongo credentials from .env (MONGO_INITDB_ROOT_USERNAME/PASSWORD).
set -a; . ./.env; set +a

BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
ARCHIVE="lexassist-${STAMP}.archive.gz"

echo "[$(date)] Backing up to ${BACKUP_DIR}/${ARCHIVE} ..."
docker exec lexassist-mongo mongodump \
    --username "${MONGO_INITDB_ROOT_USERNAME}" \
    --password "${MONGO_INITDB_ROOT_PASSWORD}" \
    --authenticationDatabase admin \
    --db lexassist \
    --archive --gzip > "${BACKUP_DIR}/${ARCHIVE}"

# Keep only the 14 most recent backups.
ls -1t "${BACKUP_DIR}"/lexassist-*.archive.gz | tail -n +15 | xargs -r rm -f

echo "[$(date)] Backup complete: ${BACKUP_DIR}/${ARCHIVE}"
