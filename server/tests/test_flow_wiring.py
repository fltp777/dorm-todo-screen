from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from content import NormalizedContent
from yijing_catalog import YIJING_DATABASE_PATH, YIJING_PAGES, yijing_page_at


ROOT = Path(__file__).resolve().parents[2]


class FlowWiringTests(unittest.TestCase):
    def test_formal_database_has_required_64_hexagrams_and_source_path(self) -> None:
        self.assertEqual(YIJING_DATABASE_PATH.name, "yijing_64_hexagrams.json")
        self.assertEqual(YIJING_DATABASE_PATH, ROOT / "yijing database" / "yijing_64_hexagrams.json")
        source = json.loads(YIJING_DATABASE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(len(source["hexagrams"]), 64)
        self.assertEqual([item["number"] for item in source["hexagrams"]], list(range(1, 65)))

    def test_each_hexagram_has_six_regular_lines_and_special_entries_are_exact(self) -> None:
        source = json.loads(YIJING_DATABASE_PATH.read_text(encoding="utf-8"))
        self.assertTrue(all(len(item["lines"]) == 6 for item in source["hexagrams"]))
        special = [(item["name"], item["special_use"]["position"]) for item in source["hexagrams"] if item["special_use"]]
        self.assertEqual(special, [("乾", "用九"), ("坤", "用六")])

    def test_flattened_sequence_has_actual_count_and_correct_boundaries(self) -> None:
        self.assertEqual(len(YIJING_PAGES), 450)
        self.assertEqual(YIJING_PAGES[0].label, "乾 · 整卦")
        self.assertEqual(YIJING_PAGES[1].label, "乾 · 初九")
        self.assertEqual(YIJING_PAGES[7].label, "乾 · 用九")
        self.assertEqual(YIJING_PAGES[8].label, "坤 · 整卦")
        self.assertEqual(YIJING_PAGES[15].label, "坤 · 用六")
        self.assertEqual(YIJING_PAGES[-1].label, "未濟 · 上九")
        self.assertEqual(yijing_page_at(449), YIJING_PAGES[-1])
        with self.assertRaises(ValueError):
            yijing_page_at(450)

    def test_page_text_preserves_database_characters_and_field_markers(self) -> None:
        first = yijing_page_at(0)
        self.assertEqual(first.paragraphs[0], "【卦辭】元、亨、利、貞。")
        self.assertTrue(first.paragraphs[1].startswith("【彖曰】大哉乾元，萬物資始"))
        self.assertTrue(first.paragraphs[-1].startswith("【大象】天行健，君子以自強不息。"))
        line = yijing_page_at(1)
        self.assertEqual(line.paragraphs, ("【爻辭】潛龍勿用。", "【小象】潛龍勿用，陽在下也。"))

    def test_normalized_content_rejects_invalid_yijing_position(self) -> None:
        with self.assertRaises(ValueError):
            NormalizedContent("todo", "", datetime.now(timezone.utc), yijing_position=-1)

    def test_editor_loads_formal_catalog_before_editor_logic(self) -> None:
        html = (ROOT / "editor.html").read_text(encoding="utf-8")
        source = (ROOT / "yijing-content.js").read_text(encoding="utf-8")
        editor = (ROOT / "editor.js").read_text(encoding="utf-8")
        self.assertLess(html.index('src="yijing-content.js"'), html.index('src="editor.js"'))
        self.assertIn("yijing_64_hexagrams.json", source)
        self.assertIn("await window.yijingCatalog.load()", editor)
        self.assertNotIn("乾 · 整卦\", summary: \"卦辭：", source)

    def test_editor_position_controls_are_bounded_and_store_is_only_data_layer(self) -> None:
        store = (ROOT / "screen-store.js").read_text(encoding="utf-8")
        editor = (ROOT / "editor.js").read_text(encoding="utf-8")
        self.assertIn("nextPosition < 0 || nextPosition >= window.yijingCatalog.pages.length", editor)
        self.assertNotIn("setInterval", editor)
        self.assertIn('select("text, daily_reminder_text, yijing_position, updated_at")', store)
        self.assertIn("yijing_position: state.yijingPosition", store)
        self.assertNotIn(".from(", editor)

    def test_existing_migration_still_matches_flow_state_without_rls_changes(self) -> None:
        sql = (ROOT / "supabase" / "stage-2c-fixed-v2-state.sql").read_text(encoding="utf-8").lower()
        self.assertIn("add column if not exists daily_reminder_text", sql)
        self.assertIn("add column if not exists yijing_position", sql)
        self.assertIn("yijing_position >= 0 and yijing_position < 450", sql)
        self.assertNotIn("create table", sql)
        self.assertNotIn("row level security", sql)
        self.assertNotIn("create policy", sql)


if __name__ == "__main__":
    unittest.main()
