"""
Core building blocks for the phishing detection module.

Defines the immutable :class:`UrlContext` shared by every analyzer, the
normalized :class:`CheckResult` contract each analyzer returns, and the
:class:`Analyzer` abstraction that makes analyzers pluggable and testable.
"""

from __future__ import annotations

import ipaddress
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping
from urllib.parse import urlparse

from app.core.exceptions import ValidationError


@dataclass(frozen=True)
class CheckResult:
    """Normalized output of a single security check."""

    check: str
    title: str
    score: int
    reason: str
    recommendation: str = ""
    data: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "score", max(0, min(100, self.score)))


@dataclass(frozen=True)
class UrlContext:
    """Parsed, validated URL shared by all phishing analyzers."""

    raw_url: str
    scheme: str
    hostname: str
    port: int | None
    path: str
    query: str
    fragment: str
    is_ip_host: bool
    has_userinfo: bool
    is_idn: bool
    labels: tuple[str, ...]
    approximate_domain: str
    subdomain_labels: tuple[str, ...]


def _is_ip_literal(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def build_url_context(url: str) -> UrlContext:
    """
    Parse and validate a URL for phishing analysis.

    Raises ``ValidationError`` (HTTP 400) when the value is not a valid
    http(s) URL with a resolvable host.
    """
    value = url.strip()

    try:
        parsed = urlparse(value)
    except ValueError:
        raise ValidationError("Provide a valid http(s) URL to analyze.")

    if parsed.scheme.lower() not in ("http", "https"):
        raise ValidationError("Provide a valid http(s) URL to analyze.")

    if not parsed.hostname:
        raise ValidationError("Provide a valid http(s) URL to analyze.")

    try:
        port = parsed.port
    except ValueError:
        raise ValidationError("The URL contains an invalid port.")

    hostname = parsed.hostname.lower()
    is_ip_host = _is_ip_literal(hostname)

    labels: tuple[str, ...] = ()
    subdomain_labels: tuple[str, ...] = ()
    approximate_domain = hostname

    if not is_ip_host:
        labels = tuple(hostname.split("."))

        if len(labels) >= 2:
            approximate_domain = ".".join(labels[-2:])
            subdomain_labels = labels[:-2]

    is_idn = any(ord(char) > 127 for char in hostname) or "xn--" in hostname

    return UrlContext(
        raw_url=value,
        scheme=parsed.scheme.lower(),
        hostname=hostname,
        port=port,
        path=parsed.path,
        query=parsed.query,
        fragment=parsed.fragment,
        is_ip_host=is_ip_host,
        has_userinfo=bool(parsed.username or parsed.password),
        is_idn=is_idn,
        labels=labels,
        approximate_domain=approximate_domain,
        subdomain_labels=subdomain_labels,
    )


def clean_result(check: str, title: str, reason: str, data: Mapping[str, Any] | None = None) -> CheckResult:
    """Build a zero-risk result for analyzers that found nothing suspicious."""
    return CheckResult(
        check=check,
        title=title,
        score=0,
        reason=reason,
        recommendation="",
        data=data or {},
    )


class Analyzer(ABC):
    """Base interface for every phishing analyzer.

    Analyzers are interchangeable: the registry in
    :mod:`app.detection.phishing.analyzers` builds the active set and each
    analyzer receives the shared configuration. ``analyze`` must never raise;
    failures are reported as low-confidence results so a single unavailable
    data source cannot break the whole analysis.
    """

    name: str = "base"
    title: str = "Base analyzer"

    def __init__(self, config: Any) -> None:
        self.config = config

    @abstractmethod
    def analyze(self, context: UrlContext) -> list[CheckResult]:
        """Run the analyzer's checks and return normalized results."""
