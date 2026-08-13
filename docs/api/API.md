# GuardianX API Reference

This document describes the versioned REST API exposed by the GuardianX backend.

- **Base URL:** `http://<host>:8000/api` (proxied to `/api` in the Docker stack)
- **OpenAPI/Swagger UI:** `http://<host>:8000/api/docs`
- **ReDoc:** `http://<host>:8000/api/redoc`
- **Health:** `GET /health`

All endpoints except the authentication and public routes require a bearer token:

```
Authorization: Bearer <access_token>
```

---

## Authentication

### POST `/auth/signup`
Create a new account and send an email verification link.

**Body (JSON):**
```json
{ "username": "jane", "email": "jane@example.com", "password": "Sup3rSecure!Long" }
```
`password` must be at least 12 characters. Returns `201`.

### POST `/auth/login`
Authenticate and return an access/refresh token pair.

Takes `application/x-www-form-urlencoded` with `username` and `password`.

**Response:**
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### POST `/auth/logout`
Revoke the presented refresh token (best-effort, always returns `204`).

```json
{ "refresh_token": "..." }
```

### POST `/auth/refresh`
Rotate a refresh token into a fresh pair. The old token is revoked, so a stolen token can only be used once.

```json
{ "refresh_token": "..." }
```

### POST `/auth/verify-email`
Confirm an email address with the one-time token from the verification link.

```json
{ "token": "..." }
```

### POST `/auth/resend-verification`
Resend the verification email. Always returns success (avoids user enumeration).

```json
{ "email": "jane@example.com" }
```

### POST `/auth/forgot-password`
Send a password-reset link. Always returns success (avoids user enumeration).

```json
{ "email": "jane@example.com" }
```

### POST `/auth/reset-password`
Set a new password with a valid reset token. Also signs out all existing sessions.

```json
{ "token": "...", "new_password": "NewSup3rng!" }
```

---

## Users

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/users/me` | ✓ | Current profile |
| PATCH | `/users/me` | ✓ | Update profile (`username`, `email`) |
| POST | `/users/me/password` | ✓ | Change own password (revokes all sessions) |
| GET | `/users/me/sessions` | ✓ | List active sessions |
| POST | `/users/me/sessions/revoke-all` | ✓ | Sign out all sessions |
| DELETE | `/users/me/sessions/{token_id}` | ✓ | Revoke a single session |
| GET | `/users` | admin | List all users |
| GET | `/users/{user_id}` | admin | Get a user |
| PATCH | `/users/{user_id}` | admin | Edit a user |
| PATCH | `/users/{user_id}/role` | admin | Change role |
| PATCH | `/users/{user_id}/status` | admin | Activate/deactivate |
| DELETE | `/users/{user_id}` | admin | Delete a user |

**Profile response:**
```json
{
  "id": 1,
  "username": "jane",
  "email": "jane@example.com",
  "role": "USER",
  "is_active": true,
  "email_verified": true
}
```

---

## Core Modules

### Assets — `/assets`
- `GET /assets` — list assets (paged, filterable)
- `POST /assets` — add an asset
- `GET /assets/{id}` — asset detail
- `PATCH /assets/{id}` — update asset
- `DELETE /assets/{id}` — delete asset

### Scans — `/scans`
- `GET /scans`, `POST /scans`, `GET /scans/{id}`, `DELETE /scans/{id}`
- `GET /scans/operations` — scan engine status
- `GET /scans/{id}/results`, `GET /scans/{id}/ws` — live results

### Findings — `/findings`
- `GET /findings`, `GET /findings/stats`
- `POST /findings/bulk-status`, `GET /findings/assignees`
- `GET /findings/export`, `GET /findings/ws`

### Schedules — `/schedules`
- `GET /schedules`, `POST /schedules`, `PATCH /schedules/{id}`, `DELETE /schedules/{id}`

### Reports — `/reports`
- `GET /reports/executive`
- `GET /reports/assets/{asset_id}`
- `GET /reports/scans/{scan_id}`

---

## Intelligence & Security

| Prefix | Endpoints |
|--------|-----------|
| `/intelligence` | `GET /domain`, `GET /ip`, `GET /hash`, `GET /url` |
| `/threat-intel` | `GET /stats`, `GET /search`, `GET /cve/{cve_id}`, `GET /kev`, `GET /trending`, `GET /attack-techniques` |
| `/virustotal` | `GET /domain/{domain}`, `GET /ip/{ip_address}`, `GET /file/{sha256}`, `GET /url` |
| `/phishing` | `POST /analyze` |
| `/security` | `GET /config` |
| `/copilot` | `GET /provider`, `GET /memory`, `POST /chat`, `POST /chat/stream` |

### SOC
| Path | Description |
|------|-------------|
| `GET /soc/overview` | SOC summary metrics |
| `GET /soc/alerts` | Alert list |
| `GET /soc/alerts/summary` | Alert aggregates |
| `PATCH /soc/alerts/{id}` | Update alert status |
| `DELETE /soc/alerts/{id}` | Delete alert |
| `GET /soc/incidents` | Incident list |
| `POST /soc/incidents` | Promote alert to incident |
| `PATCH /soc/incidents/{id}` | Update incident |
| `GET /soc/scans/health` | Scan health metrics |
| `GET /soc/activity` | Activity feed |

### Alerts / Incidents / Activity
- `GET /activity`, `GET /activity/logins`
- `GET /notifications`, `POST /notifications/read-all`, `GET /notifications/unread-count`

---

## Error Format

Errors use conventional HTTP status codes with a JSON body:

```json
{ "detail": "Human-readable explanation." }
```

Notable codes:
- `400` — validation error
- `401` — missing/invalid token
- `403` — insufficient role
- `404` — resource not found
- `429` — rate limited