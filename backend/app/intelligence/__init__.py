"""
Threat Intelligence platform.

Transforms GuardianX from a pure vulnerability scanner into a threat
intelligence platform: analysts search IP addresses, domains, URLs and SHA256
hashes, and get a normalized, cached, risk-scored report backed by the
VirusTotal BYOAPI integration, plus persistent search history.

Layout:

- ``schemas.py``             - normalized report / history / response models
- ``models.py`` (app.models) - SQLAlchemy search-history persistence
- ``cache.py``               - 24-hour in-process report cache
- ``providers/virustotal.py``- VirusTotal normalization provider
- ``service.py``             - IOC detection + orchestration + history CRUD
- ``router.py``              - REST endpoints
"""
