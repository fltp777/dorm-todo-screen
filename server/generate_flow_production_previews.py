"""Generate local, ignored PNG regression previews from the frozen Flow renderer."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from content import NormalizedContent
from PIL import Image

from renderer.todo import TodoRenderer
from yijing_catalog import YIJING_PAGES, YijingPage


OUTPUT_DIRECTORY = Path(__file__).resolve().parent / "production_previews"
REGULAR_TODO = "修改论文结果部分\n整理氨基酸分析图表\n回复导师消息\n打印实验材料"
STRESS_TODO = "\n".join(
    (
        "修改论文结果部分", "整理氨基酸分析图表", "回复导师消息", "打印实验材料",
        "检查统计脚本输出", "整理补充材料", "联系同门确认时间", "准备明天开会内容",
    )
)
REMINDERS = "钥匙\n电脑\n校园卡\n水杯\n充电器\n雨伞"
PREVIEW_REFRESH_AT = datetime(2026, 10, 2, 13, 30, tzinfo=timezone.utc)


def _longest_full_hexagram() -> YijingPage:
    return max(
        (page for page in YIJING_PAGES if page.is_full_hexagram),
        key=lambda page: sum(len(paragraph) for paragraph in page.paragraphs),
    )


def screen(todo: str, page: YijingPage) -> NormalizedContent:
    return NormalizedContent(
        "todo", todo, PREVIEW_REFRESH_AT, REMINDERS, page.position
    )


def generate() -> list[Path]:
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    renderer = TodoRenderer()
    regular_full = YIJING_PAGES[0]
    regular_line = YIJING_PAGES[1]
    longest = _longest_full_hexagram()
    requests = (
        ("01_final_regular_full_hexagram.png", REGULAR_TODO, regular_full),
        ("02_final_regular_single_line.png", REGULAR_TODO, regular_line),
        ("03_final_long_todo.png", STRESS_TODO, regular_full),
        ("04_final_long_yijing.png", REGULAR_TODO, longest),
        ("05_final_double_pressure.png", STRESS_TODO, longest),
    )
    metadata: list[dict[str, object]] = []
    paths: list[Path] = []
    for filename, todo, page in requests:
        content = screen(todo, page)
        layout = renderer.layout_flow(content, page)
        image = renderer.render_portrait(content, 64, page=page, refresh_at=PREVIEW_REFRESH_AT)
        path = OUTPUT_DIRECTORY / filename
        image.save(path, format="PNG", optimize=True)
        paths.append(path)
        metadata.append(
            {
                "file": filename,
                "mode": image.mode,
                "size": image.size,
                "layout_mode": "flow",
                "yijing_page": page.label,
                "shared_left_font_size": layout.left_font_size,
                "reminder_font_size": layout.reminder.size,
                "divider_y": layout.divider_y,
                "reminder_title_body_gap": 16,
                "yijing_glyph_width_scale": 1.20,
                "total_left_height": layout.total_left_height,
                "overflow": layout.overflow_detected,
                "truncation": {
                    "todo": layout.todo.truncated,
                    "reminder": layout.reminder.truncated,
                    "yijing": layout.yijing_body.truncated,
                },
            }
        )
    (OUTPUT_DIRECTORY / "flow_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return paths


if __name__ == "__main__":
    for output in generate():
        print(output)
