from typing import Any


def filter_cves(
    vulnerabilities: list[dict[str, Any]],
    normalized_product: str,
) -> list[dict[str, Any]]:
    """
    Filter NVD vulnerabilities to only those that apply to the
    scanned product.

    A vulnerability is considered relevant when the normalized
    product name appears in either the vendor or product portion
    of a vulnerable CPE.
    """

    normalized_product = normalized_product.lower().strip()

    matches: list[dict[str, Any]] = []

    for vuln in vulnerabilities:

        configurations = (
            vuln.get("cve", {})
            .get("configurations", [])
        )

        matched = False

        for configuration in configurations:

            for node in configuration.get("nodes", []):

                for cpe_match in node.get("cpeMatch", []):

                    if not cpe_match.get("vulnerable", False):
                        continue

                    criteria = cpe_match.get("criteria", "")

                    if not criteria.startswith("cpe:2.3:"):
                        continue

                    parts = criteria.split(":")

                    if len(parts) < 6:
                        continue

                    vendor = parts[3].lower()
                    product = parts[4].lower()

                    if (
                        normalized_product in vendor
                        or normalized_product in product
                    ):
                        matched = True
                        break

                if matched:
                    break

            if matched:
                break

        if matched:
            matches.append(vuln)

    return matches
