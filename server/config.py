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
    supabase_url: str = ""
    supabase_secret_key: str = ""
    screen_signing_secret: str = ""
    screen_url_ttl_seconds: int = 900

    @classmethod
    def from_env(cls) -> "Settings":
        public_base_url = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/") or None

        try:
            refresh_rate = int(os.getenv("REFRESH_RATE_SECONDS", "300"))
        except ValueError:
            refresh_rate = 300

        try:
            screen_url_ttl = int(os.getenv("SCREEN_URL_TTL_SECONDS", "900"))
        except ValueError:
            screen_url_ttl = 900

        return cls(
            device_id=os.getenv("NOOK_DEVICE_ID", "").strip(),
            api_key=os.getenv("NOOK_API_KEY", "").strip(),
            public_base_url=public_base_url,
            refresh_rate_seconds=max(60, refresh_rate),
            supabase_url=os.getenv("SUPABASE_URL", "").strip().rstrip("/"),
            supabase_secret_key=os.getenv("SUPABASE_SECRET_KEY", "").strip(),
            screen_signing_secret=os.getenv("SCREEN_SIGNING_SECRET", "").strip(),
            screen_url_ttl_seconds=min(3600, max(60, screen_url_ttl)),
        )

    @property
    def is_configured(self) -> bool:
        return bool(normalize_device_id(self.device_id) and self.api_key)

    @property
    def content_is_configured(self) -> bool:
        return bool(
            self.supabase_url.startswith("https://")
            and self.supabase_secret_key.startswith("sb_secret_")
            and len(self.screen_signing_secret) >= 32
        )
