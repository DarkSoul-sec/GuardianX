#!/bin/sh
set -e

echo "[entrypoint] Waiting for database at ${DATABASE_HOST}:${DATABASE_PORT}..."
python - <<'PY'
import os
import socket
import time

host = os.environ.get("DATABASE_HOST", "postgres")
port = int(os.environ.get("DATABASE_PORT", "5432"))

for attempt in range(30):
    try:
        with socket.create_connection((host, port), timeout=2):
            break
    except OSError:
        if attempt == 29:
            raise
        time.sleep(2)
else:
    raise RuntimeError(f"Timed out waiting for database at {host}:{port}")
PY

if [ -z "${POSTGRES_MIGRATE_USER:-}" ] || [ -z "${POSTGRES_MIGRATE_PASSWORD:-}" ]; then
    echo "[entrypoint] ERROR: POSTGRES_MIGRATE_USER / POSTGRES_MIGRATE_PASSWORD must be set." >&2
    exit 1
fi

echo "[entrypoint] Running database migrations as ${POSTGRES_MIGRATE_USER}..."
DATABASE_USER="$POSTGRES_MIGRATE_USER" \
DATABASE_PASSWORD="$POSTGRES_MIGRATE_PASSWORD" \
  alembic upgrade head

echo "[entrypoint] Starting application as ${DATABASE_USER}..."
# Strip bootstrap/migration credentials from the runtime process environment so
# uvicorn never has access to the SUPERUSER or migration-role password.
exec env -u POSTGRES_DB -u POSTGRES_USER -u POSTGRES_PASSWORD \
  -u POSTGRES_MIGRATE_USER -u POSTGRES_MIGRATE_PASSWORD \
  uvicorn app.main:app --host 0.0.0.0 --port 8000
