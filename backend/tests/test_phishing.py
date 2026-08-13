"""Tests for the phishing detection module."""

import socket
import unittest
from unittest import mock

from app.core.exceptions import ValidationError
from app.detection.phishing import analyze_url
from app.detection.phishing.analyzers.keywords import SuspiciousKeywordsAnalyzer
from app.detection.phishing.analyzers.ssl import SSLCertificateAnalyzer
from app.detection.phishing.analyzers.typosquatting import TyposquattingAnalyzer
from app.detection.phishing.analyzers.url_structure import URLStructureAnalyzer
from app.detection.phishing.analyzers.virustotal import VirusTotalAnalyzer
from app.detection.phishing.base import (
    Analyzer,
    CheckResult,
    build_url_context,
    clean_result,
)
from app.detection.phishing.config import PhishingConfig
from app.detection.phishing.scoring import RiskThresholds, ScoreEngine
from app.integrations.virustotal.exceptions import VirusTotalError
from app.integrations.virustotal.schemas import VirusTotalLookupResponse


def _config(**kwargs) -> PhishingConfig:
    return PhishingConfig(**kwargs)


def _public_cert() -> dict:
    return {
        "subject": ((("commonName", "example.com"),),),
        "issuer": ((("commonName", "R3"),),),
        "notAfter": "20361201120000Z",
        "subjectAltName": (("DNS", "example.com"),),
    }


class _FakeTLS:
    def __init__(self, cert: dict) -> None:
        self._cert = cert

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> bool:
        return False

    def getpeercert(self) -> dict:
        return self._cert


class _FakeSSLContext:
    def __init__(self, cert: dict) -> None:
        self._cert = cert
        self.check_hostname = True
        self.verify_mode = None

    def wrap_socket(self, sock, server_hostname=None) -> _FakeTLS:
        return _FakeTLS(self._cert)


class _FakeConnection:
    def __enter__(self):
        return self

    def __exit__(self, *exc) -> bool:
        return False


class FakeAnalyzer(Analyzer):
    """Deterministic analyzer returning a fixed score."""

    name = "virustotal"
    title = "Fake"

    def __init__(self, config, score: int, reason: str = "", recommendation: str = "") -> None:
        super().__init__(config)
        self.score = score
        self.reason = reason or f"Reason for {self.name}"
        self.recommendation = recommendation

    def analyze(self, context):
        return [
            CheckResult(
                check=self.name,
                title=self.title,
                score=self.score,
                reason=self.reason,
                recommendation=self.recommendation,
            )
        ]


class FakeCleanAnalyzer(Analyzer):
    name = "keywords"
    title = "Clean"

    def analyze(self, context):
        return [clean_result(self.name, self.title, "Nothing suspicious.")]


class UrlContextTests(unittest.TestCase):

    def test_rejects_non_http_scheme(self) -> None:
        with self.assertRaises(ValidationError):
            build_url_context("ftp://example.com/file")

    def test_rejects_missing_host(self) -> None:
        with self.assertRaises(ValidationError):
            build_url_context("http://")

    def test_parses_ip_host(self) -> None:
        context = build_url_context("http://192.168.1.1/login")
        self.assertTrue(context.is_ip_host)
        self.assertEqual(context.hostname, "192.168.1.1")

    def test_parses_userinfo(self) -> None:
        context = build_url_context("http://user:pass@example.com/path")
        self.assertTrue(context.has_userinfo)
        self.assertEqual(context.hostname, "example.com")

    def test_parses_subdomains_and_domain(self) -> None:
        context = build_url_context("https://a.b.c.example.co.uk/login")
        self.assertEqual(context.hostname, "a.b.c.example.co.uk")
        self.assertEqual(context.approximate_domain, "co.uk")
        self.assertEqual(context.subdomain_labels, ("a", "b", "c", "example"))

    def test_detects_idn(self) -> None:
        context = build_url_context("http://bücher.example.com/")
        self.assertTrue(context.is_idn)


class URLStructureAnalyzerTests(unittest.TestCase):

    def setUp(self) -> None:
        self.analyzer = URLStructureAnalyzer(_config())

    def test_flags_embedded_credentials(self) -> None:
        results = self.analyzer.analyze(build_url_context("http://admin:pw@example.com/"))
        scores = {result.title: result.score for result in results}
        self.assertGreaterEqual(scores.get("Embedded credentials", 0), 80)

    def test_flags_ip_literal_host(self) -> None:
        results = self.analyzer.analyze(build_url_context("http://10.0.0.1/login"))
        scores = {result.title: result.score for result in results}
        self.assertGreaterEqual(scores.get("IP-literal host", 0), 60)

    def test_flags_excessive_subdomains(self) -> None:
        results = self.analyzer.analyze(
            build_url_context("http://a.b.c.example.com/login")
        )
        scores = {result.title: result.score for result in results}
        self.assertGreaterEqual(scores.get("Excessive subdomains", 0), 50)

    def test_clean_url_scores_zero(self) -> None:
        results = self.analyzer.analyze(build_url_context("https://example.com/home"))
        self.assertEqual([result.score for result in results], [0])


class TyposquattingAnalyzerTests(unittest.TestCase):

    def test_near_identical_domain_is_flagged(self) -> None:
        analyzer = TyposquattingAnalyzer(_config(trusted_domains=("paypal.com",)))
        results = analyzer.analyze(build_url_context("https://paypa1.com/login"))
        self.assertTrue(any(result.score >= 85 for result in results))

    def test_exact_trusted_domain_is_clean(self) -> None:
        analyzer = TyposquattingAnalyzer(_config(trusted_domains=("paypal.com",)))
        results = analyzer.analyze(build_url_context("https://paypal.com/home"))
        self.assertEqual([result.score for result in results], [0])

    def test_trusted_domain_embedded_in_host(self) -> None:
        analyzer = TyposquattingAnalyzer(_config(trusted_domains=("paypal.com",)))
        results = analyzer.analyze(build_url_context("https://paypal.com.login.evil.net/"))
        self.assertTrue(any(result.score >= 65 for result in results))


class KeywordsAnalyzerTests(unittest.TestCase):

    def test_no_keywords_is_clean(self) -> None:
        analyzer = SuspiciousKeywordsAnalyzer(_config())
        results = analyzer.analyze(build_url_context("https://example.com/home"))
        self.assertEqual([result.score for result in results], [0])

    def test_keywords_raise_score(self) -> None:
        analyzer = SuspiciousKeywordsAnalyzer(_config())
        results = analyzer.analyze(
            build_url_context("https://example.com/secure/account/verify/password")
        )
        self.assertGreaterEqual(results[0].score, 50)
        self.assertIn("password", str(results[0].data.get("keywords")))


class VirusTotalAnalyzerTests(unittest.TestCase):

    def setUp(self) -> None:
        self.analyzer = VirusTotalAnalyzer(
            _config(),
            api_key="test-virustotal-api-key",
        )

    def test_malicious_verdict_scores_high(self) -> None:
        report = VirusTotalLookupResponse(
            resource_type="url",
            resource="https://example.com",
            permalink="https://www.virustotal.com/gui/url/x",
            found=True,
            detected=True,
            malicious=5,
            total=60,
            detection_ratio="5/60",
            reputation=-10,
        )
        with mock.patch(
            "app.detection.phishing.analyzers.virustotal.lookup_url",
            return_value=report,
        ):
            results = self.analyzer.analyze(
                build_url_context("https://example.com/")
            )

        self.assertEqual(results[0].score, 90)
        self.assertEqual(results[0].check, "virustotal")

    def test_clean_verdict_scores_zero(self) -> None:
        report = VirusTotalLookupResponse(
            resource_type="url",
            resource="https://example.com",
            permalink="https://www.virustotal.com/gui/url/x",
            found=True,
            detected=False,
            malicious=0,
            total=60,
            detection_ratio="0/60",
            reputation=10,
        )
        with mock.patch(
            "app.detection.phishing.analyzers.virustotal.lookup_url",
            return_value=report,
        ):
            results = self.analyzer.analyze(
                build_url_context("https://example.com/")
            )

        self.assertEqual(results[0].score, 0)

    def test_unavailable_verdict_is_neutral(self) -> None:
        with mock.patch(
            "app.detection.phishing.analyzers.virustotal.lookup_url",
            side_effect=VirusTotalError("down"),
        ):
            results = self.analyzer.analyze(
                build_url_context("https://example.com/")
            )

        self.assertEqual(results[0].score, 25)
        self.assertFalse(results[0].data.get("available"))


class SSLCertificateAnalyzerSsrFBlockingTests(unittest.TestCase):
    """
    The SSL analyzer must never open a connection to a protected target.

    Any loopback / private / link-local (incl. cloud metadata) destination,
    and any hostname that resolves only to them, must be refused before
    ``socket.create_connection`` is ever reached. Legitimate public HTTPS
    hosts must still be analyzed.
    """

    def setUp(self) -> None:
        self.analyzer = SSLCertificateAnalyzer(_config())

    def _assert_connection_blocked(self, url: str) -> None:
        with mock.patch(
            "app.detection.phishing.analyzers.ssl.socket.create_connection",
            side_effect=AssertionError("create_connection must not be reached"),
        ) as create_connection:
            results = self.analyzer.analyze(build_url_context(url))

        create_connection.assert_not_called()
        self.assertEqual(results[0].check, "ssl")
        self.assertFalse(results[0].data.get("available"))
        self.assertEqual(results[0].score, 35)

    def test_public_ipv4_target_is_analyzed(self) -> None:
        with mock.patch(
            "app.detection.phishing.analyzers.ssl.socket.create_connection",
            return_value=_FakeConnection(),
        ), mock.patch(
            "app.detection.phishing.analyzers.ssl.ssl._create_unverified_context",
            return_value=_FakeSSLContext(_public_cert()),
        ):
            results = self.analyzer.analyze(build_url_context("https://8.8.8.8/"))

        self.assertEqual(results[0].check, "ssl")
        self.assertTrue(results[0].data.get("available"))

    def test_public_hostname_is_still_analyzed(self) -> None:
        with mock.patch(
            "app.detection.phishing.analyzers.ssl.socket.create_connection",
            return_value=_FakeConnection(),
        ), mock.patch(
            "app.detection.phishing.analyzers.ssl.ssl._create_unverified_context",
            return_value=_FakeSSLContext(_public_cert()),
        ):
            results = self.analyzer.analyze(build_url_context("https://example.com/"))

        self.assertEqual(results[0].check, "ssl")
        self.assertTrue(results[0].data.get("available"))
        self.assertTrue(results[0].data["covers_host"])
        self.assertEqual(results[0].score, 0)

    def test_loopback_ipv4_is_blocked(self) -> None:
        self._assert_connection_blocked("https://127.0.0.1/")

    def test_localhost_hostname_is_blocked(self) -> None:
        addrinfo = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443)),
            (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("::1", 443, 0, 0)),
        ]
        with mock.patch(
            "app.core.network.socket.getaddrinfo",
            return_value=addrinfo,
        ):
            self._assert_connection_blocked("https://localhost/")

    def test_rfc1918_address_is_blocked(self) -> None:
        self._assert_connection_blocked("https://192.168.1.10/")

    def test_link_local_address_is_blocked(self) -> None:
        self._assert_connection_blocked("https://169.254.169.254/")

    def test_cloud_metadata_address_is_blocked(self) -> None:
        self._assert_connection_blocked("http://169.254.169.254/latest/meta-data/")

    def test_ipv6_loopback_is_blocked(self) -> None:
        self._assert_connection_blocked("https://[::1]/")

    def test_ipv6_unique_local_is_blocked(self) -> None:
        self._assert_connection_blocked("https://[fd00::1]/")

    def test_ipv6_link_local_is_blocked(self) -> None:
        self._assert_connection_blocked("https://[fe80::1]/")

    def test_hostname_resolving_to_private_is_blocked(self) -> None:
        addrinfo = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 443))
        ]
        with mock.patch(
            "app.core.network.socket.getaddrinfo",
            return_value=addrinfo,
        ):
            self._assert_connection_blocked("https://internal.corp.local/")

    def test_hostname_resolving_to_public_is_analyzed_via_resolved_ip(self) -> None:
        addrinfo = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ]
        with mock.patch(
            "app.core.network.socket.getaddrinfo",
            return_value=addrinfo,
        ), mock.patch(
            "app.detection.phishing.analyzers.ssl.socket.create_connection",
            return_value=_FakeConnection(),
        ), mock.patch(
            "app.detection.phishing.analyzers.ssl.ssl._create_unverified_context",
            return_value=_FakeSSLContext(_public_cert()),
        ):
            results = self.analyzer.analyze(build_url_context("https://example.com/"))

        self.assertTrue(results[0].data.get("available"))
        self.assertTrue(results[0].data["covers_host"])


class ScoreEngineTests(unittest.TestCase):

    def test_aggregates_strongest_per_check(self) -> None:
        engine = ScoreEngine(weights={"virustotal": 20.0}, thresholds=RiskThresholds())
        results = [
            CheckResult(check="virustotal", title="A", score=30, reason="x"),
            CheckResult(check="virustotal", title="B", score=90, reason="y"),
        ]
        summary = engine.aggregate(results)
        self.assertEqual(summary.contributions["virustotal"], 18.0)
        self.assertEqual(summary.threat_score, 18)

    def test_all_high_scores_round_to_100(self) -> None:
        engine = ScoreEngine(
            weights={
                "url_structure": 15.0,
                "typosquatting": 15.0,
                "whois_age": 15.0,
                "ssl": 10.0,
                "dns": 10.0,
                "virustotal": 20.0,
                "blacklist": 10.0,
                "keywords": 5.0,
            },
            thresholds=RiskThresholds(),
        )
        results = [
            CheckResult(check=name, title=name, score=100, reason="x")
            for name in engine._weights
        ]
        summary = engine.aggregate(results)
        self.assertEqual(summary.threat_score, 100)
        self.assertEqual(summary.risk_level, "critical")

    def test_reasons_and_recommendations(self) -> None:
        engine = ScoreEngine(weights={"a": 50.0, "b": 50.0}, thresholds=RiskThresholds())
        results = [
            CheckResult(check="a", title="A", score=80, reason="R1", recommendation="REC1"),
            CheckResult(check="b", title="B", score=40, reason="R2", recommendation="REC2"),
            CheckResult(check="c", title="C", score=10, reason="R3"),
        ]
        summary = engine.aggregate(results)
        self.assertEqual(summary.reasons, ["R1", "R2"])
        self.assertEqual(summary.recommendations, ["REC1"])

    def test_low_scores_are_low_risk(self) -> None:
        engine = ScoreEngine(weights={"a": 100.0}, thresholds=RiskThresholds())
        results = [CheckResult(check="a", title="A", score=10, reason="x")]
        summary = engine.aggregate(results)
        self.assertEqual(summary.risk_level, "low")


class PhishingServiceTests(unittest.TestCase):

    def test_analyze_url_builds_full_response(self) -> None:
        config = _config(enable_ai_summary=False)
        analyzers = [
            FakeAnalyzer(config, 90, reason="Malicious verdict.", recommendation="Block it."),
            FakeCleanAnalyzer(config),
        ]

        response = analyze_url(
            "https://example.com/login",
            config=config,
            analyzers=analyzers,
        )

        self.assertEqual(response.url, "https://example.com/login")
        self.assertTrue(0 <= response.threat_score <= 100)
        self.assertIn(response.risk_level, ("low", "medium", "high", "critical"))
        self.assertIn("Malicious verdict.", response.reasons)
        self.assertIn("Block it.", response.recommendations)
        self.assertIn(response.risk_level.upper(), response.ai_summary.upper())
        self.assertEqual(len(response.checks), 2)
        self.assertIsNotNone(response.generated_at)

    def test_analyze_url_adds_fallback_reason_for_clean_result(self) -> None:
        config = _config(enable_ai_summary=False)
        response = analyze_url(
            "https://example.com/",
            config=config,
            analyzers=[FakeCleanAnalyzer(config)],
        )

        self.assertEqual(response.threat_score, 0)
        self.assertEqual(response.risk_level, "low")
        self.assertNotEqual(response.reasons, [])
        self.assertNotEqual(response.recommendations, [])

    def test_analyze_url_rejects_bad_url(self) -> None:
        with self.assertRaises(ValidationError):
            analyze_url("not-a-url")

    def test_analyzer_failure_is_neutral(self) -> None:
        config = _config(enable_ai_summary=False)

        class FailingAnalyzer(FakeAnalyzer):
            def analyze(self, context):
                raise RuntimeError("boom")

        failing = FailingAnalyzer(config, score=0)

        response = analyze_url(
            "https://example.com/",
            config=config,
            analyzers=[failing],
        )

        self.assertEqual(len(response.checks), 1)
        self.assertEqual(response.checks[0].score, 25)
        self.assertIn("could not be completed", response.checks[0].reason)

    def test_risk_level_matches_threshold(self) -> None:
        config = _config(enable_ai_summary=False, thresholds=RiskThresholds())
        analyzers = [
            FakeAnalyzer(config, 100, reason="R", recommendation="REC"),
        ]

        response = analyze_url("https://example.com/", config=config, analyzers=analyzers)

        # Only 20 weight points for virustotal -> low score
        self.assertEqual(response.threat_score, 20)
        self.assertEqual(response.risk_level, "low")


if __name__ == "__main__":
    unittest.main()
