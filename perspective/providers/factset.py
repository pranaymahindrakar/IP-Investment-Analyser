"""FactSet data adapter — placeholder.

The FactSet connector inside Claude.ai is NOT usable from a standalone hosted
app. To pull FactSet data here you need FactSet API credentials (username +
API key) and the relevant FactSet SDK, then implement `fetch()`. Until then this
adapter reports itself unavailable and the app falls back to yfinance.
"""

from __future__ import annotations

from typing import Any, Mapping


class FactSetAdapter:
    name = "factset"

    def __init__(self, secrets: Mapping[str, Any]):
        self._user = secrets.get("FACTSET_USERNAME")
        self._key = secrets.get("FACTSET_API_KEY")

    def available(self) -> bool:
        return bool(self._user and self._key)

    def fetch(self, ticker: str) -> dict[str, Any]:
        if not self.available():
            raise RuntimeError(
                "FactSet not configured. Add FACTSET_USERNAME and FACTSET_API_KEY to secrets."
            )
        # TODO: implement against FactSet's APIs once credentials exist.
        raise NotImplementedError("FactSet fetch not implemented yet.")
