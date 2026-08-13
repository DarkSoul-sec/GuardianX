"""
Public blacklist (DNSBL) analyzer.

Queries configured public DNS-based blacklists using dnspython. IP hosts are
checked with reversed-octet queries; domains are checked with domain-style
queries and, when resolvable, their A records are checked against every
server too.
"""

from __future__ import annotations

import ipaddress

import dns.exception
import dns.resolver

from app.detection.phishing.base import Analyzer, CheckResult, UrlContext, clean_result


class BlacklistAnalyzer(Analyzer):
    """Report whether the target is listed on public blacklists."""

    name = "blacklist"
    title = "Public Blacklist Status"

    def analyze(self, context: UrlContext) -> list[CheckResult]:
        servers = self.config.blacklist_servers

        if not servers:
            return [
                clean_result(
                    self.name,
                    self.title,
                    "No blacklist servers are configured.",
                    data={"configured": False},
                )
            ]

        resolver = self._build_resolver()
        targets = self._query_targets(context, resolver)
        listed: list[dict] = []
        failures = 0

        for server in servers:
            for target in targets:
                query_name = self._query_name(target, server)

                if not query_name:
                    continue

                try:
                    answers = resolver.resolve(query_name, "A")
                except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                    continue
                except (dns.exception.DNSException, dns.resolver.NoNameservers):
                    failures += 1
                    continue

                if answers:
                    listed.append(
                        {
                            "server": server,
                            "target": target,
                            "record": answers[0].to_text(),
                        }
                    )

        data = {
            "listed": listed,
            "servers_checked": list(servers),
            "failures": failures,
        }

        if listed:
            names = ", ".join(sorted({item["server"] for item in listed}))
            return [
                CheckResult(
                    check=self.name,
                    title="Listed on public blacklists",
                    score=90,
                    reason=f"The resource is listed on public blacklist(s): {names}.",
                    recommendation="Block the resource immediately and investigate any related activity.",
                    data=data,
                )
            ]

        if failures == len(servers) and listed == []:
            return [
                CheckResult(
                    check=self.name,
                    title="Blacklist check unavailable",
                    score=25,
                    reason="Blacklist lookups could not be completed.",
                    recommendation="Retry the analysis later or check DNS manually.",
                    data=data,
                )
            ]

        return [
            clean_result(
                self.name,
                self.title,
                f"Not listed on the {len(servers)} checked public blacklist(s).",
                data=data,
            )
        ]

    def _build_resolver(self) -> dns.resolver.Resolver:
        resolver = dns.resolver.Resolver()
        resolver.timeout = self.config.network_timeout_seconds
        resolver.lifetime = self.config.network_timeout_seconds
        return resolver

    def _query_targets(self, context: UrlContext, resolver: dns.resolver.Resolver) -> list[str]:
        if context.is_ip_host:
            return [context.hostname]

        targets = [context.approximate_domain]

        try:
            targets.extend(
                record.to_text() for record in resolver.resolve(context.hostname, "A")
            )
        except (dns.exception.DNSException, dns.resolver.NoNameservers):
            pass

        return targets

    def _query_name(self, target: str, server: str) -> str | None:
        try:
            address = ipaddress.ip_address(target)
        except ValueError:
            return f"{target}.{server}"

        if address.version != 4:
            return None

        return ".".join(reversed(str(address).split("."))) + f".{server}"
