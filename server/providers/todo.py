"""Read the single todo screen row from Supabase REST."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from content import NormalizedContent, normalize_body
from yijing_catalog import yijing_page_at


class TodoProviderError(RuntimeError):
    """A safe, credential-free provider failure."""


class TodoProvider:
    def __init__(
        self,
        supabase_url: str,
        secret_key: str,
        *,
        client: httpx.Client | None = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._url = f"{supabase_url.strip().rstrip('/')}/rest/v1/screen_state"
        self._secret_key = secret_key
        self._client = client
        self._timeout_seconds = timeout_seconds

    def load(self) -> NormalizedContent:
        if not self._secret_key.startswith("sb_secret_") or not self._url.startswith("https://"):
            raise TodoProviderError("Todo provider is not configured")

        try:
            if self._client is not None:
                response = self._request(self._client)
            else:
                with httpx.Client(timeout=self._timeout_seconds) as client:
                    response = self._request(client)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            raise TodoProviderError("Todo provider request failed") from None

        return self._normalize_payload(payload)

    def _request(self, client: httpx.Client) -> httpx.Response:
        # New sb_secret_ keys are API keys, not JWTs: send only the apikey header.
        return client.get(
            self._url,
            params={"id": "eq.main", "select": "text,daily_reminder_text,yijing_position,updated_at"},
            headers={"apikey": self._secret_key, "Accept": "application/json"},
        )

    @staticmethod
    def _normalize_payload(payload: Any) -> NormalizedContent:
        if not isinstance(payload, list) or len(payload) != 1 or not isinstance(payload[0], dict):
            raise TodoProviderError("Todo provider returned an unexpected row count")

        row = payload[0]
        if set(("text", "daily_reminder_text", "yijing_position", "updated_at")) - row.keys():
            raise TodoProviderError("Todo provider returned an incomplete row")

        body = row["text"]
        daily_reminder_text = row["daily_reminder_text"]
        yijing_position = row["yijing_position"]
        updated_at = row["updated_at"]
        if (
            not isinstance(body, str)
            or len(body) > 300
            or not isinstance(daily_reminder_text, str)
            or len(daily_reminder_text) > 300
            or isinstance(yijing_position, bool)
            or not isinstance(yijing_position, int)
            or yijing_position < 0
            or not isinstance(updated_at, str)
        ):
            raise TodoProviderError("Todo provider returned invalid field values")

        try:
            parsed = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        except ValueError:
            raise TodoProviderError("Todo provider returned an invalid timestamp") from None
        if parsed.tzinfo is None:
            raise TodoProviderError("Todo provider returned a timestamp without timezone")
        try:
            yijing_page_at(yijing_position)
        except ValueError:
            raise TodoProviderError("Todo provider returned an invalid Yijing position") from None

        return NormalizedContent(
            type="todo",
            body=normalize_body(body),
            updated_at=parsed.astimezone(timezone.utc),
            daily_reminder_text=normalize_body(daily_reminder_text),
            yijing_position=yijing_position,
        )
