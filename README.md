<div align="center">

# 🛡 GuardianX

### AI-Powered Cyber Asset Management, Vulnerability Assessment & Attack Surface Management Platform

![Python](https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141-green?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=for-the-badge&logo=typescript)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql)
![License](https://img.shields.io/badge/License-Apache_2.0-blue?style=for-the-badge)

</div>

---

# 🚀 Overview

GuardianX is a modern cybersecurity platform that helps organizations discover
assets, identify vulnerabilities, prioritize security risks, and improve their
overall security posture through AI-powered insights.

It combines automated network scanning, vulnerability intelligence, risk
analysis, asset management, and executive reporting into one unified platform.

---

# ✨ Key Features

- 🛡 Asset Management
- 🌐 Network Discovery
- 🔎 Nmap Scan Engine (with scheduling)
- 📊 Attack Surface Management
- ⚠ CVE Enrichment & Threat Intelligence
- 📈 Risk Scoring
- 🤖 AI Security Copilot (OpenAI / Gemini / Ollama / rules)
- 📑 Executive Reports
- 👥 Role-Based Access Control (admin, security engineer, analyst, viewer)
- 🔐 JWT Authentication with first-run local admin setup & password reset
- 🚨 SOC module: alerts, incidents, activity history
- 📦 Notifications & activity log
- 🛰 VirusTotal (Bring-Your-Own-Key) integration

---

# 🏗 Architecture

```
                    Users
                      │
                      ▼
             React Frontend (nginx)
                      │
                 REST API (FastAPI)
                      │
     ┌────────────────────────────────┐
     │ Authentication                 │
     │ Asset Management               │
     │ Scan Engine                    │
     │ CVE Intelligence               │
     │ Risk Engine                    │
     │ AI Recommendation Engine       │
     │ Reporting / SOC                │
     └────────────────────────────────┘
                      │
                PostgreSQL Database
```

---

# ⚙ Technology Stack

## Backend

- Python 3.13 + FastAPI
- SQLAlchemy + Alembic
- PostgreSQL 16
- JWT authentication with refresh-token rotation
- Nmap scan engine

## Frontend

- React 19 + TypeScript
- TailwindCSS
- React Query
- Recharts

## Security & Intelligence

- Nmap
- CVE databases (NVD, KEV, EPSS)
- Threat & phishing detection
- AI risk scoring (OpenAI / Gemini / Ollama / rules)

---

# 📂 Project Structure

```
GuardianX/
├── backend/                  # FastAPI application + tests
├── guardianx-frontend/       # React/TypeScript SPA + tests
├── docs/                     # Architecture, deployment, developer guides
├── infrastructure/
│   └── compose/              # Docker Compose deployment + start.sh
├── screenshots/
└── .github/
```

See [`docs/VULNERABILITY_INTELLIGENCE.md`](docs/VULNERABILITY_INTELLIGENCE.md)
for the Vulnerability Intelligence Center.

---

# 🚀 Quick Start

## Requirements

- **Docker** ([get Docker](https://docs.docker.com/get-docker/))
- **Docker Compose** (ships with Docker; or install the Compose plugin)

> No Python, PostgreSQL, Node.js, npm, or Nmap installation is required on the
> host — everything runs inside containers, including Nmap and the scan engine.

## One-command install

```bash
git clone <repository>
cd GuardianX
./install.sh
```

`install.sh` checks Docker, generates strong random secrets, validates the
configuration, builds and starts the stack, waits for all health checks, and
prints the application URL. Open:

- Web UI: `http://localhost:8080`
- API docs: `http://localhost:8080/api/docs`

### Management

Once installed, use the root-level management CLI:

```bash
./guardianx status      # show service health
./guardianx logs        # follow all logs
./guardianx logs backend
./guardianx update      # rebuild + migrate (preserves your database)
./guardianx doctor      # full diagnostics
./guardianx stop        # stop (keeps database data)
./guardianx uninstall   # stop + remove (database preserved by default)
```

GuardianX uses **three PostgreSQL roles** (least privilege): a bootstrap
administrator (provisioning only), `guardianx_migrate` (database owner, runs
`alembic`), and `guardianx_app` (DML only — the running application never gets a
superuser). Provisioning is automatic. The default local edition sets
`DEBUG=true` and does **not** require SMTP (emails are logged to the backend
console). For production, set `DEBUG=false` and configure SMTP — see
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

---

## Development / Contributors

> Developers should use the native tooling below. **End users do not need any of
> these dependencies** — the Docker installation above is self-contained.

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# provision roles + database (one-time, idempotent):
PGPASSWORD=<postgres superuser password> ../infrastructure/scripts/provision_dev_db.sh
set -a; source .env.migrate; set +a   # migrate as the migration role
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd guardianx-frontend
npm install
npm run dev            # http://127.0.0.1:5173
```

See [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) for details.

---

# 📚 Documentation

- [API Reference](docs/api/API.md)
- [Architecture](docs/architecture/ARCHITECTURE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Developer Guide](docs/DEVELOPMENT.md)
- [Contributing](docs/CONTRIBUTING.md)
- [Vulnerability Intelligence](docs/VULNERABILITY_INTELLIGENCE.md)
- [Threat Intelligence](docs/THREAT_INTELLIGENCE.md)
- [VirusTotal Integration](docs/VIRUSTOTAL_INTEGRATION.md)

---

# 🔑 Environment Variables

## Backend (`backend/.env`)

```env
# Required
SECRET_KEY=            # a long random string; generate with `openssl rand -hex 32`
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=guardianx
DATABASE_USER=guardianx_app   # runtime role (DML only, no DDL)
DATABASE_PASSWORD=            # app role password (see provision_dev_db.sh)

# Migrations use a separate, database-owning role (guardianx_migrate); its
# credentials live in backend/.env.migrate, created by provision_dev_db.sh.

# Optional
DEBUG=true             # true => emails logged to console; REQUIRED SMTP when false
EMAIL_SMTP_HOST=       # empty + DEBUG=true => emails logged to console
EMAIL_SMTP_PORT=587    # STARTTLS (587) or implicit SSL (465)
EMAIL_SMTP_USER=
EMAIL_SMTP_PASSWORD=
EMAIL_FROM=GuardianX <noreply@example.com>
EMAIL_USE_TLS=true     # STARTTLS on port 587
EMAIL_USE_SSL=false    # implicit SSL on port 465 (never with EMAIL_USE_TLS)
EMAIL_SMTP_TIMEOUT_SECONDS=15
OPENAI_API_KEY=
GEMINI_API_KEY=
```

## Frontend (`guardianx-frontend/.env`)

The dev server proxies `/api` to the backend by default, so no variable is
required locally. To point the SPA at a remote API, set `VITE_API_URL`
(default `http://127.0.0.1:8000/api`).

## Docker (`infrastructure/compose/.env`)

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for the full variable table.

---

# 📌 Status

GuardianX is at **feature freeze**. Development is focused on Release Candidate
polish: authentication, UI/UX, installation, documentation, and stability —
no new major feature modules.

## ✅ Implemented

- Authentication: first-run local administrator setup, login, password
  reset, profile, and session management
- Role-based access control (admin, security engineer, analyst, viewer)
- Asset management
- Nmap scan engine & scheduling
- Findings triage & bulk actions
- Risk scoring
- AI Copilot (OpenAI / Gemini / Ollama / rules)
- Reporting & executive reports
- Threat intelligence & vulnerability intelligence
- VirusTotal (Bring-Your-Own-Key) integration
- Phishing detection analysis
- SOC: alerts, incidents, activity history
- Notifications and activity log

---

# 🤝 Contributing

Contributions are welcome. Please read
[`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md).

---

# 🔒 Security

Please read [`SECURITY.md`](SECURITY.md).

---

## License

GuardianX is licensed under the Apache License 2.0.

Copyright © 2026 Anirudh Sinwal.

You may use, reproduce, modify, and distribute GuardianX in accordance with the terms of the Apache License 2.0.

See the [LICENSE](LICENSE) file for the complete license text.

---

<div align="center">

**GuardianX**

*Protect. Detect. Secure.*

</div>
