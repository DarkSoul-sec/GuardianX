"""
VirusTotal provider for the Threat Intelligence platform.

Responsible for translating a raw VirusTotal v3 report into the normalized
:class:`~app.intelligence.schemas.ThreatIntelligenceReport` consumed by the
GuardianX dashboard. It performs the richer per-indicator extraction (country,
ASN, registrar, creation date, community votes, submissions, engine versions,
MITRE mapping, risk scoring) that the lightweight lookups in
``app.integrations.virustotal`` deliberately omit.

Transport, retries, timeouts, per-key rate limiting and connection pooling are
all handled by the shared ``app.integrations.virustotal.client._get`` — this
module never talks to ``requests`` directly and never logs API keys.
"""

from __future__ import annotations

import base64
from datetime import UTC, datetime
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict, Field

from app.integrations.virustotal.client import _get
from app.intelligence.cache import cache_key, get_cached, set_cached
from app.intelligence.schemas import (
    CommunityVotes,
    IOCType,
    MitreMapping,
    ThreatIntelligenceReport,
    ThreatLevel,
    VendorDetectionEntry,
)

# ---------------------------------------------------------------------
# Raw VirusTotal v3 response models (provider-specific).
# ---------------------------------------------------------------------


class VtStats(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    malicious: int = 0
    suspicious: int = 0
    undetected: int = 0
    harmless: int = 0
    timeout: int = 0
    confirmed_timeout: int = Field(default=0, alias="confirmed-timeout")
    failure: int = 0
    type_unsupported: int = Field(default=0, alias="type-unsupported")


class VtVendor(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    category: str = ""
    result: str | None = None
    method: str | None = None
    engine_name: str | None = None
    engine_version: str | None = None
    engine_update: str | None = None


class VtVotes(BaseModel):
    harmless: int = 0
    malicious: int = 0


class VtAttributes(BaseModel):
    last_analysis_stats: VtStats | None = None
    last_analysis_results: dict[str, VtVendor] = Field(default_factory=dict)
    last_analysis_date: int | None = None
    first_seen_date: int | None = None
    first_submission_date: int | None = None
    last_submission_date: int | None = None
    times_submitted: int | None = None
    reputation: int | None = None
    popular_threat_category: str | None = None
    type_description: str | None = None
    meaningful_name: str | None = None
    categories: dict[str, str] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    threat_names: list[str] = Field(default_factory=list)
    total_votes: VtVotes | None = None
    asn: int | str | None = None
    as_owner: str | None = None
    country: str | None = None
    registrar: str | None = None
    creation_date: int | str | None = None
    whois: str | None = None
    regional_internet_registry: str | None = None
    network: str | None = None


class VtData(BaseModel):
    id: str
    type: str
    attributes: VtAttributes = Field(default_factory=VtAttributes)


class VtReport(BaseModel):
    data: VtData | None = None


# ---------------------------------------------------------------------
# Link helpers
# ---------------------------------------------------------------------

_PERMALINK_TEMPLATES = {
    IOCType.IP: "https://www.virustotal.com/gui/ip-address/{value}",
    IOCType.DOMAIN: "https://www.virustotal.com/gui/domain/{value}",
    IOCType.URL: "https://www.virustotal.com/gui/url/{value}",
    IOCType.HASH: "https://www.virustotal.com/gui/file/{value}",
}


def _url_id(url: str) -> str:
    """URL-safe base64 identifier used by the VirusTotal API and web app."""
    return base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip("=")


def _api_path(ioc_type: IOCType, value: str) -> str:
    if ioc_type == IOCType.URL:
        return f"urls/{_url_id(value)}"
    if ioc_type == IOCType.DOMAIN:
        return f"domains/{quote(value, safe='')}"
    if ioc_type == IOCType.IP:
        return f"ip_addresses/{value}"
    return f"files/{value}"


def _permalink(ioc_type: IOCType, value: str) -> str:
    display = _url_id(value) if ioc_type == IOCType.URL else value
    return _PERMALINK_TEMPLATES[ioc_type].format(value=display)


# ---------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------

_WAYBACK_FMT = ("%Y%m%d", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S")


def _to_datetime(value: int | str | None) -> datetime | None:
    """Coerce a VirusTotal timestamp/date into a tz-aware ``datetime``."""
    if value is None:
        return None

    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=UTC)
        except (OverflowError, OSError, ValueError):
            return None

    text = str(value).strip()
    if not text:
        return None

    if text.isdigit():
        try:
            return datetime.fromtimestamp(int(text), tz=UTC)
        except (OverflowError, OSError, ValueError):
            return None

    for fmt in _WAYBACK_FMT:
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue

    return None


def _whois_field(whois: str | None, *labels: str) -> str | None:
    """Extract the first matching ``label: value`` pair from WHOIS text."""
    if not whois:
        return None

    for line in whois.splitlines():
        if ":" not in line:
            continue
        field, _, value = line.partition(":")
        if any(label in field.strip().lower() for label in labels):
            value = value.strip()
            if value and value.lower() not in ("none", "null", "n/a", "-"):
                return value
    return None


def _top_verdict(results: dict[str, VtVendor]) -> str | None:
    """Return the most descriptive malicious/suspicious verdict, if any."""
    for item in results.values():
        if item.category in ("malicious", "suspicious") and item.result:
            return item.result
    for item in results.values():
        if item.category in ("malicious", "suspicious"):
            return item.category
    return None


def _category_labels(attributes: VtAttributes) -> list[str]:
    """Unique category values reported by vendors, preserving order."""
    return list(dict.fromkeys(v for v in attributes.categories.values() if v))


def _vendor_detections(
    results: dict[str, VtVendor],
) -> list[VendorDetectionEntry]:
    """Normalize every engine verdict, high-signal engines first."""
    priority = {"malicious": 0, "suspicious": 1}

    entries = [
        VendorDetectionEntry(
            engine=name,
            category=item.category,
            result=item.result,
            engine_version=item.engine_version,
            update_date=_to_datetime(item.engine_update),
        )
        for name, item in results.items()
    ]

    return sorted(
        entries,
        key=lambda entry: (priority.get(entry.category, 9), entry.engine.lower()),
    )


# ---------------------------------------------------------------------
# Risk scoring
# ---------------------------------------------------------------------


def _risk_score(
    stats: VtStats,
    reputation: int | None,
    votes: VtVotes | None,
) -> tuple[int, ThreatLevel]:
    """
    Deterministic 0-100 risk score and threat tier.

    Weights are deliberately simple and explainable: each malicious vendor
    contributes 18, each suspicious vendor 8, a negative reputation adds up
    to 30, malicious community votes add up to 12, and a positive reputation
    reduces the baseline.
    """
    reputation = reputation or 0
    votes_malicious = votes.malicious if votes else 0

    score = 0
    score += min(stats.malicious * 18, 60)
    score += min(stats.suspicious * 8, 24)
    score += min(votes_malicious * 2, 12)
    if reputation < 0:
        score += min(abs(reputation) * 3, 30)
    else:
        score -= min(reputation * 2, 20)
    score = max(0, min(100, score))

    detected = stats.malicious > 0 or stats.suspicious > 0

    if score >= 75:
        level = ThreatLevel.CRITICAL
    elif score >= 50:
        level = ThreatLevel.HIGH
    elif score >= 25:
        level = ThreatLevel.MEDIUM
    elif detected:
        level = ThreatLevel.LOW
    else:
        level = ThreatLevel.CLEAN

    return score, level


# ---------------------------------------------------------------------
# MITRE ATT&CK mapping (curated heuristic, no fabricated data)
# ---------------------------------------------------------------------

_MITRE_MAP: list[tuple[tuple[str, ...], dict[str, str]]] = [
    (("ransom",), {
        "tactic": "Impact",
        "technique_id": "T1486",
        "technique": "Data Encrypted for Impact",
        "description": "Ransomware was observed, indicating data-encryption impact.",
    }),
    (("trojan", "banking", "trickbot", "emotet", "qakbot", "zbot"), {
        "tactic": "Execution",
        "technique_id": "T1204",
        "technique": "User Execution",
        "description": "Trojan behavior suggests user-assisted execution of a malicious file.",
    }),
    (("phish", "spam", "scam"), {
        "tactic": "Initial Access",
        "technique_id": "T1566",
        "technique": "Phishing",
        "description": "Phishing or spam characteristics were identified.",
    }),
    (("c2", "command and control", "botnet", "beacon"), {
        "tactic": "Command and Control",
        "technique_id": "T1071",
        "technique": "Application Layer Protocol",
        "description": "Indicators consistent with command-and-control traffic.",
    }),
    (("downloader", "dropper"), {
        "tactic": "Command and Control",
        "technique_id": "T1105",
        "technique": "Ingress Tool Transfer",
        "description": "Downloader or dropper behavior implies inbound tool transfer.",
    }),
    (("backdoor",), {
        "tactic": "Persistence",
        "technique_id": "T1543",
        "technique": "Create or Modify System Process",
        "description": "Backdoor behavior may establish or modify a persistent service.",
    }),
    (("keylogger", "stealer", "password"), {
        "tactic": "Credential Access",
        "technique_id": "T1555",
        "technique": "Credentials from Password Stores",
        "description": "Credential-harvesting behavior was observed.",
    }),
    (("miner", "coinminer", "cryptominer"), {
        "tactic": "Impact",
        "technique_id": "T1496",
        "technique": "Resource Hijacking",
        "description": "Cryptocurrency mining behavior abuses compute resources.",
    }),
    (("worm",), {
        "tactic": "Lateral Movement",
        "technique_id": "T1091",
        "technique": "Replication Through Removable Media",
        "description": "Worm behavior may propagate across hosts.",
    }),
    (("exploit", "cve-"), {
        "tactic": "Execution",
        "technique_id": "T1203",
        "technique": "Exploitation for Client Execution",
        "description": "Exploit behavior targets a vulnerability in a client application.",
    }),
    (("maldoc", "macro", "office", "docx", "pdf"), {
        "tactic": "Initial Access",
        "technique_id": "T1566.001",
        "technique": "Phishing: Spearphishing Attachment",
        "description": "Malicious document indicators were detected.",
    }),
    (("proxy", "socks", "tunnel"), {
        "tactic": "Command and Control",
        "technique_id": "T1090",
        "technique": "Proxy",
        "description": "Proxy or tunneling indicators were observed.",
    }),
    (("dns",), {
        "tactic": "Command and Control",
        "technique_id": "T1071.004",
        "technique": "Application Layer Protocol: DNS",
        "description": "DNS-based indicators were observed.",
    }),
    (("scanner", "portscan", "recon"), {
        "tactic": "Discovery",
        "technique_id": "T1046",
        "technique": "Network Service Discovery",
        "description": "Network scanning or reconnaissance behavior was observed.",
    }),
    (("webshell",), {
        "tactic": "Persistence",
        "technique_id": "T1505.003",
        "technique": "Server Software Component: Web Shell",
        "description": "Web shell indicators suggest persistent web compromise.",
    }),
    (("ddos", "flood", "amplif"), {
        "tactic": "Impact",
        "technique_id": "T1498",
        "technique": "Network Denial of Service",
        "description": "Denial-of-service indicators were observed.",
    }),
]


def _derive_mitre(attributes: VtAttributes) -> list[MitreMapping]:
    """Map observed tags/categories to MITRE ATT&CK techniques."""
    haystack = " ".join(
        part.lower()
        for part in (
            attributes.popular_threat_category,
            *attributes.tags,
            *attributes.categories.values(),
        )
        if part
    )

    if not haystack:
        return []

    return [
        MitreMapping(**mapping)
        for keywords, mapping in _MITRE_MAP
        if any(keyword in haystack for keyword in keywords)
    ]


# ---------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------


def _extract_geo(
    ioc_type: IOCType,
    attributes: VtAttributes,
) -> tuple[str | None, str | None, str | None, str | None, datetime | None, datetime | None]:
    """Per-indicator geographic and ownership metadata."""
    country = attributes.country
    as_owner = attributes.as_owner
    registrar = attributes.registrar
    creation_date = _to_datetime(attributes.creation_date)
    first_seen = _to_datetime(attributes.first_seen_date)

    asn: str | None = None
    if attributes.asn is not None:
        asn = (
            str(attributes.asn)
            if str(attributes.asn).upper().startswith("AS")
            else f"AS{attributes.asn}"
        )

    if ioc_type == IOCType.IP:
        country = country or _whois_field(attributes.whois, "country")
        as_owner = as_owner or _whois_field(
            attributes.whois,
            "orgname",
            "org-name",
            "netname",
        )
        registrar = registrar or attributes.regional_internet_registry
        if creation_date is None:
            creation_date = _to_datetime(
                _whois_field(
                    attributes.whois,
                    "created",
                    "creation date",
                    "registration date",
                )
            )
    elif ioc_type == IOCType.DOMAIN:
        country = country or _whois_field(attributes.whois, "country")
        if creation_date is None:
            creation_date = _to_datetime(
                _whois_field(
                    attributes.whois,
                    "created",
                    "creation date",
                    "registration date",
                )
            )

    return country, asn, as_owner, registrar, creation_date, first_seen


def _threat_category(
    ioc_type: IOCType,
    attributes: VtAttributes,
) -> str | None:
    if ioc_type == IOCType.HASH:
        if attributes.popular_threat_category:
            return attributes.popular_threat_category
        verdict = _top_verdict(attributes.last_analysis_results)
        if verdict:
            return verdict
        if attributes.type_description:
            return attributes.type_description

    if attributes.categories:
        return next(iter(attributes.categories.values()))
    if attributes.threat_names:
        return attributes.threat_names[0]
    return _top_verdict(attributes.last_analysis_results)


def _to_report(
    ioc_type: IOCType,
    value: str,
    raw: dict,
) -> ThreatIntelligenceReport:
    """Normalize a raw VirusTotal response into the intelligence report."""
    vt = VtReport.model_validate(raw)
    if vt.data is None:
        return _not_found(ioc_type, value)

    attributes = vt.data.attributes
    stats = attributes.last_analysis_stats or VtStats()

    risk_score, threat_level = _risk_score(
        stats,
        attributes.reputation,
        attributes.total_votes,
    )

    total = (
        stats.malicious
        + stats.suspicious
        + stats.harmless
        + stats.undetected
        + stats.timeout
        + stats.confirmed_timeout
        + stats.failure
        + stats.type_unsupported
    )

    country, asn, as_owner, registrar, creation_date, first_seen = _extract_geo(
        ioc_type,
        attributes,
    )

    votes = attributes.total_votes or VtVotes()

    return ThreatIntelligenceReport(
        resource_type=ioc_type,
        resource=value,
        permalink=_permalink(ioc_type, value),
        found=True,
        detected=stats.malicious > 0 or stats.suspicious > 0,
        threat_level=threat_level,
        risk_score=risk_score,
        reputation=attributes.reputation or 0,
        community_score=attributes.reputation or 0,
        detection_ratio=(
            f"{stats.malicious}/{total}"
            if total > 0
            else "0/0"
        ),
        threat_category=_threat_category(ioc_type, attributes),
        last_analysis=_to_datetime(attributes.last_analysis_date),
        country=country,
        asn=asn,
        as_owner=as_owner,
        registrar=registrar,
        creation_date=creation_date,
        first_seen=first_seen or _to_datetime(attributes.first_submission_date),
        first_submission=_to_datetime(attributes.first_submission_date),
        last_submission=_to_datetime(attributes.last_submission_date),
        submission_count=attributes.times_submitted or 0,
        community_votes=CommunityVotes(
            malicious=votes.malicious,
            harmless=votes.harmless,
        ),
        malicious=stats.malicious,
        suspicious=stats.suspicious,
        harmless=stats.harmless,
        undetected=stats.undetected,
        total=total,
        categories=_category_labels(attributes),
        tags=attributes.tags,
        mitre=_derive_mitre(attributes),
        vendor_detections=_vendor_detections(attributes.last_analysis_results),
    )


def _not_found(ioc_type: IOCType, value: str) -> ThreatIntelligenceReport:
    return ThreatIntelligenceReport(
        resource_type=ioc_type,
        resource=value,
        permalink=_permalink(ioc_type, value),
        found=False,
        threat_level=ThreatLevel.UNKNOWN,
    )


# ---------------------------------------------------------------------
# Public lookup
# ---------------------------------------------------------------------


def normalize_ioc_value(ioc_type: IOCType, value: str) -> str:
    """Canonicalize an IOC before querying or caching it."""
    value = value.strip()
    if ioc_type == IOCType.HASH:
        return value.lower()
    return value


def lookup(
    api_key: str,
    ioc_type: IOCType,
    value: str,
) -> ThreatIntelligenceReport:
    """
    Return the normalized threat report for an IOC.

    Serves the cached report for 24 hours when available; otherwise it queries
    VirusTotal through the shared transport, normalizes the response and
    stores it for the next caller.
    """
    value = normalize_ioc_value(ioc_type, value)
    key = cache_key(ioc_type.value, value)

    cached = get_cached(key)
    if cached is not None:
        return cached.model_copy(update={"from_cache": True})

    raw = _get(api_key, _api_path(ioc_type, value))

    if raw is None:
        report = _not_found(ioc_type, value)
    else:
        report = _to_report(ioc_type, value, raw)

    set_cached(key, report)
    return report
