import xml.etree.ElementTree as ET


class NmapParser:

    def count_timed_out_hosts(
        self,
        xml_file: str,
    ) -> int:
        """Number of hosts that nmap abandoned due to --host-timeout.

        A timed-out host is discarded by nmap entirely (no <ports> block),
        so a non-zero value means the result set may be incomplete.
        """

        tree = ET.parse(xml_file)
        root = tree.getroot()

        return sum(
            1
            for host in root.findall("host")
            if host.attrib.get("timedout") == "true"
        )

    def parse(
        self,
        xml_file: str,
    ) -> list[dict]:

        tree = ET.parse(xml_file)
        root = tree.getroot()

        services = []

        for host in root.findall("host"):

            address = host.find("address")

            ip = (
                address.attrib.get("addr")
                if address is not None
                else None
            )

            ports = host.find("ports")

            if ports is None:
                continue

            for port in ports.findall("port"):

                state_node = port.find("state")

                if state_node is None:
                    continue

                if state_node.attrib.get("state") != "open":
                    continue

                service_node = port.find("service")

                services.append({

                    "ip": ip,

                    "port": int(
                        port.attrib["portid"]
                    ),

                    "protocol": port.attrib["protocol"],

                    "state": "open",

                    "service": (
                        service_node.attrib.get("name")
                        if service_node is not None
                        else None
                    ),

                    "product": (
                        service_node.attrib.get("product")
                        if service_node is not None
                        else None
                    ),

                    "version": (
                        service_node.attrib.get("version")
                        if service_node is not None
                        else None
                    ),

                    "cpe": (
                        service_node.findtext("cpe")
                        if service_node is not None
                        else None
                    ),

                    "is_ssl": (
                        int(port.attrib["portid"]) == 443
                    ),

                })

        return services
