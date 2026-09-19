from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from anki_service import CsvBuilder, DedupeChecker
from ankiconnect_client import AnkiConnectClient
from archives import find_zips
from config import Config
from console import fatal, warn
from dictionary import DictionaryService, derive_chengyu, load_dicts
from frequency import FrequencyService, load_freq_dicts
from ingest import load_text
from sectioning import pick_chapters, slice_percent
from text_cleaning import clean_text
from word_analysis import WordAnalysisService


def check_user_zips(folder: str, label: str) -> None:
    zips = find_zips(folder)
    user_zips = [p for p in zips if not p.name.upper().startswith("ZZ")]
    if user_zips:
        return
    if zips:
        warn(f"{label}: no user dictionaries found in {folder!r}, only the bundled ZZ fallback ones are being used")
    else:
        warn(f"{label}: no dictionaries found in {folder!r} at all, so this step will be skipped entirely")


def build_freq_service(cfg: Config) -> FrequencyService:
    check_user_zips(cfg.frequency_dictionaries_dir, "Frequency dictionaries")
    freq_dict = load_freq_dicts(cfg.frequency_dictionaries_dir)
    return FrequencyService(freq_dict, cfg.top_cutoff_rank, cfg.keep_unranked_words)


def build_dict_service(cfg: Config) -> DictionaryService:
    check_user_zips(cfg.dictionaries_dir, "Dictionaries")
    source = load_dicts(cfg.dictionaries_dir)
    if source is None:
        warn("Dictionaries: no dictionary could be loaded, cards will have no definitions")
    return DictionaryService(source, cfg.stack_dict_definitions)


def main(input_name: str | None = None) -> None:
    cfg = Config.load("config.json")
    input_path = cfg.input_path or (Path("data") / input_name if input_name else None)
    if not input_path:
        fatal("Usage: python main.py <filename in data/> (or set input_path in config.json)")

    try:
        text = load_text(str(input_path))
    except FileNotFoundError:
        fatal(f"Couldn't find input file {str(input_path)!r}, check the filename (or input_path in config.json)")
    if cfg.clean_text:
        before = len(text)
        text = clean_text(text)
        print(f"Cleaned text: {before} chars, now {len(text)} chars")

    if cfg.use_chapters:
        text = pick_chapters(text)
        print(f"Chapters: using {len(text)} chars")
    elif cfg.start_percent > 0 or cfg.end_percent < 1:
        text = slice_percent(text, cfg.start_percent, cfg.end_percent)
        print(f"Section: {cfg.start_percent:.0%}-{cfg.end_percent:.0%}, {len(text)} chars")

    dict_service = build_dict_service(cfg)
    chengyu = derive_chengyu(dict_service.source)

    analysis = WordAnalysisService(
        chengyu, cfg.example_sentence_min_hanzi, cfg.example_sentence_max_hanzi, cfg.segment_batch_size
    )
    candidates = analysis.analyse(text)
    print(f"Segmented text into {len(candidates)} unique candidates")

    freq_service = build_freq_service(cfg)
    candidates = freq_service.filter_and_annotate(candidates, cfg.min_count, cfg.percentile_cutoff)
    print(f"Frequency cutoffs: {len(candidates)} candidates remain")

    if cfg.dedupe_enabled and cfg.dedupe_fields:
        client = AnkiConnectClient(cfg.ankiconnect_url)
        checker = DedupeChecker(client, cfg.dedupe_fields)
        before = len(candidates)
        candidates = [c for c in candidates if not checker.is_known(c.text)]
        print(f"Dedupe: removed {before - len(candidates)}, {len(candidates)} candidates remain")

    dict_service.annotate(candidates)

    if not cfg.show_words_with_no_defs:
        before = len(candidates)
        candidates = [c for c in candidates if c.definitions]
        dropped = before - len(candidates)
        print(f"Dictionary filter: dropped {dropped} with no definition, {len(candidates)} candidates remain")
        if dropped:
            print("(set show_words_with_no_defs=true in config.json to keep these instead)")

    backend = CsvBuilder(
        cfg.output_path,
        has_dict_rank=freq_service.freq_dict is not None,
        dict_defs_on_new_line=cfg.dict_defs_on_new_line,
    )
    backend.add(candidates)
    print(f"Done: wrote {cfg.output_path!r}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
