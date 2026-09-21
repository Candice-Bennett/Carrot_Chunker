from __future__ import annotations

from models import WordCandidate

FINGERPRINT = "# rabbit-hole export"


def is_rabbit_hole_export(text: str) -> bool:
    stripped = text.lstrip()
    if not stripped:
        return False
    first_line = stripped.splitlines()[0].strip()
    return first_line == FINGERPRINT


def parse_rabbit_hole_export(text: str) -> list[WordCandidate]:
    candidates = []
    for line in text.splitlines()[1:]:
        if not line.strip():
            continue
        parts = line.split("\t")
        word = parts[0].strip()
        if not word:
            continue
        count = int(parts[1]) if len(parts) > 1 and parts[1].strip() else 1
        example = parts[2].strip() if len(parts) > 2 and parts[2].strip() else None
        candidates.append(WordCandidate(text=word, count=count, example_sentence=example))
    return candidates
