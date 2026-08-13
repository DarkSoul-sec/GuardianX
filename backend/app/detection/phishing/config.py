"""
Configuration for the phishing detection module.

All detection behavior — keyword lists, trusted domains, blacklist servers,
risky TLDs, scoring weights and risk thresholds — is data-driven and
overridable through the backend ``.env``. Empty environment values fall back
to the enterprise defaults defined here so the module works out of the box
while staying fully configurable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.config import settings
from app.detection.phishing.scoring import RiskThresholds

DEFAULT_SUSPICIOUS_KEYWORDS: tuple[str, ...] = (
    "login",
    "signin",
    "sign-in",
    "verify",
    "verification",
    "account",
    "update",
    "confirm",
    "secure",
    "security",
    "password",
    "credential",
    "authenticate",
    "billing",
    "invoice",
    "payment",
    "wallet",
    "bank",
    "unlock",
    "suspend",
    "unusual",
    "recover",
    "session",
    "2fa",
    "otp",
    "shipping",
    "delivery",
    "tracking",
)

DEFAULT_TRUSTED_DOMAINS: tuple[str, ...] = ()

DEFAULT_BLACKLIST_SERVERS: tuple[str, ...] = (
    "zen.spamhaus.org",
    "dbl.spamhaus.org",
    "b.barracudacentral.org",
    "dnsbl.dronebl.org",
)

DEFAULT_RISKY_TLDS: tuple[str, ...] = (
    "tk",
    "ml",
    "ga",
    "cf",
    "gq",
    "zip",
    "mov",
    "click",
    "top",
    "xyz",
    "info",
    "buzz",
    "work",
    "ltd",
    "support",
    "gdn",
    "loan",
    "rest",
)

DEFAULT_WEIGHTS: dict[str, float] = {
    "url_structure": 15.0,
    "typosquatting": 15.0,
    "whois_age": 15.0,
    "ssl": 10.0,
    "dns": 10.0,
    "virustotal": 20.0,
    "blacklist": 10.0,
    "keywords": 5.0,
}

DEFAULT_THRESHOLDS = RiskThresholds(medium=25, high=50, critical=75)


def _parse_weight_pairs(raw: str) -> dict[str, float]:
    """Parse "check:weight,check:weight" into a weights map."""
    result: dict[str, float] = {}

    for part in raw.split(","):
        key, separator, value = part.partition(":")

        if not separator:
            continue

        try:
            result[key.strip()] = float(value.strip())
        except ValueError:
            continue

    return result


def _parse_thresholds(raw: str, default: RiskThresholds) -> RiskThresholds:
    """Parse "medium,high,critical" into a RiskThresholds."""
    parts = raw.split(",")

    if len(parts) < 3:
        return default

    try:
        values = [int(part.strip()) for part in parts[:3]]
    except ValueError:
        return default

    medium, high, critical = values

    return RiskThresholds(
        medium=max(0, min(100, medium)),
        high=max(0, min(100, high)),
        critical=max(0, min(100, critical)),
    )


@dataclass(frozen=True)
class PhishingConfig:
    """Immutable, environment-driven configuration for all analyzers."""

    weights: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    thresholds: RiskThresholds = DEFAULT_THRESHOLDS
    suspicious_keywords: tuple[str, ...] = DEFAULT_SUSPICIOUS_KEYWORDS
    trusted_domains: tuple[str, ...] = DEFAULT_TRUSTED_DOMAINS
    blacklist_servers: tuple[str, ...] = DEFAULT_BLACKLIST_SERVERS
    risky_tlds: tuple[str, ...] = DEFAULT_RISKY_TLDS
    new_domain_days: int = 90
    suspicious_domain_days: int = 365
    certificate_renew_days: int = 30
    network_timeout_seconds: int = 10
    enable_ai_summary: bool = True

    @classmethod
    def from_settings(cls) -> "PhishingConfig":
        """Build the active configuration from the backend settings."""
        weights = dict(DEFAULT_WEIGHTS)

        if settings.PHISHING_SCORE_WEIGHTS:
            weights.update(_parse_weight_pairs(settings.PHISHING_SCORE_WEIGHTS))

        return cls(
            weights=weights,
            thresholds=_parse_thresholds(
                settings.PHISHING_RISK_THRESHOLDS,
                DEFAULT_THRESHOLDS,
            ),
            suspicious_keywords=tuple(settings.PHISHING_SUSPICIOUS_KEYWORDS)
            or DEFAULT_SUSPICIOUS_KEYWORDS,
            trusted_domains=tuple(settings.PHISHING_TRUSTED_DOMAINS),
            blacklist_servers=tuple(settings.PHISHING_BLACKLIST_SERVERS)
            or DEFAULT_BLACKLIST_SERVERS,
            risky_tlds=tuple(settings.PHISHING_RISKY_TLDS) or DEFAULT_RISKY_TLDS,
            new_domain_days=settings.PHISHING_NEW_DOMAIN_DAYS,
            suspicious_domain_days=settings.PHISHING_SUSPICIOUS_DOMAIN_DAYS,
            certificate_renew_days=settings.PHISHING_CERTIFICATE_RENEW_DAYS,
            network_timeout_seconds=settings.PHISHING_NETWORK_TIMEOUT_SECONDS,
            enable_ai_summary=settings.PHISHING_AI_SUMMARY_ENABLED,
        )
