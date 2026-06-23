"""LLM and data-feed providers, behind a common interface.

`get_llm(secrets)` returns the configured LLM provider so the rest of the app
never imports a vendor SDK directly — swapping Gemini for Claude is a config
change, not a code change.
"""

from __future__ import annotations

from typing import Any, Mapping

from .base import LLMProvider


def get_llm(secrets: Mapping[str, Any]) -> LLMProvider:
    provider = (secrets.get("LLM_PROVIDER") or "gemini").lower()

    if provider == "gemini":
        from .gemini import GeminiProvider

        key = secrets.get("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY is missing from secrets.")
        return GeminiProvider(api_key=key, model=secrets.get("GEMINI_MODEL") or "gemini-2.5-flash")

    if provider == "claude":
        from .claude import ClaudeProvider

        key = secrets.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY is missing from secrets.")
        return ClaudeProvider(api_key=key, model=secrets.get("CLAUDE_MODEL") or "claude-opus-4-8")

    raise RuntimeError(f"Unknown LLM_PROVIDER: {provider!r}")
