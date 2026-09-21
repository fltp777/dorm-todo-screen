"""Short-lived HMAC-SHA256 URLs for unauthenticated image downloads."""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import time
from collections.abc import Callable
from urllib.parse import urlencode

from content import battery_percent_from_state

IMAGE_PATH = "/screen/current.png"
VERSION_PATTERN = re.compile(r"^[0-9a-f]{20}$")


class SignedImageURL:
    def __init__(
        self,
        secret: str,
        ttl_seconds: int = 900,
        *,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._secret = secret.encode("utf-8")
        self.ttl_seconds = ttl_seconds
        self._clock = clock

    @staticmethod
    def canonical_message(version: str, battery: str, expires_at: int) -> bytes:
        return f"GET\n{IMAGE_PATH}\nv={version}\nb={battery}\nexp={expires_at}".encode("utf-8")

    def _signature(self, version: str, battery: str, expires_at: int) -> str:
        digest = hmac.new(
            self._secret,
            self.canonical_message(version, battery, expires_at),
            hashlib.sha256,
        ).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    def signed_path(self, version: str, battery: str) -> str:
        try:
            battery_percent_from_state(battery)
        except ValueError:
            raise ValueError("Image signing is not configured") from None
        if not self._secret or not VERSION_PATTERN.fullmatch(version):
            raise ValueError("Image signing is not configured")
        expires_at = int(self._clock()) + self.ttl_seconds
        query = urlencode(
            {
                "v": version,
                "b": battery,
                "exp": str(expires_at),
                "sig": self._signature(version, battery, expires_at),
            }
        )
        return f"{IMAGE_PATH}?{query}"

    def verify(
        self,
        version: str | None,
        battery: str | None,
        expires_at: str | None,
        signature: str | None,
    ) -> bool:
        if not version or battery is None or not expires_at or not signature or not self._secret:
            return False
        if not VERSION_PATTERN.fullmatch(version):
            return False
        try:
            battery_percent_from_state(battery)
        except ValueError:
            return False
        try:
            parsed_expiry = int(expires_at)
        except ValueError:
            return False
        if parsed_expiry < int(self._clock()):
            return False
        expected = self._signature(version, battery, parsed_expiry)
        return hmac.compare_digest(signature, expected)
