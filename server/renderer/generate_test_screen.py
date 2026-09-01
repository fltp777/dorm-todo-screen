"""Generate the fixed orientation/cropping calibration image."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

TARGET_WIDTH = 600
TARGET_HEIGHT = 800
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "static" / "test-screen.png"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    windows = Path("C:/Windows/Fonts")
    candidates = [
        windows / ("msyhbd.ttc" if bold else "msyh.ttc"),
        windows / ("arialbd.ttf" if bold else "arial.ttf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def _center_text(draw: ImageDraw.ImageDraw, y: int, text: str, font: ImageFont.ImageFont) -> None:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    draw.text(((TARGET_WIDTH - (right - left)) / 2, y - top), text, fill=0, font=font)


def build_test_screen() -> Image.Image:
    # Compose the expected upright 600x800 panel first.
    portrait = Image.new("1", (TARGET_WIDTH, TARGET_HEIGHT), color=1)
    draw = ImageDraw.Draw(portrait)
    regular = _font(22)
    small = _font(17)
    title = _font(34, bold=True)
    hero = _font(76, bold=True)
    chinese = _font(48, bold=True)

    draw.rectangle((7, 7, TARGET_WIDTH - 8, TARGET_HEIGHT - 8), outline=0, width=5)
    draw.rectangle((18, 18, TARGET_WIDTH - 19, TARGET_HEIGHT - 19), outline=0, width=1)

    draw.text((27, 25), "TOP LEFT", fill=0, font=small)
    right_label = "TOP RIGHT"
    right_width = draw.textbbox((0, 0), right_label, font=small)[2]
    draw.text((TARGET_WIDTH - 27 - right_width, 25), right_label, fill=0, font=small)

    bottom_y = TARGET_HEIGHT - 53
    draw.text((27, bottom_y), "BOTTOM LEFT", fill=0, font=small)
    right_label = "BOTTOM RIGHT"
    right_width = draw.textbbox((0, 0), right_label, font=small)[2]
    draw.text((TARGET_WIDTH - 27 - right_width, bottom_y), right_label, fill=0, font=small)

    _center_text(draw, 108, "NOOK BYOS TEST", title)
    draw.line((35, 171, TARGET_WIDTH - 35, 171), fill=0, width=3)
    _center_text(draw, 224, "TEST 01", hero)
    _center_text(draw, 335, "测试成功", chinese)
    _center_text(draw, 416, "EXPECTED: UPRIGHT PORTRAIT", regular)
    _center_text(draw, 453, "SOURCE PNG: 800 x 600", regular)
    _center_text(draw, 490, "AFTER CLIENT: 600 x 800", regular)

    center_x, center_y = TARGET_WIDTH // 2, 615
    draw.line((45, center_y, TARGET_WIDTH - 45, center_y), fill=0, width=3)
    draw.line((center_x, 530, center_x, 700), fill=0, width=3)
    draw.ellipse((center_x - 10, center_y - 10, center_x + 10, center_y + 10), outline=0, width=3)
    draw.text((center_x + 14, center_y + 10), "CENTER", fill=0, font=small)

    # v0.16.0 rotates exact 800x600 images clockwise. Pre-rotate counterclockwise
    # so the physical 600x800 display is upright after that client transform.
    return portrait.transpose(Image.Transpose.ROTATE_90)


if __name__ == "__main__":
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    build_test_screen().save(OUTPUT_PATH, format="PNG", optimize=True)
    print(f"Generated {OUTPUT_PATH} ({SCREEN_WIDTH}x{SCREEN_HEIGHT})")
