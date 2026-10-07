from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from processing.cleaning import clean_record
from processing.deduplication import deduplicate, record_id
from processing.validation import validate_records
from scrapers.books_scraper import BooksToScrape
from scrapers.http_client import HttpClient
from scrapers.quotes_scraper import QuotesToScrape

FIELDS = [
    "record_id",
    "source",
    "source_url",
    "name_or_title",
    "category",
    "price",
    "rating",
    "author",
    "tags",
    "description",
    "availability",
    "author_url",
    "scraped_at",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Multi-source web scraping assignment")
    parser.add_argument("--books-pages", type=int, default=0, help="Books pages to scrape; 0 = all available pages")
    parser.add_argument("--quotes-pages", type=int, default=0, help="Quotes pages to scrape; 0 = all available pages")
    parser.add_argument("--skip-book-details", action="store_true", help="Do not request each book detail page")
    parser.add_argument("--skip-author-details", action="store_true", help="Do not request quote author pages")
    parser.add_argument("--delay", type=float, default=0.20, help="Minimum delay between requests")
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout in seconds")
    parser.add_argument("--retries", type=int, default=3, help="Retries per request")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    parser.add_argument("--log-dir", default="logs", help="Log directory")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return parser.parse_args()


def configure_logging(log_dir: Path, level: str) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "scraper.log"
    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    handlers = [logging.StreamHandler(sys.stdout), logging.FileHandler(log_file, encoding="utf-8")]
    logging.basicConfig(level=getattr(logging, level), format=fmt, handlers=handlers, force=True)
    return log_file


def write_csv(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            row = {**record}
            if isinstance(row.get("tags"), list):
                row["tags"] = "; ".join(row["tags"])
            writer.writerow({field: row.get(field) for field in FIELDS})


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    log_dir = Path(args.log_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    log_file = configure_logging(log_dir, args.log_level)
    logger = logging.getLogger("pipeline")

    started = time.perf_counter()
    scraped_at = datetime.now(timezone.utc).isoformat()
    client = HttpClient(timeout=args.timeout, retries=args.retries, delay=max(0.0, args.delay))

    all_records: list[dict] = []
    source_stats = {}

    for name, scraper, pages in [
        (
            "Books to Scrape",
            BooksToScrape(client, include_details=not args.skip_book_details),
            args.books_pages,
        ),
        (
            "Quotes to Scrape",
            QuotesToScrape(client, include_author_details=not args.skip_author_details),
            args.quotes_pages,
        ),
    ]:
        logger.info("Starting source: %s", name)
        records, stats = scraper.scrape(max_pages=pages)
        for record in records:
            record["scraped_at"] = scraped_at
        source_stats[name] = {"raw_records": len(records), **stats}
        all_records.extend(records)
        logger.info("Finished source: %s | records=%s", name, len(records))

    cleaned = [clean_record(record) for record in all_records]
    valid, rejected = validate_records(cleaned)
    unique, duplicate_count, duplicate_rows = deduplicate(valid)

    for record in unique:
        record["record_id"] = record_id(record)

    output_csv = output_dir / "final_dataset.csv"
    output_json = output_dir / "summary_report.json"
    write_csv(output_csv, unique)

    elapsed = time.perf_counter() - started
    summary = {
        "execution_status": "completed",
        "scraped_at": scraped_at,
        "execution_time_seconds": round(elapsed, 3),
        "sources": source_stats,
        "total_records_collected": len(all_records),
        "total_records_after_cleaning": len(cleaned),
        "records_rejected_during_validation": len(rejected),
        "duplicate_records_detected": duplicate_count,
        "duplicate_records_removed": duplicate_count,
        "final_record_count": len(unique),
        "validation_rejections": rejected[:25],
        "log_file": str(log_file),
        "output_file": str(output_csv),
    }
    output_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    logger.info(
        "Pipeline complete | collected=%s valid=%s rejected=%s duplicates=%s final=%s",
        len(all_records), len(valid), len(rejected), duplicate_count, len(unique),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
