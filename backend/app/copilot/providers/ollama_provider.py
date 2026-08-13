import requests

from app.core.config import settings
from app.logger import logger
from app.copilot.base import BaseCopilotProvider, CopilotProviderError


class OllamaProvider(BaseCopilotProvider):
    """
    Local Ollama provider using the native `/api/chat` endpoint.
    """

    name = "ollama"

    def __init__(self) -> None:
        self.model = settings.OLLAMA_MODEL
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        context: dict | None = None,
    ) -> str:
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "stream": False,
                },
                timeout=settings.AI_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as error:
            logger.exception("[Copilot] Ollama request failed")
            raise CopilotProviderError(
                f"Ollama request failed: {error}"
            ) from error

        data = response.json()
        content = data.get("message", {}).get("content", "")

        if not content:
            raise CopilotProviderError(
                "Ollama returned an empty response."
            )

        return content.strip()
