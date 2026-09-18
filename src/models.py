from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WordCandidate:
    text: str
    count: int
    reading: str | None = None
    definitions: list[str] = field(default_factory=list)
    text_rank: int | None = None
    dict_rank: float | None = None
    example_sentence: str | None = None
