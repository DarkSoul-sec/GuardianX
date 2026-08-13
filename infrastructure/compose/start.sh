#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -f .env ]]; then
  echo "[guardianx] No .env found. Copying .env.example -> .env"
  cp .env.example .env
  echo ""
  echo "WARNING: .env was created with placeholder secrets. For a real"
  echo "deployment, stop now and set them:"
  echo "   1. SECRET_KEY                -> openssl rand -hex 32"
  echo "   2. POSTGRES_PASSWORD         -> a strong, unique password"
  echo "   3. POSTGRES_MIGRATE_PASSWORD -> a strong, unique password"
  echo "   4. POSTGRES_APP_PASSWORD     -> a strong, unique password"
  echo ""
fi

PLACEHOLDER_RE='^[A-Z_]+=(change-me|change-me-in-production|change-me-generate-a-strong-password|change-me-generate-with-openssl-rand-hex-32|changeme|change_me|secret|secret-key|placeholder|your_password_here|your-password-here|password|postgres)$'
if grep -qE "$PLACEHOLDER_RE" .env; then
  echo "[guardianx] ERROR: at least one secret is still a placeholder."
  echo "    Set strong unique values for SECRET_KEY, POSTGRES_PASSWORD,"
  echo "    POSTGRES_MIGRATE_PASSWORD and POSTGRES_APP_PASSWORD in $(pwd)/.env"
  exit 1
fi

if grep -qE '^SECRET_KEY=change-me-' .env; then
  echo "[guardianx] ERROR: SECRET_KEY is still the placeholder. Aborting."
  echo "    Generate one with: openssl rand -hex 32"
  echo "    Then set SECRET_KEY in $(pwd)/.env"
  exit 1
fi

echo "[guardianx] Starting GuardianX stack..."
docker compose up -d --build

echo ""
echo "[guardianx] Waiting for the stack to become healthy..."

for _ in $(seq 1 60); do
  if docker compose ps --format '{{.Service}} {{.Health}}' 2>/dev/null | grep -qE 'backend healthy'; then
    echo "[guardianx] Stack is up."
    break
  fi
  sleep 2
done

echo ""
echo "[guardianx] GuardianX is ready:"
echo "   Web UI:    http://localhost:${HTTP_PORT:-8080}"
echo "   API docs:  http://localhost:${HTTP_PORT:-8080}/api/docs"
echo ""
echo "   Useful commands:"
echo "     docker compose ps                    # container status"
echo "     docker compose logs -f backend       # backend logs"
echo "     docker compose down                  # stop (keep data)"
echo "     docker compose down -v               # stop and delete data"
