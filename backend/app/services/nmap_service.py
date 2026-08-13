import subprocess
import xml.etree.ElementTree as ET


def run_nmap_scan(target: str) -> list[dict]:
    """
    Run an Nmap scan against the target and return
    structured port information.
    """

    command = [
        "nmap",
        "-sT",          # TCP Connect Scan
        "-Pn",          # Skip host discovery
        "-n",           # No DNS resolution
        "-sV",          # Service & Version Detection
        "--version-intensity",
        "7",            # Better version detection (1-9)
        "-oX",
        "-",
        target,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )

    root = ET.fromstring(result.stdout)

    findings = []

    for host in root.findall("host"):

        ports = host.find("ports")

        if ports is None:
            continue

        for port in ports.findall("port"):

            service = port.find("service")
            state = port.find("state")

            findings.append(
                {
                    "port": int(port.attrib["portid"]),
                    "protocol": port.attrib["protocol"],
                    "state": (
                        state.attrib.get("state")
                        if state is not None
                        else "unknown"
                    ),
                    "service": (
                        service.attrib.get("name")
                        if service is not None
                        else None
                    ),
                    "product": (
                        service.attrib.get("product")
                        if service is not None
                        else None
                    ),
                    "version": (
                        service.attrib.get("version")
                        if service is not None
                        else None
                    ),
                }
            )

    return findings
