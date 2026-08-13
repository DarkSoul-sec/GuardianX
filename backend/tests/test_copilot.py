"""Tests for the AI Security Copilot module."""

import unittest
from datetime import UTC, datetime
from unittest import mock

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.asset_types import AssetType
from app.core.roles import UserRole
from app.core.scan_status import ScanStatus
from app.database import models  # noqa: F401 - register mapped models
from app.database.base import Base
from app.copilot.base import BaseCopilotProvider, CopilotProviderError
from app.copilot.intents import CopilotIntent, detect_intent
from app.copilot import memory as copilot_memory
from app.copilot import sanitize as copilot_sanitize
from app.models.asset import Asset
from app.models.finding import Finding
from app.models.scan import Scan
from app.models.scan_result import ScanResult
from app.models.user import User
from app.schemas.copilot import CopilotChatRequest
from app.services.copilot_service import chat as copilot_chat
from app.services.copilot_service import stream_chat as copilot_stream_chat


class FakeProvider(BaseCopilotProvider):
    """Deterministic stand-in for a real LLM provider."""

    name = "fake"
    model = "fake-model"

    def complete(self, system_prompt, user_prompt, context=None) -> str:
        self.last_call = {
            "system": system_prompt,
            "user": user_prompt,
            "context": context,
        }
        return "Fake provider answer"


class CopilotDBTests(unittest.TestCase):
    """Shared in-memory DB fixtures for Copilot service tests."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(cls.engine)
        cls.session_factory = sessionmaker(bind=cls.engine, expire_on_commit=False)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()

    def setUp(self) -> None:
        self.db: Session = self.session_factory()
        self.alice = User(
            username="alice",
            email="alice@example.com",
            password_hash="unused",
            role=UserRole.USER,
            is_active=True,
        )
        self.bob = User(
            username="bob",
            email="bob@example.com",
            password_hash="unused",
            role=UserRole.USER,
            is_active=True,
        )
        self.db.add_all([self.alice, self.bob])
        self.db.flush()

        self.alice_asset = Asset(
            name="Alice Web Server",
            asset_type=AssetType.SERVER,
            ip_address="192.0.2.10",
            created_by=self.alice.id,
        )
        self.bob_asset = Asset(
            name="Bob Database",
            asset_type=AssetType.SERVER,
            ip_address="192.0.2.11",
            created_by=self.bob.id,
        )
        self.db.add_all([self.alice_asset, self.bob_asset])
        self.db.flush()

        now = datetime.now(UTC)
        self.alice_scan = Scan(
            asset_id=self.alice_asset.id,
            status=ScanStatus.COMPLETED,
            scanner="nmap",
            started_at=now,
            finished_at=now,
        )
        self.alice_failed_scan = Scan(
            asset_id=self.alice_asset.id,
            status=ScanStatus.FAILED,
            scanner="nmap",
            started_at=now,
        )
        self.bob_scan = Scan(
            asset_id=self.bob_asset.id,
            status=ScanStatus.COMPLETED,
            scanner="nmap",
            started_at=now,
            finished_at=now,
        )
        self.db.add_all([self.alice_scan, self.alice_failed_scan, self.bob_scan])
        self.db.flush()

        self.alice_result = ScanResult(
            scan_id=self.alice_scan.id,
            port=443,
            protocol="tcp",
            state="open",
            service="https",
            is_ssl=True,
        )
        self.bob_result = ScanResult(
            scan_id=self.bob_scan.id,
            port=5432,
            protocol="tcp",
            state="open",
            service="postgresql",
            is_ssl=False,
        )
        self.db.add_all([self.alice_result, self.bob_result])
        self.db.flush()

        self.alice_finding = Finding(
            scan_result_id=self.alice_result.id,
            title="Log4Shell",
            severity="CRITICAL",
            cve="CVE-2024-1111",
            cvss=10.0,
            description="Critical remote code execution in logging library.",
            recommendation="Upgrade to the latest patched version.",
            status="OPEN",
        )
        self.bob_finding = Finding(
            scan_result_id=self.bob_result.id,
            title="SQL Injection",
            severity="HIGH",
            cve="CVE-2023-9999",
            cvss=9.1,
            description="Remote code execution in database driver.",
            recommendation="Apply vendor security patch.",
            status="OPEN",
        )
        self.db.add_all([self.alice_finding, self.bob_finding])
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)


class CopilotTests(CopilotDBTests):

    # ------------------------------------------------------------------
    # Intent detection
    # ------------------------------------------------------------------

    def test_detect_intent_finds_cve(self) -> None:
        self.assertEqual(
            detect_intent("Explain this CVE: CVE-2024-1111"),
            CopilotIntent.EXPLAIN_CVE,
        )

    def test_detect_intent_finds_remediation_keywords(self) -> None:
        self.assertEqual(
            detect_intent("Generate remediation for that finding"),
            CopilotIntent.REMEDIATION,
        )

    def test_detect_intent_finds_explain_vulnerability(self) -> None:
        self.assertEqual(
            detect_intent("Explain this vulnerability to me"),
            CopilotIntent.EXPLAIN_VULNERABILITY,
        )
        self.assertEqual(
            detect_intent("explain the finding details"),
            CopilotIntent.EXPLAIN_VULNERABILITY,
        )

    def test_detect_intent_finds_security_recommendations(self) -> None:
        self.assertEqual(
            detect_intent("Give me security recommendations"),
            CopilotIntent.SECURITY_RECOMMENDATIONS,
        )
        self.assertEqual(
            detect_intent("what are the best practices for my estate"),
            CopilotIntent.SECURITY_RECOMMENDATIONS,
        )

    def test_detect_intent_finds_asset_summary(self) -> None:
        self.assertEqual(
            detect_intent("Summarize the assets in my estate"),
            CopilotIntent.ASSET_SUMMARY,
        )
        self.assertEqual(
            detect_intent("Give me an asset summary"),
            CopilotIntent.ASSET_SUMMARY,
        )

    def test_detect_intent_finds_technical_summary(self) -> None:
        self.assertEqual(
            detect_intent("Give me a technical summary"),
            CopilotIntent.TECHNICAL_SUMMARY,
        )
        self.assertEqual(
            detect_intent("Generate a SOC report"),
            CopilotIntent.TECHNICAL_SUMMARY,
        )

    def test_detect_intent_finds_dashboard_insights(self) -> None:
        self.assertEqual(
            detect_intent("What are my top 5 risks?"),
            CopilotIntent.DASHBOARD_INSIGHTS,
        )
        self.assertEqual(
            detect_intent("Show me dashboard insights"),
            CopilotIntent.DASHBOARD_INSIGHTS,
        )

    def test_detect_intent_finds_threat_summary_with_cve(self) -> None:
        self.assertEqual(
            detect_intent(
                "Give me a full threat summary for CVE-2024-1111 "
                "combining all sources"
            ),
            CopilotIntent.THREAT_SUMMARY,
        )

    def test_detect_intent_finds_natural_language_search(self) -> None:
        self.assertEqual(
            detect_intent("Show my critical vulnerabilities"),
            CopilotIntent.NATURAL_LANGUAGE_SEARCH,
        )
        self.assertEqual(
            detect_intent("Assets running PostgreSQL"),
            CopilotIntent.NATURAL_LANGUAGE_SEARCH,
        )
        self.assertEqual(
            detect_intent("Find exposed SSH"),
            CopilotIntent.NATURAL_LANGUAGE_SEARCH,
        )

    def test_detect_intent_prefers_explicit_intent_over_search(self) -> None:
        self.assertEqual(
            detect_intent(
                "Show me remediation for my critical vulnerabilities",
                finding_id=1,
            ),
            CopilotIntent.REMEDIATION,
        )

    def test_detect_intent_falls_back_to_general(self) -> None:
        self.assertEqual(
            detect_intent("hello there"),
            CopilotIntent.GENERAL,
        )

    # ------------------------------------------------------------------
    # Chat behaviour (rules provider, no LLM configured)
    # ------------------------------------------------------------------

    def test_chat_explain_cve_uses_rules_provider(self) -> None:
        response = copilot_chat(
            CopilotChatRequest(
                message="Explain this CVE",
                type=CopilotIntent.EXPLAIN_CVE,
                cve="CVE-2024-1111",
            ),
            db=self.db,
            current_user=self.alice,
        )
        self.assertEqual(response.provider, "rules")
        self.assertEqual(response.intent, CopilotIntent.EXPLAIN_CVE)
        self.assertIn("CVE-2024-1111", response.answer)
        self.assertIn("CRITICAL", response.answer)
        self.assertEqual(response.context.cve, "CVE-2024-1111")
        self.assertEqual(response.context.asset_name, "Alice Web Server")

    def test_chat_explain_cve_unknown_cve_gives_guidance(self) -> None:
        response = copilot_chat(
            CopilotChatRequest(
                message="Explain this CVE",
                type=CopilotIntent.EXPLAIN_CVE,
                cve="CVE-2099-0000",
            ),
            db=self.db,
            current_user=self.alice,
        )
        self.assertIn("not currently detected", response.answer.lower())

    def test_chat_asset_risk_does_not_leak_other_users_assets(self) -> None:
        response = copilot_chat(
            CopilotChatRequest(
                message="Why is this asset risky?",
                type=CopilotIntent.ASSET_RISK,
                asset_id=self.bob_asset.id,
            ),
            db=self.db,
            current_user=self.alice,
        )
        self.assertNotIn("Bob Database", response.answer)
        self.assertNotIn("CVE-2023-9999", response.answer)
        self.assertIsNone(response.context.asset_name)

    def test_chat_asset_risk_for_own_asset(self) -> None:
        response = copilot_chat(
            CopilotChatRequest(
                message="Why is this asset risky?",
                type=CopilotIntent.ASSET_RISK,
                asset_id=self.alice_asset.id,
            ),
            db=self.db,
            current_user=self.alice,
        )
        self.assertIn("Alice Web Server", response.answer)
        self.assertIn("CRITICAL", response.answer)
        self.assertEqual(response.context.asset_id, self.alice_asset.id)

    def test_chat_scan_summary_counts_only_todays_scans(self) -> None:
        response = copilot_chat(
            CopilotChatRequest(
                message="Summarize today's scans",
                type=CopilotIntent.SCAN_SUMMARY,
            ),
            db=self.db,
            current_user=self.alice,
        )
        self.assertEqual(response.intent, CopilotIntent.SCAN_SUMMARY)
        self.assertIn("Alice Web Server", response.answer)
        self.assertIn("Completed", response.answer)
        self.assertIn("Failed", response.answer)
        # Bob's scan must not appear for Alice.
        self.assertNotIn("Bob Database", response.answer)

    def test_chat_asset_summary_is_scoped_to_the_user(self) -> None:
        response = copilot_chat(
            CopilotChatRequest(
                message="Summarize the assets",
                type=CopilotIntent.ASSET_SUMMARY,
            ),
            db=self.db,
            current_user=self.alice,
        )
        self.assertEqual(response.intent, CopilotIntent.ASSET_SUMMARY)
        self.assertIn("Asset Estate Summary", response.answer)
        self.assertIn("Alice Web Server", response.answer)
        self.assertIn("SERVER", response.answer)
        # Bob's estate must not leak into Alice's summary.
        self.assertNotIn("Bob Database", response.answer)

    def test_chat_remediation(self) -> None:
        response = copilot_chat(
            CopilotChatRequest(
                message="Generate remediation",
                type=CopilotIntent.REMEDIATION,
                finding_id=self.alice_finding.id,
            ),
            db=self.db,
            current_user=self.alice,
        )
        self.assertIn("Remediation", response.answer)
        self.assertIn("CVE-2024-1111", response.answer)
        self.assertEqual(response.context.finding_id, self.alice_finding.id)

    def test_chat_prioritize(self) -> None:
        response = copilot_chat(
            CopilotChatRequest(
                message="Prioritize vulnerabilities",
                type=CopilotIntent.PRIORITIZE,
            ),
            db=self.db,
            current_user=self.alice,
        )
        self.assertIn("CVE-2024-1111", response.answer)
        self.assertIn("Alice Web Server", response.answer)

    def test_chat_executive_summary(self) -> None:
        response = copilot_chat(
            CopilotChatRequest(
                message="Generate executive summary",
                type=CopilotIntent.EXECUTIVE_SUMMARY,
            ),
            db=self.db,
            current_user=self.alice,
        )
        self.assertIn("Executive Security Summary", response.answer)
        self.assertIn("Assets monitored", response.answer)

    def test_chat_technical_summary(self) -> None:
        response = copilot_chat(
            CopilotChatRequest(
                message="Generate technical summary",
                type=CopilotIntent.TECHNICAL_SUMMARY,
            ),
            db=self.db,
            current_user=self.alice,
        )
        self.assertIn("Technical Security Summary", response.answer)
        self.assertIn("CVE-2024-1111", response.answer)
        self.assertIn("CVE", response.answer)

    def test_chat_dashboard_insights(self) -> None:
        response = copilot_chat(
            CopilotChatRequest(
                message="Show me dashboard insights",
                type=CopilotIntent.DASHBOARD_INSIGHTS,
            ),
            db=self.db,
            current_user=self.alice,
        )
        self.assertIn("Dashboard Insights", response.answer)
        self.assertIn("Improvement suggestions", response.answer)
        # Bob's data must not leak into Alice's insights.
        self.assertNotIn("Bob Database", response.answer)

    def test_chat_natural_language_search_returns_results(self) -> None:
        response = copilot_chat(
            CopilotChatRequest(
                message="Show my critical vulnerabilities",
                type=CopilotIntent.NATURAL_LANGUAGE_SEARCH,
            ),
            db=self.db,
            current_user=self.alice,
        )
        self.assertEqual(
            response.intent,
            CopilotIntent.NATURAL_LANGUAGE_SEARCH,
        )
        self.assertIn("Natural Language Search", response.answer)
        self.assertIn("CVE-2024-1111", response.answer)
        self.assertIsNotNone(response.results)
        self.assertTrue(any(item.kind == "finding" for item in response.results))
        self.assertIn(
            response.results[0].severity,
            ("CRITICAL", "HIGH", "MEDIUM", "LOW"),
        )

    def test_chat_natural_language_search_is_scoped_to_user(self) -> None:
        response = copilot_chat(
            CopilotChatRequest(
                message="Show all assets running PostgreSQL",
                type=CopilotIntent.NATURAL_LANGUAGE_SEARCH,
            ),
            db=self.db,
            current_user=self.alice,
        )
        # Bob's postgres asset must not leak into Alice's results.
        self.assertNotIn("Bob Database", response.answer)
        if response.results:
            for item in response.results:
                self.assertNotIn("Bob Database", item.title)
                self.assertNotIn("Bob Database", item.detail or "")

    def test_chat_natural_language_search_no_match_guidance(self) -> None:
        response = copilot_chat(
            CopilotChatRequest(
                message="Show assets running SAP HANA",
                type=CopilotIntent.NATURAL_LANGUAGE_SEARCH,
            ),
            db=self.db,
            current_user=self.alice,
        )
        self.assertIn("No assets, findings, or services matched", response.answer)

    def test_chat_threat_summary(self) -> None:
        response = copilot_chat(
            CopilotChatRequest(
                message="Give me a threat summary for CVE-2024-1111",
                type=CopilotIntent.THREAT_SUMMARY,
                cve="CVE-2024-1111",
            ),
            db=self.db,
            current_user=self.alice,
        )
        self.assertIn("Threat Summary", response.answer)
        self.assertEqual(response.context.cve, "CVE-2024-1111")

    def test_chat_threat_summary_auto_resolves_top_finding(self) -> None:
        response = copilot_chat(
            CopilotChatRequest(
                message="Give me a threat summary",
                type=CopilotIntent.THREAT_SUMMARY,
            ),
            db=self.db,
            current_user=self.alice,
        )
        self.assertIn("Threat Summary", response.answer)
        # Falls back to the user's highest-CVSS finding.
        self.assertEqual(response.context.cve, "CVE-2024-1111")
        self.assertNotIn("CVE-2023-9999", response.answer)

    def test_chat_explain_vulnerability(self) -> None:
        response = copilot_chat(
            CopilotChatRequest(
                message="Explain this vulnerability",
                type=CopilotIntent.EXPLAIN_VULNERABILITY,
                finding_id=self.alice_finding.id,
            ),
            db=self.db,
            current_user=self.alice,
        )
        self.assertEqual(response.intent, CopilotIntent.EXPLAIN_VULNERABILITY)
        self.assertIn("Log4Shell", response.answer)
        self.assertIn("CVE-2024-1111", response.answer)
        self.assertEqual(response.context.finding_id, self.alice_finding.id)

    def test_chat_explain_vulnerability_does_not_leak_other_users(self) -> None:
        response = copilot_chat(
            CopilotChatRequest(
                message="Explain this vulnerability",
                type=CopilotIntent.EXPLAIN_VULNERABILITY,
                finding_id=self.bob_finding.id,
            ),
            db=self.db,
            current_user=self.alice,
        )
        self.assertNotIn("CVE-2023-9999", response.answer)
        self.assertNotIn("Bob Database", response.answer)
        self.assertNotEqual(response.context.finding_id, self.bob_finding.id)

    def test_chat_security_recommendations(self) -> None:
        response = copilot_chat(
            CopilotChatRequest(
                message="Give me security recommendations",
                type=CopilotIntent.SECURITY_RECOMMENDATIONS,
            ),
            db=self.db,
            current_user=self.alice,
        )
        self.assertEqual(
            response.intent,
            CopilotIntent.SECURITY_RECOMMENDATIONS,
        )
        self.assertIn("Security Recommendations", response.answer)
        self.assertIn("Quick wins", response.answer)
        self.assertIn("Alice Web Server", response.answer)
        self.assertNotIn("Bob Database", response.answer)

    def test_chat_unknown_message_lists_capabilities(self) -> None:
        response = copilot_chat(
            CopilotChatRequest(message="hello there"),
            db=self.db,
            current_user=self.alice,
        )
        self.assertEqual(response.intent, CopilotIntent.GENERAL)
        self.assertIn("Explain a CVE", response.answer)

    # ------------------------------------------------------------------
    # Provider abstraction
    # ------------------------------------------------------------------

    def test_chat_delegates_to_configured_provider(self) -> None:
        fake = FakeProvider()
        with mock.patch(
            "app.services.copilot_service.get_copilot_provider",
            return_value=fake,
        ):
            response = copilot_chat(
                CopilotChatRequest(
                    message="Explain this CVE",
                    type=CopilotIntent.EXPLAIN_CVE,
                    cve="CVE-2024-1111",
                ),
                db=self.db,
                current_user=self.alice,
            )

        self.assertEqual(response.answer, "Fake provider answer")
        self.assertEqual(response.provider, "fake")
        self.assertEqual(response.model, "fake-model")

        self.assertIn("CVE-2024-1111", fake.last_call["user"])
        self.assertIn(
            fake.last_call["context"]["intent"],
            CopilotIntent.EXPLAIN_CVE,
        )

    def test_chat_surfaces_provider_errors(self) -> None:
        def failing_provider():
            provider = FakeProvider()

            def fail(*args, **kwargs):
                raise CopilotProviderError("provider down")

            provider.complete = fail
            return provider

        with mock.patch(
            "app.services.copilot_service.get_copilot_provider",
            side_effect=failing_provider,
        ):
            with self.assertRaises(CopilotProviderError):
                copilot_chat(
                    CopilotChatRequest(
                        message="Prioritize vulnerabilities",
                        type=CopilotIntent.PRIORITIZE,
                    ),
                    db=self.db,
                    current_user=self.alice,
                )

    def test_chat_resolves_asset_by_name(self) -> None:
        response = copilot_chat(
            CopilotChatRequest(
                message="Why is this asset risky? Alice Web Server",
                type=CopilotIntent.ASSET_RISK,
            ),
            db=self.db,
            current_user=self.alice,
        )
        self.assertIn("Alice Web Server", response.answer)
        self.assertEqual(response.context.asset_id, self.alice_asset.id)


class StreamingTests(CopilotDBTests):
    """stream_chat emits meta, token, and done events in order."""

    def _collect(self, request: CopilotChatRequest) -> list[dict]:
        return list(
            copilot_stream_chat(
                request,
                db=self.db,
                current_user=self.alice,
            )
        )

    def test_stream_emits_meta_tokens_and_done(self) -> None:
        events = self._collect(
            CopilotChatRequest(
                message="Explain this CVE",
                type=CopilotIntent.EXPLAIN_CVE,
                cve="CVE-2024-1111",
            )
        )

        self.assertGreaterEqual(len(events), 2)
        self.assertEqual(events[0]["type"], "meta")
        self.assertEqual(
            events[0]["intent"],
            CopilotIntent.EXPLAIN_CVE,
        )

        done = events[-1]
        self.assertEqual(done["type"], "done")
        self.assertIn("CVE-2024-1111", done["content"])
        self.assertEqual(done["context"]["cve"], "CVE-2024-1111")

    def test_stream_rules_provider_emits_single_token(self) -> None:
        events = self._collect(
            CopilotChatRequest(
                message="Prioritize vulnerabilities",
                type=CopilotIntent.PRIORITIZE,
            )
        )

        token_events = [event for event in events if event["type"] == "token"]
        self.assertEqual(len(token_events), 1)
        self.assertIn("CVE-2024-1111", token_events[0]["content"])

    def test_stream_natural_language_search_emits_results(self) -> None:
        events = self._collect(
            CopilotChatRequest(
                message="Show my critical vulnerabilities",
                type=CopilotIntent.NATURAL_LANGUAGE_SEARCH,
            )
        )

        done = events[-1]
        self.assertEqual(done["type"], "done")
        self.assertIsNotNone(done["results"])
        self.assertTrue(done["results"])


class MemoryTests(unittest.TestCase):
    def setUp(self) -> None:
        copilot_memory.clear(999)

    def tearDown(self) -> None:
        copilot_memory.clear(999)

    def test_push_and_recent(self) -> None:
        copilot_memory.push(
            999,
            "user",
            "Why is this asset risky?",
            intent=CopilotIntent.ASSET_RISK,
            resolved={"asset_id": 1, "asset_name": "Web"},
        )
        copilot_memory.push(
            999,
            "assistant",
            "Because of critical findings.",
            intent=CopilotIntent.ASSET_RISK,
        )

        turns = copilot_memory.recent(999)

        self.assertEqual(len(turns), 2)
        self.assertEqual(turns[0]["role"], "user")
        self.assertEqual(turns[0]["intent"], CopilotIntent.ASSET_RISK)
        self.assertEqual(turns[1]["content"], "Because of critical findings.")

    def test_build_recap_includes_user_turns_with_resolved_entities(self) -> None:
        copilot_memory.push(
            999,
            "user",
            "Why is the asset risky?",
            intent=CopilotIntent.ASSET_RISK,
            resolved={"asset_id": 7, "asset_name": "Db Box"},
        )
        copilot_memory.push(
            999,
            "assistant",
            "Long answer that is not echoed.",
            intent=CopilotIntent.ASSET_RISK,
        )

        recap = copilot_memory.build_recap(999)

        self.assertIn("Previous conversation context", recap)
        self.assertIn("Why is the asset risky?", recap)
        self.assertIn("asset=Db Box", recap)
        # Assistant content is deliberately not echoed into the recap.
        self.assertNotIn("Long answer that is not echoed", recap)

    def test_clear_returns_turn_count(self) -> None:
        copilot_memory.push(999, "user", "hello")
        copilot_memory.push(999, "user", "world")

        self.assertEqual(copilot_memory.clear(999), 2)
        self.assertEqual(copilot_memory.status(999)["turns"], 0)

    def test_status_reports_turns(self) -> None:
        copilot_memory.push(999, "user", "hello")

        status = copilot_memory.status(999)

        self.assertEqual(status["turns"], 1)
        self.assertGreater(status["ttl_seconds"], 0)


class SanitizeTests(unittest.TestCase):
    def test_redacts_jwt(self) -> None:
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        result = copilot_sanitize.sanitize_prompt(f"token {jwt} here")

        self.assertNotIn("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", result)
        self.assertIn(copilot_sanitize.REDACTED, result)

    def test_redacts_api_keys(self) -> None:
        result = copilot_sanitize.sanitize_prompt(
            "my key is sk-abcdefghijklmnopqrstuvwxyz123456"
        )
        self.assertIn(copilot_sanitize.REDACTED, result)
        self.assertNotIn("sk-abcdefghijklmnopqrstuvwxyz123456", result)

    def test_redacts_gemini_keys(self) -> None:
        key = "AIzaSyD6X3kL9mP0qRv8TzUaBcDeFgH1234567890xyz"
        result = copilot_sanitize.sanitize_prompt(f"gemini key {key}")

        self.assertIn(copilot_sanitize.REDACTED, result)
        self.assertNotIn("AIzaSyD6X3kL9mP0qRv8TzUaBcDeFgH1234567890xyz", result)

    def test_redacts_key_assignments(self) -> None:
        result = copilot_sanitize.sanitize_prompt("API_KEY=superSecretValue12345")
        self.assertIn(copilot_sanitize.REDACTED, result)
        self.assertNotIn("superSecretValue12345", result)

    def test_redacts_bearer_tokens(self) -> None:
        result = copilot_sanitize.sanitize_prompt(
            "Authorization: Bearer abcdefghijklmnopqrstuvwxyz1234567890"
        )
        self.assertIn(copilot_sanitize.REDACTED, result)

    def test_leaves_plain_text_unchanged(self) -> None:
        message = "Show me the critical vulnerabilities on my web server."
        result = copilot_sanitize.sanitize_prompt(message)

        self.assertEqual(result, message)
        self.assertNotIn(copilot_sanitize.REDACTED, result)

    def test_empty_input(self) -> None:
        self.assertEqual(copilot_sanitize.sanitize_prompt(""), "")
        self.assertEqual(copilot_sanitize.sanitize_prompt(None), None)


if __name__ == "__main__":
    unittest.main()
