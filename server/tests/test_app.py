from __future__ import annotations

import io
import unittest

from fastapi.testclient import TestClient
from PIL import Image

from app import create_app
from config import Settings


class ByosApiTests(unittest.TestCase):
    def setUp(self) -> None:
        settings = Settings(
            device_id="AA:BB:CC:DD:EE:FF",
            api_key="test-only-key",
            public_base_url="https://byos.example.test",
            refresh_rate_seconds=300,
        )
        self.client = TestClient(create_app(settings))
        self.headers = {"ID": "aa-bb-cc-dd-ee-ff", "access-token": "test-only-key"}

    def test_health(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_display_accepts_correct_credentials(self) -> None:
        response = self.client.get("/api/display", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": 0,
                "image_url": "https://byos.example.test/screen/test.png",
                "filename": "test-screen.png",
                "refresh_rate": 300,
            },
        )

    def test_display_rejects_wrong_key(self) -> None:
        response = self.client.get(
            "/api/display",
            headers={"ID": "AA:BB:CC:DD:EE:FF", "access-token": "wrong"},
        )
        self.assertEqual(response.status_code, 401)

    def test_display_rejects_wrong_device_id(self) -> None:
        response = self.client.get(
            "/api/display",
            headers={"ID": "11:22:33:44:55:66", "access-token": "test-only-key"},
        )
        self.assertEqual(response.status_code, 401)

    def test_public_test_image_is_png_800_by_600(self) -> None:
        response = self.client.get("/screen/test.png")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "image/png")
        image = Image.open(io.BytesIO(response.content))
        self.assertEqual(image.format, "PNG")
        self.assertEqual(image.size, (800, 600))


if __name__ == "__main__":
    unittest.main()
