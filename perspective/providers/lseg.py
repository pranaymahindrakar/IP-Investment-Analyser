"""LSEG (Refinitiv) data adapter — placeholder.

The LSEG connector available inside Claude.ai is NOT usable from a standalone
hosted app. To pull LSEG data here you need a real LSEG Data Library / Workspace
licence + app key, then implement `fetch()` with the `lseg-data` SDK. Until then
this adapter reports itself unavailable and the app falls back to yfinance.
"""

from __future__ import annotations

from typing import Any, Mapping


class LSEGAdapter:
    name = "lseg"

    def __init__(self, secrets: Mapping[str, Any]):
        self._app_key = secrets.get("LSEG_APP_KEY")

    def available(self) -> bool:
        return bool(self._app_key)

    def fetch(self, ticker: str) -> dict[str, Any]:
        if not self.available():
            raise RuntimeError(
                "LSEG not configured. Add LSEG_APP_KEY to secrets and install `lseg-data`."
            )
        # TODO: implement with the lseg-data SDK once credentials exist.
        raise NotImplementedError("LSEG fetch not implemented yet.")
