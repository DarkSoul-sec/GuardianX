#!/usr/bin/env bash
#
# One-time / idempotent provisioning for a NATIVE (non-Docker) PostgreSQL dev
# database, using the same three-role least-privilege model as Docker.
#
# Creates (or repairs) two non-superuser roles and provisions the GuardianX
# database:
#   guardianx_migrate  - database owner, used only for `alembic upgrade head`
#   guardianx_app      - restricted runtime role used by the app
#
# The bootstrap connection uses your local PostgreSQL superuser (default
# `postgres`). It NEVER runs GuardianX as a superuser.
#
# Usage:
#   infrastructure/scripts/provision_dev_db.sh [bootstrap_user] [bootstrap_db]
#
# Environment:
#   PGPASSWORD          password for the bootstrap superuser (used if provided)
#   PROVISION_DB_HOST   default localhost
#   PROVISION_DB_PORT   default 5432
#   GX_DB_NAME          database name, default guardianx
#
# On success it writes DATABASE_USER/DATABASE_PASSWORD for the app role into
# backend/.env (creating the file from .env.example if needed).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BOOTSTRAP_USER="${1:-postgres}"
BOOTSTRAP_DB="${2:-postgres}"
DB_NAME="${GX_DB_NAME:-guardianx}"
HOST="${PROVISION_DB_HOST:-localhost}"
PORT="${PROVISION_DB_PORT:-5432}"

MIGRATE_USER="${GX_MIGRATE_USER:-guardianx_migrate}"
APP_USER="${GX_APP_USER:-guardianx_app}"

if [[ -z "${PGPASSWORD:-}" ]]; then
  echo "Using a password-less local socket for bootstrap superuser '${BOOTSTRAP_USER}'."
  echo "If that fails, set PGPASSWORD and re-run."
fi

if ! command -v psql >/dev/null 2>&1; then
  echo "error: psql not found on PATH" >&2
  exit 1
fi

# db-init.sh requires a non-empty bootstrap password. With peer/local socket
# auth psql ignores the value entirely, so a sentinel is harmless; when password
# auth is required, the operator sets PGPASSWORD and this is overridden.

# Generate fresh passwords if none exist in backend/.env.migrate already.
BACKEND_ENV="$ROOT/backend/.env"
MIGRATE_ENV="$ROOT/backend/.env.migrate"
MIGRATE_PASSWORD=""
APP_PASSWORD=""
if [[ -f "$MIGRATE_ENV" ]]; then
  MIGRATE_PASSWORD="$(grep -E '^DATABASE_PASSWORD=' "$MIGRATE_ENV" | head -1 | cut -d= -f2- || true)"
fi
if [[ -f "$BACKEND_ENV" ]]; then
  APP_PASSWORD="$(grep -E '^DATABASE_PASSWORD=' "$BACKEND_ENV" | head -1 | cut -d= -f2- || true)"
fi

if [[ -z "$MIGRATE_PASSWORD" || "$MIGRATE_PASSWORD" == your_* ]]; then
  MIGRATE_PASSWORD="$(openssl rand -hex 32)"
fi
if [[ -z "$APP_PASSWORD" || "$APP_PASSWORD" == your_* ]]; then
  APP_PASSWORD="$(openssl rand -hex 32)"
fi

export POSTGRES_DB="$DB_NAME"
export POSTGRES_USER="$BOOTSTRAP_USER"
export POSTGRES_PASSWORD="${PGPASSWORD:-dev_peer_auth_placeholder}"
export POSTGRES_MIGRATE_USER="$MIGRATE_USER"
export POSTGRES_MIGRATE_PASSWORD="$MIGRATE_PASSWORD"
export POSTGRES_APP_USER="$APP_USER"
export POSTGRES_APP_PASSWORD="$APP_PASSWORD"
export PROVISION_DB_HOST="$HOST"
export PROVISION_DB_PORT="$PORT"

# Ensure the GuardianX database exists.
psql --username "$BOOTSTRAP_USER" --dbname "$BOOTSTRAP_DB" --host "$HOST" --port "$PORT" \
  --no-psqlrc --quiet --set=ON_ERROR_STOP=1 \
  --set=db_name="$DB_NAME" <<'SQL'
SELECT 'CREATE DATABASE ' || quote_ident(:'db_name')
WHERE NOT EXISTS (SELECT FROM pg_catalog.pg_database WHERE datname = :'db_name') \gexec
SQL

"$ROOT/infrastructure/docker/db-init.sh"

# Write the app role credentials into backend/.env (runtime) and the migrate
# role credentials into backend/.env.migrate (used ONLY for alembic). The
# migrate file is gitignored and never read by the FastAPI app.
if [[ ! -f "$BACKEND_ENV" ]]; then
  cp "$ROOT/backend/.env.example" "$BACKEND_ENV"
fi
python3 - "$BACKEND_ENV" "$APP_USER" "$APP_PASSWORD" <<'PY'
import re, sys
path, app_user, app_pw = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path) as f:
    s = f.read()
def setk(s, k, v):
    pat = re.compile(rf'^{k}=.*$', re.M)
    if pat.search(s):
        return pat.sub(f'{k}={v}', s, count=1)
    return s + f'\n{k}={v}\n'
s = setk(s, 'DATABASE_USER', app_user)
s = setk(s, 'DATABASE_PASSWORD', app_pw)
with open(path, 'w') as f:
    f.write(s)
PY

printf 'DATABASE_USER=%s\nDATABASE_PASSWORD=%s\n' "$MIGRATE_USER" "$MIGRATE_PASSWORD" > "$MIGRATE_ENV"
chmod 600 "$MIGRATE_ENV"

echo ""
echo "Provisioning complete."
echo "  Database:      ${HOST}:${PORT}/${DB_NAME}"
echo "  App role:      ${APP_USER} (DML only) -> backend/.env"
echo "  Migrate role:  ${MIGRATE_USER} (db owner, for alembic) -> backend/.env.migrate"
echo ""
echo "Run migrations with the migration role:"
echo "  set -a; source backend/.env.migrate; set +a"
echo "  (cd backend && .venv/bin/alembic upgrade head)"
