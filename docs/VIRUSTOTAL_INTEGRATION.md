# VirusTotal Integration (Bring Your Own API Key)

GuardianX integrates with VirusTotal using a **Bring Your Own API Key (BYOAPI)**
model. Each user supplies their own VirusTotal API key; GuardianX never stores
or uses a shared platform key. Keys are encrypted at rest and are never
returned by any API response.

## Getting a free VirusTotal API key

1. Create a free account at [VirusTotal](https://www.virustotal.com/).
2. Open your API key page: <https://www.virustotal.com/gui/my-apikey>.
3. Copy the key. It starts with `vt` and is 32–200 characters long.

## Configuration (in-app)

1. Open **Settings → Integrations → VirusTotal**.
2. Paste your API key into the **API Key** field.
3. Click **Test Connection** to validate the key without saving it:
   - 🟢 **Connected** — the key is valid.
   - 🔴 **Invalid Key** — the key was rejected (401/403).
   - 🟡 **Rate Limited** — the key's quota is currently exhausted.
   - ⚪ **Not Configured** — no key is stored yet.
4. Click **Save Key**. The key is validated again, encrypted with the
   application secret, and stored per user.
5. Use **Remove Key** to permanently delete your stored key.

The connection status is also shown on the same page with the last test time.

## Security

- Keys are encrypted with Fernet using a key derived from `SECRET_KEY`
  (`app/core/encryption.py`) and stored in the `integration_credentials`
  table. The plaintext key never touches the database.
- The API never returns a stored key. Only status and timestamps are exposed.
- Per-key rate limiting (128 cached keys) keeps requests inside VirusTotal
  quotas; 429 responses are retried with `Retry-After` awareness.

## Where VirusTotal intelligence surfaces in the UI

- **VirusTotal Intelligence** page (`/virustotal`): URL, domain, IP and SHA256
  reputation lookups.
- **Findings drawer**: findings containing URLs, domains, IP addresses or
  SHA256 hashes get an **Analyze with VirusTotal** section.
- **Asset details**: assets with an IP address or domain show a
  **Threat Intelligence** panel with reputation, community score, detection
  ratio and vendor detections.

## API endpoints

All endpoints require a JWT (`Authorization: Bearer <token>`).

### Integration management

| Method | Path                              | Description                              |
| ------ | --------------------------------- | ---------------------------------------- |
| GET    | `/api/v1/integrations/virustotal/status` | Current connection status.         |
| POST   | `/api/v1/integrations/virustotal/connect` | Validate, encrypt and store a key (`{"api_key": "..."}`). |
| POST   | `/api/v1/integrations/virustotal/test` | Test a candidate key (`{"api_key": "..."}`) or the stored key (empty body). |
| DELETE | `/api/v1/integrations/virustotal/disconnect` | Remove the stored key. |

### Intelligence lookups

| Method | Path                      | Body                 | Lookup                |
| ------ | ------------------------- | -------------------- | --------------------- |
| POST   | `/api/v1/intelligence/url`     | `{"value": "https://…"}` | URL reputation   |
| POST   | `/api/v1/intelligence/domain`  | `{"value": "example.com"}` | Domain reputation |
| POST   | `/api/v1/intelligence/ip`      | `{"value": "8.8.8.8"}` | IP reputation    |
| POST   | `/api/v1/intelligence/hash`    | `{"value": "<sha256>"}` | File hash reputation |

Lookups return a normalized `VirusTotalLookupResponse` (detection ratio,
malicious/suspicious/undetected/harmless counts, reputation, community score,
threat category, last analysis date, vendor detections). Raw VirusTotal
payloads never cross the API boundary.

> Legacy GET endpoints under `/api/v1/virustotal/*` remain available and use
> the authenticated user's stored key.

## Configuration variables

`VIRUSTOTAL_API_KEY` is intentionally **not** a setting. The following
tunables remain in `app/core/config.py`:

| Variable                            | Default | Purpose                        |
| ----------------------------------- | ------- | ------------------------------ |
| `VIRUSTOTAL_API_URL`                | `https://www.virustotal.com/api/v3` | Base URL. |
| `VIRUSTOTAL_TIMEOUT_SECONDS`        | `15`    | Per-request timeout.           |
| `VIRUSTOTAL_MAX_RETRIES`            | `3`     | Retries on 429/5xx.            |
| `VIRUSTOTAL_RATE_LIMIT_PER_MINUTE`  | `60`    | Per-key request budget.        |
| `VIRUSTOTAL_CACHE_TTL_SECONDS`      | `900`   | Lookup cache TTL.              |
| `VIRUSTOTAL_CACHE_MAX_ENTRIES`      | `512`   | Lookup cache size.             |
