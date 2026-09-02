from __future__ import annotations

import io
import unittest
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
from PIL import Image

from app import create_app
from cache import ArtifactCache
from config import Settings
from content import NormalizedContent
from renderer.todo import TodoRenderer
from security.signed_url import SignedImageURL


class MutableProvider:
    def __init__(self) -> None:
        self.content = NormalizedContent(
            "todo",
            "明天下午组会\n修改 PPT",
            datetime(2026, 9, 1, tzinfo=timezone.utc),
        )
        self.fail = False
        self.calls = 0

    def load(self) -> NormalizedContent:
        self.calls += 1
        if self.fail:
            raise RuntimeError("provider failure")
        return self.content


class PngRenderer:
    def __init__(self) -> None:
        self.calls = 0
        self.fail = False

    def render(self, content: NormalizedContent) -> bytes:
        self.calls += 1
        if self.fail:
            raise RuntimeError("renderer failure")
        image = Image.new("1", (800, 600), color=1)
        image.putpixel((0, 0), 0 if content.body else 255)
        output = io.BytesIO()
        image.save(output, format="PNG")
        return output.getvalue()


class ByosApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = Settings(
            device_id="AA:BB:CC:DD:EE:FF",
            api_key="test-only-nook-key",
            public_base_url="https://byos.example.test",
            refresh_rate_seconds=300,
            supabase_url="https://project.example.supabase.co",
            supabase_secret_key="sb_secret_test-only-placeholder",
            screen_signing_secret="test-signing-secret-value-that-is-long",
            screen_url_ttl_seconds=900,
        )
        self.provider = MutableProvider()
        self.renderer = PngRenderer()
        self.cache = ArtifactCache(max_versions=2)
        self.signer = SignedImageURL(
            self.settings.screen_signing_secret,
            900,
            clock=lambda: 1_000,
        )
        self.client = TestClient(
            create_app(
                self.settings,
                provider=self.provider,
                renderer=self.renderer,
                cache=self.cache,
                signer=self.signer,
            )
        )
        self.headers = {"ID": "aa-bb-cc-dd-ee-ff", "access-token": "test-only-nook-key"}

    def display(self):
        return self.client.get("/api/display", headers=self.headers)

    def test_health(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_display_returns_dynamic_signed_url_and_refresh_rate(self) -> None:
        response = self.display()
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        parsed = urlparse(payload["image_url"])
        query = parse_qs(parsed.query)
        self.assertEqual(parsed.path, "/screen/current.png")
        self.assertEqual(set(query), {"v", "exp", "sig"})
        self.assertEqual(payload["refresh_rate"], 300)
        self.assertTrue(payload["filename"].startswith("todo-"))
        serialized = response.text
        self.assertNotIn(self.provider.content.body, serialized)
        self.assertNotIn(self.settings.supabase_secret_key, serialized)
        self.assertNotIn(self.settings.screen_signing_secret, serialized)

    def test_display_rejects_wrong_key(self) -> None:
        response = self.client.get(
            "/api/display",
            headers={"ID": "AA:BB:CC:DD:EE:FF", "access-token": "wrong"},
        )
        self.assertEqual(response.status_code, 401)

    def test_display_rejects_wrong_device_id(self) -> None:
        response = self.client.get(
            "/api/display",
            headers={"ID": "11:22:33:44:55:66", "access-token": "test-only-nook-key"},
        )
        self.assertEqual(response.status_code, 401)

    def test_display_without_dynamic_configuration_returns_503(self) -> None:
        unconfigured = Settings(device_id="AA", api_key="key")
        client = TestClient(create_app(unconfigured, provider=self.provider, renderer=self.renderer))
        response = client.get("/api/display", headers={"ID": "AA", "access-token": "key"})
        self.assertEqual(response.status_code, 503)

    def test_public_stage_2b1_image_remains_png_800_by_600(self) -> None:
        response = self.client.get("/screen/test.png")
        self.assertEqual(response.status_code, 200)
        image = Image.open(io.BytesIO(response.content))
        self.assertEqual(response.headers["content-type"], "image/png")
        self.assertEqual(image.size, (800, 600))

    def test_signed_current_image_success(self) -> None:
        image_url = self.display().json()["image_url"]
        parsed = urlparse(image_url)
        response = self.client.get(f"{parsed.path}?{parsed.query}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "image/png")
        self.assertEqual(response.headers["cache-control"], "private, no-store")
        self.assertEqual(Image.open(io.BytesIO(response.content)).size, (800, 600))

    def test_real_renderer_integrates_with_signed_image_endpoint(self) -> None:
        client = TestClient(
            create_app(
                self.settings,
                provider=self.provider,
                renderer=TodoRenderer(),
                cache=ArtifactCache(max_versions=2),
                signer=self.signer,
            )
        )
        display = client.get("/api/display", headers=self.headers)
        parsed = urlparse(display.json()["image_url"])
        response = client.get(f"{parsed.path}?{parsed.query}")
        image = Image.open(io.BytesIO(response.content))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(image.mode, "1")
        self.assertEqual(image.size, (800, 600))

    def test_invalid_signed_image_urls_are_rejected(self) -> None:
        image_url = self.display().json()["image_url"]
        parsed = urlparse(image_url)
        query = {key: values[0] for key, values in parse_qs(parsed.query).items()}
        cases = [
            "/screen/current.png",
            f"/screen/current.png?v={query['v']}&exp={query['exp']}&sig=wrong",
            f"/screen/current.png?v={'f' * 20}&exp={query['exp']}&sig={query['sig']}",
            f"/screen/current.png?v={query['v']}&exp=invalid&sig={query['sig']}",
        ]
        for path in cases:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 403)

    def test_cache_miss_rebuilds_matching_version(self) -> None:
        image_url = self.display().json()["image_url"]
        self.cache.clear()
        calls_before = self.provider.calls
        parsed = urlparse(image_url)
        response = self.client.get(f"{parsed.path}?{parsed.query}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.provider.calls, calls_before + 1)

    def test_stale_version_is_rejected_after_cache_miss(self) -> None:
        image_url = self.display().json()["image_url"]
        self.cache.clear()
        self.provider.content = NormalizedContent(
            "todo",
            "new content",
            datetime(2026, 9, 1, 0, 0, 1, tzinfo=timezone.utc),
        )
        parsed = urlparse(image_url)
        self.assertEqual(self.client.get(f"{parsed.path}?{parsed.query}").status_code, 410)

    def test_provider_failure_with_cache_returns_last_success(self) -> None:
        first = self.display().json()
        self.provider.fail = True
        second = self.display().json()
        self.assertEqual(first["filename"], second["filename"])

    def test_provider_failure_without_cache_returns_503(self) -> None:
        self.provider.fail = True
        self.assertEqual(self.display().status_code, 503)

    def test_renderer_failure_with_cache_returns_last_success(self) -> None:
        first = self.display().json()
        self.provider.content = NormalizedContent(
            "todo",
            "new content",
            datetime(2026, 9, 1, 0, 0, 1, tzinfo=timezone.utc),
        )
        self.renderer.fail = True
        second = self.display().json()
        self.assertEqual(first["filename"], second["filename"])

    def test_empty_text_creates_new_version_instead_of_fallback(self) -> None:
        first = self.display().json()
        self.provider.content = NormalizedContent(
            "todo",
            "",
            datetime(2026, 9, 1, 0, 0, 1, tzinfo=timezone.utc),
        )
        second = self.display().json()
        self.assertNotEqual(first["filename"], second["filename"])


if __name__ == "__main__":
    unittest.main()
