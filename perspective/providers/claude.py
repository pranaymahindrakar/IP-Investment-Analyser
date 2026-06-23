"""Claude provider (for when you switch LLM_PROVIDER to 'claude').

Requires `pip install anthropic` and ANTHROPIC_API_KEY in secrets. Uses the
server-side web_search tool when use_search=True so it matches Gemini grounding.
"""

from __future__ import annotations

from .base import LLMProvider


class ClaudeProvider(LLMProvider):
    name = "claude"

    def __init__(self, api_key: str, model: str = "claude-opus-4-8"):
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def generate(self, prompt: str, system: str | None = None, use_search: bool = False) -> str:
        kwargs: dict = {
            "model": self._model,
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        if use_search:
            kwargs["tools"] = [{"type": "web_search_20260209", "name": "web_search"}]

        resp = self._client.messages.create(**kwargs)
        return "".join(
            block.text for block in resp.content if getattr(block, "type", None) == "text"
        ).strip()
