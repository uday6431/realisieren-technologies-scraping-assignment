# Python Web Scraping Interview Assignment

## 1. Overview

This project implements a reusable Python pipeline that scrapes two public practice websites:

- **Books to Scrape** — https://books.toscrape.com/
- **Quotes to Scrape** — https://quotes.toscrape.com/

The pipeline follows the assignment flow:

**Scraping → Cleaning → Validation → Deduplication → Consolidation → CSV + JSON report + logs**

The implementation keeps source-specific parsing isolated in `scrapers/` and keeps data transformation, validation, and duplicate detection in `processing/`.

The assignment explicitly permits AI assistance, but the final implementation is intended to be reviewed and explainable by the candidate.

## 2. Python version

Python 3.10+ (tested for standard Python 3.10+ syntax; Python 3.11/3.12/3.13 are suitable).

## 3. Project structure

```text
realisieren_scraping_assignment/
├── scrapers/
│   ├── __init__.py
│   ├── http_client.py
│   ├── books_scraper.py
│   └── quotes_scraper.py
├── processing/
│   ├── __init__.py
│   ├── cleaning.py
│   ├── validation.py
│   └── deduplication.py
├── output/
│   ├── final_dataset.csv
│   └── summary_report.json
├── logs/
│   └── sample_execution.log
├── tests/
│   ├── __init__.py
│   ├── fixtures/
│   │   ├── books_page.html
│   │   └── quotes_page.html
│   └── test_pipeline.py
├── main.py
├── requirements.txt
├── README.md
└── AI_USAGE.md
```

## 4. Installation

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## 5. Run the complete scraper

```bash
python main.py
```

By default, the scraper follows pagination until each source has no `next` link. Books detail pages and quote author pages are also requested so source-specific metadata can be normalized into the common schema.

### Useful options

```bash
python main.py --books-pages 2 --quotes-pages 2
python main.py --skip-book-details --skip-author-details
python main.py --delay 0.5 --retries 4
python main.py --output-dir output --log-dir logs --log-level DEBUG
```

`--books-pages 0` and `--quotes-pages 0` mean all available pages.

## 6. Pagination

### Books to Scrape
The scraper starts at the Books category listing and follows the `li.next a` link. The live page currently reports 1,000 book results over 50 pages, so the implementation does not hard-code `50` and instead stops when there is no next link.

### Quotes to Scrape
The scraper starts at `/page/1/` and follows `nav li.next a` until the next link is absent.

This design is deliberately selector-based rather than URL-count-based so that pagination changes do not require changing the page loop.

## 7. Data model

The consolidated record schema is:

| Field | Meaning |
|---|---|
| `record_id` | Stable hash-based identifier |
| `source` | Source website name |
| `source_url` | Original page URL |
| `name_or_title` | Book title or quote text |
| `category` | Book category when provided |
| `price` | Numeric book price; null for quotes |
| `rating` | Numeric 1–5 rating when provided |
| `author` | Quote author when provided |
| `tags` | Quote tags, standardized as a list then CSV text |
| `description` | Book description or author description when available |
| `availability` | Book stock/availability text |
| `author_url` | Author profile URL when available |
| `scraped_at` | UTC timestamp for the run |

The scraper uses null/empty values when a field does not exist for a source rather than inventing data.

## 8. Cleaning and standardization

`processing/cleaning.py` provides reusable transformations:

- collapses unnecessary whitespace;
- normalizes text casing only for comparison, preserving display text;
- converts currency strings such as `£51.77` into numeric values;
- maps star names (`One`–`Five`) to numbers;
- normalizes and validates `http`/`https` URLs;
- normalizes tag collections and removes repeated tags.

The cleaning logic is separate from source scraping so the same transformation rules can be reused across sources.

## 9. Validation

`processing/validation.py` rejects records when:

- the source is unknown;
- the source URL is missing or not URL-shaped;
- the standardized title/text field is missing;
- price is negative/non-numeric after normalization;
- rating is outside the expected 1–5 range;
- a quote has no recognizable author.

Rejected records are retained in `summary_report.json` as a bounded sample of validation failures.

## 10. Deduplication

`processing/deduplication.py` creates a normalized comparison key using:

- source;
- normalized title/text;
- normalized author;
- normalized source URL.

This means trivial differences in whitespace/case do not create a second record, while records from different source systems remain distinct even if they happen to share a title.

Duplicates are removed from the final dataset and their count is recorded in the JSON summary.

## 11. Error handling and logging

The HTTP client implements:

- request timeouts;
- HTTP error handling;
- configurable retries;
- exponential backoff with small jitter;
- a request delay/rate limiter;
- page/detail failure logging;
- per-record parsing exception isolation.

A failed individual detail page does not stop the complete source scrape.

## 12. Outputs

The live run generates:

- `output/final_dataset.csv`
- `output/summary_report.json`
- `logs/scraper.log`

The JSON report includes:

- total records collected per source;
- pages requested and failed;
- total records after cleaning;
- validation rejections;
- duplicate records detected/removed;
- final record count;
- execution time;
- output locations.

## 13. Tests

Run:

```bash
pytest -q
```

Tests are fixture-based and do not require network access. They cover:

- book parsing;
- quote parsing;
- cleaning/numeric normalization;
- validation;
- duplicate detection.

## 14. Sample output note

The ZIP includes a small, source-grounded sample `output/final_dataset.csv` created from the publicly readable listing snapshots used while packaging the submission. The execution environment used for packaging could not resolve external DNS from Python, so a live end-to-end network scrape could not be honestly claimed as executed here.

The submitted `main.py` is the complete runnable solution. Running it in a normal network-enabled environment regenerates the full dataset and summary report from the two live practice sites.

## 15. Assumptions

1. The supplied practice websites remain publicly accessible.
2. The expected HTML selectors remain reasonably stable.
3. Missing source-specific values are represented as null/empty values.
4. Prices are normalized to numeric values without converting currencies.
5. Ratings use the websites' five-point rating semantics.
6. Reasonable request spacing and retries are preferred over aggressive parallel crawling.

## 16. Known limitations

- This is a medium-level take-home solution rather than a distributed production crawler.
- No database is required by the assignment, so the canonical output is CSV + JSON.
- A single process is used for predictability and politeness.
- Selector changes at the source sites may require parser updates.
- The package's included CSV is a sample snapshot; use `python main.py` for a fresh live scrape.

## 17. Production next steps

For a scheduled production workload, the next useful improvements would be a persistent request cache/checkpoint, a database sink, structured metrics/observability, stronger schema versioning, and incremental change detection.

## 18. Source verification notes

The live public pages used for implementation review show that Books to Scrape exposes paginated book listings and a `next` link, and Quotes to Scrape exposes paginated quote pages with quote/author/tag blocks and a next link. The scraper therefore uses those observed mechanisms instead of assuming a fixed page count.
