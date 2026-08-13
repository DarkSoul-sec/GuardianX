#!/usr/bin/env bash
#
# GuardianX PostgreSQL startup credential guard.
#
# Runs BEFORE the official postgres image entrypoint. Refuses to start when any
# required database credential is missing, is a known placeholder, or is too
# short to be treated as a real secret. This guarantees a misconfigured
# deployment fails fast and clearly instead of silently provisioning the
# database with default/guessable credentials.
#
# All three database credentials are checked here because they are the ones
# db-init.sh bakes into PostgreSQL roles. SECRET_KEY is enforced separately by
# the application at startup (app/main.py), and by start.sh.
#
# The official entrypoint is then exec'd unchanged, so image behaviour
# (initdb on first run, /docker-entrypoint-initdb.d scripts, runtime start) is
# fully preserved.
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

_check_credential POSTGRES_PASSWORD
_check_credential POSTGRES_MIGRATE_PASSWORD
_check_credential POSTGRES_APP_PASSWORD

exec /usr/local/bin/docker-entrypoint.sh "$@"
