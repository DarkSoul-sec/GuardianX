#!/usr/bin/env bash
#
# GuardianX PostgreSQL least-privilege provisioning (idempotent).
#
# Provisions the GuardianX database with a three-role model:
#
#   POSTGRES_USER          bootstrap administrator (SUPERUSER) - provisioning only
#   POSTGRES_MIGRATE_USER  database owner, used only for `alembic upgrade head`
#   POSTGRES_APP_USER      restricted runtime role used by the FastAPI app
#
# Safe to run repeatedly. It never drops or rewrites data: it only creates
# roles, transfers ownership, adjusts grants, and sets default privileges.
#
# Usage contexts:
#   1. As a /docker-entrypoint-initdb.d script (fresh PostgreSQL data dir).
#      In this context the postgres image provides PGHOST via the local
#      socket; PROVISION_DB_HOST must be left unset.
#   2. As a one-shot provisioning service against an existing database
#      (fresh or existing volume). Set PROVISION_DB_HOST / PROVISION_DB_PORT
#      to point at the running postgres service.
#   3. Manually, for native development:
#      POSTGRES_DB=guardianx POSTGRES_USER=postgres POSTGRES_PASSWORD=... \
#      POSTGRES_MIGRATE_USER=... POSTGRES_MIGRATE_PASSWORD=... \
#      POSTGRES_APP_USER=... POSTGRES_APP_PASSWORD=... \
#      PROVISION_DB_HOST=localhost ./db-init.sh
#
# No password is ever echoed or written to disk.
set -euo pipefail

require_var() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "error: $name must be set" >&2
    exit 1
  fi
}

require_var POSTGRES_DB
require_var POSTGRES_USER
require_var POSTGRES_MIGRATE_USER
require_var POSTGRES_APP_USER

# Known placeholder values that must never become production credentials.
# Kept in sync with infrastructure/docker/postgres-entrypoint.sh.
PLACEHOLDERS=(
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

# Require a real, non-placeholder, sufficiently strong secret.
check_credential() {
  local name="$1"
  local value="${!name:-}"

  if [[ -z "$value" ]]; then
    echo "error: $name must be set" >&2
    exit 1
  fi

  if [[ ${#value} -lt 16 ]]; then
    echo "error: $name must be at least 16 characters (openssl rand -hex 32)" >&2
    exit 1
  fi

  local candidate
  for candidate in "${PLACEHOLDERS[@]}"; do
    if [[ "$value" == "$candidate" ]]; then
      echo "error: $name is still set to the placeholder '$candidate'. Set a strong, unique value (openssl rand -hex 32)." >&2
      exit 1
    fi
  done
}

check_credential POSTGRES_PASSWORD
check_credential POSTGRES_MIGRATE_PASSWORD
check_credential POSTGRES_APP_PASSWORD

# Reject names that would need quoting inside the SQL below. Simple
# alphanumeric/underscore identifiers keep every statement injection-safe.
for v in POSTGRES_DB POSTGRES_MIGRATE_USER POSTGRES_APP_USER; do
  if [[ ! "${!v}" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
    echo "error: $v must be a simple PostgreSQL identifier (got '${!v}')" >&2
    exit 1
  fi
done

PSQL_OPTS=(
  --username "$POSTGRES_USER"
  --dbname "$POSTGRES_DB"
  --no-psqlrc
  --quiet
  --set=ON_ERROR_STOP=1
)
if [[ -n "${PROVISION_DB_HOST:-}" ]]; then
  PSQL_OPTS+=(--host "$PROVISION_DB_HOST" --port "${PROVISION_DB_PORT:-5432}")
fi

export PGPASSWORD="$POSTGRES_PASSWORD"

psql "${PSQL_OPTS[@]}" \
  --set=db_name="$POSTGRES_DB" \
  --set=bootstrap_user="$POSTGRES_USER" \
  --set=bootstrap_password="$POSTGRES_PASSWORD" \
  --set=migrate_user="$POSTGRES_MIGRATE_USER" \
  --set=migrate_password="$POSTGRES_MIGRATE_PASSWORD" \
  --set=app_user="$POSTGRES_APP_USER" \
  --set=app_password="$POSTGRES_APP_PASSWORD" <<'SQL'
-- This script must run as the bootstrap superuser.
DO $$
BEGIN
  IF NOT (SELECT rolsuper FROM pg_catalog.pg_roles WHERE rolname = current_user) THEN
    RAISE EXCEPTION 'db-init must run as a PostgreSQL superuser (bootstrap role)';
  END IF;
END
$$;

-- 0. Resynchronise the bootstrap role and its password to the current env so
--    a stale volume (roles still protected by an older .env) can be repaired
--    in place by a plain `docker compose run --rm db-init`.
SELECT format('ALTER ROLE %I LOGIN SUPERUSER PASSWORD %L', :'bootstrap_user', :'bootstrap_password') \gexec

-- 1. Create roles if they do not exist yet.
SELECT format('CREATE ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS', :'migrate_user')
WHERE NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = :'migrate_user') \gexec

SELECT format('CREATE ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS', :'app_user')
WHERE NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = :'app_user') \gexec

-- 2. Enforce the least-privilege attribute set and password on every run.
--    This also repairs a pre-existing role that was created over-privileged.
ALTER ROLE :migrate_user LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD :'migrate_password';
ALTER ROLE :app_user LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD :'app_password';

-- 3. Strip schema-wide privileges from PUBLIC. GuardianX owns this database.
REVOKE CONNECT ON DATABASE :db_name FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- 4. Ownership. The migration role owns the GuardianX database (valid for a
--    NOCREATEDB owner when set by a superuser), the public schema, and every
--    application object. The bootstrap role keeps full access as SUPERUSER.
ALTER DATABASE :db_name OWNER TO :migrate_user;
ALTER SCHEMA public OWNER TO :migrate_user;

SELECT format('ALTER TABLE public.%I OWNER TO %I', tablename, :'migrate_user'::text)
FROM pg_catalog.pg_tables
WHERE schemaname = 'public' AND tableowner <> :'migrate_user'::name \gexec

SELECT format('ALTER SEQUENCE public.%I OWNER TO %I', sequencename, :'migrate_user'::text)
FROM pg_catalog.pg_sequences
WHERE schemaname = 'public' AND sequenceowner <> :'migrate_user'::name \gexec

SELECT format('ALTER TYPE public.%I OWNER TO %I', t.typname, :'migrate_user'::text)
FROM pg_catalog.pg_type t
JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
WHERE n.nspname = 'public'
  AND t.typtype = 'e'
  AND NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_depend d
        WHERE d.objid = t.oid AND d.deptype = 'e'
      ) \gexec

-- 5. Application role runtime grants: CONNECT, schema USAGE, DML on tables,
--    USAGE/SELECT on sequences. No CREATE, no DDL, no superuser attributes.
GRANT CONNECT ON DATABASE :db_name TO :app_user;
GRANT USAGE ON SCHEMA public TO :app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO :app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO :app_user;

-- 6. Default privileges: objects created by the migration role (future
--    Alembic migrations) automatically grant the application role its
--    runtime privileges, so a new table never breaks the running app.
ALTER DEFAULT PRIVILEGES FOR ROLE :migrate_user IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO :app_user;
ALTER DEFAULT PRIVILEGES FOR ROLE :migrate_user IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO :app_user;
SQL

echo "[db-init] provisioning complete for database '${POSTGRES_DB}'."
