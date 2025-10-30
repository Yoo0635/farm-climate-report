"""SOLAPI SMS client wrapper used by the MVP.

Uses the official `solapi` Python SDK. No HTTP fallback is implemented.
Supports a local dry-run mode via `SOLAPI_DRY_RUN` for demos.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from solapi.model import RequestMessage

from solapi import SolapiMessageService


class SolapiError(RuntimeError):
    """Raised when SOLAPI responds with a non-success status."""


@dataclass
class SolapiConfig:
    """Configuration container for SOLAPI credentials."""

    access_key: str
    secret_key: str
    sender_number: str

    @classmethod
    def from_env(cls) -> "SolapiConfig":
        """Load credentials from environment variables."""
        return cls(
            access_key=os.environ.get("SOLAPI_ACCESS_KEY", ""),
            secret_key=os.environ.get("SOLAPI_SECRET_KEY", ""),
            sender_number=os.environ.get("SOLAPI_SENDER_NUMBER", ""),
        )

    def validate(self) -> None:
        """Ensure required fields are present."""
        missing = [
            name
            for name, value in (
                ("SOLAPI_ACCESS_KEY", self.access_key),
                ("SOLAPI_SECRET_KEY", self.secret_key),
                ("SOLAPI_SENDER_NUMBER", self.sender_number),
            )
            if not value
        ]
        if missing:
            raise ValueError(f"Missing SOLAPI credentials: {', '.join(missing)}")


class SolapiClient:
    """SOLAPI client using the official SDK."""

    def __init__(self, config: SolapiConfig | None = None) -> None:
        self._dry_run = os.environ.get("SOLAPI_DRY_RUN", "").lower() in {
            "1",
            "true",
            "yes",
        }
        self.config = config or SolapiConfig.from_env()
        if not self._dry_run:
            self.config.validate()

    def send_sms(self, recipient: str, text: str) -> dict[str, Any]:
        """Send a single SMS message using the official SDK when available."""
        if self._dry_run:
            return {
                "status": "dry_run",
                "to": recipient,
                "from": self.config.sender_number,
                "text_len": len(text),
            }

        # SDK path
        try:
            svc = SolapiMessageService(
                api_key=self.config.access_key, api_secret=self.config.secret_key
            )
            msg = RequestMessage(
                from_=self.config.sender_number, to=recipient, text=text
            )
            resp = svc.send(msg)
            # Normalize to dict for our API surface
            return {
                "status": "ok",
                "group_id": getattr(resp.group_info, "group_id", None),
                "registered_success": getattr(
                    resp.group_info.count, "registered_success", None
                ),
            }
        except Exception as exc:  # noqa: BLE001 - surface as service error
            raise SolapiError(str(exc)) from exc

    def close(self) -> None:
        """No persistent resources to close when using SDK."""
        return None


__all__ = ["SolapiClient", "SolapiError", "SolapiConfig"]
