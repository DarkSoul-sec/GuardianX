import requests

from app.core.config import settings
from app.logger import logger
from app.copilot.base import BaseCopilotProvider, CopilotProviderError


class GeminiProvider(BaseCopilotProvider):
    """
    Google Gemini provider using the generateContent REST API.
    """

    name = "gemini"

    def __init__(self) -> None:
        self.model = settings.GEMINI_MODEL
        self.base_url = settings.GEMINI_BASE_URL.rstrip("/")
        self.api_key = settings.GEMINI_API_KEY

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        context: dict | None = None,
    ) -> str:
        if not self.api_key:
            raise CopilotProviderError(
                "Gemini API key is not configured."
            )

        url = (
            f"{self.base_url}/v1beta/models/"
            f"{self.model}:generateContent"
        )

        try:
            response = requests.post(
                url,
                params={"key": self.api_key},
                json={
                    "systemInstruction": {
                        "parts": [{"text": system_prompt}],
                    },
                    "contents": [
                        {
                            "parts": [{"text": user_prompt}],
                        }
                    ],
                },
                timeout=settings.AI_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as error:
            logger.exception("[Copilot] Gemini request failed")
            raise CopilotProviderError(
                f"Gemini request failed: {error}"
            ) from error

        data = response.json()

        try:
            parts = (
                data["candidates"][0]["content"]["parts"]
            )
            content = "".join(
                part.get("text", "") for part in parts
            )
        except (KeyError, IndexError, TypeError):
            logger.exception("[Copilot] Unexpected Gemini response")
            raise CopilotProviderError(
                "Gemini returned an unexpected response."
            )

        if not content:
            raise CopilotProviderError(
                "Gemini returned an empty response."
            )

        return content.strip()
