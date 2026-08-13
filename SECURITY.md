# Security Policy

## Reporting a Vulnerability

GuardianX takes security seriously. If you discover a security issue, please
report it privately rather than opening a public issue.

- **Preferred:** open a [GitHub Security Advisory](https://github.com/DarkSoul-sec/GuardianX/security/advisories/new)
  on the repository.
- **Email:** if you prefer, contact the maintainers via the address listed on
  the GitHub repository page.

Please include:

- A description of the vulnerability and its impact.
- Steps to reproduce, including the GuardianX version and environment.
- Any suggested fix, if you have one.

You should receive a response within a few days. We ask that you do not
disclose the issue publicly until a fix has been released.

## Scope

The following are in scope:

- The GuardianX backend API (`backend/`) and frontend (`guardianx-frontend/`).
- The Docker Compose deployment (`infrastructure/compose/`).
- Dependencies and their known vulnerabilities.

Out of scope: infrastructure you deploy on your own (host OS, cloud provider
configuration) and third-party services you connect to GuardianX.

## Supported Versions

| Version | Supported |
|---------|-----------|
| latest release | ✅ |
| development (main) | ✅ |

Older releases are not supported; please upgrade to the latest release.

## Security Notes & Hardening

Deployment hardening guidance lives in
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md). Key points:

- Always use a strong, unique `SECRET_KEY` and `POSTGRES_PASSWORD`.
- Keep `DEBUG=false` in production.
- Configure real SMTP in production; the backend refuses to start in
  production mode without it (verification/reset emails would otherwise not
  be delivered).
- Keep `ALLOW_PRIVATE_NETWORK_SCANS=false` (the default) to preserve
  SSRF / internal-scan protection.
- Terminate TLS in front of the web UI and never expose the backend port
  directly.
- Never commit `.env` files, API keys, or other secrets.
