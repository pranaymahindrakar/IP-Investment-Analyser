"""Gemini provider using the google-genai SDK, with Google Search grounding."""

from __future__ import annotations

import re
import time
from typing import Any

from .base import LLMProvider, parse_json

_TRANSIENT = ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "overloaded")


def _retry_delay(msg: str) -> float | None:
    """Honor the server's suggested wait (capped) on rate-limit errors."""
    m = re.search(r"retry in ([\d.]+)s", msg) or re.search(r"retryDelay'?:?\s*'?(\d+)s", msg)
    if m:
        try:
            return min(float(m.group(1)) + 0.5, 30.0)
        except ValueError:
            return None
    return None


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        from google import genai  # imported lazily so the SDK is only needed for Gemini

        self._genai = genai
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def _run(self, prompt: str, config) -> str:
        """Single call with backoff retry on transient overloads."""
        last_err: Exception | None = None
        for attempt in range(4):  # ~0.8s, 1.6s, 3.2s backoff between tries
            try:
                resp = self._client.models.generate_content(
                    model=self._model, contents=prompt, config=config
                )
                return (resp.text or "").strip()
            except Exception as e:  # noqa: BLE001
                last_err = e
                msg = str(e)
                if attempt < 3 and any(t in msg for t in _TRANSIENT):
                    time.sleep(_retry_delay(msg) or 0.8 * (2**attempt))
                    continue
                raise
        raise last_err  # pragma: no cover

    def generate(self, prompt: str, system: str | None = None, use_search: bool = False) -> str:
        from google.genai import types

        kwargs: dict = {}
        if system:
            kwargs["system_instruction"] = system
        if use_search:
            kwargs["tools"] = [types.Tool(google_search=types.GoogleSearch())]
        config = types.GenerateContentConfig(**kwargs) if kwargs else None
        return self._run(prompt, config)

    def generate_json(self, prompt: str, system: str | None = None) -> dict[str, Any]:
        from google.genai import types

        kwargs: dict = {"response_mime_type": "application/json"}
        if system:
            kwargs["system_instruction"] = system
        return parse_json(self._run(prompt, types.GenerateContentConfig(**kwargs)))
