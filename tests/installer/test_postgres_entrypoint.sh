#!/usr/bin/env bash
#
# GuardianX PostgreSQL entrypoint (stale-volume credential resync) tests.
#
# These tests exercise infrastructure/docker/postgres-entrypoint.sh WITHOUT a
# real PostgreSQL instance or a Docker daemon, so they run on any host / CI.
# A mock environment stubs pg_bin discovery (ls), mktemp, pg_ctl and psql so
# the credential-resync and EXIT-trap paths can be driven deterministically.
#
# Run:
#   tests/installer/test_postgres_entrypoint.sh
#
set -euo pipefail

GX_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENTRYPOINT="$GX_ROOT/infrastructure/docker/postgres-entrypoint.sh"

TESTS_PASS=0
TESTS_FAIL=0

pass() { TESTS_PASS=$((TESTS_PASS+1)); printf '  ok: %s\n' "$1"; }
fail() { TESTS_FAIL=$((TESTS_FAIL+1)); printf '  FAIL: %s\n' "$1" >&2; }

# Real, non-placeholder, >= 16 char credentials accepted by the entrypoint guard.
VALID_ENV=(
  POSTGRES_USER=postgres
  POSTGRES_PASSWORD=test_pg_password_1234567890x
  POSTGRES_MIGRATE_USER=guardianx_migrate
  POSTGRES_MIGRATE_PASSWORD=test_migrate_pw_1234567890x
  POSTGRES_APP_USER=guardianx_app
  POSTGRES_APP_PASSWORD=test_app_password_1234567890
)

# --------------------------------------------------------------------------- #
# Mock environment
# --------------------------------------------------------------------------- #

# $1 = work dir. Creates:
#   $1/bin/ls, $1/bin/mktemp          PATH stubs used by the entrypoint
#   $1/fake-pg/bin/pg_ctl, psql       fake PostgreSQL binaries
# Environment knobs (exported by the caller before run_entrypoint):
#   FAKE_PG_BIN        path printed by the ls stub (overrides pg_bin discovery)
#   LS_EMPTY=1         make ls print nothing  (simulate missing PostgreSQL bins)
#   MKTEMP_FIXED       fixed dir returned by `mktemp -d`
#   PGCTL_LOG          log file for pg_ctl invocations
#   PGCTL_START_FAIL=1 make `pg_ctl ... start` fail
#   PSQL_LOG           log file for psql invocations
#   PSQL_FAIL=1        make psql fail
setup_mock() {
  local work="$1"
  mkdir -p "$work/bin" "$work/fake-pg/bin" "$work/pgdata"

  cat > "$work/bin/ls" <<'STUB'
#!/usr/bin/env bash
if [[ "${LS_EMPTY:-0}" == "1" ]]; then
  exit 0
elif [[ -n "${FAKE_PG_BIN:-}" ]]; then
  printf '%s\n' "$FAKE_PG_BIN"
else
  /bin/ls "$@"
fi
STUB

  cat > "$work/bin/mktemp" <<'STUB'
#!/usr/bin/env bash
if [[ -n "${MKTEMP_FIXED:-}" ]]; then
  mkdir -p "$MKTEMP_FIXED"
  printf '%s\n' "$MKTEMP_FIXED"
  exit 0
fi
if [[ -x /usr/bin/mktemp ]]; then
  exec /usr/bin/mktemp "$@"
fi
exec /bin/mktemp "$@"
STUB

  cat > "$work/fake-pg/bin/pg_ctl" <<'STUB'
#!/usr/bin/env bash
printf 'pg_ctl arg: %s\n' "$@" >> "${PGCTL_LOG:-/dev/null}"
case "$*" in
  *" start")
    if [[ "${PGCTL_START_FAIL:-0}" == "1" ]]; then
      echo "pg_ctl: mock start failure" >&2
      exit 1
    fi
    ;;
esac
exit 0
STUB

  cat > "$work/fake-pg/bin/psql" <<'STUB'
#!/usr/bin/env bash
printf 'psql invoked\n' >> "${PSQL_LOG:-/dev/null}"
[[ "${PSQL_FAIL:-0}" == "1" ]] && exit 1
exit 0
STUB

  chmod +x "$work/bin/ls" "$work/bin/mktemp" \
    "$work/fake-pg/bin/pg_ctl" "$work/fake-pg/bin/psql"
}

# Run the entrypoint as a subprocess inside the mock environment.
# $1 = work dir; remaining args are extra env overrides as KEY=value.
# Populates $RC (exit status) and $OUT (stdout + stderr).
run_entrypoint() {
  local work="$1"; shift
  if (
    cd "$work" || exit 1
    export PATH="$work/bin:$PATH"
    export PGDATA="$work/pgdata"
    export FAKE_PG_BIN="$work/fake-pg/bin"
    export PGCTL_LOG="$work/pgctl.log"
    export PSQL_LOG="$work/psql.log"
    local kv
    for kv in "${VALID_ENV[@]}"; do export "$kv"; done
    for kv in "$@"; do export "$kv"; done
    bash "$ENTRYPOINT" >"$work/out.log" 2>"$work/err.log"
  ); then
    RC=0
  else
    RC=$?
  fi
  OUT="$(cat "$work/out.log" "$work/err.log")"
}

# --------------------------------------------------------------------------- #
# T1. Temporary server startup options are hardened and safe
# --------------------------------------------------------------------------- #
test_startup_options() {
  printf '\n== TEST: temporary server options (log_statement=none, socket-only) ==\n'

  if grep -q 'log_statement=none' "$ENTRYPOINT"; then
    pass "startup options set log_statement=none"
  else
    fail "startup options do not set log_statement=none"
  fi
  if grep -q 'log_statement=off' "$ENTRYPOINT"; then
    fail "invalid log_statement=off is still present"
  else
    pass "invalid log_statement=off is absent"
  fi

  if grep -q "listen_addresses=''" "$ENTRYPOINT"; then
    pass "temporary server binds to the socket only (listen_addresses='')"
  else
    fail "temporary server listen_addresses is not forced to ''"
  fi
  if grep -q "hba_file='\$tmp_hba'" "$ENTRYPOINT"; then
    pass "temporary hba_file points into the temp directory (never PGDATA)"
  else
    fail "temporary hba_file is not scoped to the temp directory"
  fi
  if grep -q "printf 'local all all trust" "$ENTRYPOINT"; then
    pass "temporary HBA uses a Unix-socket-only trust rule"
  else
    fail "temporary HBA trust rule not found"
  fi
  if grep -Eq '^\s*(host|hostssl|hostnossl)\s+all\s+all' "$ENTRYPOINT"; then
    fail "non-socket HBA rule found"
  else
    pass "no host/hostssl HBA rule (socket-only)"
  fi
}

# --------------------------------------------------------------------------- #
# T2. Temporary server stop is bounded (-t 30) everywhere
# --------------------------------------------------------------------------- #
test_bounded_stop() {
  printf '\n== TEST: temporary server stop is bounded with -t 30 ==\n'

  if grep -q -- '-m fast -w -t 30 stop' "$ENTRYPOINT"; then
    pass "pg_ctl stop uses -m fast -w -t 30"
  else
    fail "pg_ctl stop is not bounded with -t 30"
  fi
  if grep -q -- '-m fast -w stop' "$ENTRYPOINT"; then
    fail "unbounded pg_ctl stop (-m fast -w stop) found"
  else
    pass "no unbounded pg_ctl stop remains"
  fi
}

# --------------------------------------------------------------------------- #
# T3. Successful sync: log_statement=none passed to pg_ctl; sync runs; the
#     official entrypoint is then handed off to (normal PostgreSQL startup).
# --------------------------------------------------------------------------- #
test_success_resync_and_startup() {
  printf '\n== TEST: successful sync hands off to normal PostgreSQL startup ==\n'

  local work
  work="$(mktemp -d)"
  setup_mock "$work"
  echo "16" > "$work/pgdata/PG_VERSION"
  run_entrypoint "$work"

  if grep -q 'log_statement=none' "$work/pgctl.log"; then
    pass "pg_ctl received log_statement=none"
  else
    fail "pg_ctl did not receive log_statement=none"
  fi
  if grep -q "listen_addresses=''" "$work/pgctl.log"; then
    pass "pg_ctl received listen_addresses=''"
  else
    fail "pg_ctl did not receive listen_addresses=''"
  fi
  if grep -q 'logging_collector=off' "$work/pgctl.log"; then
    pass "pg_ctl received logging_collector=off"
  else
    fail "pg_ctl did not receive logging_collector=off"
  fi
  if grep 'hba_file=' "$work/pgctl.log" | grep -q "$work/pgdata"; then
    fail "temporary hba_file was pointed into PGDATA"
  else
    pass "temporary hba_file stays out of PGDATA"
  fi

  if grep -q 'existing data directory detected' <<<"$OUT"; then
    pass "stale-volume credential resync was triggered"
  else
    fail "credential resync was not triggered"
  fi
  if grep -q 'credential resync complete' <<<"$OUT"; then
    pass "credential resync completed successfully"
  else
    fail "credential resync did not complete"
  fi
  if grep -q 'psql invoked' "$work/psql.log"; then
    pass "psql resync statements were executed"
  else
    fail "psql resync statements were not executed"
  fi

  if [[ "$(grep -c 'pg_ctl arg: .*start' "$work/pgctl.log" 2>/dev/null || true)" -ge 1 ]] &&
     [[ "$(grep -c 'pg_ctl arg: .*stop' "$work/pgctl.log" 2>/dev/null || true)" -ge 1 ]]; then
    pass "temporary server was stopped after the sync"
  else
    fail "temporary server start/stop not both observed"
  fi

  # Handoff to the official image entrypoint (bash reports the exec attempt when
  # /usr/local/bin/docker-entrypoint.sh is absent on the test host).
  if grep -q 'docker-entrypoint.sh' "$work/err.log"; then
    pass "official postgres entrypoint was invoked after the sync"
  else
    fail "official postgres entrypoint was not reached (rc=$RC)"
  fi

  rm -rf "$work"
}

# --------------------------------------------------------------------------- #
# T4. Temporary server startup failure: no unbound-variable error, temp dir
#     cleaned up by the EXIT trap.
# --------------------------------------------------------------------------- #
test_start_failure_no_unbound() {
  printf '\n== TEST: startup failure is clean (no unbound variable, cleanup runs) ==\n'

  local work
  work="$(mktemp -d)"
  setup_mock "$work"
  echo "16" > "$work/pgdata/PG_VERSION"
  run_entrypoint "$work" MKTEMP_FIXED="$work/tmpdir" PGCTL_START_FAIL=1

  if [[ "$RC" -ne 0 ]]; then
    pass "startup failure exits non-zero (rc=$RC)"
  else
    fail "startup failure unexpectedly exited 0"
  fi
  if grep -q 'unbound variable' <<<"$OUT"; then
    fail "cleanup produced an unbound-variable error"
  else
    pass "cleanup ran without an unbound-variable error"
  fi
  if [[ ! -d "$work/tmpdir" ]]; then
    pass "temporary directory was removed by the EXIT trap"
  else
    fail "temporary directory was left behind"
  fi
  if grep -q 'pg_ctl arg: .*stop' "$work/pgctl.log" 2>/dev/null; then
    pass "EXIT trap attempted to stop the temporary server"
  else
    fail "EXIT trap did not attempt to stop the temporary server"
  fi

  rm -rf "$work"
}

# --------------------------------------------------------------------------- #
# T5. Cleanup stays safe when pg_bin is unset / binaries are missing.
# --------------------------------------------------------------------------- #
test_cleanup_when_pg_bin_unset() {
  printf '\n== TEST: missing PostgreSQL binaries fail cleanly ==\n'

  local work
  work="$(mktemp -d)"
  setup_mock "$work"
  echo "16" > "$work/pgdata/PG_VERSION"
  run_entrypoint "$work" LS_EMPTY=1 MKTEMP_FIXED="$work/tmpdir"

  if grep -q 'could not locate PostgreSQL binaries' <<<"$OUT"; then
    pass "missing PostgreSQL binaries reported clearly"
  else
    fail "missing PostgreSQL binaries not reported"
  fi
  if grep -q 'unbound variable' <<<"$OUT"; then
    fail "missing pg_bin produced an unbound-variable error"
  else
    pass "no unbound-variable error when pg_bin is unset"
  fi
  if [[ "$RC" -ne 0 ]]; then
    pass "exited non-zero (rc=$RC)"
  else
    fail "unexpectedly exited 0"
  fi

  rm -rf "$work"
}

# --------------------------------------------------------------------------- #
# T6. A failed resync is reported and cleaned up.
# --------------------------------------------------------------------------- #
test_psql_failure() {
  printf '\n== TEST: psql resync failure is reported and cleaned up ==\n'

  local work
  work="$(mktemp -d)"
  setup_mock "$work"
  echo "16" > "$work/pgdata/PG_VERSION"
  run_entrypoint "$work" MKTEMP_FIXED="$work/tmpdir" PSQL_FAIL=1

  if grep -q 'could not resync database role credentials' <<<"$OUT"; then
    pass "psql resync failure reported"
  else
    fail "psql resync failure not reported"
  fi
  if [[ "$RC" -ne 0 ]]; then
    pass "exited non-zero (rc=$RC)"
  else
    fail "unexpectedly exited 0"
  fi
  if [[ ! -d "$work/tmpdir" ]]; then
    pass "temporary directory was removed"
  else
    fail "temporary directory was left behind"
  fi

  rm -rf "$work"
}

# --------------------------------------------------------------------------- #
# T7. Placeholder credentials fail fast, before any server is started.
# --------------------------------------------------------------------------- #
test_placeholder_fails_fast() {
  printf '\n== TEST: placeholder credentials still fail fast ==\n'

  local work
  work="$(mktemp -d)"
  setup_mock "$work"
  echo "16" > "$work/pgdata/PG_VERSION"
  run_entrypoint "$work" POSTGRES_PASSWORD=your-password-here

  if grep -q 'placeholder' <<<"$OUT"; then
    pass "placeholder password rejected"
  else
    fail "placeholder password was not rejected"
  fi
  if [[ "$RC" -ne 0 ]]; then
    pass "exited non-zero (rc=$RC)"
  else
    fail "unexpectedly exited 0"
  fi
  if [[ ! -e "$work/pgctl.log" ]]; then
    pass "no server was started"
  else
    fail "server was started despite placeholder credentials"
  fi
  if ! grep -q 'docker-entrypoint.sh' "$work/err.log" 2>/dev/null; then
    pass "did not hand off to the official entrypoint"
  else
    fail "handed off to the official entrypoint despite placeholder credentials"
  fi

  rm -rf "$work"
}

# --------------------------------------------------------------------------- #
# T8. Fresh data directory (no PG_VERSION) skips resync and starts normally.
# --------------------------------------------------------------------------- #
test_fresh_volume_skips_resync() {
  printf '\n== TEST: fresh data directory skips resync ==\n'

  local work
  work="$(mktemp -d)"
  setup_mock "$work"
  run_entrypoint "$work"

  if grep -q 'resync' <<<"$OUT"; then
    fail "resync ran on a fresh data directory"
  else
    pass "no resync on a fresh data directory"
  fi
  if grep -q 'docker-entrypoint.sh' "$work/err.log" 2>/dev/null; then
    pass "official postgres entrypoint was reached directly"
  else
    fail "official postgres entrypoint was not reached on fresh volume (rc=$RC)"
  fi

  rm -rf "$work"
}

# --------------------------------------------------------------------------- #
# T9. Source-level invariants: EXIT trap uses globals only, resync SQL intact,
#     credential validation intact, normal startup exec'd after sync.
# --------------------------------------------------------------------------- #
test_source_invariants() {
  printf '\n== TEST: source invariants ==\n'

  if grep -q 'trap _resync_cleanup EXIT' "$ENTRYPOINT"; then
    pass "EXIT trap installed"
  else
    fail "EXIT trap not installed"
  fi

  local trap_body
  trap_body="$(sed -n '/^  _resync_cleanup() {/,/^  }$/p' "$ENTRYPOINT")"
  if grep -Eq '\$(pg_bin|tmp_dir|run_postgres)([^_a-zA-Z]|$)' <<<"$trap_body"; then
    fail "EXIT trap references a function local (unbound under set -u)"
  else
    pass "EXIT trap only reads pre-initialised globals"
  fi

  if grep -q 'ALTER ROLE %I LOGIN SUPERUSER PASSWORD' "$ENTRYPOINT"; then
    pass "bootstrap role resync SQL intact"
  else
    fail "bootstrap role resync SQL missing"
  fi
  if grep -q 'CREATE ROLE %I LOGIN NOSUPERUSER' "$ENTRYPOINT"; then
    pass "least-privilege role provisioning SQL intact"
  else
    fail "least-privilege role provisioning SQL missing"
  fi
  if grep -q '_check_credential POSTGRES_PASSWORD' "$ENTRYPOINT" &&
     grep -q '_check_credential POSTGRES_MIGRATE_PASSWORD' "$ENTRYPOINT" &&
     grep -q '_check_credential POSTGRES_APP_PASSWORD' "$ENTRYPOINT"; then
    pass "credential validation intact for all three passwords"
  else
    fail "credential validation missing a password"
  fi
  if grep -q 'if \[\[ -s "\$PGDATA/PG_VERSION" \]\]' "$ENTRYPOINT"; then
    pass "resync gated on an existing data directory"
  else
    fail "resync is not gated on an existing data directory"
  fi
  if tail -n 1 "$ENTRYPOINT" | grep -q 'exec /usr/local/bin/docker-entrypoint.sh'; then
    pass "normal PostgreSQL startup is exec'd after any sync"
  else
    fail "official entrypoint exec not the final step"
  fi
}

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
main() {
  test_startup_options
  test_bounded_stop
  test_success_resync_and_startup
  test_start_failure_no_unbound
  test_cleanup_when_pg_bin_unset
  test_psql_failure
  test_placeholder_fails_fast
  test_fresh_volume_skips_resync
  test_source_invariants

  printf '\n== RESULTS ==\n'
  printf 'passed: %d  failed: %d\n' "$TESTS_PASS" "$TESTS_FAIL"
  if [[ "$TESTS_FAIL" -gt 0 ]]; then
    exit 1
  fi
  exit 0
}

main "$@"