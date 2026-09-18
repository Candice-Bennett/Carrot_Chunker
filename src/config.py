from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DedupeField:
    note_type: str
    field_name: str

@dataclass
class Config:
    min_count: int = 2
    percentile_cutoff: float = 0.0
    top_cutoff_rank: int | None = None
    dedupe_enabled: bool = True
    dedupe_fields: list[DedupeField] = field(default_factory=list)

    input_path: str = ""
    output_path: str = "output/deck.csv"
    dictionaries_dir: str = "dictionaries"
    frequency_dictionaries_dir: str = "frequency_dictionaries"

    segment_batch_size: int = 32
    clean_text: bool = True
    keep_unranked_words: bool = True
    debug: bool = False
    example_sentence_min_hanzi: int = 6
    example_sentence_max_hanzi: int = 25
    ankiconnect_url: str = "http://127.0.0.1:8765"

    @classmethod
    def load(cls, path: str | Path) -> "Config":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        raw = {k: v for k, v in raw.items() if v != ""}
        raw_fields = raw.pop("dedupe_fields", [])
        dedupe_fields = [DedupeField(**d) for d in raw_fields]
        return cls(dedupe_fields=dedupe_fields, **raw)
