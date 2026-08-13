#!/usr/bin/env bash
#
# GuardianX PostgreSQL least-privilege integration tests.
#
# Verifies the db-init.sh provisioning logic against scratch databases:
#   * fresh database initialization (roles, ownership, grants, defaults)
#   * full `alembic upgrade head` executed as the non-superuser migrate role
#   * runtime CRUD + sequence + enum usage as the restricted app role
#   * negative checks (app role cannot run DDL / DROP / CREATE ROLE / CREATE DB)
#   * existing-database upgrade (objects owned by another role are transferred)
#   * idempotency (running db-init.sh twice is safe)
#
# No GuardianX database is touched: only scratch databases whose names are
# prefixed with `gx_security_test_` are created and dropped again.
#
# Requirements:
#   * a reachable PostgreSQL server
#   * a superuser account for scratch setup/teardown
#   * the backend virtualenv (for alembic)
#
# Usage:
#   PG_TEST_HOST=localhost PG_TEST_PORT=5432 \
#   PG_TEST_SUPERUSER=postgres PG_TEST_SUPERPASSWORD=... \
#   BACKEND_DIR=/path/to/backend infrastructure/scripts/test_db_security.sh
#
set -euo pipefail

PG_TEST_HOST="${PG_TEST_HOST:-localhost}"
PG_TEST_PORT="${PG_TEST_PORT:-5432}"
PG_TEST_SUPERUSER="${PG_TEST_SUPERUSER:-postgres}"
PG_TEST_SUPERPASSWORD="${PG_TEST_SUPERPASSWORD:?PG_TEST_SUPERPASSWORD must be set}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="${BACKEND_DIR:-$(cd "$SCRIPT_DIR/../../backend" && pwd)}"
DB_INIT_SCRIPT="$(cd "$SCRIPT_DIR/../docker" && pwd)/db-init.sh"

MIGRATE_ROLE="${MIGRATE_ROLE:-guardianx_migrate}"
APP_ROLE="${APP_ROLE:-guardianx_app}"
TEST_PASSWORD="${TEST_PASSWORD:-guardianx-test-password-1}"
EXPECTED_HEAD="${EXPECTED_HEAD:-f4a2b6c8d0e1}"

SU="psql --host $PG_TEST_HOST --port $PG_TEST_PORT --username $PG_TEST_SUPERUSER --no-psqlrc --set=ON_ERROR_STOP=1"
export PGPASSWORD="$PG_TEST_SUPERPASSWORD"

STAMP="$(date +%s)_$$"
FRESH_DB="gx_security_test_fresh_${STAMP}"
EXISTING_DB="gx_security_test_existing_${STAMP}"

PASS=0
FAIL=0

ok()   { echo "  ok: $1"; PASS=$((PASS+1)); }
fail() { echo "  FAIL: $1" >&2; FAIL=$((FAIL+1)); }

cleanup() {
  set +e
  $SU --dbname postgres -c "DROP DATABASE IF EXISTS \"$FRESH_DB\" WITH (FORCE);" >/dev/null 2>&1
  $SU --dbname postgres -c "DROP DATABASE IF EXISTS \"$EXISTING_DB\" WITH (FORCE);" >/dev/null 2>&1
  set -e
}
trap cleanup EXIT

as_super() { # db then psql args (e.g. -At -c "sql")
  local db="$1"; shift
  $SU --dbname "$db" "$@"
}

as_role() { # role db then psql args
  local role="$1" db="$2"; shift 2
  PGPASSWORD="$TEST_PASSWORD" psql --host "$PG_TEST_HOST" --port "$PG_TEST_PORT" \
    --username "$role" --dbname "$db" --no-psqlrc --set=ON_ERROR_STOP=1 "$@"
}

expect_fail() { # role db -c sql
  if as_role "$@" >/dev/null 2>&1; then
    fail "expected failure but succeeded: ${*:3}"
  else
    ok "denied as expected: ${*:3}"
  fi
}

run_provision() {
  POSTGRES_DB="$1" \
  POSTGRES_USER="$PG_TEST_SUPERUSER" \
  POSTGRES_PASSWORD="$PG_TEST_SUPERPASSWORD" \
  POSTGRES_MIGRATE_USER="$MIGRATE_ROLE" \
  POSTGRES_MIGRATE_PASSWORD="$TEST_PASSWORD" \
  POSTGRES_APP_USER="$APP_ROLE" \
  POSTGRES_APP_PASSWORD="$TEST_PASSWORD" \
  PROVISION_DB_HOST="$PG_TEST_HOST" PROVISION_DB_PORT="$PG_TEST_PORT" \
  bash "$DB_INIT_SCRIPT"
}

alembic_as() { # db role password
  local db="$1" role="$2" password="$3"
  (
    cd "$BACKEND_DIR"
    DATABASE_HOST="$PG_TEST_HOST" DATABASE_PORT="$PG_TEST_PORT" \
    DATABASE_NAME="$db" DATABASE_USER="$role" DATABASE_PASSWORD="$password" \
    .venv/bin/alembic upgrade head
  )
}

verify_role_attrs() { # db
  local attrs
  attrs="$(as_super "$1" -At -c "SELECT NOT r.rolsuper AND NOT r.rolcreaterole AND NOT r.rolcreatedb AND NOT r.rolreplication AND NOT r.rolbypassrls AND r.rolcanlogin FROM pg_roles r WHERE r.rolname='$APP_ROLE'")"
  if [[ "$attrs" == "t" ]]; then
    ok "app role: NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS LOGIN"
  else
    fail "unexpected app role attributes: '$attrs'"
  fi
  attrs="$(as_super "$1" -At -c "SELECT NOT r.rolsuper AND NOT r.rolcreaterole AND NOT r.rolcreatedb AND NOT r.rolreplication AND NOT r.rolbypassrls AND r.rolcanlogin FROM pg_roles r WHERE r.rolname='$MIGRATE_ROLE'")"
  if [[ "$attrs" == "t" ]]; then
    ok "migrate role: NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS LOGIN"
  else
    fail "unexpected migrate role attributes: '$attrs'"
  fi
}

echo "== Creating scratch databases =="
$SU --dbname postgres -c "CREATE DATABASE \"$FRESH_DB\";"
$SU --dbname postgres -c "CREATE DATABASE \"$EXISTING_DB\";"

echo ""
echo "== TEST: fresh database initialization =="
run_provision "$FRESH_DB"
verify_role_attrs "$FRESH_DB"
owner="$(as_super "$FRESH_DB" -At -c "SELECT pg_catalog.pg_get_userbyid(datdba) FROM pg_database WHERE datname='$FRESH_DB'")"
[[ "$owner" == "$MIGRATE_ROLE" ]] && ok "database owned by $MIGRATE_ROLE" || fail "database owner is '$owner'"
schema_owner="$(as_super "$FRESH_DB" -At -c "SELECT pg_catalog.pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname='public'")"
[[ "$schema_owner" == "$MIGRATE_ROLE" ]] && ok "public schema owned by $MIGRATE_ROLE" || fail "schema owner is '$schema_owner'"

echo ""
echo "== TEST: full alembic upgrade head as non-superuser migrate role =="
if alembic_as "$FRESH_DB" "$MIGRATE_ROLE" "$TEST_PASSWORD" >/tmp/opencode/alembic_fresh.log 2>&1; then
  ok "alembic upgrade head succeeded as $MIGRATE_ROLE (fresh)"
else
  fail "alembic upgrade head failed as $MIGRATE_ROLE - see /tmp/opencode/alembic_fresh.log"
fi
head_rev="$(as_super "$FRESH_DB" -At -c "SELECT version_num FROM alembic_version")"
[[ "$head_rev" == "$EXPECTED_HEAD" ]] && ok "migrations at head ($EXPECTED_HEAD)" || fail "migration head is '$head_rev'"
app_dml="$(as_super "$FRESH_DB" -At -c "SELECT string_agg(has_table_privilege('$APP_ROLE','public.'||tablename,'INSERT')::text, '' ORDER BY tablename) FROM pg_tables WHERE schemaname='public'")"
if [[ "$app_dml" == *"f"* ]]; then
  fail "app role missing INSERT on some table"
else
  ok "app role has INSERT on every application table"
fi

echo ""
echo "== TEST: runtime CRUD, sequence usage, enum usage (app role) =="
as_role "$APP_ROLE" "$FRESH_DB" -c "INSERT INTO users (username, email, password_hash, is_active, email_verified, role) VALUES ('sec_test_user', 'sec_test@example.com', 'x', true, true, 'ADMIN');" >/dev/null 2>&1 \
  && ok "app INSERT into users (enum role column + serial sequence)" || fail "app INSERT into users failed"
as_role "$APP_ROLE" "$FRESH_DB" -c "UPDATE users SET role='VIEWER' WHERE username='sec_test_user';" >/dev/null 2>&1 \
  && ok "app UPDATE users" || fail "app UPDATE users failed"
cnt="$(as_role "$APP_ROLE" "$FRESH_DB" -At -c "SELECT count(*) FROM users WHERE username='sec_test_user'")"
[[ "$cnt" == "1" ]] && ok "app SELECT users" || fail "app SELECT users returned '$cnt'"
uid="$(as_role "$APP_ROLE" "$FRESH_DB" -At -c "SELECT id FROM users WHERE username='sec_test_user'")"
as_role "$APP_ROLE" "$FRESH_DB" -c "INSERT INTO assets (name, asset_type, created_by) VALUES ('sec-test', 'SERVER', $uid);" >/dev/null 2>&1 \
  && ok "app INSERT assets (enum asset_type + serial sequence)" || fail "app INSERT assets failed"
as_role "$APP_ROLE" "$FRESH_DB" -c "DELETE FROM assets WHERE name='sec-test';" >/dev/null 2>&1 \
  && ok "app DELETE assets" || fail "app DELETE assets failed"
as_role "$APP_ROLE" "$FRESH_DB" -c "INSERT INTO activity_logs (user_id, action, meta) VALUES ($uid, 'test', '{\"k\":\"v\"}'::jsonb);" >/dev/null 2>&1 \
  && ok "app INSERT activity_logs (jsonb column)" || fail "app INSERT activity_logs failed"
as_role "$APP_ROLE" "$FRESH_DB" -c "DELETE FROM users WHERE username='sec_test_user';" >/dev/null 2>&1 \
  && ok "app DELETE users (cascade)" || fail "app DELETE users failed"

echo ""
echo "== TEST: app role negative checks (no DDL, no DROP, no role/db create) =="
expect_fail "$APP_ROLE" "$FRESH_DB" -c "CREATE TABLE evil (x int);"
expect_fail "$APP_ROLE" "$FRESH_DB" -c "CREATE TYPE evil_t AS ENUM ('x');"
expect_fail "$APP_ROLE" "$FRESH_DB" -c "ALTER TABLE users ADD COLUMN y int;"
expect_fail "$APP_ROLE" "$FRESH_DB" -c "DROP TABLE users;"
expect_fail "$APP_ROLE" "$FRESH_DB" -c "CREATE ROLE evil_role;"
expect_fail "$APP_ROLE" "$FRESH_DB" -c "CREATE DATABASE evil_db;"

echo ""
echo "== TEST: migrate role can perform DDL on migrated schema =="
as_role "$MIGRATE_ROLE" "$FRESH_DB" -c "CREATE TABLE migrate_can_ddl (id serial PRIMARY KEY);" >/dev/null 2>&1 \
  && ok "migrate role can CREATE TABLE" || fail "migrate role could not CREATE TABLE"
as_role "$MIGRATE_ROLE" "$FRESH_DB" -c "CREATE TYPE migrate_can_type AS ENUM ('a','b');" >/dev/null 2>&1 \
  && ok "migrate role can CREATE TYPE" || fail "migrate role could not CREATE TYPE"
as_role "$MIGRATE_ROLE" "$FRESH_DB" -c "ALTER TYPE scan_status ADD VALUE 'TEST_LABEL';" >/dev/null 2>&1 \
  && ok "migrate role can ALTER TYPE ADD VALUE" || fail "migrate role could not ALTER TYPE"
as_role "$MIGRATE_ROLE" "$FRESH_DB" -c "DROP TABLE migrate_can_ddl; DROP TYPE migrate_can_type;" >/dev/null 2>&1 \
  && ok "migrate role can DROP objects" || fail "migrate role could not DROP objects"
expect_fail "$MIGRATE_ROLE" "$FRESH_DB" -c "CREATE ROLE evil_role2;"

echo ""
echo "== TEST: default privileges for future migration-created objects =="
as_role "$MIGRATE_ROLE" "$FRESH_DB" -c "CREATE TABLE future_table (id serial PRIMARY KEY, status scan_status);" >/dev/null 2>&1 \
  && ok "migrate created future_table" || fail "migrate could not create future_table"
as_role "$APP_ROLE" "$FRESH_DB" -c "INSERT INTO future_table (status) VALUES ('PENDING');" >/dev/null 2>&1 \
  && ok "app auto-granted DML + sequence + enum on future_table" || fail "app missing auto-grant on future_table"
as_role "$MIGRATE_ROLE" "$FRESH_DB" -c "DROP TABLE future_table;" >/dev/null 2>&1

echo ""
echo "== TEST: idempotency (run db-init.sh again) =="
if run_provision "$FRESH_DB" >/tmp/opencode/dbinit_fresh2.log 2>&1; then
  ok "db-init.sh ran a second time without error"
else
  fail "db-init.sh second run failed - see /tmp/opencode/dbinit_fresh2.log"
fi

echo ""
echo "== TEST: existing database upgrade =="
echo "-- building full schema owned by the legacy superuser (simulates legacy install)"
if alembic_as "$EXISTING_DB" "$PG_TEST_SUPERUSER" "$PG_TEST_SUPERPASSWORD" >/tmp/opencode/alembic_legacy.log 2>&1; then
  ok "legacy schema created by old owner"
else
  fail "could not build legacy schema - see /tmp/opencode/alembic_legacy.log"
fi
before_owner="$(as_super "$EXISTING_DB" -At -c "SELECT string_agg(DISTINCT tableowner, ',') FROM pg_tables WHERE schemaname='public'")"
echo "-- legacy table owners: $before_owner"

if run_provision "$EXISTING_DB" >/tmp/opencode/dbinit_existing.log 2>&1; then
  ok "db-init.sh provisioned the existing database"
else
  fail "db-init.sh failed on existing database - see /tmp/opencode/dbinit_existing.log"
fi
verify_role_attrs "$EXISTING_DB"
owner="$(as_super "$EXISTING_DB" -At -c "SELECT string_agg(DISTINCT tableowner, ',') FROM pg_tables WHERE schemaname='public'")"
if [[ "$owner" == "$MIGRATE_ROLE" ]]; then
  ok "all legacy tables transferred to $MIGRATE_ROLE"
else
  fail "legacy table owners after transfer: '$owner'"
fi
if alembic_as "$EXISTING_DB" "$MIGRATE_ROLE" "$TEST_PASSWORD" >/tmp/opencode/alembic_existing.log 2>&1; then
  ok "alembic upgrade head succeeded as $MIGRATE_ROLE on existing database"
else
  fail "alembic upgrade head failed on existing DB as migrate - see /tmp/opencode/alembic_existing.log"
fi
as_role "$APP_ROLE" "$EXISTING_DB" -c "INSERT INTO users (username, email, password_hash, is_active, email_verified, role) VALUES ('sec_existing_user', 'sec_existing@example.com', 'x', true, true, 'ANALYST');" >/dev/null 2>&1 \
  && ok "app CRUD on existing (legacy) tables" || fail "app CRUD failed on existing tables"
as_role "$APP_ROLE" "$EXISTING_DB" -c "DELETE FROM users WHERE username='sec_existing_user';" >/dev/null 2>&1

echo ""
echo "== TESTS COMPLETE =="
echo "passed: $PASS  failed: $FAIL"
if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
exit 0
