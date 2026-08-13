import json
from collections.abc import Iterator

import requests

from app.core.config import settings
from app.logger import logger
from app.copilot.base import BaseCopilotProvider, CopilotProviderError


class OpenAIProvider(BaseCopilotProvider):
    """
    OpenAI-compatible chat completions provider.

    Uses the standard `/chat/completions` endpoint so it also works with
    any OpenAI-compatible gateway (Azure, local proxies, etc.).
    """

    name = "openai"

    def __init__(self) -> None:
        self.model = settings.OPENAI_MODEL
        self.base_url = settings.OPENAI_BASE_URL.rstrip("/")
        self.api_key = settings.OPENAI_API_KEY

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        context: dict | None = None,
    ) -> str:
        if not self.api_key:
            raise CopilotProviderError(
                "OpenAI API key is not configured."
            )

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.3,
                },
                timeout=settings.AI_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as error:
            logger.exception("[Copilot] OpenAI request failed")
            raise CopilotProviderError(
                f"OpenAI request failed: {error}"
            ) from error

        data = response.json()
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

        if not content:
            raise CopilotProviderError(
                "OpenAI returned an empty response."
            )

        return content.strip()

    def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        context: dict | None = None,
    ) -> Iterator[str]:
        if not self.api_key:
            raise CopilotProviderError(
                "OpenAI API key is not configured."
            )

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.3,
                    "stream": True,
                },
                timeout=settings.AI_TIMEOUT_SECONDS,
                stream=True,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as error:
            logger.exception("[Copilot] OpenAI streaming request failed")
            raise CopilotProviderError(
                f"OpenAI request failed: {error}"
            ) from error

        emitted = False

        for raw_line in response.iter_lines(decode_unicode=True):
            if not raw_line or not raw_line.startswith("data:"):
                continue

            payload = raw_line[5:].strip()

            if payload == "[DONE]":
                break

            try:
                chunk = json.loads(payload)
            except json.JSONDecodeError:
                continue

            delta = (
                chunk.get("choices", [{}])[0]
                .get("delta", {})
                .get("content", "")
            )

            if delta:
                emitted = True
                yield delta

        if not emitted:
            raise CopilotProviderError(
                "OpenAI returned an empty streaming response."
            )
