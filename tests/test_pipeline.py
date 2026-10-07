from pathlib import Path

from bs4 import BeautifulSoup

from processing.cleaning import clean_record
from processing.deduplication import deduplicate
from processing.validation import validate_record
from scrapers.books_scraper import RATINGS
from scrapers.quotes_scraper import QuotesToScrape


FIXTURES = Path(__file__).parent / "fixtures"


def test_book_fixture_has_expected_selector_contract():
    html = (FIXTURES / "books_page.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    card = soup.select_one("article.product_pod")
    assert card.select_one("h3 a")["title"] == "Example Book"
    assert card.select_one(".price_color").get_text(strip=True) == "£12.34"
    assert "Three" in card.select_one(".star-rating")["class"]
    assert RATINGS["Three"] == 3
    assert soup.select_one("li.next a")["href"] == "page-2.html"


def test_quote_fixture_parses_core_fields():
    html = (FIXTURES / "quotes_page.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    quote = soup.select_one("div.quote")
    assert quote.select_one("span.text").get_text(strip=True) == "“A sample quote.”"
    assert quote.select_one("small.author").get_text(strip=True) == "Ada Example"
    assert [x.get_text(strip=True) for x in quote.select("a.tag")] == ["python", "testing"]


def test_cleaning_normalizes_price_rating_and_tags():
    record = clean_record(
        {
            "source": " Books to Scrape ",
            "source_url": "https://books.toscrape.com/foo/#fragment",
            "name_or_title": "  Example   Book ",
            "price": "£12.34",
            "rating": "Three",
            "tags": ["Python", "python", " testing "],
        }
    )
    assert record["name_or_title"] == "Example Book"
    assert record["price"] == 12.34
    assert record["rating"] == 3.0
    assert record["tags"] == ["Python", "testing"]
    assert record["source_url"] == "https://books.toscrape.com/foo/"


def test_validation_and_deduplication():
    base = clean_record(
        {
            "source": "Books to Scrape",
            "source_url": "https://books.toscrape.com/a",
            "name_or_title": "Example Book",
            "price": "10.00",
            "rating": "Five",
        }
    )
    assert validate_record(base)[0]
    duplicate = dict(base)
    duplicate["name_or_title"] = " example   book "
    unique, duplicate_count, duplicate_rows = deduplicate([base, duplicate])
    assert len(unique) == 1
    assert duplicate_count == 1
    assert len(duplicate_rows) == 1


def test_quote_scraper_constants():
    scraper = QuotesToScrape.__new__(QuotesToScrape)
    assert scraper.source == "Quotes to Scrape"
    assert QuotesToScrape.start_url.endswith("/page/1/")
