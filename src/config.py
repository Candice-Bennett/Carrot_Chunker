from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from console import warn


@dataclass
class DedupeField:
    note_type: str
    field_name: str

@dataclass
class Config:
    
    # Filtering
    min_count: int = 2
    percentile_cutoff: float = 0.0
    top_cutoff_rank: int | None = None
    set_lowest_freq: bool = False
    use_chapters: bool = False
    start_percent: float = 0.0
    end_percent: float = 1.0
    dedupe_enabled: bool = True
    dedupe_fields: list[DedupeField] = field(default_factory=list)

    # Paths
    input_path: str = ""
    output_path: str = "output/deck.csv"
    dictionaries_dir: str = "dictionaries"
    frequency_dictionaries_dir: str = "frequency_dictionaries"

    # Card settings
    stack_dict_definitions: bool = False
    dict_defs_on_new_line: bool = False
    space_pinyin: bool = True
    example_sentence_min_hanzi: int = 6
    example_sentence_max_hanzi: int = 25

    # Debug
    keep_words_with_no_defs: bool = False
    segment_batch_size: int = 32
    clean_text: bool = True
    keep_unranked_words: bool = True
    ankiconnect_url: str = "http://127.0.0.1:8765"

    @classmethod
    def load(cls, path: str | Path) -> "Config":
        try:
            raw = json.loads(Path(path).read_text(encoding="utf-8"))
            raw = {k: v for k, v in raw.items() if v != ""}
            raw_fields = raw.pop("dedupe_fields", [])
            dedupe_fields = [DedupeField(**d) for d in raw_fields]
            return cls(dedupe_fields=dedupe_fields, **raw)
        except FileNotFoundError:
            warn(f"Config: couldn't find {str(path)!r}, using default settings")
        except (json.JSONDecodeError, TypeError) as e:
            warn(f"Config: {str(path)!r} is malformed ({e}), using default settings")
        return cls()
