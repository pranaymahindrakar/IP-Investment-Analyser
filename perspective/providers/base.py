"""Common interface every LLM provider implements."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any


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

    def generate_json(self, prompt: str, system: str | None = None) -> dict[str, Any]:
        """Return a parsed JSON object. Default: parse the text completion.

        Providers with a native JSON mode (e.g. Gemini) should override this.
        """
        return parse_json(self.generate(prompt, system=system, use_search=False))


def parse_json(text: str) -> dict[str, Any]:
    """Tolerant JSON parse: strips ``` fences and any prose around the object."""
    t = (text or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\n?", "", t)
        t = re.sub(r"\n?```$", "", t).strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", t, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise
