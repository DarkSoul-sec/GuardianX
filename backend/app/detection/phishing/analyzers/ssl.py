"""
SSL certificate analyzer.

Connects to the host on port 443, retrieves the TLS certificate without
verification (so expired and mismatched certificates can still be inspected),
and scores it based on expiry and hostname coverage. Connection failures are
reported as a neutral "unable to verify" signal rather than a hard error.
"""

from __future__ import annotations

import socket
import ssl
from datetime import UTC, datetime

from app.core.exceptions import ValidationError
from app.core.network import resolve_ssl_connection_target
from app.detection.phishing.base import Analyzer, CheckResult, UrlContext

_DEFAULT_PORT = 443


def _parse_not_after(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y%m%d%H%M%SZ").replace(tzinfo=UTC)
    except ValueError:
        return None


def _wildcard_matches(pattern: str, hostname: str) -> bool:
    if not pattern.startswith("*."):
        return False

    suffix = pattern[2:].lower()
    labels = hostname.lower().split(".")

    return len(labels) >= 2 and hostname.lower().endswith(suffix)


def _cert_covers_host(cert: dict, hostname: str) -> bool:
    names: list[str] = []

    for entry in cert.get("subjectAltName", ()):
        if isinstance(entry, (tuple, list)) and len(entry) == 2:
            kind, value = entry

            if kind == "DNS":
                names.append(str(value).lower())

    if names:
        hostname = hostname.lower()
        return hostname in names or any(_wildcard_matches(name, hostname) for name in names)

    for rdn in cert.get("subject", ()):
        for key, value in rdn:
            if key == "commonName":
                return str(value).lower() == hostname.lower()

    return False


class SSLCertificateAnalyzer(Analyzer):
    """Score the target's TLS certificate for expiry and coverage."""

    name = "ssl"
    title = "SSL Certificate"

    def analyze(self, context: UrlContext) -> list[CheckResult]:
        host = context.hostname
        cert = self._fetch_certificate(host)

        if cert is None:
            return [
                CheckResult(
                    check=self.name,
                    title="TLS connection failed",
                    score=35,
                    reason=f"Could not establish a TLS connection to '{host}:{_DEFAULT_PORT}'.",
                    recommendation="Verify the site actually serves HTTPS before trusting it.",
                    data={"available": False},
                )
            ]

        data = {
            "available": True,
            "not_after": cert.get("notAfter"),
            "issuer": cert.get("issuer"),
            "covers_host": _cert_covers_host(cert, host),
        }

        expiry = _parse_not_after(cert.get("notAfter"))

        if expiry is None:
            return [
                CheckResult(
                    check=self.name,
                    title="Certificate unverifiable",
                    score=45,
                    reason=f"The TLS certificate for '{host}' could not be inspected.",
                    recommendation="Manually inspect the certificate before sharing data.",
                    data=data,
                )
            ]

        days_left = (expiry - datetime.now(UTC)).days

        if days_left < 0:
            score = 90
            reason = f"The TLS certificate for '{host}' expired {abs(days_left)} day(s) ago."
            recommendation = "An expired certificate is a strong indicator of an unmaintained or malicious site."
        elif days_left < self.config.certificate_renew_days:
            score = 50
            reason = f"The TLS certificate for '{host}' expires in {days_left} day(s)."
            recommendation = "Recent/impending expiry is common on short-lived phishing infrastructure."
        elif not data["covers_host"]:
            score = 60
            reason = f"The TLS certificate for '{host}' does not cover the requested hostname."
            recommendation = "A certificate mismatch suggests a certificate from another domain is being used."
        else:
            score = 0
            reason = f"'{host}' presents a valid TLS certificate expiring in {days_left} day(s)."
            recommendation = "No action needed based on the certificate."

        data["expires_in_days"] = days_left

        return [
            CheckResult(
                check=self.name,
                title="Certificate expiry and coverage",
                score=score,
                reason=reason,
                recommendation=recommendation,
                data=data,
            )
        ]

    def _fetch_certificate(self, host: str) -> dict | None:
        # SSRF guard: resolve the target once and refuse loopback, private,
        # link-local (incl. cloud metadata) and reserved destinations, and
        # hostnames that resolve only to them. The validated IP is what we
        # connect to (with the hostname used only for SNI), so a DNS rebind
        # between validation and connection cannot redirect us internally.
        try:
            dest, server_hostname = resolve_ssl_connection_target(host)
        except ValidationError:
            return None

        context = ssl._create_unverified_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        try:
            with socket.create_connection(
                (dest, _DEFAULT_PORT),
                timeout=self.config.network_timeout_seconds,
            ) as sock:
                with context.wrap_socket(sock, server_hostname=server_hostname) as tls:
                    return tls.getpeercert()
        except (ssl.SSLError, OSError, ValueError):
            return None
