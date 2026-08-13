# GuardianX Developer Guide

## Prerequisites

- Python 3.13+
- Node.js 22+ and npm
- PostgreSQL 16 (or use Docker for the DB)

## 1. Backend

### Database setup (least-privilege, one script)

GuardianX uses three PostgreSQL roles (see `docs/DEPLOYMENT.md`). For a native
development database, provision them with:

```bash
cd GuardianX
PGPASSWORD=<your postgres superuser password> infrastructure/scripts/provision_dev_db.sh
```

This script (idempotent, run it as often as you like):

1. Ensures the `guardianx` database exists.
2. Creates/repairs `guardianx_migrate` (database owner, migrations only) and
   `guardianx_app` (DML only, no DDL) — both non-superuser.
3. Transfers ownership and grants to the migration role, grants the app role
   its runtime privileges plus default privileges for future tables.
4. Writes the **app role** credentials into `backend/.env`
   (`DATABASE_USER`/`DATABASE_PASSWORD`) and the **migration role** credentials
   into `backend/.env.migrate`.

### Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# edit .env: DATABASE_* connection details + a strong SECRET_KEY
# (provision_dev_db.sh already writes DATABASE_USER/DATABASE_PASSWORD)

# Run migrations as the migration role (reads backend/.env.migrate)
set -a; source .env.migrate; set +a
.venv/bin/alembic upgrade head

# Start the API (with live reload) — runs as the application role
uvicorn app.main:app --reload --port 8000
```

The API is available at `http://127.0.0.1:8000` with interactive docs at
`http://127.0.0.1:8000/api/docs`.

The shipped `backend/.env.example` defaults `DEBUG=true`, so the backend boots
out of the box without an SMTP server: emails (verification / password reset)
are rendered to the backend logs instead of being sent. Set `DEBUG=false` (and
an SMTP server) only for a production-style run — see
[`docs/DEPLOYMENT.md`](./DEPLOYMENT.md).

**Always use the venv's interpreter.** Running backend tests with the system
Python fails (missing `pydantic_settings`). Use:

```bash
source .venv/bin/activate
python -m pytest tests -q
# or
.venv/bin/python -m pytest tests -q
```

### Security test suite

`infrastructure/scripts/test_db_security.sh` spins up two scratch databases and
verifies the whole provisioning model end-to-end: role attributes, ownership,
migrations as the non-superuser migrate role, application CRUD, denied DDL, and
the existing-database upgrade path. Run it against a local PostgreSQL:

```bash
PG_TEST_SUPERUSER=postgres PG_TEST_SUPERPASSWORD=... \
PG_TEST_HOST=localhost PG_TEST_PORT=5432 \
BACKEND_DIR=$PWD/backend infrastructure/scripts/test_db_security.sh
```

### Backend layout

- `app/api/v1/` — HTTP route modules
- `app/services/` — business logic
- `app/models/`, `app/schemas/` — ORM models and Pydantic schemas
- `app/alembic/versions/` — database migrations
- `tests/` — test suite

## 2. Frontend

```bash
cd guardianx-frontend
npm install
npm run dev            # http://127.0.0.1:5173
```

### Frontend scripts

```bash
npm run dev        # dev server with HMR
npm run build      # type-check + production build
npm test           # run vitest once
npm run lint       # oxlint
npm run preview    # preview the production build
```

### Frontend layout

- `src/pages/` — route-level views
- `src/services/` — API clients (axios) and feature hooks
- `src/components/` — reusable UI + feature components
- `src/shared/` — design system, layout, storage helpers

## 3. Running the whole stack locally (manual)

Terminal 1 — backend:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Terminal 2 — frontend:

```bash
cd guardianx-frontend
npm run dev
```

The frontend dev server proxies `/api` to the backend, so `VITE_API_URL` only
needs overriding if you point the frontend at a remote backend
(e.g. `VITE_API_URL=https://api.example.com/api`).

## Testing

```bash
# Backend (from backend/, with the venv active)
python -m pytest tests -q

# Frontend
cd guardianx-frontend
npm test
```

Please add tests for new backend flows — see `tests/test_auth_flow.py` and
`tests/test_email_token.py` for the established unittest patterns.

## Code style

- Follow the existing patterns in the module you are editing.
- Include focused tests for new endpoints and services.
- Keep secrets in `.env` / environment variables — never commit them.
- Run `npm run lint` and `npm run build` for frontend changes, and the backend
  test suite for backend changes, before finishing.