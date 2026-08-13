"""
Threat Intelligence data providers.

Providers translate raw external feeds into the normalized
``ThreatIntelligenceReport`` schema. The VirusTotal provider is the reference
implementation; additional providers can be added without touching the service
or router layers.
"""
