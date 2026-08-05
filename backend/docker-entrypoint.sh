#!/bin/sh
set -e

# Runs as root only long enough to make the mounted storage volumes writable
# by the unprivileged app user (named volumes are created root-owned, and a
# build-time chown is shadowed by the runtime mount), then drops privileges
# and execs the app as appuser. Works for both fresh and pre-existing volumes.
chown -R appuser:appuser /app/storage 2>/dev/null || true

exec gosu appuser "$@"
