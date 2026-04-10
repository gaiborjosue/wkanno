from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any


_QUOTE_CHARS = "\"'`“”‘’"
_NAME_PREFIXES = ("annotations ", "annotation ")


def slugify(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    text = re.sub(r"_+", "_", text)
    return text.strip("_") or "item"


def normalize_lookup_name(value: str | None) -> str:
    text = unicodedata.normalize("NFKC", value or "").strip()
    while len(text) >= 2 and text[0] in _QUOTE_CHARS and text[-1] in _QUOTE_CHARS:
        text = text[1:-1].strip()
    text = re.sub(r"\s+", " ", text)
    return text.casefold()


def lookup_name_variants(value: str | None) -> set[str]:
    normalized = normalize_lookup_name(value)
    if not normalized:
        return set()

    variants = {normalized}
    for prefix in _NAME_PREFIXES:
        if normalized.startswith(prefix):
            stripped = normalized.removeprefix(prefix).strip()
            if stripped:
                variants.add(stripped)
    return variants


def names_match(left: str | None, right: str | None) -> bool:
    left_variants = lookup_name_variants(left)
    if not left_variants:
        return False

    right_variants = lookup_name_variants(right)
    if not right_variants:
        return False

    return bool(left_variants & right_variants)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path