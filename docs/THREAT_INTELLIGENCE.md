# Threat Intelligence Platform

GuardianX ships a self-hosted Threat Intelligence Platform for analyzing IP
addresses, domains, URLs and SHA256 hashes. It is built around **your own
VirusTotal API key** — GuardianX never provisions or embeds third-party keys.

## Overview

The platform turns a raw IOC into a risk-scored, cached report:

```
IOC input
   └─ IOC type detection (IP / Domain / URL / SHA256)
        └─ VirusTotal provider (API v3)
             └─ 24-hour in-memory cache
                  └─ Risk scoring (0-100) + threat level
                       └─ Frontend dashboard + persistent search history
```

## Architecture

| Layer       | Location                                              | Responsibility                                  |
| ----------- | ----------------------------------------------------- | ----------------------------------------------- |
| API         | `backend/app/intelligence/router.py`                  | HTTP endpoints (lookup, history, status)        |
| Service     | `backend/app/intelligence/service.py`                 | IOC type detection, history persistence         |
| Provider    | `backend/app/intelligence/providers/virustotal.py`    | VirusTotal API v3 translation + risk scoring    |
| Cache       | `backend/app/intelligence/cache.py`                   | TTL cache of translated reports                 |
| Schemas     | `backend/app/intelligence/schemas.py`                 | Pydantic request/response models                |
| History     | `backend/app/models/intelligence_search.py`           | Per-user `intelligence_searches` table          |
| Frontend    | `guardianx-frontend/src/pages/ThreatIntelligence.tsx` | Dashboard (search, report, indicators, history) |

The provider reuses the existing VirusTotal transport layer
(`app/integrations/virustotal/`): connection pooling, retries, timeouts and
token-bucket rate limiting. API keys are read at request time from the
encrypted per-user integration credentials and are never logged or returned to
the client.

## API endpoints

All endpoints require a valid JWT (prefix `/api/v1` by default).

| Method   | Path                       | Description                                             |
| -------- | -------------------------- | ------------------------------------------------------- |
| `POST`   | `/intelligence/lookup`     | Analyze an IOC, body `{ "value": "<ioc>" }`             |
| `GET`    | `/intelligence/history`    | Paginated search history (`ioc_type`, `q`, `page`, `limit`) |
| `DELETE` | `/intelligence/history`    | Clear the caller's search history                       |
| `DELETE` | `/intelligence/history/{id}` | Delete a single history entry                         |
| `GET`    | `/intelligence/status`     | Provider configuration status                           |

### IOC detection

Lookups auto-detect the indicator type in this order:

1. URL (`http`/`https` schemes)
2. SHA256 hash (64 hex characters)
3. IPv4 / IPv6 address
4. Hostname / domain (validated against the scan-target allowlist rules)

Values that match none of these are rejected.

## Risk scoring

Each report is scored 0-100:

| Signal               | Contribution                        |
| -------------------- | ----------------------------------- |
| Malicious vendors    | +18 each, capped at +60             |
| Suspicious vendors   | +8 each, capped at +24              |
| Malicious votes      | +2 each, capped at +12              |
| Negative reputation  | +3 per point, capped at +30         |
| Positive reputation  | reduced by up to -20                |

The threat level is derived from the score: `critical` (>=75), `high` (>=50),
`medium` (>=25), `low` (detected but low score), otherwise `clean`. Reports also
include a best-effort MITRE ATT&CK mapping derived from the top detection
result, plus ASN, geo country and WHOIS metadata when the provider returns it.

## Caching

VirusTotal responses are translated into normalized reports and cached
in-memory for **24 hours** (configurable):

| Variable                          | Default | Description               |
| --------------------------------- | ------- | ------------------------- |
| `INTELLIGENCE_CACHE_TTL_SECONDS`  | `86400` | Report cache lifetime     |
| `INTELLIGENCE_CACHE_MAX_ENTRIES`  | `2048`  | Maximum cached reports    |

Cached responses are flagged `from_cache: true` in the report so the UI can
show that the result was served from cache. The cache is namespaced by IOC type
and normalized value and shared across users (the API key is read per request,
so each user's key is used on the first lookups that miss the cache).

## Search history

Every successful lookup stores a compact summary
(`intelligence_searches`): resource, type, threat level, risk score, reputation,
detection counts, ratio and threat category. History is scoped to the
authenticated user, is paginated, filterable by IOC type, and searchable by
resource value. Users can delete individual entries or clear all history.

## Frontend

The Threat Intelligence dashboard lives at `/intelligence`:

- **Search** — IOC type auto-detection with contextual placeholder
- **Summary** — verdict badge, risk gauge, cached indicator, VT permalink
- **Stat cards** — threat level, reputation, detection ratio, last analysis,
  geo country, ASN, registrar, creation date, community votes, vendor counts
- **Reputation** — verdict distribution, community votes, categories, tags,
  MITRE mapping
- **Timeline** — submission and analysis history
- **Detection table** — per-engine results, searchable and sortable
- **History** — recent lookups with re-search, delete and clear actions

The page is lazy-loaded, uses the shared glassmorphism design system, and
shows skeleton loaders, error and empty states throughout. Pure helpers
(IOC detection, table filtering/sorting) are covered by unit tests.

## Setting up your API key

1. Create a VirusTotal account and generate an API key.
2. In GuardianX, go to **Settings → Integrations → VirusTotal** and store the
   key (encrypted at rest, per-user).
3. Open **Threat Intelligence** and run your first lookup.

If no key is configured, the dashboard shows a setup banner and lookups return
a clear "not configured" error instead of leaking stack traces.
