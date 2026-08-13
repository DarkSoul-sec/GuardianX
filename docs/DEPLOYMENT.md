# GuardianX Deployment Guide

This guide covers the recommended production deployment using Docker Compose,
plus the manual development setup.

## Least-privilege database model

GuardianX runs against PostgreSQL using **three separate roles** (never the
application as a superuser):

| Role | Used for | Capabilities |
|------|----------|--------------|
| `guardianx` (bootstrap) | initial provisioning only | SUPERUSER |
| `guardianx_migrate` | `alembic upgrade head` only | owns the DB, no superuser |
| `guardianx_app` | the running FastAPI app | DML only, no DDL |

The application role can `SELECT`/`INSERT`/`UPDATE`/`DELETE` on application
tables and use sequences, but cannot create/drop tables, types, roles or
databases. The migration role owns the schema and runs migrations, but also has
no superuser attributes. Default privileges mean any table a future migration
creates is automatically granted to the application role.

Provisioning is performed by `infrastructure/docker/db-init.sh`, which is fully
idempotent and never drops or rewrites data.

## Quick start (Docker, one command)

```bash
cd infrastructure/compose
./start.sh
```

`start.sh` will:

1. Copy `.env.example` to `.env` on first run.
2. Refuse to start if `SECRET_KEY` or any database password is still a
   placeholder.
3. Start `postgres`, then a one-shot `db-init` provisioning service, then the
   `backend` (which runs `alembic upgrade head` as the migration role), then the
   `frontend`.
4. Wait for the stack to become healthy and print the URLs.

If you already have a `.env`:

```bash
cd infrastructure/compose
docker compose up -d --build
```

> **Important:** Generate strong, unique secrets before deploying:
> ```bash
> openssl rand -hex 32   # run 4x: SECRET_KEY + the three DB passwords
> ```
>
> **First run:** the shipped `.env.example` defaults `DEBUG=true` so a fresh
> stack boots without an SMTP server (emails are logged to the console). For a
> production deployment, set `DEBUG=false` and configure SMTP (see below).

### Upgrading an existing deployment

`db-init.sh` upgrades an existing database volume in place on the first
`docker compose up` with the new compose file: it creates the two non-superuser
roles, transfers ownership of the database/schema/tables to `guardianx_migrate`,
and grants the application role its DML privileges. No data is rewritten.
Re-provision at any time with:

```bash
docker compose run --rm db-init
```

## Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | **yes** | — | JWT signing secret (≥ 16 chars, random) |
| `POSTGRES_DB` | no | `guardianx` | Database name |
| `POSTGRES_USER` | no | `guardianx` | Bootstrap admin (SUPERUSER, provisioning only) |
| `POSTGRES_PASSWORD` | **yes** | `change-me` | Bootstrap password (never used by the app) |
| `POSTGRES_MIGRATE_USER` | no | `guardianx_migrate` | Migration role (DB owner) |
| `POSTGRES_MIGRATE_PASSWORD` | **yes** | `change-me` | Migration role password |
| `POSTGRES_APP_USER` | no | `guardianx_app` | Runtime role (DML only) |
| `POSTGRES_APP_PASSWORD` | **yes** | `change-me` | Runtime role password |
| `DEBUG` | no | `false` | Enable dev mode (never `true` in prod) |
| `PUBLIC_APP_URL` | no | `http://localhost:8080` | Public origin (email links) |
| `CORS_ORIGINS` | no | `http://localhost:8080` | Comma-separated allowed origins |
| `HTTP_PORT` | no | `8080` | Host port for the web UI |
| `EMAIL_SMTP_HOST` | prod only | empty | SMTP server (empty = log only; **required** when `DEBUG=false`) |
| `EMAIL_SMTP_PORT` | no | `587` | SMTP port (`587` with STARTTLS, `465` with SSL) |
| `EMAIL_SMTP_USER` | no | empty | SMTP username / API key |
| `EMAIL_SMTP_PASSWORD` | no | empty | SMTP password / API key secret |
| `EMAIL_FROM` | no | `GuardianX <noreply@localhost>` | Sender shown to recipients |
| `EMAIL_USE_TLS` | no | `true` | Use STARTTLS (port 587) |
| `EMAIL_USE_SSL` | no | `false` | Use implicit TLS/SSL (port 465) |
| `EMAIL_SMTP_TIMEOUT_SECONDS` | no | `15` | SMTP connect/send timeout |

### Email (password reset / notifications / cloud mode)

The **local edition** (`AUTH_MODE=local`, the default) does not require SMTP at
all: the first-run administrator is created without an email address, and local
administrator password recovery is handled at the deployment level via
`backend/scripts/reset_admin_password.py`. SMTP is optional and only used for
accounts that have an email configured.

When `EMAIL_SMTP_HOST` is empty and `DEBUG=true`, emails are rendered to the
backend logs — clearly labelled `EMAIL DELIVERY MODE: DEVELOPMENT / LOG ONLY`
— instead of being sent. This is intended for local development only.

**Cloud mode (`AUTH_MODE=cloud`) with `DEBUG=false` requires `EMAIL_SMTP_HOST`.**
The app fails fast at startup with a clear error if cloud mode is configured
without SMTP, so you can never silently ship a deployment where verification
/reset emails are not delivered.

Use **STARTTLS (port 587)** or **implicit SSL (port 465)** — never both:

```bash
# STARTTLS (recommended for most providers)
EMAIL_SMTP_HOST=smtp.example.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=apikey
EMAIL_SMTP_PASSWORD=...
EMAIL_FROM="GuardianX <noreply@example.com>"
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
EMAIL_SMTP_TIMEOUT_SECONDS=15
```

```bash
# Implicit SSL (e.g. port 465 providers)
EMAIL_SMTP_HOST=smtp.example.com
EMAIL_SMTP_PORT=465
EMAIL_SMTP_USER=apikey
EMAIL_SMTP_PASSWORD=...
EMAIL_FROM="GuardianX <noreply@example.com>"
EMAIL_USE_TLS=false
EMAIL_USE_SSL=true
```

`PUBLIC_APP_URL` must be the origin users actually visit, because verification
and reset emails link back to it.

**Logging & privacy:** in production, delivery logs only ever contain safe
metadata — the recipient's domain, the email type (e.g. `password_reset`), a
correlation id, and the delivery outcome. One-time tokens, full verification /
reset URLs and SMTP credentials are never written to the logs.

## Health checks

| Service | Endpoint | Purpose |
|---------|----------|---------|
| backend | `GET /health` | API liveness (container healthcheck) |
| postgres | `pg_isready` | Database readiness |

`start.sh` waits for the backend to report `healthy` before printing the ready
message.

## Operations

```bash
docker compose ps                  # status + health
docker compose logs -f backend     # backend logs
docker compose logs -f frontend    # frontend / nginx logs
docker compose run --rm db-init    # re-provision roles/grants (idempotent)
docker compose down                # stop (keep the database volume)
docker compose down -v             # stop and delete the database volume
```

## Production hardening checklist

Before exposing GuardianX publicly:

- [ ] Set **unique, random** `SECRET_KEY`, `POSTGRES_PASSWORD`,
      `POSTGRES_MIGRATE_PASSWORD` and `POSTGRES_APP_PASSWORD`.
- [ ] Set `DEBUG=false`.
- [ ] Configure a real SMTP host for email flows.
- [ ] Set `PUBLIC_APP_URL` to the public HTTPS origin.
- [ ] Put a TLS-terminating proxy (e.g. Traefik, nginx, or a cloud LB) in
      front of `HTTP_PORT` with valid certificates.
- [ ] Keep `ALLOW_PRIVATE_NETWORK_SCANS=false` (the default) to preserve
      SSRF / internal-scan protection.
- [ ] Restrict the ventilator to trusted reverse proxies and sources.
- [ ] Back up the `postgres_data` volume regularly.
- [ ] Verify the application role has no DDL privileges:
      `docker compose run --rm db-init` after `psql \du`-style checks, or run
      `infrastructure/scripts/test_db_security.sh`.

## Migrations

On every backend start the entrypoint runs `alembic upgrade head` **as the
migration role** (`guardianx_migrate`), then launches uvicorn **as the
application role** (`guardianx_app`) with the bootstrap/migration credentials
stripped from the runtime environment. The application process therefore never
has access to the SUPERUSER or migration-role passwords.

Create a new migration after model changes:

```bash
cd backend
.venv/bin/alembic revision --autogenerate -m "describe change"
```

Run migrations manually against a native development database with the
migration role (see `docs/DEVELOPMENT.md` for provisioning):

```bash
set -a; source backend/.env.migrate; set +a
cd backend && .venv/bin/alembic upgrade head
```

### PostgreSQL enum limitation (downgrades)

Some migrations add values to PostgreSQL `enum` types (`ALTER TYPE ... ADD
VALUE`). PostgreSQL **cannot remove a value from an enum type** — `ALTER TYPE
... DROP VALUE` does not exist, so rolling back an enum-changing migration is
not possible without rebuilding the type. Before relying on a downgrade, check
the migration files for `ADD VALUE` statements.

Recovery procedure (only if you must undo an enum change):

1. Stop the stack: `docker compose down` (keeps the volume).
2. Restore the `postgres_data` volume from a backup taken before the upgrade,
   or dump/restore the affected table with the old type definition.
3. Bring the stack back up: `docker compose up -d --build`.

There is no in-place `downgrade` for enum changes; plan upgrades to be
permanent or back up first.