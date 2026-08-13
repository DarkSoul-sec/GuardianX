from typing import Optional

from app.services.product_normalizer import normalize_product


VENDOR_MAP = {
    "postgresql": "postgresql",
    "apache": "apache",
    "nginx": "nginx",
    "mysql": "mysql",
    "redis": "redis",
    "mongodb": "mongodb",
    "uvicorn": "encode",
    "iis": "microsoft",
    "openssh": "openbsd",
}


def build_cpe(product: Optional[str], version: Optional[str]) -> Optional[str]:
    """
    Build a CPE 2.3 string from a normalized product and version.

    When the service version is unknown, the CPE uses a wildcard version.
    The NVD client can still fall back to a keyword search for this product.
    """

    if not product:
        return None

    normalized = normalize_product(product)

    if not normalized:
        return None

    vendor = VENDOR_MAP.get(normalized, normalized)
    cleaned_version = (version or "").strip()

    if not cleaned_version:
        cleaned_version = "*"

    return (
        f"cpe:2.3:a:"
        f"{vendor}:"
        f"{normalized}:"
        f"{cleaned_version}:"
        f"*:*:*:*:*:*:*"
    )
