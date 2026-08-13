from typing import Any

from app.logger import logger
from app.services.product_normalizer import normalize_product
from app.services.cpe_builder import build_cpe
from app.services.cve_filter import filter_cves
from app.services.nvd_service import get_cves_by_cpe


def enrich_service(
    product: str | None,
    version: str | None,
) -> dict[str, Any]:
    """
    Build vulnerability intelligence for a scanned service.

    Steps:
        1. Normalize the product name.
        2. Build a CPE.
        3. Query the NVD API.
        4. Filter unrelated CVEs.
    """

    normalized_product = normalize_product(product)

    logger.info("[INTELLIGENCE] Product: %s", normalized_product)
    logger.info("[INTELLIGENCE] Version: %s", version)

    cpe = build_cpe(
        normalized_product,
        version,
    )

    logger.info("[INTELLIGENCE] CPE: %s", cpe)

    if not cpe:
        logger.warning(
            "[INTELLIGENCE] Skipping NVD lookup because the product/version does not produce a valid CPE 2.3 string.",
        )
        return {
            "product": normalized_product,
            "cpe": None,
            "cves": [],
            "count": 0,
        }

    vulnerabilities = get_cves_by_cpe(cpe)

    filtered = filter_cves(
        vulnerabilities=vulnerabilities,
        normalized_product=normalized_product or "",
    )

    return {
        "product": normalized_product,
        "cpe": cpe,
        "cves": filtered,
        "count": len(filtered),
    }
