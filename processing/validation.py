from __future__ import annotations

from urllib.parse import urlparse

ALLOWED_SOURCES = {"Books to Scrape", "Quotes to Scrape"}


def validate_record(record: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if record.get("source") not in ALLOWED_SOURCES:
        errors.append("unrecognized_source")
    if not record.get("source_url"):
        errors.append("missing_source_url")
    else:
        parsed = urlparse(record["source_url"])
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append("invalid_source_url")
    if not record.get("name_or_title"):
        errors.append("missing_name_or_title")
    price = record.get("price")
    if price is not None and price < 0:
        errors.append("negative_price")
    rating = record.get("rating")
    if rating is not None and not (1 <= rating <= 5):
        errors.append("rating_out_of_range")
    if record.get("source") == "Quotes to Scrape" and not record.get("author"):
        errors.append("missing_quote_author")
    return not errors, errors


def validate_records(records: list[dict]) -> tuple[list[dict], list[dict]]:
    valid = []
    rejected = []
    for record in records:
        ok, errors = validate_record(record)
        if ok:
            valid.append(record)
        else:
            rejected.append({**record, "validation_errors": errors})
    return valid, rejected
