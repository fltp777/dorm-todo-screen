"""Shared, deterministic measurement primitives for the Stage 2C flow screen."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import ImageDraw, ImageFont


@dataclass(frozen=True)
class FlowGeometry:
    portrait_width: int = 600
    portrait_height: int = 800
    vertical_divider_x: int = 392
    footer_top_y: int = 746
    left_padding: int = 26
    right_padding: int = 26
    right_column_padding: int = 24
    safe_content_bottom_y: int = 732
    content_top_y: int = 22
    divider_before_gap: int = 10
    divider_after_gap: int = 10

    @property
    def left_text_width(self) -> int:
        return self.vertical_divider_x - self.left_padding - self.right_padding

    @property
    def right_text_x(self) -> int:
        return self.vertical_divider_x + self.right_column_padding

    @property
    def right_text_width(self) -> int:
        return self.portrait_width - self.right_text_x - self.right_padding


FLOW = FlowGeometry()
CLOSING_PUNCTUATION = frozenset("，。！？；：、】【》〉）】〕」』”’")


@dataclass(frozen=True)
class FittedText:
    size: int
    line_count: int
    truncated: bool = False


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    return round(draw.textlength(text, font=font))


def line_step(font: ImageFont.FreeTypeFont, size: int) -> int:
    return line_box_height(font, size) + line_leading(font, size)


def line_box_height(font: ImageFont.FreeTypeFont, size: int) -> int:
    """Height occupied by one rendered line, excluding following leading."""
    box = font.getbbox("國Ag")
    return max(box[3] - box[1], size)


def line_leading(font: ImageFont.FreeTypeFont, size: int) -> int:
    """The inter-line leading included in ``line_step``."""
    return max(4, size // 5)


def wrapped_lines_height(line_count: int, font: ImageFont.FreeTypeFont, size: int) -> int:
    """Height of a block without reserving leading after its final line."""
    if line_count <= 0:
        return 0
    return line_box_height(font, size) + (line_count - 1) * line_step(font, size)


def wrap_cjk_text_by_pixel_width(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, width: int
) -> list[str]:
    """Wrap manual and automatic CJK lines without a label-column indent."""
    lines: list[str] = []
    for manual_line in text.split("\n"):
        if not manual_line:
            lines.append("")
            continue
        current = ""
        for character in manual_line:
            candidate = current + character
            if current and text_width(draw, candidate, font) > width:
                if character in CLOSING_PUNCTUATION and len(current) > 1:
                    tail_length = 2 if len(current) > 2 else 1
                    lines.append(current[:-tail_length])
                    current = current[-tail_length:] + character
                else:
                    lines.append(current)
                    current = character
            else:
                current = candidate
        lines.append(current)
    return lines or [""]


def item_lines(
    draw: ImageDraw.ImageDraw, items: tuple[str, ...], font: ImageFont.FreeTypeFont, width: int
) -> list[str]:
    return [line for item in items for line in wrap_cjk_text_by_pixel_width(draw, item, font, width)]


def paragraph_lines(
    draw: ImageDraw.ImageDraw, paragraphs: tuple[str, ...], font: ImageFont.FreeTypeFont, width: int
) -> list[list[str]]:
    return [wrap_cjk_text_by_pixel_width(draw, paragraph, font, width) for paragraph in paragraphs]


def paragraph_height(groups: list[list[str]], font: ImageFont.FreeTypeFont, size: int, gap: int = 3) -> int:
    return wrapped_lines_height(sum(len(group) for group in groups), font, size) + max(0, len(groups) - 1) * gap


def fit_plain_items(
    draw: ImageDraw.ImageDraw,
    items: tuple[str, ...],
    font_for: callable,
    maximum: int,
    minimum: int,
    width: int,
    available_height: int,
) -> FittedText:
    for size in range(maximum, minimum - 1, -2):
        font = font_for(size)
        count = len(item_lines(draw, items, font, width))
        if count * line_step(font, size) <= available_height:
            return FittedText(size, count)
    font = font_for(minimum)
    return FittedText(minimum, len(item_lines(draw, items, font, width)), True)


def draw_flow_dividers(draw: ImageDraw.ImageDraw) -> None:
    draw.line((FLOW.vertical_divider_x, 0, FLOW.vertical_divider_x, FLOW.footer_top_y), fill=0, width=1)
    draw.line((0, FLOW.footer_top_y, FLOW.portrait_width, FLOW.footer_top_y), fill=0, width=1)
