"""
Provider selection and registry.

Providers are selected by configuration, never hardcoded in call sites.
"""

from app.core.config import settings
from app.copilot.base import BaseCopilotProvider
from app.copilot.providers.gemini_provider import GeminiProvider
from app.copilot.providers.ollama_provider import OllamaProvider
from app.copilot.providers.openai_provider import OpenAIProvider
from app.copilot.rules import RulesProvider

SUPPORTED_PROVIDERS = (
    "openai",
    "gemini",
    "ollama",
    "rules",
)

PROVIDER_REGISTRY = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "ollama": OllamaProvider,
    "rules": RulesProvider,
}


def resolve_provider_name() -> str:
    """
    Pick the active provider:
    explicit config first, then any configured API key, then built-in rules.
    """

    explicit = (settings.AI_PROVIDER or "").strip().lower()

    if explicit in SUPPORTED_PROVIDERS:
        return explicit

    if settings.OPENAI_API_KEY:
        return "openai"

    if settings.GEMINI_API_KEY:
        return "gemini"

    return "rules"


def get_copilot_provider() -> BaseCopilotProvider:
    name = resolve_provider_name()
    return PROVIDER_REGISTRY[name]()


def get_copilot_provider_info() -> dict:
    provider = get_copilot_provider()

    return {
        "provider": provider.name,
        "model": provider.model,
        "built_in": isinstance(provider, RulesProvider),
        "available": list(SUPPORTED_PROVIDERS),
    }
