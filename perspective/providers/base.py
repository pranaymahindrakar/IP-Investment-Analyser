"""Common interface every LLM provider implements."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    name: str = "llm"

    @abstractmethod
    def generate(self, prompt: str, system: str | None = None, use_search: bool = False) -> str:
        """Return a text completion.

        Args:
            prompt: the user/content prompt.
            system: optional system instruction.
            use_search: if True, enable the provider's web-search/grounding so the
                answer can reflect recent, real-world information.
        """
        raise NotImplementedError
