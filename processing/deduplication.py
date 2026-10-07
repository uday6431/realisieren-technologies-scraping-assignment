from __future__ import annotations

import hashlib
import re


def _norm(value) -> str:
    if value is None:
        return ""
    text = re.sub(r"\s+", " ", str(value)).strip().casefold()
    return text


def record_key(record: dict) -> str:
    parts = [
        _norm(record.get("source")),
        _norm(record.get("name_or_title")),
        _norm(record.get("author")),
        _norm(record.get("source_url")),
    ]
    return "|".join(parts)


def record_id(record: dict) -> str:
    payload = record_key(record).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def deduplicate(records: list[dict]) -> tuple[list[dict], int, list[dict]]:
    seen = set()
    unique = []
    duplicates = []
    for record in records:
        key = record_key(record)
        if key in seen:
            duplicates.append(record)
        else:
            seen.add(key)
            unique.append(record)
    return unique, len(duplicates), duplicates
