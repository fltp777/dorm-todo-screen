from __future__ import annotations

import hmac
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from cache import ArtifactCache, ScreenArtifact
from content import NormalizedContent, display_version, refresh_state
from display_service import DisplayService, DisplayUnavailable, StaleContentVersion
from security.signed_url import SignedImageURL


def item(second: int, body: str = "todo") -> NormalizedContent:
    return NormalizedContent("todo", body, datetime(2026, 9, 1, 0, 0, second, tzinfo=timezone.utc))


class MutableProvider:
    def __init__(self, content: NormalizedContent) -> None:
        self.content = content
        self.fail = False
        self.calls = 0

    def load(self) -> NormalizedContent:
        self.calls += 1
        if self.fail:
            raise RuntimeError("provider failed")
        return self.content


class CountingRenderer:
    def __init__(self) -> None:
        self.calls = 0
        self.fail = False

    def render(self, content: NormalizedContent, battery_percent: int | None = None, *, refresh_at=None) -> bytes:
        self.calls += 1
        if self.fail:
            raise RuntimeError("renderer failed")
        return f"png:{content.body}:{battery_percent}:{refresh_state(refresh_at)}".encode()


class SignedImageURLTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = 1_000
        self.signer = SignedImageURL("test-signing-secret-value-that-is-long", 900, clock=lambda: self.now)
        self.version = "0123456789abcdefabcd"

    def query(self, battery: str = "63", refresh: str = "12345") -> dict[str, str]:
        parsed = parse_qs(urlparse(self.signer.signed_path(self.version, battery, refresh)).query)
        return {key: values[0] for key, values in parsed.items()}

    def test_canonical_format_and_valid_signature(self) -> None:
        query = self.query()
        self.assertEqual(
            self.signer.canonical_message(self.version, "63", "12345", 1900),
            b"GET\n/screen/current.png\nv=0123456789abcdefabcd\nb=63\nr=12345\nexp=1900",
        )
        self.assertTrue(self.signer.verify(query["v"], query["b"], query["r"], query["exp"], query["sig"]))

    def test_rejects_signature_expiry_and_state_tampering(self) -> None:
        query = self.query()
        self.assertFalse(self.signer.verify(query["v"], query["b"], query["r"], query["exp"], "wrong"))
        self.assertFalse(self.signer.verify(query["v"], "62", query["r"], query["exp"], query["sig"]))
        self.assertFalse(self.signer.verify(query["v"], query["b"], "12346", query["exp"], query["sig"]))
        self.assertFalse(self.signer.verify("f" * 20, query["b"], query["r"], query["exp"], query["sig"]))

    def test_rejects_missing_invalid_and_expired_fields(self) -> None:
        query = self.query()
        self.assertFalse(self.signer.verify(None, query["b"], query["r"], query["exp"], query["sig"]))
        self.assertFalse(self.signer.verify(query["v"], None, query["r"], query["exp"], query["sig"]))
        self.assertFalse(self.signer.verify(query["v"], query["b"], None, query["exp"], query["sig"]))
        self.assertFalse(self.signer.verify(query["v"], "101", query["r"], query["exp"], query["sig"]))
        self.assertFalse(self.signer.verify(query["v"], query["b"], "invalid", query["exp"], query["sig"]))
        self.now = 1901
        self.assertFalse(self.signer.verify(query["v"], query["b"], query["r"], query["exp"], query["sig"]))

    def test_verification_uses_compare_digest(self) -> None:
        query = self.query()
        with patch("security.signed_url.hmac.compare_digest", wraps=hmac.compare_digest) as compared:
            self.assertTrue(self.signer.verify(query["v"], query["b"], query["r"], query["exp"], query["sig"]))
            compared.assert_called_once()


class ArtifactCacheTests(unittest.TestCase):
    def test_retains_only_two_most_recent_versions(self) -> None:
        cache = ArtifactCache(max_versions=2)
        for version in ("a" * 20, "b" * 20, "c" * 20):
            cache.put(ScreenArtifact(version, version.encode()))
        self.assertEqual(len(cache), 2)
        self.assertIsNone(cache.get("a" * 20))
        self.assertEqual(cache.latest().version, "c" * 20)


class DisplayServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = MutableProvider(item(1, "first"))
        self.renderer = CountingRenderer()
        self.cache = ArtifactCache(max_versions=2)
        self.refresh_at = datetime(2026, 10, 2, 13, 30, tzinfo=timezone.utc)
        self.service = DisplayService(self.provider, self.renderer, self.cache, clock=lambda: self.refresh_at)

    def test_same_content_battery_and_refresh_minute_does_not_render_twice(self) -> None:
        first = self.service.current(63)
        second = self.service.current(63)
        self.assertEqual(first, second)
        self.assertEqual(self.renderer.calls, 1)

    def test_refresh_minute_participates_in_version_and_cache_stays_bounded(self) -> None:
        first = self.service.current(63)
        self.refresh_at += timedelta(minutes=1)
        second = self.service.current(63)
        self.refresh_at += timedelta(minutes=1)
        third = self.service.current(63)
        self.assertNotEqual(first.version, second.version)
        self.assertNotEqual(second.version, third.version)
        self.assertEqual(self.renderer.calls, 3)
        self.assertEqual(len(self.cache), 2)

    def test_provider_or_renderer_failure_returns_latest_exact_artifact(self) -> None:
        expected = self.service.current(63)
        self.provider.fail = True
        self.assertEqual(self.service.current(62), expected)
        self.provider.fail = False
        self.provider.content = item(2, "new")
        self.renderer.fail = True
        self.assertEqual(self.service.current(63), expected)

    def test_failure_without_cache_is_unavailable(self) -> None:
        self.provider.fail = True
        with self.assertRaises(DisplayUnavailable):
            self.service.current(63)

    def test_cache_miss_rebuilds_only_matching_content_battery_and_refresh(self) -> None:
        expected = self.service.current(63)
        self.cache.clear()
        rebuilt = self.service.for_version(expected.version, 63, expected.refresh_state)
        self.assertEqual(rebuilt.version, expected.version)
        with self.assertRaises(StaleContentVersion):
            self.service.for_version(expected.version, 62, expected.refresh_state)
        with self.assertRaises(StaleContentVersion):
            self.service.for_version(expected.version, 63, "999999")

    def test_content_and_battery_changes_create_new_artifacts(self) -> None:
        first = self.service.current(63)
        second = self.service.current(62)
        self.provider.content = item(2, "changed")
        third = self.service.current(62)
        self.assertNotEqual(first.version, second.version)
        self.assertNotEqual(second.version, third.version)
        self.assertEqual(third.version, display_version(self.provider.content, 62, self.refresh_at))


if __name__ == "__main__":
    unittest.main()
