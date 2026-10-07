# AI_USAGE.md

## Tools used

- **ChatGPT (OpenAI)**

## How AI was used

ChatGPT was used for:

1. Understanding the assignment requirements and mapping them into a project structure.
2. Reviewing the HTML structure and pagination patterns of the two public practice sites.
3. Designing the standardized record schema.
4. Drafting initial scraper/parser code.
5. Designing cleaning, validation, deduplication, retry, and logging helpers.
6. Generating unit-test fixtures and tests.
7. Reviewing README documentation and edge cases.

## Representative prompts

- "Build a Python web-scraping pipeline for Books to Scrape and Quotes to Scrape with pagination, cleaning, validation, deduplication, logging and a consolidated CSV."
- "Design a reusable normalization function for whitespace, price, rating, tags and URLs."
- "Write tests that validate a Books to Scrape listing parser and a Quotes to Scrape parser without network access."
- "Review the duplicate-detection strategy for case and whitespace variations."

## AI-assisted parts

The following parts were AI-assisted during initial drafting:

- `scrapers/http_client.py`
- `scrapers/books_scraper.py`
- `scrapers/quotes_scraper.py`
- `processing/cleaning.py`
- `processing/validation.py`
- `processing/deduplication.py`
- initial project README and test structure.

## Review and changes after AI output

The implementation was reviewed and adjusted to:

- keep source-specific selectors isolated;
- continue after page/detail request failures;
- use retries with exponential backoff and jitter;
- avoid hard-coded pagination counts;
- normalize records before validation and deduplication;
- keep missing source fields as null rather than fabricating values;
- make tests network-independent;
- expose CLI controls for page limits, rate limiting, retries, and detail fetching.

## Incorrect/incomplete AI suggestions discovered

A live-network execution from the packaging environment was not possible because Python could not resolve the external practice-site hostnames. The solution therefore does not claim that a live end-to-end scrape was executed during packaging.

The packaged sample CSV is explicitly identified as a source-grounded sample snapshot. A normal network-enabled execution of `python main.py` is the intended verification step for the complete dataset.

## Verification

Verification performed during preparation:

- The assignment requirements were mapped to code modules and deliverables.
- The live public websites were inspected for page layout and pagination.
- Offline parser and processing tests are included and are designed to run without network access.
- The repository is structured so a reviewer can run `pytest -q` and then `python main.py` from a clean environment.
