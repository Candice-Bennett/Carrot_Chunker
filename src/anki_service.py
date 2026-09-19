from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Protocol

import requests

from ankiconnect_client import AnkiConnectClient
from config import DedupeField
from console import warn
from models import WordCandidate


class OutputBackend(Protocol):
    def add(self, candidates: list[WordCandidate]) -> None: ...


def example_field(c: WordCandidate) -> str:
    if not c.example_sentence:
        return ""
    return c.example_sentence.replace(c.text, f"<b>{c.text}</b>")


class CsvBuilder:
    def __init__(self, output_path: str, has_dict_rank: bool = False, dict_defs_on_new_line: bool = False):
        self.output_path = output_path
        self.has_dict_rank = has_dict_rank
        self.dict_defs_on_new_line = dict_defs_on_new_line

    def add(self, candidates: list[WordCandidate]) -> None:
        Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)
        header = ["Hanzi", "Pinyin", "Definition", "Count", "Rank"]
        if self.has_dict_rank:
            header.append("Dict Rank")
        header.append("Example")

        with open(self.output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for c in candidates:
                definition = "; ".join(c.definitions)
                if self.dict_defs_on_new_line:
                    definition = definition.replace("\n", "<br>")
                    definition = definition.replace("; ", ";<br>")
                row = [
                    c.text,
                    c.reading or "",
                    definition,
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
        self.loaded = True
        try:
            self.client.invoke("version")
        except requests.exceptions.ConnectionError:
            warn(
                "Warning: could not connect to AnkiConnect, dedupe was skipped.\n"
                "  - Make sure Anki is open\n"
                "  - Make sure the AnkiConnect add-on is installed (code 2055492159) and Anki was restarted after installing it\n"
                f"  - Check that ankiconnect_url in config.json matches AnkiConnect's address (currently {self.client.url!r})"
            )
            return
        except requests.exceptions.Timeout:
            warn(
                "Warning: AnkiConnect took too long to respond, dedupe was skipped.\n"
                "  - Anki might be showing a popup asking to allow this app, check Anki and click yes then run this again\n"
                "  - Otherwise Anki might just be busy (e.g. syncing), try again in a bit"
            )
            return
        for f in self.fields:
            note_ids = self.client.invoke("findNotes", {"query": f'note:"{f.note_type}"'})
            if not note_ids:
                warn(f"Dedupe: no notes found for note type {f.note_type!r}, check the spelling in Anki")
                continue

            actual_fields = self.client.invoke("modelFieldNames", {"modelName": f.note_type})
            resolved_name = f.field_name
            if f.field_name not in actual_fields:
                match = next((a for a in actual_fields if a.lower() == f.field_name.lower()), None)
                if match:
                    warn(f"Dedupe: field {f.field_name!r} not found on {f.note_type!r}, using {match!r} instead")
                    resolved_name = match
                else:
                    warn(f"Dedupe: field {f.field_name!r} not found on {f.note_type!r} (fields: {actual_fields})")
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
                warn(f"Dedupe: field {resolved_name!r} exists but is empty on every note")

    def existing_words(self) -> set[str]:
        self.load()
        return self.known

    def is_known(self, word: str) -> bool:
        self.load()
        return word in self.known


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()
