"""Environment-backed configuration for the single Nook device."""

from __future__ import annotations

import os
from dataclasses import dataclass


def normalize_device_id(value: str) -> str:
    """Compare MAC-like IDs independent of separators and letter case."""
    return "".join(character for character in value.lower() if character.isalnum())


@dataclass(frozen=True)
class Settings:
    device_id: str
    api_key: str
    public_base_url: str | None = None
    refresh_rate_seconds: int = 300

    @classmethod
    def from_env(cls) -> "Settings":
        public_base_url = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/") or None

        try:
            refresh_rate = int(os.getenv("REFRESH_RATE_SECONDS", "300"))
        except ValueError:
            refresh_rate = 300

        return cls(
            device_id=os.getenv("NOOK_DEVICE_ID", "").strip(),
            api_key=os.getenv("NOOK_API_KEY", "").strip(),
            public_base_url=public_base_url,
            refresh_rate_seconds=max(60, refresh_rate),
        )

    @property
    def is_configured(self) -> bool:
        return bool(normalize_device_id(self.device_id) and self.api_key)
