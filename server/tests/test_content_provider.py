from __future__ import annotations

import unittest
from datetime import datetime, timezone

import httpx

from content import NormalizedContent, content_version, normalize_body
from providers.todo import TodoProvider, TodoProviderError


class ContentTests(unittest.TestCase):
    def test_normalizes_newlines_without_stripping(self) -> None:
        self.assertEqual(normalize_body("  第一行\r\n第二行\r"), "  第一行\n第二行\n")

    def test_version_is_stable_and_uses_updated_at(self) -> None:
        first = NormalizedContent("todo", "A", datetime(2026, 9, 1, tzinfo=timezone.utc))
        same_time = NormalizedContent("todo", "B", datetime(2026, 9, 1, tzinfo=timezone.utc))
        later = NormalizedContent("todo", "A", datetime(2026, 9, 1, 0, 0, 1, tzinfo=timezone.utc))
        self.assertEqual(content_version(first), content_version(same_time))
        self.assertNotEqual(content_version(first), content_version(later))
        self.assertRegex(content_version(first), r"^[0-9a-f]{20}$")

    def test_requires_timezone_aware_updated_at(self) -> None:
        with self.assertRaises(ValueError):
            NormalizedContent("todo", "text", datetime(2026, 9, 1))


class TodoProviderTests(unittest.TestCase):
    def provider_for(self, handler) -> TodoProvider:
        client = httpx.Client(transport=httpx.MockTransport(handler))
        self.addCleanup(client.close)
        return TodoProvider(
            "https://project.example.supabase.co/",
            "sb_secret_test-only-placeholder",
            client=client,
        )

    @staticmethod
    def valid_payload() -> list[dict[str, str]]:
        return [{"text": "第一行\r\n第二行", "updated_at": "2026-09-01T01:02:03.123456Z"}]

    def test_uses_exact_rest_query_and_secret_header(self) -> None:
        captured: dict[str, object] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured["url"] = str(request.url.copy_with(query=None))
            captured["id"] = request.url.params.get("id")
            captured["select"] = request.url.params.get("select")
            captured["apikey"] = request.headers.get("apikey")
            captured["authorization"] = request.headers.get("authorization")
            return httpx.Response(200, json=self.valid_payload())

        content = self.provider_for(handler).load()
        self.assertEqual(captured["url"], "https://project.example.supabase.co/rest/v1/screen_state")
        self.assertEqual(captured["id"], "eq.main")
        self.assertEqual(captured["select"], "text,updated_at")
        self.assertEqual(captured["apikey"], "sb_secret_test-only-placeholder")
        self.assertIsNone(captured["authorization"])
        self.assertEqual(content.type, "todo")
        self.assertEqual(content.body, "第一行\n第二行")
        self.assertEqual(content.updated_at.tzinfo, timezone.utc)

    def assert_payload_error(self, payload) -> None:
        provider = self.provider_for(lambda request: httpx.Response(200, json=payload))
        with self.assertRaises(TodoProviderError):
            provider.load()

    def test_rejects_no_rows(self) -> None:
        self.assert_payload_error([])

    def test_rejects_multiple_rows(self) -> None:
        self.assert_payload_error(self.valid_payload() * 2)

    def test_rejects_missing_fields(self) -> None:
        self.assert_payload_error([{"text": "only text"}])

    def test_rejects_invalid_timestamp(self) -> None:
        self.assert_payload_error([{"text": "text", "updated_at": "not-a-time"}])

    def test_rejects_timestamp_without_timezone(self) -> None:
        self.assert_payload_error([{"text": "text", "updated_at": "2026-09-01T01:02:03"}])

    def test_rejects_body_over_300_characters(self) -> None:
        self.assert_payload_error([{"text": "字" * 301, "updated_at": "2026-09-01T01:02:03Z"}])

    def test_wraps_timeout_without_leaking_request_details(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("simulated timeout", request=request)

        with self.assertRaisesRegex(TodoProviderError, "Todo provider request failed"):
            self.provider_for(handler).load()

    def test_wraps_non_success_response(self) -> None:
        provider = self.provider_for(lambda request: httpx.Response(503, text="internal detail"))
        with self.assertRaisesRegex(TodoProviderError, "Todo provider request failed"):
            provider.load()

    def test_rejects_unconfigured_or_non_secret_key(self) -> None:
        provider = TodoProvider("https://project.example.supabase.co", "sb_publishable_not-secret")
        with self.assertRaisesRegex(TodoProviderError, "not configured"):
            provider.load()


if __name__ == "__main__":
    unittest.main()
