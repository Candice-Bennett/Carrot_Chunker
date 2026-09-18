from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Iterator


def find_zips(folder: str) -> list[Path]:
    path = Path(folder)
    if not path.is_dir():
        return []
    return sorted(path.glob("*.zip"))


def zip_names(zip_path: str) -> list[str]:
    with zipfile.ZipFile(zip_path) as zf:
        return zf.namelist()


def read_banks(zip_path: str, prefixes: tuple[str, ...]) -> Iterator[tuple[str, list]]:
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if name.startswith(prefixes):
                yield name, json.loads(zf.read(name))


def read_texts(zip_path: str) -> Iterator[str]:
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if not name.endswith("/"):
                yield zf.read(name).decode("utf-8", errors="ignore")
