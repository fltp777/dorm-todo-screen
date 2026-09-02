from __future__ import annotations

import hmac
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from cache import ArtifactCache, ScreenArtifact
from content import NormalizedContent, content_version
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

    def render(self, content: NormalizedContent) -> bytes:
        self.calls += 1
        if self.fail:
            raise RuntimeError("renderer failed")
        return f"png:{content.body}".encode()


class SignedImageURLTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = 1_000
        self.signer = SignedImageURL("test-signing-secret-value-that-is-long", 900, clock=lambda: self.now)
        self.version = "0123456789abcdefabcd"

    def query(self) -> dict[str, str]:
        parsed = parse_qs(urlparse(self.signer.signed_path(self.version)).query)
        return {key: values[0] for key, values in parsed.items()}

    def test_canonical_format_and_valid_signature(self) -> None:
        query = self.query()
        self.assertEqual(
            self.signer.canonical_message(self.version, 1900),
            b"GET\n/screen/current.png\nv=0123456789abcdefabcd\nexp=1900",
        )
        self.assertTrue(self.signer.verify(query["v"], query["exp"], query["sig"]))

    def test_rejects_signature_expiry_and_version_tampering(self) -> None:
        query = self.query()
        self.assertFalse(self.signer.verify(query["v"], query["exp"], "wrong"))
        self.assertFalse(self.signer.verify(query["v"], "1901", query["sig"]))
        self.assertFalse(self.signer.verify("f" * 20, query["exp"], query["sig"]))

    def test_rejects_missing_invalid_and_expired_fields(self) -> None:
        query = self.query()
        self.assertFalse(self.signer.verify(None, query["exp"], query["sig"]))
        self.assertFalse(self.signer.verify(query["v"], "invalid", query["sig"]))
        self.now = 1901
        self.assertFalse(self.signer.verify(query["v"], query["exp"], query["sig"]))

    def test_verification_uses_compare_digest(self) -> None:
        query = self.query()
        with patch("security.signed_url.hmac.compare_digest", wraps=hmac.compare_digest) as compared:
            self.assertTrue(self.signer.verify(query["v"], query["exp"], query["sig"]))
            compared.assert_called_once()


class ArtifactCacheTests(unittest.TestCase):
    def test_retains_only_two_most_recent_versions(self) -> None:
        cache = ArtifactCache(max_versions=2)
        first = ScreenArtifact("a" * 20, b"one")
        second = ScreenArtifact("b" * 20, b"two")
        third = ScreenArtifact("c" * 20, b"three")
        cache.put(first)
        cache.put(second)
        cache.put(third)
        self.assertEqual(len(cache), 2)
        self.assertIsNone(cache.get(first.version))
        self.assertEqual(cache.latest(), third)


class DisplayServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = MutableProvider(item(1, "first"))
        self.renderer = CountingRenderer()
        self.cache = ArtifactCache(max_versions=2)
        self.service = DisplayService(self.provider, self.renderer, self.cache)

    def test_same_version_does_not_render_twice(self) -> None:
        first = self.service.current()
        second = self.service.current()
        self.assertEqual(first, second)
        self.assertEqual(self.renderer.calls, 1)

    def test_new_version_rerenders_and_cache_stays_bounded(self) -> None:
        versions = []
        for second in (1, 2, 3):
            self.provider.content = item(second, str(second))
            versions.append(self.service.current().version)
        self.assertEqual(self.renderer.calls, 3)
        self.assertEqual(len(self.cache), 2)
        self.assertIsNone(self.cache.get(versions[0]))

    def test_provider_failure_returns_latest_cache(self) -> None:
        expected = self.service.current()
        self.provider.fail = True
        self.assertEqual(self.service.current(), expected)

    def test_provider_failure_without_cache_is_unavailable(self) -> None:
        self.provider.fail = True
        with self.assertRaises(DisplayUnavailable):
            self.service.current()

    def test_renderer_failure_returns_latest_cache(self) -> None:
        expected = self.service.current()
        self.provider.content = item(2, "new")
        self.renderer.fail = True
        self.assertEqual(self.service.current(), expected)

    def test_empty_text_is_rendered_as_new_content(self) -> None:
        old = self.service.current()
        self.provider.content = item(2, "")
        new = self.service.current()
        self.assertNotEqual(old.version, new.version)
        self.assertEqual(new.png, b"png:")

    def test_cache_miss_rebuilds_only_matching_current_version(self) -> None:
        expected_version = content_version(self.provider.content)
        artifact = self.service.for_version(expected_version)
        self.assertEqual(artifact.version, expected_version)
        with self.assertRaises(StaleContentVersion):
            self.service.for_version("f" * 20)


if __name__ == "__main__":
    unittest.main()
