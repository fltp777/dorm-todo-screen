"""Render the Stage 2C flow information screen for the verified Nook path."""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from content import NormalizedContent
from renderer.flow_layout import (
    FLOW,
    FittedText,
    draw_flow_dividers,
    fit_plain_items,
    item_lines,
    line_box_height,
    line_step,
    paragraph_height,
    paragraph_lines,
    text_width,
    wrapped_lines_height,
)
from yijing_catalog import YijingPage, yijing_page_at


LOGGER = logging.getLogger(__name__)
PORTRAIT_WIDTH = FLOW.portrait_width
PORTRAIT_HEIGHT = FLOW.portrait_height
OUTPUT_SIZE = (800, 600)
DEFAULT_FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "NotoSansCJKsc-Regular.otf"
REMINDER_TITLE_BODY_GAP = 16
# Final frozen production geometry, selected from the local width comparison.
YIJING_GLYPH_WIDTH_SCALE = 1.20
# China Standard Time is a stable UTC+8 offset; using it avoids an extra tzdata
# runtime dependency on Windows and Render while preserving the required clock.
SHANGHAI = timezone(timedelta(hours=8), name="Asia/Shanghai")

# Values are bottom-to-top, matching the lower then upper trigrams in the data.
TRIGRAM_LINES: dict[str, tuple[bool, bool, bool]] = {
    "乾": (True, True, True),
    "兌": (True, True, False),
    "離": (True, False, True),
    "震": (True, False, False),
    "巽": (False, True, True),
    "坎": (False, True, False),
    "艮": (False, False, True),
    "坤": (False, False, False),
}


class TodoRenderError(RuntimeError):
    """Raised when a safe screen artifact cannot be produced."""


@dataclass(frozen=True)
class FlowRenderLayout:
    left_font_size: int
    todo: FittedText
    reminder: FittedText
    yijing_header: FittedText
    yijing_body: FittedText
    todo_start_y: int
    divider_y: int
    yijing_header_y: int
    yijing_body_y: int
    reminder_start_y: int
    todo_visible_line_count: int
    total_left_height: int
    overflow_detected: bool

    @property
    def todo_title_font_size(self) -> int:
        return self.left_font_size

    @property
    def todo_body_font_size(self) -> int:
        return self.left_font_size

    @property
    def yijing_heading_font_size(self) -> int:
        return self.left_font_size

    @property
    def yijing_body_font_size(self) -> int:
        return self.left_font_size


@dataclass(frozen=True)
class _MeasuredFlow:
    todo_lines: list[str]
    body_groups: list[list[str]]
    todo_height: int
    header_height: int
    body_height: int
    divider_y: int
    header_y: int
    body_y: int
    bottom_y: int


class TodoRenderer:
    """A flow renderer; it never changes the stored Yijing position."""

    def __init__(self, font_path: Path = DEFAULT_FONT_PATH) -> None:
        self.font_path = Path(font_path)

    def _font(self, size: int) -> ImageFont.FreeTypeFont:
        if not self.font_path.is_file():
            raise TodoRenderError("Bundled CJK font is unavailable")
        try:
            return ImageFont.truetype(str(self.font_path), size=size)
        except OSError:
            raise TodoRenderError("Bundled CJK font could not be loaded") from None

    @staticmethod
    def _items_from_text(text: str, empty_text: str) -> tuple[str, ...]:
        items = tuple(line for line in text.split("\n") if line != "")
        return items or (empty_text,)

    @staticmethod
    def _ellipsize(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, width: int) -> str:
        clipped = text
        while clipped and text_width(draw, clipped + "…", font) > width:
            clipped = clipped[:-1]
        return clipped + "…"

    @staticmethod
    def _draw_bold(
        draw: ImageDraw.ImageDraw, position: tuple[int, int], text: str, font: ImageFont.FreeTypeFont
    ) -> None:
        draw.text(position, text, fill=0, font=font, stroke_width=1, stroke_fill=0)

    @staticmethod
    def _base_glyph_width(size: int, line_count: int) -> int:
        return max(16, round(size * (0.72 if line_count == 6 else 0.62)))

    @classmethod
    def _glyph_width(cls, size: int, line_count: int, *, width_scale: float = YIJING_GLYPH_WIDTH_SCALE) -> int:
        return round(cls._base_glyph_width(size, line_count) * width_scale)

    @classmethod
    def _yin_gap(cls, size: int, line_count: int) -> int:
        """Keep the central yin break stable while the overall glyph widens."""
        return max(3, cls._base_glyph_width(size, line_count) // 4)

    def _draw_yang_yin_symbol(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        size: int,
        lines_bottom_to_top: tuple[bool, ...],
        *,
        width_scale: float = YIJING_GLYPH_WIDTH_SCALE,
    ) -> int:
        """Draw a 1-bit hexagram/trigram when bundled text font lacks its glyph."""
        line_count = len(lines_bottom_to_top)
        width = self._glyph_width(size, line_count, width_scale=width_scale)
        stroke = max(1, size // 16)
        gap = max(1, size // 15)
        height = len(lines_bottom_to_top) * stroke + (len(lines_bottom_to_top) - 1) * gap
        top = y + max(1, (size - height) // 2)
        for index, solid in enumerate(reversed(lines_bottom_to_top)):
            line_y = top + index * (stroke + gap)
            if solid:
                draw.line((x, line_y, x + width, line_y), fill=0, width=stroke)
            else:
                half = max(2, (width - self._yin_gap(size, line_count)) // 2)
                draw.line((x, line_y, x + half, line_y), fill=0, width=stroke)
                draw.line((x + width - half, line_y, x + width, line_y), fill=0, width=stroke)
        return x + width

    @staticmethod
    def _hexagram_lines(page: YijingPage) -> tuple[bool, ...]:
        try:
            return TRIGRAM_LINES[page.lower_name] + TRIGRAM_LINES[page.upper_name]
        except KeyError as error:
            raise TodoRenderError("Formal Yijing trigram is unsupported") from error

    def _header_width(
        self, draw: ImageDraw.ImageDraw, page: YijingPage, font: ImageFont.FreeTypeFont,
        *, width_scale: float = YIJING_GLYPH_WIDTH_SCALE,
    ) -> int:
        cursor = self._glyph_width(font.size, 6, width_scale=width_scale) + text_width(draw, " ", font) + text_width(draw, page.name, font)
        if not page.is_full_hexagram:
            return cursor + text_width(draw, f"　{page.entry_position}", font)
        cursor += text_width(draw, f"　上{page.upper_name}", font) + self._glyph_width(font.size, 3, width_scale=width_scale)
        cursor += text_width(draw, f" 下{page.lower_name}", font) + self._glyph_width(font.size, 3, width_scale=width_scale)
        return cursor

    def _fit_header(self, draw: ImageDraw.ImageDraw, page: YijingPage) -> FittedText:
        for size in range(40, 25, -2):
            if self._header_width(draw, page, self._font(size)) <= FLOW.left_text_width:
                return FittedText(size, 1)
        return FittedText(26, 1, True)

    def _draw_yijing_header(
        self, draw: ImageDraw.ImageDraw, page: YijingPage, x: int, y: int, size: int
    ) -> int:
        font = self._font(size)
        cursor = self._draw_yang_yin_symbol(draw, x, y, size, self._hexagram_lines(page))
        draw.text((cursor, y), " ", fill=0, font=font)
        cursor += text_width(draw, " ", font)
        self._draw_bold(draw, (cursor, y), page.name, font)
        cursor += text_width(draw, page.name, font)
        if not page.is_full_hexagram:
            self._draw_bold(draw, (cursor, y), f"　{page.entry_position}", font)
        else:
            text = f"　上{page.upper_name}"
            self._draw_bold(draw, (cursor, y), text, font)
            cursor += text_width(draw, text, font)
            cursor = self._draw_yang_yin_symbol(draw, cursor, y, size, TRIGRAM_LINES[page.upper_name])
            text = f" 下{page.lower_name}"
            self._draw_bold(draw, (cursor, y), text, font)
            cursor += text_width(draw, text, font)
            self._draw_yang_yin_symbol(draw, cursor, y, size, TRIGRAM_LINES[page.lower_name])
        return y + line_box_height(font, size) + 5

    def _title_end_y(self, size: int) -> int:
        return FLOW.content_top_y + line_box_height(self._font(size), size) + 8

    def _reminder_title_bbox(self, draw: ImageDraw.ImageDraw) -> tuple[int, int, int, int]:
        return draw.textbbox(
            (FLOW.right_text_x, FLOW.content_top_y), "每日提醒", font=self._font(40), stroke_width=1
        )

    def _reminder_body_start_y(
        self, draw: ImageDraw.ImageDraw, font: ImageFont.FreeTypeFont, first_line: str
    ) -> int:
        title_bottom = self._reminder_title_bbox(draw)[3]
        first_line_top = draw.textbbox((FLOW.right_text_x, 0), first_line, font=font)[1]
        return title_bottom + REMINDER_TITLE_BODY_GAP - first_line_top

    def _fit_reminder(
        self, draw: ImageDraw.ImageDraw, reminder_items: tuple[str, ...]
    ) -> tuple[FittedText, int]:
        for size in range(50, 23, -2):
            font = self._font(size)
            lines = item_lines(draw, reminder_items, font, FLOW.right_text_width)
            body_start_y = self._reminder_body_start_y(draw, font, lines[0])
            if len(lines) * line_step(font, size) <= FLOW.footer_top_y - 16 - body_start_y:
                return FittedText(size, len(lines)), body_start_y
        font = self._font(24)
        lines = item_lines(draw, reminder_items, font, FLOW.right_text_width)
        return FittedText(24, len(lines), True), self._reminder_body_start_y(draw, font, lines[0])

    def _measure(
        self,
        draw: ImageDraw.ImageDraw,
        todo_items: tuple[str, ...],
        page: YijingPage,
        left_size: int,
        *,
        visible_todo_lines: int | None = None,
    ) -> _MeasuredFlow:
        left_font = self._font(left_size)
        todo_font = left_font
        body_font = left_font
        todo_lines = item_lines(draw, todo_items, todo_font, FLOW.left_text_width)
        if visible_todo_lines is not None:
            todo_lines = todo_lines[:visible_todo_lines]
        groups = paragraph_lines(draw, page.paragraphs, body_font, FLOW.left_text_width)
        todo_height = wrapped_lines_height(len(todo_lines), todo_font, left_size)
        divider_y = self._title_end_y(left_size) + todo_height + FLOW.divider_before_gap
        header_y = divider_y + 1 + FLOW.divider_after_gap
        header_height = line_box_height(left_font, left_size) + 5
        body_y = header_y + header_height
        body_height = paragraph_height(groups, body_font, left_size)
        return _MeasuredFlow(
            todo_lines, groups, todo_height, header_height, body_height,
            divider_y, header_y, body_y, body_y + body_height,
        )

    def layout_flow(self, content: NormalizedContent, page: YijingPage | None = None) -> FlowRenderLayout:
        """Find one largest font size that fits every left-column block together."""
        scratch = Image.new("1", (PORTRAIT_WIDTH, PORTRAIT_HEIGHT), color=1)
        draw = ImageDraw.Draw(scratch)
        page = page or yijing_page_at(content.yijing_position)
        todo_items = self._items_from_text(content.body, "暂无待办")
        reminder_items = self._items_from_text(content.daily_reminder_text, "暂无提醒")
        current: _MeasuredFlow | None = None
        left_size = 22
        for candidate in range(40, 21, -2):
            measured = self._measure(draw, todo_items, page, candidate)
            if self._header_width(draw, page, self._font(candidate)) <= FLOW.left_text_width and measured.bottom_y <= FLOW.safe_content_bottom_y:
                left_size = candidate
                current = measured
                break
        if current is None:
            current = self._measure(draw, todo_items, page, left_size)
        overflow = current.bottom_y > FLOW.safe_content_bottom_y
        visible_todo = len(current.todo_lines)

        reminder, reminder_start_y = self._fit_reminder(draw, reminder_items)
        body_count = sum(len(group) for group in current.body_groups)
        return FlowRenderLayout(
            left_font_size=left_size,
            todo=FittedText(left_size, len(current.todo_lines), overflow),
            reminder=reminder,
            yijing_header=FittedText(left_size, 1, overflow),
            yijing_body=FittedText(left_size, body_count, overflow),
            todo_start_y=self._title_end_y(left_size),
            divider_y=current.divider_y,
            yijing_header_y=current.header_y,
            yijing_body_y=current.body_y,
            reminder_start_y=reminder_start_y,
            todo_visible_line_count=visible_todo,
            total_left_height=current.bottom_y - FLOW.content_top_y,
            overflow_detected=overflow or reminder.truncated,
        )

    @staticmethod
    def battery_footer_text(battery_percent: int | None) -> str | None:
        if battery_percent is None:
            return None
        if not 0 <= battery_percent <= 100:
            raise ValueError("Battery percentage must be between 0 and 100")
        if battery_percent >= 20:
            return f"电量 {battery_percent}%"
        if battery_percent >= 10:
            return f"电量 {battery_percent}% · 请充电"
        return f"电量 {battery_percent}% · 充电！"

    def _draw_limited_lines(
        self, draw: ImageDraw.ImageDraw, x: int, y: int, lines: list[str], font: ImageFont.FreeTypeFont,
        width: int, max_y: int, *, limit: int | None = None, use_ink_height: bool = False
    ) -> tuple[int, bool]:
        step = line_step(font, font.size)
        line_height = line_box_height(font, font.size) if use_ink_height else step
        shown = lines if limit is None else lines[:limit]
        truncated = len(shown) < len(lines)
        for index, line in enumerate(shown):
            if y + line_height > max_y:
                return y, True
            text = self._ellipsize(draw, line, font, width) if truncated and index == len(shown) - 1 else line
            draw.text((x, y), text, fill=0, font=font)
            y += step
        return y, truncated

    def _draw_paragraphs_limited(
        self, draw: ImageDraw.ImageDraw, x: int, y: int, paragraphs: tuple[str, ...], font: ImageFont.FreeTypeFont,
        width: int, max_y: int
    ) -> bool:
        step = line_step(font, font.size)
        line_height = line_box_height(font, font.size)
        groups = paragraph_lines(draw, paragraphs, font, width)
        visible: list[tuple[int, str]] = []
        truncated = False
        for group_index, group in enumerate(groups):
            for line in group:
                if y + line_height > max_y:
                    truncated = True
                    break
                visible.append((y, line))
                y += step
            if truncated:
                break
            if group_index < len(groups) - 1:
                y += 3
                if y >= max_y:
                    truncated = True
                    break
        for index, (line_y, line) in enumerate(visible):
            text = self._ellipsize(draw, line, font, width) if truncated and index == len(visible) - 1 else line
            draw.text((x, line_y), text, fill=0, font=font)
        return truncated

    def _draw_footer(self, draw: ImageDraw.ImageDraw, battery_percent: int | None, refresh_at: datetime) -> None:
        footer_font = self._font(19)
        local_time = refresh_at.astimezone(SHANGHAI).strftime("%H:%M")
        draw.text((FLOW.left_padding, FLOW.footer_top_y + 15), f"更新 {local_time}", fill=0, font=footer_font)
        battery = self.battery_footer_text(battery_percent)
        if battery is not None:
            x = PORTRAIT_WIDTH - FLOW.right_padding - text_width(draw, battery, footer_font)
            draw.text((x, FLOW.footer_top_y + 15), battery, fill=0, font=footer_font)

    def render_portrait(
        self, content: NormalizedContent, battery_percent: int | None = None, *, page: YijingPage | None = None,
        refresh_at: datetime | None = None
    ) -> Image.Image:
        portrait = Image.new("1", (PORTRAIT_WIDTH, PORTRAIT_HEIGHT), color=1)
        draw = ImageDraw.Draw(portrait)
        page = page or yijing_page_at(content.yijing_position)
        layout = self.layout_flow(content, page)
        if layout.overflow_detected:
            raise TodoRenderError("Flow left column cannot fit without truncation")
        todo_items = self._items_from_text(content.body, "暂无待办")
        reminder_items = self._items_from_text(content.daily_reminder_text, "暂无提醒")
        todo_lines = item_lines(draw, todo_items, self._font(layout.todo.size), FLOW.left_text_width)
        draw_flow_dividers(draw)
        self._draw_bold(draw, (FLOW.left_padding, FLOW.content_top_y), "短期待办", self._font(layout.left_font_size))
        _, todo_overflow = self._draw_limited_lines(
            draw, FLOW.left_padding, layout.todo_start_y, todo_lines, self._font(layout.todo.size),
            FLOW.left_text_width, layout.divider_y - FLOW.divider_before_gap, limit=layout.todo_visible_line_count,
            use_ink_height=True,
        )
        draw.line((FLOW.left_padding, layout.divider_y, FLOW.vertical_divider_x - FLOW.right_padding, layout.divider_y), fill=0, width=1)
        self._draw_yijing_header(draw, page, FLOW.left_padding, layout.yijing_header_y, layout.yijing_header.size)
        yijing_overflow = self._draw_paragraphs_limited(
            draw, FLOW.left_padding, layout.yijing_body_y, page.paragraphs, self._font(layout.yijing_body.size),
            FLOW.left_text_width, FLOW.safe_content_bottom_y,
        )
        self._draw_bold(draw, (FLOW.right_text_x, FLOW.content_top_y), "每日提醒", self._font(40))
        reminder_lines = item_lines(draw, reminder_items, self._font(layout.reminder.size), FLOW.right_text_width)
        _, reminder_overflow = self._draw_limited_lines(
            draw, FLOW.right_text_x, layout.reminder_start_y, reminder_lines, self._font(layout.reminder.size),
            FLOW.right_text_width, FLOW.footer_top_y - 16,
        )
        self._draw_footer(draw, battery_percent, refresh_at or datetime.now(timezone.utc))
        if layout.overflow_detected or todo_overflow or yijing_overflow or reminder_overflow:
            LOGGER.warning("Flow layout overflow detected; the final visible line was ellipsized")
        return portrait

    def render_image(
        self, content: NormalizedContent, battery_percent: int | None = None, *, refresh_at: datetime | None = None
    ) -> Image.Image:
        # v0.16.0 rotates exact 800x600 images clockwise on the Nook.
        return self.render_portrait(content, battery_percent, refresh_at=refresh_at).transpose(Image.Transpose.ROTATE_90)

    def render(
        self, content: NormalizedContent, battery_percent: int | None = None, *, refresh_at: datetime | None = None
    ) -> bytes:
        try:
            image = self.render_image(content, battery_percent, refresh_at=refresh_at)
            output = io.BytesIO()
            image.save(output, format="PNG", optimize=True)
            return output.getvalue()
        except TodoRenderError:
            raise
        except Exception:
            raise TodoRenderError("Todo image rendering failed") from None
