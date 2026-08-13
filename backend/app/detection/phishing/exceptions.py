"""
Domain errors for the phishing detection module.
"""

from __future__ import annotations

from app.core.exceptions import GuardianXError


class PhishingDetectionError(GuardianXError):
    """A phishing analysis could not be produced."""

    status_code = 502
    code = "phishing_detection_error"
    detail = "The phishing analysis could not be completed."
