"""Tests for scan-target validation (SSRF / internal-scan protection)."""

import ipaddress
import socket
import unittest
from unittest import mock

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.core.network import (
    is_address_allowed,
    resolve_host_ips,
    resolve_ssl_connection_target,
    validate_domain_target,
    validate_ip_target,
    validate_resolved_address,
    validate_scan_target,
)


class ScanTargetValidationTests(unittest.TestCase):
    def test_public_ipv4_is_allowed(self) -> None:
        self.assertEqual(validate_ip_target("8.8.8.8"), "8.8.8.8")
        self.assertEqual(validate_scan_target(" 1.1.1.1 "), "1.1.1.1")

    def test_documentation_range_remains_allowed(self) -> None:
        self.assertEqual(validate_ip_target("192.0.2.10"), "192.0.2.10")

    def test_loopback_is_blocked(self) -> None:
        with self.assertRaises(ValidationError):
            validate_ip_target("127.0.0.1")

    def test_cloud_metadata_is_blocked(self) -> None:
        with self.assertRaises(ValidationError):
            validate_ip_target("169.254.169.254")

    def test_private_ranges_are_blocked(self) -> None:
        for ip in ("10.0.0.1", "172.16.0.1", "192.168.1.1"):
            with self.assertRaises(ValidationError):
                validate_ip_target(ip)

    def test_cgnat_range_is_blocked(self) -> None:
        with self.assertRaises(ValidationError):
            validate_ip_target("100.64.0.1")

    def test_multicast_is_blocked(self) -> None:
        with self.assertRaises(ValidationError):
            validate_ip_target("224.0.0.1")

    def test_ipv6_loopback_is_blocked(self) -> None:
        with self.assertRaises(ValidationError):
            validate_ip_target("::1")

    def test_invalid_ip_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            validate_ip_target("999.999.999.999")

    def test_valid_hostname_is_allowed(self) -> None:
        self.assertEqual(
            validate_domain_target("scanme.example.com"),
            "scanme.example.com",
        )

    def test_hostname_with_scheme_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            validate_domain_target("http://example.com")

    def test_hostname_with_leading_dash_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            validate_domain_target("-example.com")

    def test_scan_target_none_passes_through(self) -> None:
        self.assertIsNone(validate_scan_target(None))
        self.assertIsNone(validate_scan_target(""))

    def test_scan_target_routes_to_ip_validation(self) -> None:
        with self.assertRaises(ValidationError):
            validate_scan_target("127.0.0.1")


class ResolveHostIpsTests(unittest.TestCase):
    def test_returns_deduplicated_addresses(self) -> None:
        ai_v4 = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))
        ai_v6 = (
            socket.AF_INET6,
            socket.SOCK_STREAM,
            6,
            "",
            ("2606:2800:220:1:248:1893:25c8:1946", 0, 0, 0),
        )
        with mock.patch(
            "app.core.network.socket.getaddrinfo",
            return_value=[ai_v4, ai_v4, ai_v6],
        ):
            addresses = resolve_host_ips("example.com")

        self.assertEqual(len(addresses), 2)
        self.assertIn(ipaddress.ip_address("93.184.216.34"), addresses)
        self.assertIn(ipaddress.ip_address("2606:2800:220:1:248:1893:25c8:1946"), addresses)

    def test_unresolvable_host_raises(self) -> None:
        with mock.patch(
            "app.core.network.socket.getaddrinfo",
            side_effect=socket.gaierror(-2, "Name or service not known"),
        ):
            with self.assertRaises(ValidationError):
                resolve_host_ips("nxdomain.invalid")


class ResolveSslConnectionTargetTests(unittest.TestCase):
    @staticmethod
    def _addrinfo(ip: str) -> list:
        family = socket.AF_INET6 if ":" in ip else socket.AF_INET
        sockaddr = (ip, 0, 0, 0) if family == socket.AF_INET6 else (ip, 0)
        return [(family, socket.SOCK_STREAM, 6, "", sockaddr)]

    def test_public_ipv4_literal_is_allowed(self) -> None:
        self.assertEqual(
            resolve_ssl_connection_target("8.8.8.8"),
            ("8.8.8.8", None),
        )

    def test_public_ipv6_literal_is_allowed(self) -> None:
        self.assertEqual(
            resolve_ssl_connection_target("2606:4700:4700::1111"),
            ("2606:4700:4700::1111", None),
        )

    def test_loopback_ipv4_is_blocked(self) -> None:
        with self.assertRaises(ValidationError):
            resolve_ssl_connection_target("127.0.0.1")

    def test_rfc1918_addresses_are_blocked(self) -> None:
        for ip in ("10.0.0.1", "172.16.0.1", "192.168.1.1"):
            with self.assertRaises(ValidationError):
                resolve_ssl_connection_target(ip)

    def test_link_local_and_metadata_are_blocked(self) -> None:
        for ip in ("169.254.169.254", "169.254.10.1"):
            with self.assertRaises(ValidationError):
                resolve_ssl_connection_target(ip)

    def test_ipv6_loopback_is_blocked(self) -> None:
        with self.assertRaises(ValidationError):
            resolve_ssl_connection_target("::1")

    def test_ipv6_unique_local_is_blocked(self) -> None:
        with self.assertRaises(ValidationError):
            resolve_ssl_connection_target("fc00::1")

    def test_ipv6_link_local_is_blocked(self) -> None:
        with self.assertRaises(ValidationError):
            resolve_ssl_connection_target("fe80::1")

    def test_public_hostname_is_allowed(self) -> None:
        with mock.patch(
            "app.core.network.socket.getaddrinfo",
            return_value=self._addrinfo("93.184.216.34"),
        ):
            self.assertEqual(
                resolve_ssl_connection_target("example.com"),
                ("93.184.216.34", "example.com"),
            )

    def test_hostname_resolving_to_loopback_is_blocked(self) -> None:
        with mock.patch(
            "app.core.network.socket.getaddrinfo",
            return_value=self._addrinfo("127.0.0.1"),
        ):
            with self.assertRaises(ValidationError):
                resolve_ssl_connection_target("localhost")

    def test_hostname_resolving_to_private_is_blocked(self) -> None:
        with mock.patch(
            "app.core.network.socket.getaddrinfo",
            return_value=self._addrinfo("10.0.0.7"),
        ):
            with self.assertRaises(ValidationError):
                resolve_ssl_connection_target("internal.corp.local")

    def test_hostname_resolving_to_metadata_is_blocked(self) -> None:
        with mock.patch(
            "app.core.network.socket.getaddrinfo",
            return_value=self._addrinfo("169.254.169.254"),
        ):
            with self.assertRaises(ValidationError):
                resolve_ssl_connection_target("metadata.internal")

    def test_mixed_resolution_uses_first_public_address(self) -> None:
        public = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))
        private = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 0))
        with mock.patch(
            "app.core.network.socket.getaddrinfo",
            return_value=[public, private],
        ):
            self.assertEqual(
                resolve_ssl_connection_target("example.com"),
                ("93.184.216.34", "example.com"),
            )


class ValidateResolvedAddressTests(unittest.TestCase):
    def test_public_address_is_allowed(self) -> None:
        self.assertEqual(
            validate_resolved_address(ipaddress.ip_address("8.8.8.8")),
            "8.8.8.8",
        )

    def test_loopback_address_is_blocked(self) -> None:
        with self.assertRaises(ValidationError):
            validate_resolved_address(ipaddress.ip_address("127.0.0.1"))

    def test_private_address_is_blocked(self) -> None:
        with self.assertRaises(ValidationError):
            validate_resolved_address(ipaddress.ip_address("192.168.1.1"))

    def test_is_address_allowed_matches_policy(self) -> None:
        self.assertTrue(is_address_allowed(ipaddress.ip_address("8.8.8.8")))
        self.assertFalse(is_address_allowed(ipaddress.ip_address("10.0.0.1")))
        self.assertFalse(is_address_allowed(ipaddress.ip_address("169.254.169.254")))
        self.assertFalse(is_address_allowed(ipaddress.ip_address("::1")))


class DevModePermitsPrivateScansTests(unittest.TestCase):
    """Local development mode bypasses private/loopback/reserved blocks."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._patcher = mock.patch.object(
            settings,
            "ALLOW_PRIVATE_NETWORK_SCANS",
            True,
        )
        cls._patcher.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._patcher.stop()

    def test_loopback_is_permitted_in_dev_mode(self) -> None:
        self.assertEqual(validate_ip_target("127.0.0.1"), "127.0.0.1")
        self.assertEqual(validate_ip_target("::1"), "::1")

    def test_private_ranges_are_permitted_in_dev_mode(self) -> None:
        for ip in ("10.0.0.1", "192.168.1.1", "172.16.0.1"):
            self.assertEqual(validate_ip_target(ip), ip)

    def test_link_local_is_permitted_in_dev_mode(self) -> None:
        self.assertEqual(
            validate_ip_target("169.254.169.254"),
            "169.254.169.254",
        )

    def test_localhost_hostname_is_permitted(self) -> None:
        self.assertEqual(validate_scan_target("localhost"), "localhost")

    def test_dev_mode_still_rejects_invalid_ip(self) -> None:
        with self.assertRaises(ValidationError):
            validate_ip_target("999.999.999.999")

    def test_public_ip_still_valid_in_dev_mode(self) -> None:
        self.assertEqual(validate_ip_target("8.8.8.8"), "8.8.8.8")


if __name__ == "__main__":
    unittest.main()
