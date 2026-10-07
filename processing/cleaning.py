from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit, urlunsplit


def clean_text(value):
    if value is None:
        return None
    if isinstance(value, list):
        return [clean_text(v) for v in value if clean_text(v)]
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text or None


def normalize_tags(value):
    if value is None:
        return None
    if isinstance(value, str):
        parts = [part.strip() for part in re.split(r"[,;|]", value) if part.strip()]
    else:
        parts = [clean_text(part) for part in value]
        parts = [part for part in parts if part]
    seen = set()
    result = []
    for part in parts:
        key = part.casefold()
        if key not in seen:
            seen.add(key)
            result.append(part)
    return result or None


def normalize_price(value):
    if value is None or value == "":
        return None
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    text = re.sub(r"[^0-9.,-]", "", str(value).strip())
    if not text:
        return None
    # Books to Scrape uses a decimal point. Keep this conservative for other inputs.
    try:
        return float(Decimal(text.replace(",", "")))
    except InvalidOperation:
        return None


def normalize_rating(value):
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"(?:rating\s*)?(one|two|three|four|five)", str(value), re.I)
    if match:
        return float({"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}[match.group(1).lower()])
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_url(value):
    if not value:
        return None
    try:
        parts = urlsplit(str(value).strip())
    except ValueError:
        return None
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        return None
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, ""))


def clean_record(record: dict) -> dict:
    cleaned = dict(record)
    for field in ("source", "source_url", "name_or_title", "category", "author", "description", "availability", "author_url"):
        cleaned[field] = clean_text(cleaned.get(field))
    cleaned["source_url"] = normalize_url(cleaned.get("source_url"))
    cleaned["author_url"] = normalize_url(cleaned.get("author_url"))
    cleaned["price"] = normalize_price(cleaned.get("price"))
    cleaned["rating"] = normalize_rating(cleaned.get("rating"))
    cleaned["tags"] = normalize_tags(cleaned.get("tags"))
    return cleaned
