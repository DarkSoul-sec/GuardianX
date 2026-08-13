from abc import ABC, abstractmethod
from collections.abc import Iterator


class CopilotProviderError(RuntimeError):
    """
    Raised when an AI provider fails to produce an answer.
    """


class BaseCopilotProvider(ABC):
    """
    Base interface for every AI provider.

    Providers are interchangeable: swap the configured provider to change
    where answers come from without touching the rest of the system.
    """

    name: str = "base"
    model: str | None = None

    @abstractmethod
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        context: dict | None = None,
    ) -> str:
        """
        Produce an answer for the given prompts.

        `context` carries the structured, database-backed estate data.
        LLM providers only need the prompts (context is already embedded
        in the user prompt); deterministic providers may read it directly.
        """
        pass

    def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        context: dict | None = None,
    ) -> Iterator[str]:
        """
        Yield the answer incrementally.

        The default implementation streams the full completion as a single
        chunk so every provider supports streaming; providers that natively
        stream should override this to emit tokens as they arrive.
        """
        yield self.complete(
            system_prompt,
            user_prompt,
            context,
        )
