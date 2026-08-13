# Development Mode: Private Network Scanning

GuardianX blocks scanning of private, loopback and reserved IPv4/IPv6 ranges
(and CGNAT, benchmarking, multicast, cloud-metadata and documentation ranges)
by default. This is an SSRF / internal-scan protection that **must stay
enabled in any public deployment**.

For **local development only**, GuardianX can lift this restriction with a
single environment variable. No security validation is ever removed — it is
only bypassed when the flag is explicitly turned on.

## Opting in (local development only)

```bash
ALLOW_PRIVATE_NETWORK_SCANS=true
```

Set this in `backend/.env` (see `backend/.env.example`). The default is
`false`.

When enabled, the following become valid scan targets (they are rejected when
the flag is off):

| Category        | Examples                     |
| --------------- | ---------------------------- |
| Loopback        | `127.0.0.1`, `::1`           |
| Private (RFC1918) | `10.x.x.x`, `172.16.x.x`, `192.168.x.x`, `fc00::/7` |
| Link-local      | `169.254.x.x`, `fe80::/10`  |
| Cloud metadata  | `169.254.169.254`           |
| Reserved / CGNAT / benchmarking / multicast | `240.0.0.0/4`, `100.64.0.0/10`, `198.18.0.0/15`, `224.0.0.0/4` |
| Hostname        | `localhost` (always a valid hostname) |

## Clear logging

Each permitted target is logged at **WARNING** level so accidental enabling
is noticed:

```
[DEV MODE] Private network scan permitted (ALLOW_PRIVATE_NETWORK_SCANS=true): 127.0.0.1
```

On startup, if the flag is enabled, the backend logs an explicit warning:

```
[DEV MODE] ALLOW_PRIVATE_NETWORK_SCANS=true — private, loopback and reserved address scan validation is bypassed. Never enable this in a public deployment.
```

## Frontend warning banner

When the backend reports the flag is enabled, the dashboard shows a persistent
amber banner:

> ⚠ Development Mode · Private Network Scanning Enabled

The banner is driven by the public endpoint `GET /api/security/config`, which
returns:

```json
{ "private_network_scanning_enabled": false }
```

The frontend polls this endpoint (`src/hooks/useSecurity.ts`) and renders
`<DevModeBanner />` in the layout only when it is `true`. In production the
flag defaults to `false`, so no banner is shown and all blocking validation
applies unchanged.

## Production safety

```text
• Existing security validation is NOT removed.
• Validation is bypassed ONLY when ALLOW_PRIVATE_NETWORK_SCANS=true.
• The flag defaults to false; nothing changes unless explicitly enabled.
• Public deployments should never set the flag.
• A warning banner is displayed to make relaxed policies obvious.
• Only the private/loopback/reserved IP block is relaxed — malformed
  targets, invalid IPs and bad hostnames are still rejected.
```

## Where the change lives

| Area                | File                                     |
| ------------------- | ---------------------------------------- |
| Setting             | `backend/app/core/config.py` — `ALLOW_PRIVATE_NETWORK_SCANS` |
| Validation bypass   | `backend/app/core/network.py` — `validate_ip_target`   |
| Startup warning     | `backend/app/main.py`                    |
| Config endpoint     | `backend/app/api/v1/security.py` — `GET /api/v1/security/config` |
| Frontend service    | `guardianx-frontend/src/services/security.ts` |
| Frontend hook       | `guardianx-frontend/src/hooks/useSecurity.ts` |
| Frontend banner     | `guardianx-frontend/src/components/DevModeBanner.tsx` |

> Note: this document doubles as the feature record. See also
> `docs/VIRUSTOTAL_INTEGRATION.md` for other integration docs.