"""Gemini provider using the google-genai SDK, with Google Search grounding."""

from __future__ import annotations

import time

from .base import LLMProvider

_TRANSIENT = ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "overloaded")


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        from google import genai  # imported lazily so the SDK is only needed for Gemini

        self._genai = genai
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate(self, prompt: str, system: str | None = None, use_search: bool = False) -> str:
        from google.genai import types

        config_kwargs: dict = {}
        if system:
            config_kwargs["system_instruction"] = system
        if use_search:
            config_kwargs["tools"] = [types.Tool(google_search=types.GoogleSearch())]

        config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

        last_err: Exception | None = None
        for attempt in range(4):  # ~0.8s, 1.6s, 3.2s backoff between tries
            try:
                resp = self._client.models.generate_content(
                    model=self._model, contents=prompt, config=config
                )
                return (resp.text or "").strip()
            except Exception as e:  # noqa: BLE001
                last_err = e
                if attempt < 3 and any(t in str(e) for t in _TRANSIENT):
                    time.sleep(0.8 * (2**attempt))
                    continue
                raise
        raise last_err  # pragma: no cover
