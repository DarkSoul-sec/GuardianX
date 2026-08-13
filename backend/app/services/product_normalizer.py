from typing import Optional


PRODUCT_MAP = {
    "postgresql db": "postgresql",
    "postgresql": "postgresql",
    "postgres": "postgresql",

    "apache httpd": "apache",
    "apache http server": "apache",
    "apache": "apache",

    "microsoft iis": "iis",
    "iis": "iis",

    "nginx": "nginx",

    "uvicorn": "uvicorn",

    "mysql": "mysql",

    "redis": "redis",

    "mongodb": "mongodb",

    "openssh": "openssh",
}


def normalize_product(product: Optional[str]) -> Optional[str]:
    """
    Normalize Nmap product names into a consistent identifier.
    """

    if not product:
        return None

    product = product.lower().strip()

    return PRODUCT_MAP.get(product, product)
