"""
VirusTotal Intelligence integration.

Implements a Bring Your Own API Key (BYOAPI) workflow: each user stores their
own VirusTotal API key (encrypted at rest, decrypted only in memory) and can
run URL, domain, IP and SHA256 file-hash reputation lookups against the
VirusTotal v3 API with automatic retries, per-key client-side rate limiting
and an in-process response cache.

Layout:

- ``client.py``    - HTTP transport (retries, throttling, auth, parsing)
- ``cache.py``     - thread-safe TTL cache
- ``rate_limit.py``- per-key token-bucket limiter
- ``models.py``    - raw VirusTotal v3 response models
- ``schemas.py``   - normalized lookup + connection schemas
- ``service.py``   - credentials, validation, mapping and orchestration
- ``router.py``    - REST endpoints for connection management
"""

from __future__ import annotations

from app.integrations.virustotal.schemas import (
    VendorDetection,
    VirusTotalLookupResponse,
)
from app.integrations.virustotal.service import (
    connect_api_key,
    disconnect_api_key,
    get_configured_api_key,
    get_optional_api_key,
    get_status,
    lookup_domain,
    lookup_file_hash,
    lookup_ip,
    lookup_url,
    test_connection,
    test_stored_connection,
)

__all__ = [
    "VendorDetection",
    "VirusTotalLookupResponse",
    "connect_api_key",
    "disconnect_api_key",
    "get_configured_api_key",
    "get_optional_api_key",
    "get_status",
    "lookup_domain",
    "lookup_file_hash",
    "lookup_ip",
    "lookup_url",
    "test_connection",
    "test_stored_connection",
]
