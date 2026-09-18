from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Protocol

from archives import find_zips, read_banks, read_texts, zip_names

from progress import tqdm

LINE = re.compile(r"^(\S+)\s+(\S+)\s+\[([^\]]*)\]\s+/(.+)/\s*$")


class DictionarySource(Protocol):
    def lookup(self, word: str) -> tuple[str | None, list[str]]: ...
    def iter_entries(self) -> Iterator[tuple[str, list[str]]]: ...


@dataclass
class CedictEntry:
    traditional: str
    simplified: str
    pinyin: str
    definitions: list[str]


class CedictDictionary:
    def __init__(self, zip_path: str):
        self.table: dict[str, list[CedictEntry]] = self.load(zip_path)

    def load(self, zip_path: str) -> dict[str, list[CedictEntry]]:
        table: dict[str, list[CedictEntry]] = {}
        for raw in read_texts(zip_path):
            for line in raw.splitlines():
                entry = self.parse_line(line)
                if entry is None:
                    continue
                table.setdefault(entry.simplified, []).append(entry)
                if entry.traditional != entry.simplified:
                    table.setdefault(entry.traditional, []).append(entry)
        return table

    @staticmethod
    def parse_line(line: str) -> CedictEntry | None:
        line = line.strip()
        if not line or line.startswith("#"):
            return None
        m = LINE.match(line)
        if not m:
            return None
        traditional, simplified, pinyin, defs = m.groups()
        definitions = [d for d in defs.split("/") if d]
        return CedictEntry(traditional, simplified, pinyin, definitions)

    def lookup(self, word: str) -> tuple[str | None, list[str]]:
        entries = self.table.get(word)
        if not entries:
            return None, []
        groups: dict[str, list[str]] = {}
        for e in entries:
            defs = groups.setdefault(e.pinyin, [])
            for d in e.definitions:
                if d not in defs:
                    defs.append(d)
        return resolve_readings(groups)

    def iter_entries(self) -> Iterator[tuple[str, list[str]]]:
        for word, entries in self.table.items():
            defs: list[str] = []
            for e in entries:
                for d in e.definitions:
                    if d not in defs:
                        defs.append(d)
            yield word, defs


def resolve_readings(groups: dict[str, list[str]]) -> tuple[str | None, list[str]]:
    if not groups:
        return None, []
    primary_reading = max(groups, key=lambda r: len(groups[r]))
    definitions: list[str] = list(groups[primary_reading])
    for reading, defs in groups.items():
        if reading == primary_reading:
            continue
        for d in defs:
            if d not in definitions:
                definitions.append(d)
    return (primary_reading or None), definitions


def load_dictionary(zip_path: str) -> DictionarySource:
    names = zip_names(zip_path)
    if any(n.startswith("term_bank") or n.startswith("kanji_bank") for n in names):
        return YomitanDictionary(zip_path)
    return CedictDictionary(zip_path)


class DictionaryChain:
    def __init__(self, sources: list[DictionarySource]):
        self.sources = sources

    def lookup(self, word: str) -> tuple[str | None, list[str]]:
        for source in self.sources:
            reading, definitions = source.lookup(word)
            if reading is not None or definitions:
                return reading, definitions
        return None, []

    def iter_entries(self) -> Iterator[tuple[str, list[str]]]:
        for source in self.sources:
            yield from source.iter_entries()


def load_dicts(folder: str) -> DictionarySource | None:
    paths = find_zips(folder)
    if not paths:
        return None
    sources = [load_dictionary(str(p)) for p in paths]
    return sources[0] if len(sources) == 1 else DictionaryChain(sources)


class YomitanDictionary:
    def __init__(self, zip_path: str):
        self.table: dict[str, tuple[str | None, list[str]]] = self.load(zip_path)

    def load(self, zip_path: str) -> dict[str, tuple[str | None, list[str]]]:
        raw: dict[str, dict[str, list[str]]] = {}
        for name, entries in read_banks(zip_path, ("term_bank", "kanji_bank")):
            if name.startswith("term_bank"):
                for entry in entries:
                    try:
                        term, reading = entry[0], entry[1]
                        definitions: list[str] = []
                        for d in entry[5]:
                            definitions.extend(flatten_definition(d))
                        self.merge(raw, term, reading, definitions)
                    except (IndexError, TypeError):
                        continue
            elif name.startswith("kanji_bank"):
                for entry in entries:
                    try:
                        term, reading, meanings = entry[0], entry[1], entry[4]
                        self.merge(raw, term, reading, list(meanings))
                    except (IndexError, TypeError):
                        continue
        return {term: resolve_readings(groups) for term, groups in raw.items()}

    @staticmethod
    def merge(raw: dict[str, dict[str, list[str]]], term: str, reading: str, definitions: list[str]) -> None:
        defs = raw.setdefault(term, {}).setdefault(reading or "", [])
        for d in definitions:
            if d not in defs:
                defs.append(d)

    def lookup(self, word: str) -> tuple[str | None, list[str]]:
        return self.table.get(word, (None, []))

    def iter_entries(self) -> Iterator[tuple[str, list[str]]]:
        for term, (_reading, definitions) in self.table.items():
            yield term, definitions


def flatten_definition(item) -> list[str]:
    if isinstance(item, str):
        return [item]
    texts: list[str] = []

    def walk(node) -> None:
        if isinstance(node, str):
            texts.append(node)
        elif isinstance(node, dict):
            if isinstance(node.get("text"), str):
                texts.append(node["text"])
            content = node.get("content")
            if isinstance(content, list):
                for child in content:
                    walk(child)
            elif content is not None:
                walk(content)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(item)
    return texts


class DictionaryService:
    def __init__(self, source: DictionarySource | None):
        self.source = source

    def annotate(self, candidates) -> None:
        if self.source is None:
            return
        for c in tqdm(candidates, desc="dictionary lookup", unit="word"):
            c.reading, c.definitions = self.source.lookup(c.text)


IDIOM_MARKER = re.compile(r"\bidiom\b", re.IGNORECASE)


def derive_chengyu(source: DictionarySource | None) -> set[str]:
    if source is None:
        return set()
    chengyu: set[str] = set()
    for word, definitions in source.iter_entries():
        if any(IDIOM_MARKER.search(d) for d in definitions):
            chengyu.add(word)
    return chengyu
