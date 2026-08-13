"""
URL structure analyzer.

Flags structural phishing indicators that are visible from the URL alone:
embedded credentials, IP-literal hosts, unusual ports, excessive subdomains,
internationalized domain names, risky TLDs, overly long URLs and heavy URL
encoding.
"""

from __future__ import annotations

from app.detection.phishing.base import Analyzer, CheckResult, UrlContext, clean_result


class URLStructureAnalyzer(Analyzer):
    """Inspect the raw URL for structural phishing signals."""

    name = "url_structure"
    title = "URL Structure"

    def analyze(self, context: UrlContext) -> list[CheckResult]:
        results: list[CheckResult] = []

        if context.has_userinfo:
            results.append(
                CheckResult(
                    check=self.name,
                    title="Embedded credentials",
                    score=85,
                    reason="The URL embeds a username or password before the host using '@'.",
                    recommendation="Do not visit the URL; embedded credentials are a strong phishing indicator.",
                    data={"has_userinfo": True},
                )
            )

        if context.is_ip_host:
            results.append(
                CheckResult(
                    check=self.name,
                    title="IP-literal host",
                    score=70,
                    reason="The URL host is a raw IP address instead of a domain name.",
                    recommendation="Legitimate services rarely use bare IPs; verify the destination.",
                    data={"host": context.hostname},
                )
            )

        if context.port and context.port not in (80, 443):
            results.append(
                CheckResult(
                    check=self.name,
                    title="Unusual port",
                    score=45,
                    reason=f"The URL uses non-standard port {context.port}.",
                    recommendation="Confirm the service legitimately uses this port before connecting.",
                    data={"port": context.port},
                )
            )

        if len(context.subdomain_labels) >= 3:
            results.append(
                CheckResult(
                    check=self.name,
                    title="Excessive subdomains",
                    score=55,
                    reason=f"The host '{context.hostname}' contains {len(context.subdomain_labels)} subdomain label(s).",
                    recommendation="Deep subdomain chains are commonly used to disguise phishing domains.",
                    data={"subdomains": list(context.subdomain_labels)},
                )
            )

        if context.is_idn:
            results.append(
                CheckResult(
                    check=self.name,
                    title="Internationalized domain",
                    score=60,
                    reason="The host contains non-ASCII characters (IDN), which enables homograph spoofing.",
                    recommendation="Carefully confirm the punycode form of the domain before trusting it.",
                    data={"host": context.hostname},
                )
            )

        if not context.is_ip_host and context.labels:
            tld = context.labels[-1]

            if tld in self.config.risky_tlds:
                results.append(
                    CheckResult(
                        check=self.name,
                        title="Risky top-level domain",
                        score=55,
                        reason=f"The domain uses TLD '.{tld}', which is frequently abused in phishing.",
                        recommendation="Treat '.{tld}' domains with extra scrutiny.".format(tld=tld),
                        data={"tld": tld},
                    )
                )

        if len(context.raw_url) > 100:
            results.append(
                CheckResult(
                    check=self.name,
                    title="Overly long URL",
                    score=30,
                    reason="The URL is over 100 characters long; phishing URLs are often padded.",
                    recommendation="Review the full URL, especially the query string.",
                    data={"length": len(context.raw_url)},
                )
            )

        if context.path.count("%") >= 3:
            results.append(
                CheckResult(
                    check=self.name,
                    title="Heavy URL encoding",
                    score=25,
                    reason="The URL path contains many percent-encoded characters.",
                    recommendation="Decode the URL to inspect the actual destination.",
                    data={"encoded_chars": context.path.count("%")},
                )
            )

        if not results:
            results.append(
                clean_result(
                    self.name,
                    self.title,
                    "The URL structure looks normal.",
                    data={"scheme": context.scheme, "host": context.hostname},
                )
            )

        return results
