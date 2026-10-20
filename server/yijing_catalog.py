"""Read the checked-in classical Yijing dataset and flatten display pages.

The database remains the source of every classical character. This module only
adds presentation labels such as ``【卦辭】`` and a stable zero-based position.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DATABASE_FILENAME = "yijing_64_hexagrams.json"


def _database_path() -> Path:
    """Resolve the checked-in dataset relative to the repository root."""
    candidate = Path(__file__).resolve().parent.parent / "yijing database" / DATABASE_FILENAME
    if candidate.is_file():
        return candidate
    raise RuntimeError("The formal Yijing database is unavailable")


YIJING_DATABASE_PATH = _database_path()


@dataclass(frozen=True)
class YijingPage:
    """One manually selectable display page derived from the formal database."""

    position: int
    number: int
    name: str
    symbol: str
    upper_name: str
    upper_symbol: str
    lower_name: str
    lower_symbol: str
    entry_kind: str
    entry_position: str
    paragraphs: tuple[str, ...]

    @property
    def label(self) -> str:
        if self.entry_kind == "hexagram":
            return f"{self.name} · 整卦"
        return f"{self.name} · {self.entry_position}"

    @property
    def summary(self) -> str:
        return self.paragraphs[0] if self.paragraphs else ""

    @property
    def is_full_hexagram(self) -> bool:
        return self.entry_kind == "hexagram"


def _required_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"Formal Yijing database has invalid {label}")
    return value


def _page(
    *, position: int, row: dict[str, Any], entry_kind: str, entry_position: str, paragraphs: tuple[str, ...]
) -> YijingPage:
    upper = row.get("upper_trigram")
    lower = row.get("lower_trigram")
    if not isinstance(upper, dict) or not isinstance(lower, dict):
        raise RuntimeError("Formal Yijing database has invalid trigram data")
    return YijingPage(
        position=position,
        number=row["number"],
        name=_required_string(row.get("name"), "hexagram name"),
        symbol=_required_string(row.get("symbol"), "hexagram symbol"),
        upper_name=_required_string(upper.get("name"), "upper trigram name"),
        upper_symbol=_required_string(upper.get("symbol"), "upper trigram symbol"),
        lower_name=_required_string(lower.get("name"), "lower trigram name"),
        lower_symbol=_required_string(lower.get("symbol"), "lower trigram symbol"),
        entry_kind=entry_kind,
        entry_position=entry_position,
        paragraphs=paragraphs,
    )


def _whole_hexagram_paragraphs(row: dict[str, Any]) -> tuple[str, ...]:
    judgment = _required_string(row.get("judgment"), "judgment")
    tuan = row.get("tuan")
    great_image = _required_string(row.get("great_image"), "great_image")
    if not isinstance(tuan, list) or not tuan or not all(isinstance(item, str) and item for item in tuan):
        raise RuntimeError("Formal Yijing database has invalid tuan data")
    # Preserve all database paragraph boundaries. Only the first has the field label.
    return (
        f"【卦辭】{judgment}",
        f"【彖曰】{tuan[0]}",
        *tuple(tuan[1:]),
        f"【大象】{great_image}",
    )


def _load_pages(path: Path = YIJING_DATABASE_PATH) -> tuple[YijingPage, ...]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("Formal Yijing database could not be read") from error
    hexagrams = document.get("hexagrams") if isinstance(document, dict) else None
    if not isinstance(hexagrams, list) or len(hexagrams) != 64:
        raise RuntimeError("Formal Yijing database must contain 64 hexagrams")

    pages: list[YijingPage] = []
    special_count = 0
    for expected_number, row in enumerate(hexagrams, start=1):
        if not isinstance(row, dict) or row.get("number") != expected_number:
            raise RuntimeError("Formal Yijing database has a non-continuous order")
        pages.append(_page(
            position=len(pages), row=row, entry_kind="hexagram", entry_position="整卦",
            paragraphs=_whole_hexagram_paragraphs(row),
        ))
        lines = row.get("lines")
        if not isinstance(lines, list) or len(lines) != 6:
            raise RuntimeError("Formal Yijing database must have six lines per hexagram")
        for line in lines:
            if not isinstance(line, dict):
                raise RuntimeError("Formal Yijing database has invalid line data")
            line_position = _required_string(line.get("position"), "line position")
            line_text = _required_string(line.get("text"), "line text")
            small_image = _required_string(line.get("small_image"), "small_image")
            pages.append(_page(
                position=len(pages), row=row, entry_kind="line", entry_position=line_position,
                paragraphs=(f"【爻辭】{line_text}", f"【小象】{small_image}"),
            ))
        special = row.get("special_use")
        if special is not None:
            if row.get("name") not in {"乾", "坤"} or not isinstance(special, dict):
                raise RuntimeError("Formal Yijing database has an invalid special use entry")
            special_position = _required_string(special.get("position"), "special use position")
            special_text = _required_string(special.get("text"), "special use text")
            special_image = _required_string(special.get("small_image"), "special use small_image")
            pages.append(_page(
                position=len(pages), row=row, entry_kind="special_use", entry_position=special_position,
                paragraphs=(f"【爻辭】{special_text}", f"【小象】{special_image}"),
            ))
            special_count += 1
    if special_count != 2 or len(pages) != 450:
        raise RuntimeError("Formal Yijing database has an unexpected display sequence")
    return tuple(pages)


YIJING_PAGES = _load_pages()


def yijing_page_at(position: int) -> YijingPage:
    """Resolve a stored position; rendering never advances it."""
    if isinstance(position, bool) or not isinstance(position, int) or position < 0:
        raise ValueError("Yijing position must be a non-negative integer")
    if position >= len(YIJING_PAGES):
        raise ValueError("Yijing position is outside the formal catalog")
    return YIJING_PAGES[position]
