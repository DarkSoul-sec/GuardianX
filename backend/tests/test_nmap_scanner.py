import tempfile
import xml.etree.ElementTree as ET
from unittest.mock import patch

from app.scanners.nmap import NmapParser
from app.scanners.nmap.scanner import (
    DEFAULT_NMAP_ARGS,
    NmapScanner,
    build_nmap_args,
    build_nmap_command,
)
from app.scanners.manager import ScannerManager


def _write_xml(hosts: list[ET.Element]) -> str:
    root = ET.Element("nmaprun")
    root.append(ET.Element("scaninfo"))
    for host in hosts:
        root.append(host)

    with tempfile.NamedTemporaryFile(
        suffix=".xml", delete=False, mode="w", encoding="utf-8"
    ) as handle:
        handle.write(
            ET.tostring(root, encoding="unicode")
        )
        return handle.name


def _host(
    ip: str,
    ports: list[tuple[int, str, str]],
    timedout: bool = False,
) -> ET.Element:
    host = ET.Element("host")
    if timedout:
        host.set("timedout", "true")
    address = ET.SubElement(host, "address")
    address.set("addr", ip)
    address.set("addrtype", "ipv4")
    ports_node = ET.SubElement(host, "ports")
    for portid, state, service in ports:
        port = ET.SubElement(ports_node, "port")
        port.set("portid", str(portid))
        port.set("protocol", "tcp")
        state_node = ET.SubElement(port, "state")
        state_node.set("state", state)
        if service:
            service_node = ET.SubElement(port, "service")
            service_node.set("name", service)
    return host


class TestNmapParserTimedOut:

    def test_counts_timed_out_hosts(self):
        xml = _write_xml(
            [
                _host("10.0.0.1", [(443, "open", "https")]),
                _host("10.0.0.2", [], timedout=True),
                _host("10.0.0.3", [], timedout=True),
            ]
        )
        assert NmapParser().count_timed_out_hosts(xml) == 2

    def test_counts_zero_when_no_timeouts(self):
        xml = _write_xml(
            [
                _host("10.0.0.1", [(80, "open", "http")]),
                _host("10.0.0.2", [(443, "closed", "")]),
            ]
        )
        assert NmapParser().count_timed_out_hosts(xml) == 0

    def test_parse_keeps_open_ports_from_healthy_host(self):
        xml = _write_xml(
            [
                _host(
                    "10.0.0.1",
                    [(443, "open", "https"), (80, "closed", ""), (22, "open", "ssh")],
                )
            ]
        )
        services = NmapParser().parse(xml)
        assert [s["port"] for s in services] == [443, 22]

    def test_parse_skips_timed_out_host(self):
        xml = _write_xml(
            [
                _host("10.0.0.1", [(443, "open", "https")]),
                _host("10.0.0.2", [], timedout=True),
            ]
        )
        services = NmapParser().parse(xml)
        assert [s["ip"] for s in services] == ["10.0.0.1"]

    def test_parse_is_ssl_flag(self):
        xml = _write_xml([_host("10.0.0.1", [(443, "open", "https")])])
        services = NmapParser().parse(xml)
        assert services[0]["is_ssl"] is True


class TestNmapDefaultArgs:

    def test_generous_host_timeout(self):
        args = DEFAULT_NMAP_ARGS
        assert "--host-timeout" in args
        value = args.split("--host-timeout")[1].split()[0]
        seconds = int(value.rstrip("s"))
        assert seconds >= 300

    def test_has_fast_timing_configuration(self):
        args = DEFAULT_NMAP_ARGS
        assert "-T4" in args
        assert "--min-rate" in args

    def test_keeps_version_and_connect_scan(self):
        args = DEFAULT_NMAP_ARGS
        assert "-sT" in args
        assert "-sV" in args


class TestBuildNmapArgs:

    def test_standard_uses_default_args(self):
        assert build_nmap_args("standard") == DEFAULT_NMAP_ARGS

    def test_full_appends_full_port_range(self):
        args = build_nmap_args("full")
        assert args.startswith(DEFAULT_NMAP_ARGS)
        assert "-p 1-65535" in args

    def test_standard_has_no_port_restriction(self):
        assert "-p " not in build_nmap_args("standard")

    def test_unknown_profile_falls_back_to_standard(self):
        assert build_nmap_args("unknown") == DEFAULT_NMAP_ARGS


class TestBuildNmapCommand:

    def test_none_arguments_add_no_flags(self):
        assert build_nmap_command("10.0.0.1", None) == [
            "nmap", "-oX", "-", "10.0.0.1",
        ]

    def test_empty_string_arguments_add_no_flags(self):
        assert build_nmap_command("10.0.0.1", "") == [
            "nmap", "-oX", "-", "10.0.0.1",
        ]

    def test_supplied_arguments_are_appended(self):
        command = build_nmap_command("10.0.0.1", "-sT -p 80,443")
        assert command == [
            "nmap", "-oX", "-", "10.0.0.1", "-sT", "-p", "80,443",
        ]


class _FakeProcess:

    returncode = 0

    def communicate(self):
        return (
            b'<nmaprun><scaninfo/></nmaprun>',
            b"",
        )


class TestNmapScanInvocation:

    def _run_scan(self, target, arguments):
        with patch(
            "app.scanners.nmap.scanner.subprocess.Popen",
            return_value=_FakeProcess(),
        ) as mock_popen:
            NmapScanner().scan(target, arguments=arguments)
        return mock_popen.call_args.args[0]

    def test_scan_with_none_arguments_runs_plain_nmap_command(self):
        command = self._run_scan("10.0.0.1", arguments=None)
        assert command == ["nmap", "-oX", "-", "10.0.0.1"]

    def test_scan_with_empty_arguments_runs_plain_nmap_command(self):
        command = self._run_scan("10.0.0.1", arguments="")
        assert command == ["nmap", "-oX", "-", "10.0.0.1"]

    def test_scan_with_supplied_arguments_runs_full_command(self):
        command = self._run_scan("10.0.0.1", arguments="-sT -p 80,443")
        assert command == [
            "nmap", "-oX", "-", "10.0.0.1", "-sT", "-p", "80,443",
        ]


class TestScannerManagerInvocation:

    def _run_scan(self, target, arguments):
        with patch(
            "app.scanners.nmap.scanner.subprocess.Popen",
            return_value=_FakeProcess(),
        ) as mock_popen:
            ScannerManager().run(
                scanner="nmap",
                target=target,
                arguments=arguments,
            )
        return mock_popen.call_args.args[0]

    def test_run_nmap_without_arguments_uses_plain_command(self):
        command = self._run_scan("10.0.0.1", None)
        assert command == ["nmap", "-oX", "-", "10.0.0.1"]

    def test_run_nmap_with_arguments_uses_full_command(self):
        command = self._run_scan("10.0.0.1", "-sT -p 80,443")
        assert command == [
            "nmap", "-oX", "-", "10.0.0.1", "-sT", "-p", "80,443",
        ]
