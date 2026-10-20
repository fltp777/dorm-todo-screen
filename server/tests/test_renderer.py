from __future__ import annotations

import io
import unittest
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw

from content import NormalizedContent
from renderer.flow_layout import FLOW, item_lines, line_box_height, line_step, paragraph_height, wrapped_lines_height
from renderer.todo import (
    OUTPUT_SIZE,
    REMINDER_TITLE_BODY_GAP,
    TRIGRAM_LINES,
    YIJING_GLYPH_WIDTH_SCALE,
    TodoRenderError,
    TodoRenderer,
)
from yijing_catalog import YIJING_PAGES, YijingPage


REGULAR_TODO = "修改论文结果部分\n整理氨基酸分析图表\n回复导师消息\n打印实验材料"
STRESS_TODO = "\n".join((
    "修改论文结果部分", "整理氨基酸分析图表", "回复导师消息", "打印实验材料",
    "检查统计脚本输出", "整理补充材料", "联系同门确认时间", "准备明天开会内容",
))
REMINDERS = "钥匙\n电脑\n校园卡\n水杯\n充电器\n雨伞"


def content(todo: str = REGULAR_TODO, *, reminder: str = REMINDERS, position: int = 0) -> NormalizedContent:
    return NormalizedContent("todo", todo, datetime(2026, 10, 2, 13, 30, tzinfo=timezone.utc), reminder, position)


def longest_full_page() -> YijingPage:
    return max((page for page in YIJING_PAGES if page.is_full_hexagram), key=lambda page: sum(map(len, page.paragraphs)))


class TodoRendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.renderer = TodoRenderer()

    def test_bundled_font_supports_chinese_and_traditional_text(self) -> None:
        font = self.renderer._font(32)
        self.assertEqual(font.getname(), ("Noto Sans CJK SC", "Regular"))
        self.assertIsNotNone(font.getmask("測試乾坤彖曰").getbbox())

    def test_flow_geometry_keeps_only_the_approved_static_boundaries(self) -> None:
        self.assertEqual(FLOW.vertical_divider_x, 392)
        self.assertEqual(FLOW.footer_top_y, 746)
        self.assertEqual(FLOW.left_text_width, 340)
        source = (self.renderer.__class__.__module__)
        self.assertEqual(source, "renderer.todo")
        renderer_source = __import__(source, fromlist=["__file__"]).__file__
        self.assertNotIn("todo_divider_y", Path(renderer_source).read_text(encoding="utf-8"))

    def test_regular_and_long_todo_have_dynamic_dividers(self) -> None:
        regular = self.renderer.layout_flow(content())
        long_todo = self.renderer.layout_flow(content(STRESS_TODO))
        self.assertLess(regular.divider_y, long_todo.divider_y)
        self.assertNotEqual(regular.divider_y, 373)
        self.assertLess(long_todo.divider_y, FLOW.safe_content_bottom_y)
        self.assertGreaterEqual(regular.todo.size, long_todo.todo.size)

    def test_all_left_blocks_share_one_font_size_and_only_weight_differs(self) -> None:
        layout = self.renderer.layout_flow(content())
        self.assertEqual(layout.todo_title_font_size, layout.left_font_size)
        self.assertEqual(layout.todo_body_font_size, layout.left_font_size)
        self.assertEqual(layout.yijing_heading_font_size, layout.left_font_size)
        self.assertEqual(layout.yijing_body_font_size, layout.left_font_size)
        self.assertEqual(layout.todo.size, layout.left_font_size)
        self.assertEqual(layout.yijing_header.size, layout.left_font_size)
        self.assertEqual(layout.yijing_body.size, layout.left_font_size)

    def test_flow_block_budget_does_not_reserve_leading_after_final_line(self) -> None:
        font = self.renderer._font(30)
        ink = line_box_height(font, 30)
        step = line_step(font, 30)
        self.assertEqual(wrapped_lines_height(1, font, 30), ink)
        self.assertEqual(wrapped_lines_height(3, font, 30), ink + 2 * step)
        self.assertEqual(paragraph_height([["甲", "乙"], ["丙"]], font, 30), ink + 2 * step + 3)

    def test_reminder_body_uses_actual_title_bbox_gap_without_shrinking(self) -> None:
        item = content()
        layout = self.renderer.layout_flow(item)
        image = Image.new("1", (600, 800), color=1)
        draw = ImageDraw.Draw(image)
        reminder_lines = item_lines(
            draw, self.renderer._items_from_text(item.daily_reminder_text, "暂无提醒"),
            self.renderer._font(layout.reminder.size), FLOW.right_text_width,
        )
        title_bbox = self.renderer._reminder_title_bbox(draw)
        first_bbox = draw.textbbox(
            (FLOW.right_text_x, layout.reminder_start_y), reminder_lines[0], font=self.renderer._font(layout.reminder.size)
        )
        last_y = layout.reminder_start_y + (len(reminder_lines) - 1) * line_step(self.renderer._font(layout.reminder.size), layout.reminder.size)
        last_bbox = draw.textbbox((FLOW.right_text_x, last_y), reminder_lines[-1], font=self.renderer._font(layout.reminder.size))
        self.assertEqual(layout.reminder.size, 50)
        self.assertGreaterEqual(first_bbox[1] - title_bbox[3], REMINDER_TITLE_BODY_GAP)
        self.assertLessEqual(last_bbox[3], FLOW.footer_top_y - 16)

    def test_yijing_glyph_width_scale_preserves_break_and_vertical_geometry(self) -> None:
        size = 30
        current_hex = self.renderer._glyph_width(size, 6, width_scale=1.0)
        self.assertEqual(current_hex, 22)
        self.assertEqual(self.renderer._glyph_width(size, 6, width_scale=1.15), 25)
        self.assertEqual(self.renderer._glyph_width(size, 6, width_scale=1.20), 26)
        self.assertEqual(self.renderer._glyph_width(size, 6, width_scale=1.25), 28)
        self.assertEqual(self.renderer._yin_gap(size, 3), 4)
        self.assertEqual(max(1, size // 16), 1)
        self.assertEqual(max(1, size // 15), 2)

        image = Image.new("1", (100, 80), color=1)
        draw = ImageDraw.Draw(image)
        x, y = 10, 10
        width = self.renderer._glyph_width(size, 3, width_scale=YIJING_GLYPH_WIDTH_SCALE)
        self.assertEqual(
            self.renderer._draw_yang_yin_symbol(draw, x, y, size, TRIGRAM_LINES["離"]), x + width
        )
        glyph_height = 3 + 2 * 2
        top = y + max(1, (size - glyph_height) // 2)
        yin_y = top + 2 + 1
        self.assertEqual(image.getpixel((x, top)), 0)
        self.assertEqual(image.getpixel((x + width // 2, yin_y)), 1)

    def test_wider_glyph_candidates_do_not_exceed_current_heading_width(self) -> None:
        image = Image.new("1", (600, 800), color=1)
        draw = ImageDraw.Draw(image)
        samples = ((YIJING_PAGES[0], 30), (YIJING_PAGES[1], 40), (longest_full_page(), 24))
        for page, size in samples:
            for width_scale in (1.0, 1.15, 1.20, 1.25):
                with self.subTest(page=page.label, size=size, width_scale=width_scale):
                    self.assertLessEqual(
                        self.renderer._header_width(draw, page, self.renderer._font(size), width_scale=width_scale),
                        FLOW.left_text_width,
                    )

    def test_yijing_pages_fit_as_full_width_paragraphs_without_label_columns(self) -> None:
        full = self.renderer.layout_flow(content(position=0))
        line = self.renderer.layout_flow(content(position=1))
        self.assertEqual(full.yijing_body.size, full.left_font_size)
        self.assertEqual(line.yijing_body.size, line.left_font_size)
        self.assertGreaterEqual(line.left_font_size, 22)
        page = YIJING_PAGES[0]
        self.assertTrue(any(paragraph.startswith("【卦辭】") for paragraph in page.paragraphs))
        self.assertTrue(any(paragraph.startswith("【彖曰】") for paragraph in page.paragraphs))
        self.assertTrue(any(paragraph.startswith("【大象】") for paragraph in page.paragraphs))

    def test_long_yijing_shrinks_body_without_moving_same_todo_divider(self) -> None:
        regular = self.renderer.layout_flow(content(position=0))
        stressed_page = longest_full_page()
        stressed = self.renderer.layout_flow(content(position=stressed_page.position), stressed_page)
        # Body shrinking is preferred. If the actual classical page remains too
        # long at 22 px, todo is then allowed to shrink, never to grow.
        self.assertLessEqual(stressed.divider_y, regular.divider_y)
        self.assertLessEqual(stressed.left_font_size, regular.left_font_size)
        self.assertEqual(stressed.todo.size, stressed.yijing_body.size)

    def test_double_pressure_stays_inside_left_column_and_footer(self) -> None:
        page = longest_full_page()
        layout = self.renderer.layout_flow(content(STRESS_TODO, position=page.position), page)
        portrait = self.renderer.render_portrait(content(STRESS_TODO, position=page.position), 64, page=page)
        self.assertEqual(portrait.mode, "1")
        self.assertEqual(portrait.size, (600, 800))
        self.assertLess(layout.divider_y, FLOW.safe_content_bottom_y)
        self.assertLessEqual(layout.yijing_body_y, FLOW.safe_content_bottom_y)
        self.assertEqual(portrait.getpixel((FLOW.left_padding, layout.divider_y)), 0)
        self.assertEqual(portrait.getpixel((FLOW.vertical_divider_x, 100)), 0)
        self.assertEqual(portrait.getpixel((0, FLOW.footer_top_y)), 0)

    def test_extreme_content_fails_safe_without_truncation(self) -> None:
        item = content("\n".join("行" for _ in range(160)))
        layout = self.renderer.layout_flow(item)
        self.assertTrue(layout.overflow_detected)
        with self.assertRaises(TodoRenderError):
            self.renderer.render_portrait(item, 64)

    def test_yijing_position_is_read_only_during_render(self) -> None:
        item = content(position=7)
        self.renderer.render_portrait(item, 64)
        self.assertEqual(item.yijing_position, 7)

    def test_header_geometry_supports_non_qian_trigrams(self) -> None:
        kun_full = YIJING_PAGES[8]
        layout = self.renderer.layout_flow(content(position=kun_full.position), kun_full)
        self.assertGreaterEqual(layout.yijing_header.size, 22)
        self.assertEqual(self.renderer.render_portrait(content(position=kun_full.position), 64, page=kun_full).mode, "1")

    def test_footer_time_is_request_time_in_china_standard_time(self) -> None:
        item = content()
        one = self.renderer.render_portrait(item, 64, refresh_at=datetime(2026, 10, 2, 13, 30, tzinfo=timezone.utc))
        two = self.renderer.render_portrait(item, 64, refresh_at=datetime(2026, 10, 2, 13, 31, tzinfo=timezone.utc))
        self.assertNotEqual(one.crop((0, FLOW.footer_top_y, FLOW.vertical_divider_x, 800)).tobytes(), two.crop((0, FLOW.footer_top_y, FLOW.vertical_divider_x, 800)).tobytes())

    def test_footer_text_uses_exact_low_battery_thresholds(self) -> None:
        self.assertEqual(self.renderer.battery_footer_text(63), "电量 63%")
        self.assertEqual(self.renderer.battery_footer_text(20), "电量 20%")
        self.assertEqual(self.renderer.battery_footer_text(19), "电量 19% · 请充电")
        self.assertEqual(self.renderer.battery_footer_text(10), "电量 10% · 请充电")
        self.assertEqual(self.renderer.battery_footer_text(9), "电量 9% · 充电！")
        self.assertIsNone(self.renderer.battery_footer_text(None))

    def test_output_is_strict_black_white_png_800_by_600(self) -> None:
        png = self.renderer.render(content(), 63, refresh_at=datetime(2026, 10, 2, 13, 30, tzinfo=timezone.utc))
        image = Image.open(io.BytesIO(png))
        self.assertEqual(image.format, "PNG")
        self.assertEqual(image.mode, "1")
        self.assertEqual(image.size, OUTPUT_SIZE)

    def test_output_is_counterclockwise_prerotation_of_portrait(self) -> None:
        item = content(position=1)
        refresh_at = datetime(2026, 10, 2, 13, 30, tzinfo=timezone.utc)
        portrait = self.renderer.render_portrait(item, 63, refresh_at=refresh_at)
        output = self.renderer.render_image(item, 63, refresh_at=refresh_at)
        self.assertEqual(output.tobytes(), portrait.transpose(Image.Transpose.ROTATE_90).tobytes())


if __name__ == "__main__":
    unittest.main()
