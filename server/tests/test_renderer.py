from __future__ import annotations

import io
import unittest
from datetime import datetime, timezone

from PIL import Image, ImageDraw

from content import NormalizedContent
from renderer.todo import OUTPUT_SIZE, TodoRenderer


def content(body: str) -> NormalizedContent:
    return NormalizedContent("todo", body, datetime(2026, 9, 1, tzinfo=timezone.utc))


class TodoRendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.renderer = TodoRenderer()

    def assert_layout_safe(self, body: str) -> None:
        layout = self.renderer.layout_text(body)
        font = self.renderer._font(layout.font_size)
        draw = ImageDraw.Draw(Image.new("1", (600, 800), color=1))
        self.assertLessEqual(layout.text_height, self.renderer.max_text_height)
        for line in layout.lines:
            self.assertLessEqual(draw.textlength(line, font=font), self.renderer.max_text_width)

    def test_bundled_font_supports_chinese(self) -> None:
        font = self.renderer._font(32)
        self.assertEqual(font.getname(), ("Noto Sans CJK SC", "Regular"))
        self.assertIsNotNone(font.getmask("测试成功").getbbox())

    def test_preserves_manual_newlines(self) -> None:
        layout = self.renderer.layout_text("第一行\nSecond line")
        self.assertEqual(layout.lines, ("第一行", "Second line"))

    def test_wraps_chinese_english_and_unbroken_text(self) -> None:
        samples = ["中文内容" * 80, "English words and numbers 12345 " * 30, "A" * 300]
        for sample in samples:
            with self.subTest(sample=sample[:10]):
                layout = self.renderer.layout_text(sample)
                self.assertGreater(len(layout.lines), 1)
                self.assert_layout_safe(sample)

    def test_300_chinese_characters_fit_without_truncation(self) -> None:
        body = "待" * 300
        layout = self.renderer.layout_text(body)
        self.assertFalse(layout.truncated)
        self.assert_layout_safe(body)

    def test_many_manual_lines_are_safely_truncated(self) -> None:
        body = "\n".join("行" for _ in range(160))
        layout = self.renderer.layout_text(body)
        self.assertTrue(layout.truncated)
        self.assertTrue(layout.lines[-1].endswith("…"))
        self.assert_layout_safe(body)

    def test_empty_content_renders_visible_empty_state(self) -> None:
        portrait = self.renderer.render_portrait(content(""))
        colors = portrait.getcolors(maxcolors=3)
        self.assertIsNotNone(colors)
        self.assertEqual({value for _, value in colors or []}, {0, 1})

    def test_output_is_strict_black_white_png_800_by_600(self) -> None:
        png = self.renderer.render(content("明天下午组会\n修改 PPT\n查两篇文献"))
        image = Image.open(io.BytesIO(png))
        self.assertEqual(image.format, "PNG")
        self.assertEqual(image.mode, "1")
        self.assertEqual(image.size, OUTPUT_SIZE)
        self.assertTrue(
            {value for _, value in image.getcolors(maxcolors=3) or []}.issubset({0, 1, 255})
        )

    def test_output_is_counterclockwise_prerotation_of_portrait(self) -> None:
        item = content("TOP\n测试")
        portrait = self.renderer.render_portrait(item)
        output = self.renderer.render_image(item)
        expected = portrait.transpose(Image.Transpose.ROTATE_90)
        self.assertEqual(portrait.size, (600, 800))
        self.assertEqual(output.size, (800, 600))
        self.assertEqual(output.tobytes(), expected.tobytes())


if __name__ == "__main__":
    unittest.main()
