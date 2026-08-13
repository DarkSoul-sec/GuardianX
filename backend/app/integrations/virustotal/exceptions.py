"""
Domain errors for the VirusTotal integration.

Every error subclasses :class:`app.core.exceptions.ExternalServiceError` so
the shared ``GuardianXError`` handler in ``app.main`` maps them to a stable
HTTP 502 (or 503 for the not-configured case) envelope without any extra
route-level handling.
"""

from __future__ import annotations

from app.core.exceptions import ExternalServiceError


class VirusTotalError(ExternalServiceError):
    """The VirusTotal API could not be reached or returned an error."""

    code = "virustotal_error"
    detail = "The VirusTotal API could not be reached."


class VirusTotalNotConfiguredError(VirusTotalError):
    """No VirusTotal API key is stored for the requesting user."""

    code = "virustotal_not_configured"
    detail = (
        "VirusTotal is not configured. Add your API key in "
        "Settings > Integrations > VirusTotal."
    )


class VirusTotalInvalidKeyError(VirusTotalError):
    """The stored API key was rejected by VirusTotal (401/403)."""

    code = "virustotal_invalid_key"
    detail = "The VirusTotal API key is invalid. Check your credentials."


class VirusTotalRateLimitError(VirusTotalError):
    """VirusTotal is throttling this API key (HTTP 429)."""

    code = "virustotal_rate_limited"
    detail = "VirusTotal rate limit reached. You've exceeded the current quota."


class VirusTotalNotFoundError(VirusTotalError):
    """The VirusTotal API returned 404 for the requested resource."""

    code = "virustotal_not_found"
    detail = "No VirusTotal data found for the requested resource."
