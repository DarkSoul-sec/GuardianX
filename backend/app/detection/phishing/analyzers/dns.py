"""
DNS resolution analyzer.

Uses dnspython to resolve A records, name servers and mail exchangers for the
host. A domain that fails to resolve (NXDOMAIN) or has no addresses is
suspicious; healthy domains resolve normally. IP hosts are not applicable.
"""

from __future__ import annotations

import dns.exception
import dns.resolver

from app.detection.phishing.base import Analyzer, CheckResult, UrlContext, clean_result


class DNSAnalyzer(Analyzer):
    """Score the host based on DNS resolution health."""

    name = "dns"
    title = "DNS Resolution"

    def analyze(self, context: UrlContext) -> list[CheckResult]:
        if context.is_ip_host:
            return [
                clean_result(
                    self.name,
                    self.title,
                    "DNS checks are not applicable to an IP address.",
                    data={"applicable": False},
                )
            ]

        host = context.hostname
        resolver = self._build_resolver()

        try:
            a_records = [record.to_text() for record in resolver.resolve(host, "A")]
        except dns.resolver.NXDOMAIN:
            return [
                CheckResult(
                    check=self.name,
                    title="Domain does not resolve",
                    score=70,
                    reason=f"'{host}' does not resolve (NXDOMAIN).",
                    recommendation="A non-resolving domain is often used by short-lived phishing campaigns.",
                    data={"nxdomain": True, "host": host},
                )
            ]
        except (dns.exception.DNSException, dns.resolver.NoNameservers):
            return [
                CheckResult(
                    check=self.name,
                    title="DNS check unavailable",
                    score=25,
                    reason=f"DNS resolution failed for '{host}'.",
                    recommendation="Re-run the analysis or check DNS manually.",
                    data={"available": False},
                )
            ]

        ns_records = self._resolve_safely(resolver, host, "NS")
        mx_records = self._resolve_safely(resolver, host, "MX")

        data = {
            "available": True,
            "host": host,
            "a_records": a_records,
            "ns_records": ns_records,
            "mx_records": mx_records,
        }

        if not a_records:
            return [
                CheckResult(
                    check=self.name,
                    title="No address records",
                    score=45,
                    reason=f"'{host}' has no A records, so it cannot be reached normally.",
                    recommendation="A host with no DNS records is a strong indicator of abuse.",
                    data=data,
                )
            ]

        return [
            clean_result(
                self.name,
                self.title,
                f"'{host}' resolves to {len(a_records)} address(es).",
                data=data,
            )
        ]

    def _build_resolver(self) -> dns.resolver.Resolver:
        resolver = dns.resolver.Resolver()
        resolver.timeout = self.config.network_timeout_seconds
        resolver.lifetime = self.config.network_timeout_seconds
        return resolver

    def _resolve_safely(
        self,
        resolver: dns.resolver.Resolver,
        host: str,
        record_type: str,
    ) -> list[str]:
        try:
            return [record.to_text() for record in resolver.resolve(host, record_type)]
        except (dns.exception.DNSException, dns.resolver.NoNameservers):
            return []
