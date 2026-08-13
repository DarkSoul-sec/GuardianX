#!/usr/bin/env bash
#
# GuardianX installer.
#
# One-command bootstrap for a fresh clone:
#
#     git clone <repository>
#     cd GuardianX
#     ./install.sh
#
# The host is required to have ONLY Docker + Docker Compose. Python, PostgreSQL,
# Node.js, npm, Alembic and Nmap are all provided inside containers.
#
# What this installer does:
#   1. checks prerequisites (Docker, Compose)
#   2. validates host resources / port availability
#   3. creates infrastructure/compose/.env with strong random secrets (chmod 600)
#      - never overwriting an existing .env
#   4. validates the configuration
#   5. builds and starts the existing Compose stack
#   6. waits for PostgreSQL, db-init, migrations, backend and frontend health
#   7. prints a concise installation summary
#
# It does NOT install Docker or host OS packages.
# It does NOT run `docker compose down -v`.
#
set -euo pipefail

GX_LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/guardianx.lib.sh"
# shellcheck source=guardianx.lib.sh
. "$GX_LIB"

# Track whether we created the .env (so we can summarize).
GX_CREATED_ENV=0

# --------------------------------------------------------------------------- #
# 1. Prerequisites
# --------------------------------------------------------------------------- #
check_prerequisites() {
    step "Checking prerequisites"

    local docker_state compose_state os
    docker_state="$(gx_check_docker)"
    compose_state="$(gx_check_compose)"
    os="$(gx_os)"

    if [[ "$docker_state" != "ok" ]]; then
        fail_step "Docker"
        case "$docker_state" in
            missing)
                cat >&2 <<'MSG'

Docker is required to run GuardianX.
Please install Docker and Docker Compose, then run ./install.sh again.

  Linux/macOS:  https://docs.docker.com/get-docker/
  Windows:     install Docker Desktop (https://www.docker.com/products/docker-desktop)
               which includes Docker Compose and runs Linux containers via WSL 2.

MSG
                ;;
            daemon-not-running)
                cat >&2 <<'MSG'

The Docker daemon is not running.

  Linux:       sudo systemctl start docker   (or: sudo service docker start)
  macOS:       start Docker Desktop
  Windows:     start Docker Desktop

Then run ./install.sh again.
MSG
                ;;
        esac
        exit 1
    fi
    done_step "Docker"

    if [[ "$compose_state" != "ok"* ]]; then
        fail_step "Docker Compose"
        cat >&2 <<'MSG'

Docker Compose is required to run GuardianX.

Docker Compose v2 ships with Docker Desktop (Windows/macOS) and with
Docker Engine on Linux. If you only have the standalone v1 binary
(`docker-compose`), that is also accepted.

Install instructions: https://docs.docker.com/compose/install/
MSG
        exit 1
    fi
    done_step "Docker Compose"

    # Windows guidance: do not attempt system changes.
    if [[ "$os" == "windows" ]]; then
        gx_warn "Windows host detected"
        cat >&2 <<'MSG'

GuardianX is designed for Linux and macOS hosts.
On Windows, Docker Desktop (with WSL 2 backend) is required; the WSL 2 Linux
distribution is recommended. This installer will not modify your Windows
package manager. If Docker Desktop is already running, re-run this installer
from a WSL 2 shell or Git Bash.
MSG
        # Not fatal if Docker itself is working, but warn.
    fi

    # csprng needed for secret generation.
    if ! gx_have_csprng; then
        fail_step "Secret generator (openssl or python3)"
        cat >&2 <<'MSG'

GuardianX needs a cryptographic source to generate strong secrets.
Install openssl (or python3) on the host, then run ./install.sh again.

  Linux: sudo apt install openssl  (or: python3)
  macOS: openssl is available via Homebrew / LibreSSL
MSG
        exit 1
    fi
    done_step "Cryptographic source for secrets"
}

# --------------------------------------------------------------------------- #
# Resource checks (best-effort, never fatal on unsupported probes)
# --------------------------------------------------------------------------- #
check_resources() {
    step "Checking resources"

    # Disk space: warn if the default docker volume target looks tight.
    if [[ -w "/" ]]; then
        local avail_kb
        avail_kb="$(df -P / 2>/dev/null | awk 'NR==2{print $4}')"
        if [[ -n "${avail_kb:-}" ]] && [[ "$avail_kb" -lt 2097152 ]]; then
            gx_warn "Disk space: less than 2 GB free available; builds may fail"
        else
            done_step "Disk space"
        fi
    fi

    # Memory probe (Linux only via /proc/meminfo).
    if [[ -r /proc/meminfo ]]; then
        local mem_kb
        mem_kb="$(awk '/^MemTotal:/ {print $2}' /proc/meminfo)"
        if [[ -n "${mem_kb:-}" ]] && [[ "$mem_kb" -lt 2097152 ]]; then
            gx_warn "Memory: less than 2 GB detected; GuardianX may run slowly"
        else
            done_step "Memory"
        fi
    else
        done_step "Memory (not probed on this host)"
    fi
}

# --------------------------------------------------------------------------- #
# 5. Configuration UX
# --------------------------------------------------------------------------- #
interactive_config() {
    step "Configuring deployment"

    local http_port=8080
    local debug=true
    local auth_mode="local"

    printf 'GuardianX installation\n'
    printf '  Press ENTER to accept the default shown in [brackets].\n\n'

    # HTTP port.
    while true; do
        read -r -p "HTTP port [8080]: " input
        http_port="${input:-8080}"

        if ! [[ "$http_port" =~ ^[0-9]+$ ]] || \
           [ "$http_port" -lt 1 ] || [ "$http_port" -gt 65535 ]; then
            printf '  Please enter a valid TCP port (1-65535).\n'
            continue
        fi

        if ! gx_port_free "$http_port"; then
            printf '  Port %s is already in use.\n' "$http_port"
            while true; do
                read -r -p "  Use another port? [Y/n] " yn
                case "${yn:-y}" in
                    [Nn]*) exit 0 ;;
                    *) break ;;
                esac
            done
            continue
        fi
        break
    done

    # Deployment mode.
    printf '\nDeployment mode:\n'
    printf '  1) Local / development (DEBUG=true, no SMTP needed)\n'
    printf '  2) Production (DEBUG=false, SMTP required)\n'
    while true; do
        read -r -p "Choose [1]: " mode
        case "${mode:-1}" in
            1) debug=true;  auth_mode="local";  break ;;
            2) debug=false; auth_mode="local";  break ;;
            *) printf '  Enter 1 or 2.\n' ;;
        esac
    done

    if [[ "$debug" == "false" ]]; then
        printf '\nProduction mode selected.\n'
        printf '  Email verification / password-reset / cloud-mode signup require SMTP.\n'
        printf '  The stack will fail to start until EMAIL_SMTP_HOST is configured.\n'
        printf '  You can edit %s after installation to add SMTP settings.\n' "$ENV_FILE"
        read -r -p "Continue without SMTP now? [y/N] " yn
        case "$yn" in
            [Yy]*) : ;;
            *)  gx_log "Configure SMTP in $ENV_FILE, then run: ./guardianx start"; exit 0 ;;
        esac
    fi

    printf '\nUsing HTTP_PORT=%s, DEBUG=%s\n' "$http_port" "$debug"

    # Export for the writer.
    GX_HTTP_PORT="$http_port"
    GX_DEBUG="$debug"
    GX_AUTH_MODE="$auth_mode"
}

# --------------------------------------------------------------------------- #
# Generate / preserve .env
# --------------------------------------------------------------------------- #
write_env() {
    step "Preparing configuration"

    if [[ -f "$ENV_FILE" ]]; then
        # NEVER overwrite. Validate and preserve.
        gx_log "Existing $ENV_FILE detected — preserving existing credentials."

        local missing=0
        for v in SECRET_KEY POSTGRES_PASSWORD POSTGRES_MIGRATE_PASSWORD POSTGRES_APP_PASSWORD; do
            local val
            val="$(gx_env_get "$ENV_FILE" "$v")"
            if ! gx_validate_secret "$v" "$val"; then
                missing=1
            fi
        done

        if [[ "$missing" -ne 0 ]]; then
            fail_step "Existing secrets are invalid"
            cat >&2 <<MSG

$ENV_FILE exists but contains a missing or placeholder secret.
Refusing to overwrite it automatically.

Edit $ENV_FILE and set strong unique values:
    openssl rand -hex 32   # run 4x

Then run ./install.sh again (or: ./guardianx start).
MSG
            exit 1
        fi
        done_step "Existing configuration preserved"
        return 0
    fi

    # Fresh generation.
    local secret_key pg_pw mg_pw app_pw
    secret_key="$(gx_generate_secret)"
    pg_pw="$(gx_generate_secret)"
    mg_pw="$(gx_generate_secret)"
    app_pw="$(gx_generate_secret)"

    # Validate we actually got strong values.
    gx_validate_secret SECRET_KEY "$secret_key" || { fail_step "SECRET_KEY"; exit 1; }
    gx_validate_secret POSTGRES_PASSWORD "$pg_pw" || { fail_step "POSTGRES_PASSWORD"; exit 1; }
    gx_validate_secret POSTGRES_MIGRATE_PASSWORD "$mg_pw" || { fail_step "POSTGRES_MIGRATE_PASSWORD"; exit 1; }
    gx_validate_secret POSTGRES_APP_PASSWORD "$app_pw" || { fail_step "POSTGRES_APP_PASSWORD"; exit 1; }

    {
        printf '# GuardianX deployment configuration — generated by ./install.sh\n'
        printf '# NEVER commit this file. It contains secrets.\n'
        printf '# Generated: %s\n' "$(date -u '+%Y-%m-%d %H:%M:%S UTC')"
        printf '\n'
        printf '# ---- REQUIRED (auto-generated strong secrets) ----\n'
        printf 'SECRET_KEY=%s\n' "$secret_key"
        printf '\n'
        printf '# ---- Postgres (three-role least-privilege model) ----\n'
        printf 'POSTGRES_DB=guardianx\n'
        printf '# Bootstrap administrator (SUPERUSER, provisioning only)\n'
        printf 'POSTGRES_USER=guardianx\n'
        printf 'POSTGRES_PASSWORD=%s\n' "$pg_pw"
        printf '# Migration role (database owner, alembic only)\n'
        printf 'POSTGRES_MIGRATE_USER=guardianx_migrate\n'
        printf 'POSTGRES_MIGRATE_PASSWORD=%s\n' "$mg_pw"
        printf '# Application runtime role (DML only)\n'
        printf 'POSTGRES_APP_USER=guardianx_app\n'
        printf 'POSTGRES_APP_PASSWORD=%s\n' "$app_pw"
        printf '\n'
        printf '# ---- App ----\n'
        printf 'AUTH_MODE=%s\n' "$GX_AUTH_MODE"
        printf 'DEBUG=%s\n' "$GX_DEBUG"
        printf 'PUBLIC_APP_URL=http://localhost:%s\n' "$GX_HTTP_PORT"
        printf 'CORS_ORIGINS=http://localhost:%s\n' "$GX_HTTP_PORT"
        printf '\n'
        printf '# ---- Ports ----\n'
        printf 'HTTP_PORT=%s\n' "$GX_HTTP_PORT"
        printf '\n'
        printf '# ---- Email (empty => log-only; configure for production) ----\n'
        printf '# EMAIL_SMTP_HOST=\n'
        printf '# EMAIL_SMTP_PORT=587\n'
        printf '# EMAIL_SMTP_USER=\n'
        printf '# EMAIL_SMTP_PASSWORD=\n'
        printf '# EMAIL_FROM=GuardianX <noreply@example.com>\n'
        printf '# EMAIL_USE_TLS=true\n'
        printf '# EMAIL_USE_SSL=false\n'
        printf '# EMAIL_SMTP_TIMEOUT_SECONDS=15\n'
    } > "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    GX_CREATED_ENV=1
    done_step "Configuration generated (chmod 600)"
}

# --------------------------------------------------------------------------- #
# 6-7. Build, start, wait for health
# --------------------------------------------------------------------------- #
start_stack() {
    step "Building and starting the stack"

    gx_log "Pulling base images (may take a moment)..."
    if ! gx_compose pull postgres 2>&1; then
        gx_warn "Could not pull postgres image (will build/use cache)"
    fi

    gx_log "Building images..."
    # Prefer --pull (fresh base images) when the registry is reachable. If the
    # network is unavailable, fall back to cached images so an offline/fresh
    # machine install still succeeds using whatever is already present.
    if ! gx_compose build --pull 2>&1; then
        gx_warn "--pull failed (network/registry issue); retrying with cached images"
        if ! gx_compose build 2>&1; then
            fail_step "Build"
            cat >&2 <<MSG

Image build failed. Inspect with:

    ./guardianx logs backend

or:

    docker compose -f infrastructure/compose/docker-compose.yml -p ${PROJECT_NAME:-guardianx} build
MSG
            exit 1
        fi
    fi
    done_step "Build"

    gx_log "Starting services..."
    if ! gx_compose up -d 2>&1; then
        fail_step "Start"
        cat >&2 <<MSG

Stack failed to start. Inspect with:

    ./guardianx status
    ./guardianx logs
MSG
        exit 1
    fi
    done_step "Services started"
}

wait_health() {
    step "Waiting for services to become healthy"

    local -a checks=(
        "PostgreSQL:postgres"
        "Database init:db-init"
        "Backend:backend"
        "Frontend:frontend"
    )

    local idx=0 total=${#checks[@]} svc label
    for entry in "${checks[@]}"; do
        idx=$((idx+1))
        svc="${entry%%:*}"
        label="${entry#*:}"

        printf '[guardianx]   [%d/%d] %s ... ' "$idx" "$total" "$svc"

        case "$svc" in
            "Database init")
                if gx_dbinit_done; then
                    printf '%s\n' "$GX_OK"
                else
                    printf '%s\n' "$GX_FAIL"
                    fail_summary "$label"
                    return 1
                fi
                ;;
            "Migrations")
                # Migrations run inside the backend entrypoint; covered by backend health.
                printf '%s\n' "$GX_OK"
                ;;
            *)
                if gx_wait_service_healthy "$label" 240; then
                    printf '%s\n' "$GX_OK"
                else
                    printf '%s\n' "$GX_FAIL"
                    fail_summary "$label"
                    return 1
                fi
                ;;
        esac
    done
    done_step "All services healthy"
    return 0
}

# --------------------------------------------------------------------------- #
# Diagnostics on failure
# --------------------------------------------------------------------------- #
fail_summary() {
    local svc="$1"
    cat >&2 <<MSG

GuardianX failed to start on service: $svc

Check the status:

    ./guardianx status

Inspect recent logs:

    ./guardianx logs $svc

MSG
    gx_compose_ps 2>/dev/null || true
}

# --------------------------------------------------------------------------- #
# Summary
# --------------------------------------------------------------------------- #
summary() {
    step "Installation summary"

    local port
    port="$(gx_env_get "$ENV_FILE" HTTP_PORT)"
    port="${port:-8080}"

    printf '\nGuardianX is ready!\n\n'
    printf '  Web UI:    http://localhost:%s\n' "$port"
    printf '  API docs:  http://localhost:%s/api/docs\n\n' "$port"
    printf '  Manage with:\n'
    printf '    ./guardianx status     # show service health\n'
    printf '    ./guardianx logs       # follow all logs\n'
    printf '    ./guardianx logs backend\n'
    printf '    ./guardianx update     # rebuild + migrate\n'
    printf '    ./guardianx doctor     # full diagnostics\n'
    printf '    ./guardianx uninstall  # remove (keeps database)\n\n'
}

# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
main() {
    gx_log "GuardianX installer"

    if [[ ! -f "$COMPOSE_FILE" ]]; then
        fail_step "Compose file"
        gx_log "Missing $COMPOSE_FILE — are you running from the repository root?"
        exit 1
    fi

    check_prerequisites
    check_resources
    interactive_config
    write_env
    start_stack

    if wait_health; then
        summary
    else
        fail_step "Health checks"
        exit 1
    fi
}

main "$@"
