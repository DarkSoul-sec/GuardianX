"""
Analyzer registry and factory.

The active set of analyzers is declared here and instantiated with the shared
configuration. Adding a new check is a matter of implementing the
:class:`Analyzer` contract and registering it in ``ANALYZER_REGISTRY``; the
service, scoring and API layers need no changes.
"""

from __future__ import annotations

from app.detection.phishing.analyzers.blacklist import BlacklistAnalyzer
from app.detection.phishing.analyzers.dns import DNSAnalyzer
from app.detection.phishing.analyzers.keywords import SuspiciousKeywordsAnalyzer
from app.detection.phishing.analyzers.ssl import SSLCertificateAnalyzer
from app.detection.phishing.analyzers.typosquatting import TyposquattingAnalyzer
from app.detection.phishing.analyzers.url_structure import URLStructureAnalyzer
from app.detection.phishing.analyzers.virustotal import VirusTotalAnalyzer
from app.detection.phishing.analyzers.whois import WhoIsAgeAnalyzer
from app.detection.phishing.base import Analyzer

ANALYZER_REGISTRY: tuple[type[Analyzer], ...] = (
    URLStructureAnalyzer,
    TyposquattingAnalyzer,
    WhoIsAgeAnalyzer,
    SSLCertificateAnalyzer,
    DNSAnalyzer,
    VirusTotalAnalyzer,
    BlacklistAnalyzer,
    SuspiciousKeywordsAnalyzer,
)


def build_analyzers(
    config,
    *,
    virustotal_api_key: str | None = None,
) -> list[Analyzer]:
    """Instantiate the full analyzer set with the given configuration."""
    analyzers: list[Analyzer] = []

    for analyzer_class in ANALYZER_REGISTRY:
        if analyzer_class is VirusTotalAnalyzer:
            analyzers.append(
                analyzer_class(
                    config,
                    api_key=virustotal_api_key,
                )
            )
        else:
            analyzers.append(analyzer_class(config))

    return analyzers
