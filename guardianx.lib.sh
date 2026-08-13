#!/usr/bin/env bash
#
# guardianx.lib.sh
# Shared library used by install.sh and the guardianx management CLI.
# Centralizes prerequisite detection, secret generation, health waiting,
# port management, and Compose-project scoping so the two entry points never
# duplicate logic.
set -o pipefail

GX_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$GX_ROOT/infrastructure/compose"
COMPOSE_FILE="$COMPOSE_DIR/docker-compose.yml"
ENV_FILE="$COMPOSE_DIR/.env"
ENV_EXAMPLE="$COMPOSE_DIR/.env.example"
PROJECT_NAME="${GX_PROJECT_NAME:-guardianx}"

GX_OK="OK"
GX_FAIL="FAIL"
GX_WARN="WARN"

# --------------------------------------------------------------------------- #
# Logging helpers
# --------------------------------------------------------------------------- #
gx_log() { printf '[guardianx] %s\n' "$*"; }
gx_ok() { printf '[guardianx] %s ... %s\n' "$1" "$GX_OK"; }
gx_fail() { printf '[guardianx] %s ... %s\n' "$1" "$GX_FAIL" >&2; }
gx_warn() { printf '[guardianx] %s ... %s\n' "$1" "$GX_WARN" >&2; }

# Step banner used by both install.sh and the guardianx CLI.
step()    { printf '\n[guardianx] %s\n' "$1"; }
done_step() { printf '[guardianx] %s ... %s\n' "$1" "$GX_OK"; }
fail_step() { printf '[guardianx] %s ... %s\n' "$1" "$GX_FAIL" >&2; }

# --------------------------------------------------------------------------- #
# Platform / environment detection
# --------------------------------------------------------------------------- #
gx_os() {
    case "$(uname -s)" in
        Linux*)  echo "linux" ;;
        Darwin*) echo "macos" ;;
        MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
        *)       echo "unknown" ;;
    esac
}

gx_is_root() { [ "$(id -u)" = "0" ]; }

# --------------------------------------------------------------------------- #
# Prerequisite checks
# --------------------------------------------------------------------------- #
# Returns 0 if a command exists on PATH.
gx_have() { command -v "$1" >/dev/null 2>&1; }

# Verify Docker binary & daemon. Echoes "ok" on success or a reason string.
gx_check_docker() {
    if ! gx_have docker; then
        echo "missing"
        return 1
    fi
    if ! docker info >/dev/null 2>&1; then
        echo "daemon-not-running"
        return 1
    fi
    echo "ok"
    return 0
}

# Verify docker compose (v2 plugin or legacy v1). Echoes "ok" or reason.
gx_check_compose() {
    if docker compose version >/dev/null 2>&1; then
        echo "ok"
        return 0
    fi
    # Legacy v1 standalone?
    if gx_have docker-compose; then
        echo "ok-legacy"
        return 0
    fi
    echo "missing"
    return 1
}

# Pick the compose invocation prefix so callers always get a working command.
gx_compose_cmd() {
    if docker compose version >/dev/null 2>&1; then
        echo "docker compose"
    elif gx_have docker-compose; then
        echo "docker-compose"
    else
        return 1
    fi
}

# Run compose scoped to the project root + compose file + project name tag.
gx_compose() {
    local cmd
    cmd="$(gx_compose_cmd)" || return 1
    ( cd "$COMPOSE_DIR" && $cmd -f "$(basename "$COMPOSE_FILE")" -p "$PROJECT_NAME" "$@" )
}

# --------------------------------------------------------------------------- #
# Secret generation
# A "strong" secret: >= 32 hex chars produced by a CSPRNG.
# --------------------------------------------------------------------------- #
gx_have_csprng() {
    # Prefer openssl (widely available, cryptographic).
    if gx_have openssl; then return 0; fi
    # Python fallback (only used during install; not a host runtime requirement).
    if gx_have python3; then return 0; fi
    return 1
}

gx_generate_secret() {
    if gx_have openssl; then
        openssl rand -hex 32
    elif gx_have python3; then
        python3 -c 'import secrets; print(secrets.token_hex(32))'
    else
        return 1
    fi
}

# Known placeholder values the stack refuses (mirrors postgres-entrypoint.sh).
GX_PLACEHOLDERS=(
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

# Validate that a secret is not a known placeholder and is long enough.
# Args: name value -> returns 0 if valid, 1 otherwise.
gx_validate_secret() {
    local name="$1" value="${2:-}"
    if [[ -z "$value" ]]; then
        gx_fail "$name is empty"
        return 1
    fi
    if [[ ${#value} -lt 16 ]]; then
        gx_fail "$name is shorter than 16 characters"
        return 1
    fi
    local cand
    for cand in "${GX_PLACEHOLDERS[@]}"; do
        if [[ "$value" == "$cand" ]]; then
            gx_fail "$name is still the placeholder '$cand'"
            return 1
        fi
    done
    return 0
}

# --------------------------------------------------------------------------- #
# Environment file helpers
# --------------------------------------------------------------------------- #
# Read a value from an existing .env (NAME=value). Echoes the value or "".
gx_env_get() {
    local file="$1" name="$2"
    [[ -f "$file" ]] || return 0
    local line val
    line="$(grep -E "^${name}=" "$file" 2>/dev/null | head -1 || true)"
    if [[ -z "$line" ]]; then
        echo ""
        return 0
    fi
    # Strip NAME= prefix, handling surrounding quotes.
    val="${line#*=}"
    val="${val%\"}"; val="${val#\"}"
    echo "$val"
}

# --------------------------------------------------------------------------- #
# Port helpers
# --------------------------------------------------------------------------- #
# Returns 0 if the TCP port is free on the host (no listener).
gx_port_free() {
    local port="$1"
    if gx_have ss; then
        ! ss -ltn 2>/dev/null | awk '{print $4}' | grep -qE ":${port}$"
        return $?
    elif gx_have netstat; then
        ! netstat -ltn 2>/dev/null | awk '{print $4}' | grep -qE ":${port}$"
        return $?
    fi
    # Fallback: try connecting; success means it is in use.
    if ! (echo >/dev/tcp/127.0.0.1/"$port") >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

# --------------------------------------------------------------------------- #
# Health waiting
# --------------------------------------------------------------------------- #
# Wait until a named compose service reports healthy, or time out.
# Args: service timeout_seconds
gx_wait_service_healthy() {
    local svc="$1" timeout="${2:-180}" deadline elapsed=0
    deadline=$(( $(date +%s) + timeout ))
    while true; do
        local state
        state="$(gx_compose ps --format '{{.Service}} {{.Health}}' 2>/dev/null \
            | awk -v s="$svc" '$1==s {print $2}')"
        if [[ "$state" == "healthy" ]]; then
            return 0
        fi
        # A failed service should abort early.
        if [[ "$state" == "unhealthy" || "$state" == "exited" ]]; then
            return 1
        fi
        [[ $(date +%s) -ge $deadline ]] && return 1
        sleep 2
    done
    return 1
}

# Wait for db-init to complete successfully.
# db-init is a one-shot `restart: "no"` container. `docker compose ps` hides
# exited one-shots by default, so `--all` is required to observe its final
# state + exit code.
gx_wait_dbinit() {
    local timeout="${1:-180}" deadline
    deadline=$(( $(date +%s) + timeout ))
    while true; do
        # Try the v2 `--all` form first; fall back to a label-based query.
        local state code
        state="$(gx_compose ps --all --format '{{.Service}} {{.State}} {{.ExitCode}}' 2>/dev/null \
            | awk '$1=="db-init" {print $2; print $3}' 2>/dev/null || true)"
        if [[ -z "$state" ]]; then
            # Fallback: inspect via docker labels (works on legacy compose too).
            local info
            info="$(docker ps -a --filter "label=com.docker.compose.project=${PROJECT_NAME}" \
                --filter "label=com.docker.compose.service=db-init" \
                --format '{{.State}} {{.Status}}' 2>/dev/null || true)"
            if [[ -n "$info" ]]; then
                state="${info%% *}"
                code="$info"
                code="${code#* }"
            fi
        else
            code="$(printf '%s\n' "$state" | tail -1)"
            state="$(printf '%s\n' "$state" | head -1)"
        fi

        if [[ -n "$state" ]]; then
            case "$state" in
                exited|completed*)
                    if [[ "$code" == "0" || "$code" == *"0"* ]]; then
                        return 0
                    fi
                    return 1
                    ;;
            esac
        fi
        [[ $(date +%s) -ge $deadline ]] && return 1
        sleep 2
    done
    return 1
}

# A more robust combined check: db-init has exited successfully. Because the
# backend depends_on db-init (condition: service_completed_successfully), a
# healthy backend is also sufficient proof that db-init + migrations ran.
gx_dbinit_done() {
    # If the backend is healthy, db-init must have completed successfully.
    if gx_wait_service_healthy backend 5 >/dev/null 2>&1; then
        return 0
    fi
    # Otherwise explicitly inspect db-init's exit code.
    gx_wait_dbinit 60 >/dev/null 2>&1
}

# Wait for postgres to become healthy.
gx_wait_postgres() {
    local timeout="${1:-180}"
    gx_wait_service_healthy postgres "$timeout"
}

# --------------------------------------------------------------------------- #
# Container listing scoped to this project only.
# --------------------------------------------------------------------------- #
gx_containers() {
    # Only GuardianX project containers (filtered by the project name label).
    docker ps -a --filter "label=com.docker.compose.project=${PROJECT_NAME}" \
        --format '{{.Names}} {{.Status}} {{.Ports}}' 2>/dev/null
}

# --------------------------------------------------------------------------- #
# Compose health summary
# --------------------------------------------------------------------------- #
gx_compose_ps() {
    gx_compose ps --format "table {{.ID}}\t{{.Name}}\t{{.Command}}\t{{.State}}\t{{.Ports}}\t{{.Health}}" 2>/dev/null
}
