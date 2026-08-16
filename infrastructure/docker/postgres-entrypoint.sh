#!/usr/bin/env bash
#
# GuardianX PostgreSQL startup credential guard + stale-volume self-heal.
#
# Runs BEFORE the official postgres image entrypoint.
#
# 1. Credential guard: refuses to start when any required database credential
#    is missing, is a known placeholder, or is too short to be treated as a
#    real secret. This guarantees a misconfigured deployment fails fast and
#    clearly instead of silently provisioning the database with
#    default/guessable credentials.
#
# 2. Stale-volume self-heal: PostgreSQL only applies POSTGRES_PASSWORD when it
#    runs initdb (an EMPTY data directory). If the container is started against
#    an existing volume that was provisioned with an older .env, the database
#    roles keep their old passwords while the containers advertise new ones,
#    which surfaces as "password authentication failed for user ...". To make
#    this impossible, when a live data directory is detected the bootstrap,
#    migration and application role passwords are resynchronised to the current
#    environment over the local socket (trust auth) before the server starts.
#    The official entrypoint then exec's unchanged, so image behaviour (initdb
#    on first run, /docker-entrypoint-initdb.d scripts, runtime start) is fully
#    preserved.
#
# All three database credentials are checked here because they are the ones
# db-init.sh bakes into PostgreSQL roles. SECRET_KEY is enforced separately by
# the application at startup (app/main.py), and by start.sh.
set -euo pipefail

# Known placeholder values that must never become production credentials.
_PLACEHOLDERS=(
  "change-me"
  "change-me-in-production"
  "change-me-generate-a-strong-password"
  "change-me-generate-with-openssl-rand-hex-32"
  "changeme"
  "change_me"
  "secret"
  "secret-key"
  "placeholder"
  "your_password_here"
  "your-password-here"
  "password"
  "postgres"
)

_fail() {
  echo "error: $1" >&2
  exit 1
}

_check_credential() {
  local name="$1"
  local value="${!name:-}"

  if [[ -z "$value" ]]; then
    _fail "$name is not set. Copy infrastructure/compose/.env.example to infrastructure/compose/.env and set $name to a strong random value (openssl rand -hex 32), then run ./start.sh again."
  fi

  if [[ ${#value} -lt 16 ]]; then
    _fail "$name is shorter than 16 characters. Set a strong random value (openssl rand -hex 32) in infrastructure/compose/.env."
  fi

  local candidate
  for candidate in "${_PLACEHOLDERS[@]}"; do
    if [[ "$value" == "$candidate" ]]; then
      _fail "$name is still set to the placeholder '$candidate'. Set a strong, unique value (openssl rand -hex 32) in infrastructure/compose/.env."
    fi
  done
}

# Reject names that would need quoting inside the psql variables below.
# Simple alphanumeric/underscore identifiers keep every statement safe.
_check_identifier() {
  local name="$1"
  if [[ ! "${!name}" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
    _fail "$name must be a simple PostgreSQL identifier (got '${!name}')"
  fi
}

# Resynchronise role credentials on an existing data directory so a stale
# volume can never out-vote the current .env. Connects through the local Unix
# socket where pg_hba.conf trusts local connections, so this does not depend
# on the (possibly stale) password stored in the database.
_resync_credentials() {
  local pg_bin tmp_dir tmp_hba run_postgres
  pg_bin="$(ls -d /usr/lib/postgresql/*/bin 2>/dev/null | head -n 1 || true)"
  [[ -n "$pg_bin" ]] || _fail "could not locate PostgreSQL binaries"
  tmp_dir="$(mktemp -d)" || _fail "could not create a temporary directory"
  tmp_hba="$tmp_dir/pg_hba.conf"
  printf 'local all all trust\n' > "$tmp_hba"

  run_postgres=()
  if [[ "$(id -u)" == "0" ]]; then
    run_postgres=(gosu postgres)
    # The temporary server runs as the postgres user (which owns PGDATA) and
    # must be able to create its socket/lock files inside the temp directory.
    chown postgres:postgres "$tmp_dir"
  fi

  # Stop the temporary server and remove the temp directory if this shell exits
  # unexpectedly (set -e failure, exit 1, signal) so the temp instance can never
  # be left running against PGDATA or leak the trust-auth socket directory.
  _resync_cleanup() {
    "${run_postgres[@]}" "$pg_bin/pg_ctl" -D "$PGDATA" -m fast -w -t 30 stop >/dev/null 2>&1 || true
    rm -rf "$tmp_dir"
  }
  trap _resync_cleanup EXIT

  "${run_postgres[@]}" "$pg_bin/pg_ctl" -D "$PGDATA" \
    -o "-c listen_addresses='' -c unix_socket_directories='$tmp_dir' -c hba_file='$tmp_hba' -c logging_collector=off -c log_statement=off" \
    -w -t 60 start

  echo "[guardianx-postgres-entrypoint] existing data directory detected: resyncing role credentials to the current environment"

  if ! "${run_postgres[@]}" "$pg_bin/psql" -h "$tmp_dir" \
      --username "$POSTGRES_USER" --dbname postgres \
      --no-psqlrc --quiet --set=ON_ERROR_STOP=1 \
      --set=bootstrap_user="$POSTGRES_USER" \
      --set=bootstrap_password="$POSTGRES_PASSWORD" \
      --set=migrate_user="$POSTGRES_MIGRATE_USER" \
      --set=migrate_password="$POSTGRES_MIGRATE_PASSWORD" \
      --set=app_user="$POSTGRES_APP_USER" \
      --set=app_password="$POSTGRES_APP_PASSWORD" <<'SQL'
-- This script must run as the bootstrap superuser (trust local socket).
DO $$
BEGIN
  IF NOT (SELECT rolsuper FROM pg_catalog.pg_roles WHERE rolname = current_user) THEN
    RAISE EXCEPTION 'guardianx-postgres-entrypoint resync must run as a PostgreSQL superuser';
  END IF;
END
$$;

-- Resynchronise the bootstrap role and its password to the current env.
SELECT format('ALTER ROLE %I LOGIN SUPERUSER PASSWORD %L', :'bootstrap_user', :'bootstrap_password') \gexec

-- Create the least-privilege roles on demand and enforce their attributes and
-- password on every start, repairing stale volumes in place.
SELECT format('CREATE ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS', :'migrate_user')
WHERE NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = :'migrate_user') \gexec

SELECT format('ALTER ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD %L', :'migrate_user', :'migrate_password') \gexec

SELECT format('CREATE ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS', :'app_user')
WHERE NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = :'app_user') \gexec

SELECT format('ALTER ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD %L', :'app_user', :'app_password') \gexec
SQL
  then
    echo "error: could not resync database role credentials (psql failed)" >&2
    "${run_postgres[@]}" "$pg_bin/pg_ctl" -D "$PGDATA" -m fast -w -t 30 stop >/dev/null 2>&1 || true
    rm -rf "$tmp_dir"
    exit 1
  fi

  "${run_postgres[@]}" "$pg_bin/pg_ctl" -D "$PGDATA" -m fast -w -t 30 stop >/dev/null
  rm -rf "$tmp_dir"
  echo "[guardianx-postgres-entrypoint] credential resync complete"
}

_check_credential POSTGRES_PASSWORD
_check_credential POSTGRES_MIGRATE_PASSWORD
_check_credential POSTGRES_APP_PASSWORD

_check_identifier POSTGRES_USER
_check_identifier POSTGRES_MIGRATE_USER
_check_identifier POSTGRES_APP_USER

# Self-heal existing volumes; leave fresh ones to the official entrypoint,
# which runs initdb and provisions roles via /docker-entrypoint-initdb.d.
if [[ -s "$PGDATA/PG_VERSION" ]]; then
  _resync_credentials
fi

exec /usr/local/bin/docker-entrypoint.sh "$@"
