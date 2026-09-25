from __future__ import annotations

import re

from console import warn
from ingest import CHAPTER_BREAK
from text_cleaning import DIVIDER

CHAPTER = re.compile(r"^第[0-9〇一二三四五六七八九十百千两零]+[章节回].*$", re.MULTILINE)
HANZI = re.compile(r"[一-鿿]")
MIN_HEADINGS = 2
MIN_LEAD_LINES = 2


def split_chapters(text: str) -> list[str]:
    if CHAPTER_BREAK in text:
        return [p.strip() for p in text.split(CHAPTER_BREAK)]

    starts = [m.start() for m in CHAPTER.finditer(text)]
    if len(starts) >= MIN_HEADINGS:
        return split_at(text, starts)

    starts = [m.end() for m in DIVIDER.finditer(text)]
    if starts:
        return split_at(text, starts)

    return [text]


def split_at(text: str, starts: list[int]) -> list[str]:
    bounds = [0, *starts, len(text)]
    lead, *chapters = [text[a:b] for a, b in zip(bounds, bounds[1:])]
    if sum(1 for line in lead.splitlines() if HANZI.search(line)) >= MIN_LEAD_LINES:
        return [lead, *chapters]
    chapters[0] = lead + chapters[0]
    return chapters


def parse_chapters(raw: str, n: int) -> list[int] | None:
    picked: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, _, hi = part.partition("-")
            if not (lo.strip().isdigit() and hi.strip().isdigit()):
                return None
            picked.update(range(min(int(lo), int(hi)), max(int(lo), int(hi)) + 1))
        elif part.isdigit():
            picked.add(int(part))
        else:
            return None
    picked = {p for p in picked if 1 <= p <= n}
    return sorted(picked) or None


def pick_chapters(text: str) -> str:
    chapters = split_chapters(text)
    if len(chapters) <= 1:
        warn("Chapters: no chapter headings or dividers found, using the whole text")
        return text
    print(f"Chapters: found {len(chapters)}")
    while True:
        raw = input(f"Which ones do you want? (5 / 10-100 / 4,5,6,9,10, out of 1-{len(chapters)}): ")
        chosen = parse_chapters(raw, len(chapters))
        if chosen:
            return "\n\n".join(chapters[i - 1] for i in chosen)
        warn("Chapters: couldn't parse that, try again")


def slice_percent(text: str, start: float, end: float) -> str:
    if start <= 0 and end >= 1:
        return text
    if start >= end:
        warn(f"start_percent ({start}) must be less than end_percent ({end}), using the whole text")
        return text
    n = len(text)
    return text[int(n * start) : int(n * end)]
