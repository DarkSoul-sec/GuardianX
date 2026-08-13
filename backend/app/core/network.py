"""
Scan-target validation.

Prevents SSRF and internal-network scanning by rejecting targets that
resolve into loopback, link-local, private, CGNAT, benchmarking, multicast
or reserved ranges, and by enforcing hostname syntax for domain targets.

Ranges are listed explicitly (rather than using the ``ipaddress`` boolean
flags) so documentation ranges like ``192.0.2.0/24`` — used by tests and
demos — remain valid while every genuinely dangerous range stays blocked.
"""

from __future__ import annotations

import ipaddress
import re
import socket

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.logger import logger

_HOSTNAME_RE = re.compile(
    r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*$"
)

_BLOCKED_IPV4_NETWORKS: list[ipaddress.IPv4Network] = [
    ipaddress.ip_network("0.0.0.0/8"),        # "this" network
    ipaddress.ip_network("127.0.0.0/8"),      # loopback
    ipaddress.ip_network("10.0.0.0/8"),       # RFC 1918
    ipaddress.ip_network("172.16.0.0/12"),    # RFC 1918
    ipaddress.ip_network("192.168.0.0/16"),   # RFC 1918
    ipaddress.ip_network("169.254.0.0/16"),   # link-local (incl. cloud metadata)
    ipaddress.ip_network("100.64.0.0/10"),    # CGNAT
    ipaddress.ip_network("198.18.0.0/15"),    # benchmarking
    ipaddress.ip_network("224.0.0.0/4"),      # multicast
    ipaddress.ip_network("240.0.0.0/4"),      # reserved
    ipaddress.ip_network("255.255.255.255/32"),
]

_BLOCKED_IPV6_NETWORKS: list[ipaddress.IPv6Network] = [
    ipaddress.ip_network("::/128"),           # unspecified
    ipaddress.ip_network("::1/128"),          # loopback
    ipaddress.ip_network("fc00::/7"),         # unique local
    ipaddress.ip_network("fe80::/10"),        # link-local
    ipaddress.ip_network("ff00::/8"),         # multicast
]


def _private_network_enabled() -> bool:
    """
    Whether private / loopback / reserved scan targets are permitted.

    Controlled by ``ALLOW_PRIVATE_NETWORK_SCANS`` and intended only for
    local development. When disabled, the public-security validation below
    applies unchanged and nothing is bypassed.
    """
    return settings.ALLOW_PRIVATE_NETWORK_SCANS


def is_address_allowed(address) -> bool:
    """
    Whether ``address`` is permitted as an outbound network target.

    Encapsulates the single blocked-range policy (loopback, RFC1918/private,
    link-local including cloud metadata, CGNAT, benchmarking, multicast,
    reserved, plus the explicit IPv6 equivalents) shared by every outbound
    target validator in the codebase. The dev-only
    ``ALLOW_PRIVATE_NETWORK_SCANS`` override bypasses the policy exactly as
    it does for nmap scan targets.
    """
    blocked = (
        _BLOCKED_IPV6_NETWORKS
        if address.version == 6
        else _BLOCKED_IPV4_NETWORKS
    )

    if any(address in network for network in blocked):
        if _private_network_enabled():
            logger.warning(
                "[DEV MODE] Private network target permitted "
                "(ALLOW_PRIVATE_NETWORK_SCANS=true): %s",
                address,
            )
            return True

        return False

    return True


def validate_resolved_address(address) -> str:
    """
    Validate an already-resolved destination IP address.

    Raises:
        ValidationError: When the address falls into a blocked range.

    Returns:
        The canonical string form of the address.
    """
    if not is_address_allowed(address):
        raise ValidationError(
            "Loopback, link-local, private or reserved addresses are not "
            "allowed as network targets."
        )

    return str(address)


def validate_ip_target(value: str) -> str:
    """
    Validate an IP literal as a safe scan target.

    Raises:
        ValidationError: When the value is not an IP address or falls into
            a blocked (loopback/private/link-local/...) range.

    In local development mode only (``ALLOW_PRIVATE_NETWORK_SCANS=true``),
    blocked ranges are explicitly permitted and logged. Public deployments
    keep the full security policy.
    """

    value = value.strip()

    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        raise ValidationError(
            f"'{value}' is not a valid IP address."
        )

    return validate_resolved_address(address)


def validate_domain_target(value: str) -> str:
    """
    Validate a hostname as a safe scan target.

    Only plain DNS hostnames are accepted; protocol prefixes, paths, and
    leading dashes (which nmap would interpret as flags) are rejected.

    Raises:
        ValidationError: When the value is not a well-formed hostname.
    """

    value = value.strip().lower()

    if len(value) > 253 or not _HOSTNAME_RE.fullmatch(value):
        raise ValidationError(
            f"'{value}' is not a valid hostname."
        )

    return value


def validate_scan_target(value: str | None) -> str | None:
    """
    Validate an IP literal or hostname scan target.

    Returns the trimmed value, or ``None`` when the input is falsy. Raises
    ``ValidationError`` for malformed or blocked targets.
    """

    if not value:
        return None

    value = value.strip()

    try:
        ipaddress.ip_address(value)
    except ValueError:
        return validate_domain_target(value)

    return validate_ip_target(value)


def resolve_host_ips(host: str) -> list:
    """
    Resolve a hostname to its IP addresses via the system resolver.

    Raises:
        ValidationError: When the hostname cannot be resolved to any address.

    Returns:
        A de-duplicated list of :class:`ipaddress` address objects (IPv4 and
        IPv6 are both returned when the resolver reports them).
    """
    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise ValidationError(f"Could not resolve host '{host}'.")

    addresses: list = []
    seen: set = set()

    for info in infos:
        raw = info[4][0]

        try:
            address = ipaddress.ip_address(raw)
        except ValueError:
            continue

        if address not in seen:
            seen.add(address)
            addresses.append(address)

    if not addresses:
        raise ValidationError(f"Could not resolve host '{host}'.")

    return addresses


def resolve_ssl_connection_target(host: str) -> tuple[str, str | None]:
    """
    Resolve and validate a TLS connection target (SSRF guard).

    Accepts an IP literal or a DNS hostname. A hostname is resolved exactly
    once here; the caller MUST connect to the returned validated IP address
    (presenting ``host`` as the TLS SNI server name) rather than
    re-resolving the name, which closes the simple DNS-rebinding gap between
    validation and connection.

    Raises:
        ValidationError: When ``host`` is a protected address, or when a
            hostname resolves only to protected addresses.

    Returns:
        A ``(connect_address, sni_hostname)`` pair: the validated IP address
        to connect to, and the hostname to present as the TLS SNI server
        name. ``sni_hostname`` is ``None`` for IP-literal targets (no SNI is
        sent).
    """
    host = host.strip().rstrip(".").lower()

    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        for candidate in resolve_host_ips(host):
            if is_address_allowed(candidate):
                return str(candidate), host

        raise ValidationError(
            f"'{host}' resolves only to loopback, link-local, private or "
            "reserved addresses; refusing to connect."
        )

    return validate_resolved_address(address), None
