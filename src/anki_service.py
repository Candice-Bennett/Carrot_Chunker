from __future__ import annotations

import csv
import re
from typing import Protocol

from ankiconnect_client import AnkiConnectClient
from config import DedupeField
from models import WordCandidate


class OutputBackend(Protocol):
    def add(self, candidates: list[WordCandidate]) -> None: ...


def example_field(c: WordCandidate) -> str:
    if not c.example_sentence:
        return ""
    return c.example_sentence.replace(c.text, f"<b>{c.text}</b>")


class CsvBuilder:
    def __init__(self, output_path: str, has_dict_rank: bool = False):
        self.output_path = output_path
        self.has_dict_rank = has_dict_rank

    def add(self, candidates: list[WordCandidate]) -> None:
        header = ["Hanzi", "Pinyin", "Definition", "Count", "Rank"]
        if self.has_dict_rank:
            header.append("Dict Rank")
        header.append("Example")

        with open(self.output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for c in candidates:
                row = [
                    c.text,
                    c.reading or "",
                    "; ".join(c.definitions),
                    c.count,
                    "" if c.text_rank is None else c.text_rank,
                ]
                if self.has_dict_rank:
                    row.append("" if c.dict_rank is None else c.dict_rank)
                row.append(example_field(c))
                writer.writerow(row)


class DedupeChecker:
    def __init__(self, client: AnkiConnectClient, fields: list[DedupeField]):
        self.client = client
        self.fields = fields
        self.known: set[str] = set()
        self.loaded = False

    def load(self) -> None:
        if self.loaded:
            return
        for f in self.fields:
            note_ids = self.client.invoke("findNotes", {"query": f'note:"{f.note_type}"'})
            if not note_ids:
                print(f"Dedupe: no notes found for note type {f.note_type!r}, check the spelling in Anki")
                continue

            actual_fields = self.client.invoke("modelFieldNames", {"modelName": f.note_type})
            resolved_name = f.field_name
            if f.field_name not in actual_fields:
                match = next((a for a in actual_fields if a.lower() == f.field_name.lower()), None)
                if match:
                    print(f"Dedupe: field {f.field_name!r} not found on {f.note_type!r}, using {match!r} instead")
                    resolved_name = match
                else:
                    print(f"Dedupe: field {f.field_name!r} not found on {f.note_type!r} (fields: {actual_fields})")
                    continue

            infos = self.client.invoke("notesInfo", {"notes": note_ids})
            extracted = 0
            for info in infos:
                field_data = info.get("fields", {}).get(resolved_name)
                if field_data and field_data.get("value"):
                    self.known.add(strip_html(field_data["value"]))
                    extracted += 1
            print(f"Dedupe: {f.note_type}.{resolved_name}, {len(note_ids)} notes, {extracted} values found")
            if extracted == 0:
                print(f"Dedupe: field {resolved_name!r} exists but is empty on every note")
        self.loaded = True

    def existing_words(self) -> set[str]:
        self.load()
        return self.known

    def is_known(self, word: str) -> bool:
        self.load()
        return word in self.known


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()
