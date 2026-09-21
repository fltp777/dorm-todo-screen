"""Render normalized todo text for the verified Nook orientation path."""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from content import NormalizedContent

PORTRAIT_WIDTH = 600
PORTRAIT_HEIGHT = 800
OUTPUT_SIZE = (800, 600)
MARGIN = 44
MAX_FONT_SIZE = 52
MIN_FONT_SIZE = 20
FONT_STEP = 2
FOOTER_FONT_SIZE = 18
FOOTER_RESERVED_HEIGHT = 56
DEFAULT_FONT_PATH = (
    Path(__file__).resolve().parent.parent / "assets" / "fonts" / "NotoSansCJKsc-Regular.otf"
)


class TodoRenderError(RuntimeError):
    """Raised when a safe screen artifact cannot be produced."""


@dataclass(frozen=True)
class TextLayout:
    lines: tuple[str, ...]
    font_size: int
    line_step: int
    text_height: int
    truncated: bool


@dataclass(frozen=True)
class FooterLayout:
    text: str
    x: int
    y: int
    width: int
    height: int


class TodoRenderer:
    def __init__(self, font_path: Path = DEFAULT_FONT_PATH) -> None:
        self.font_path = Path(font_path)

    @property
    def max_text_width(self) -> int:
        return PORTRAIT_WIDTH - (MARGIN * 2)

    @property
    def max_text_height(self) -> int:
        # Always reserve the footer band so content does not jump when the optional
        # device header is temporarily unavailable.
        return PORTRAIT_HEIGHT - (MARGIN * 2) - FOOTER_RESERVED_HEIGHT

    def _font(self, size: int) -> ImageFont.FreeTypeFont:
        if not self.font_path.is_file():
            raise TodoRenderError("Bundled CJK font is unavailable")
        try:
            return ImageFont.truetype(str(self.font_path), size=size)
        except OSError:
            raise TodoRenderError("Bundled CJK font could not be loaded") from None

    def _wrap_line(
        self,
        draw: ImageDraw.ImageDraw,
        line: str,
        font: ImageFont.FreeTypeFont,
    ) -> list[str]:
        if line == "":
            return [""]

        wrapped: list[str] = []
        current = ""
        for character in line:
            candidate = current + character
            width = draw.textlength(candidate, font=font)
            if current and width > self.max_text_width:
                wrapped.append(current)
                current = character
            else:
                current = candidate
        wrapped.append(current)
        return wrapped

    def _wrap_text(
        self,
        draw: ImageDraw.ImageDraw,
        body: str,
        font: ImageFont.FreeTypeFont,
    ) -> list[str]:
        lines: list[str] = []
        for logical_line in body.split("\n"):
            lines.extend(self._wrap_line(draw, logical_line, font))
        return lines or [""]

    @staticmethod
    def _line_step(font: ImageFont.FreeTypeFont, size: int) -> int:
        top, bottom = font.getbbox("国Ag")[1], font.getbbox("国Ag")[3]
        return max(bottom - top, size) + max(4, size // 4)

    def _ellipsize(
        self,
        draw: ImageDraw.ImageDraw,
        line: str,
        font: ImageFont.FreeTypeFont,
    ) -> str:
        ellipsis = "…"
        candidate = line + ellipsis
        while line and draw.textlength(candidate, font=font) > self.max_text_width:
            line = line[:-1]
            candidate = line + ellipsis
        return candidate

    def layout_text(self, body: str) -> TextLayout:
        scratch = Image.new("1", (PORTRAIT_WIDTH, PORTRAIT_HEIGHT), color=1)
        draw = ImageDraw.Draw(scratch)

        for size in range(MAX_FONT_SIZE, MIN_FONT_SIZE - 1, -FONT_STEP):
            font = self._font(size)
            lines = self._wrap_text(draw, body, font)
            line_step = self._line_step(font, size)
            text_height = len(lines) * line_step
            if text_height <= self.max_text_height:
                return TextLayout(tuple(lines), size, line_step, text_height, False)

        font = self._font(MIN_FONT_SIZE)
        lines = self._wrap_text(draw, body, font)
        line_step = self._line_step(font, MIN_FONT_SIZE)
        max_lines = max(1, self.max_text_height // line_step)
        visible = lines[:max_lines]
        visible[-1] = self._ellipsize(draw, visible[-1], font)
        return TextLayout(
            tuple(visible),
            MIN_FONT_SIZE,
            line_step,
            len(visible) * line_step,
            True,
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

    def footer_layout(self, battery_percent: int | None) -> FooterLayout | None:
        text = self.battery_footer_text(battery_percent)
        if text is None:
            return None
        font = self._font(FOOTER_FONT_SIZE)
        scratch = Image.new("1", (PORTRAIT_WIDTH, PORTRAIT_HEIGHT), color=1)
        box = ImageDraw.Draw(scratch).textbbox((0, 0), text, font=font)
        width = box[2] - box[0]
        height = box[3] - box[1]
        return FooterLayout(
            text=text,
            # Position by the measured glyph bounds, not only their dimensions,
            # because CJK font bounds can have non-zero top offsets.
            x=PORTRAIT_WIDTH - MARGIN - box[2],
            y=PORTRAIT_HEIGHT - MARGIN - box[3],
            width=width,
            height=height,
        )

    def render_portrait(
        self,
        content: NormalizedContent,
        battery_percent: int | None = None,
    ) -> Image.Image:
        portrait = Image.new("1", (PORTRAIT_WIDTH, PORTRAIT_HEIGHT), color=1)
        draw = ImageDraw.Draw(portrait)
        body = content.body if content.body != "" else "暂无内容"
        layout = self.layout_text(body)
        font = self._font(layout.font_size)
        y = MARGIN + max(0, (self.max_text_height - layout.text_height) // 2)

        for line in layout.lines:
            draw.text((MARGIN, y), line, fill=0, font=font, anchor="lt")
            y += layout.line_step
        footer = self.footer_layout(battery_percent)
        if footer is not None:
            draw.text(
                (footer.x, footer.y),
                footer.text,
                fill=0,
                font=self._font(FOOTER_FONT_SIZE),
            )
        return portrait

    def render_image(
        self,
        content: NormalizedContent,
        battery_percent: int | None = None,
    ) -> Image.Image:
        # v0.16.0 rotates exact 800x600 images clockwise on the Nook.
        return self.render_portrait(content, battery_percent).transpose(Image.Transpose.ROTATE_90)

    def render(self, content: NormalizedContent, battery_percent: int | None = None) -> bytes:
        try:
            image = self.render_image(content, battery_percent)
            output = io.BytesIO()
            image.save(output, format="PNG", optimize=True)
            return output.getvalue()
        except TodoRenderError:
            raise
        except Exception:
            raise TodoRenderError("Todo image rendering failed") from None
