from __future__ import annotations

from typing import Protocol

from archives import find_zips, read_banks
from console import warn
from progress import tqdm

from models import WordCandidate


class FreqSource(Protocol):
    def lookup(self, word: str) -> float | None: ...


class YomitanFreqDict:
    def __init__(self, zip_path: str):
        self.table: dict[str, float] = self.load(zip_path)

    def load(self, zip_path: str) -> dict[str, float]:
        table: dict[str, float] = {}
        for _name, entries in read_banks(zip_path, ("term_meta_bank", "kanji_meta_bank")):
            for entry in entries:
                try:
                    term, kind, data = entry
                    if kind != "freq":
                        continue
                    value = data["value"] if isinstance(data, dict) else data
                    table[term] = float(value)
                except (ValueError, TypeError):
                    continue
        return table

    def lookup(self, word: str) -> float | None:
        return self.table.get(word)


class FreqChain:
    def __init__(self, dicts: list[FreqSource]):
        self.dicts = dicts

    def lookup(self, word: str) -> float | None:
        for d in self.dicts:
            value = d.lookup(word)
            if value is not None:
                return value
        return None

    def lookup_all(self, word: str) -> list[float]:
        values = []
        for d in self.dicts:
            value = d.lookup(word)
            if value is not None:
                values.append(value)
        return values


def load_freq_dicts(folder: str) -> FreqSource | None:
    paths = find_zips(folder)
    if not paths:
        return None
    dicts = []
    for p in paths:
        try:
            dicts.append(YomitanFreqDict(str(p)))
        except Exception as e:
            warn(f"Frequency dictionaries: couldn't read {p.name!r} ({e}), skipping it")
    if not dicts:
        return None
    return dicts[0] if len(dicts) == 1 else FreqChain(dicts)


def cutoff(candidates: list[WordCandidate], min_count: int = 1, percentile_cutoff: float = 0.0) -> list[WordCandidate]:
    survivors = [c for c in candidates if c.count >= min_count]

    if percentile_cutoff > 0:
        survivors.sort(key=lambda c: c.count)
        cut = int(len(survivors) * percentile_cutoff)
        survivors = survivors[cut:]

    return survivors


def rank_by_count(candidates: list[WordCandidate]) -> list[WordCandidate]:
    ordered = sorted(candidates, key=lambda c: -c.count)
    for i, c in enumerate(ordered, start=1):
        c.text_rank = i
    return ordered


class FrequencyService:
    def __init__(
        self,
        freq_dict: FreqSource | None,
        top_cutoff_rank: int | None = None,
        keep_unranked_words: bool = True,
        set_lowest_freq: bool = False,
    ):
        self.freq_dict = freq_dict
        self.top_cutoff_rank = top_cutoff_rank
        self.keep_unranked_words = keep_unranked_words
        self.set_lowest_freq = set_lowest_freq

    def _lookup(self, word: str) -> float | None:
        if self.set_lowest_freq and isinstance(self.freq_dict, FreqChain):
            values = self.freq_dict.lookup_all(word)
            return min(values) if values else None
        return self.freq_dict.lookup(word)

    def filter_and_annotate(
        self,
        candidates: list[WordCandidate],
        min_count: int,
        percentile_cutoff: float,
    ) -> list[WordCandidate]:
        survivors = cutoff(candidates, min_count, percentile_cutoff)

        if self.freq_dict is not None and not self.keep_unranked_words:
            survivors = [c for c in survivors if self._lookup(c.text) is not None]

        if self.top_cutoff_rank is not None and self.freq_dict is not None:
            def too_common(c: WordCandidate) -> bool:
                rank = self._lookup(c.text)
                return rank is not None and rank <= self.top_cutoff_rank

            survivors = [c for c in survivors if not too_common(c)]

        if self.freq_dict is not None:
            for c in tqdm(survivors, desc="frequency lookup", unit="word"):
                c.dict_rank = self._lookup(c.text)

        return rank_by_count(survivors)
