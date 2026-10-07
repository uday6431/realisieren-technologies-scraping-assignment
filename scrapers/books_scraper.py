from __future__ import annotations

import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .http_client import HttpClient


RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


class BooksToScrape:
    source = "Books to Scrape"
    start_url = "https://books.toscrape.com/catalogue/category/books_1/index.html"

    def __init__(self, client: HttpClient, include_details: bool = True) -> None:
        self.client = client
        self.include_details = include_details
        self.logger = logging.getLogger(self.__class__.__name__)
        self._detail_cache: dict[str, dict] = {}

    def scrape(self, max_pages: int = 0) -> tuple[list[dict], dict]:
        records: list[dict] = []
        stats = {"pages_requested": 0, "pages_failed": 0, "detail_pages_failed": 0}
        current_url = self.start_url

        while current_url and (max_pages <= 0 or stats["pages_requested"] < max_pages):
            stats["pages_requested"] += 1
            response = self.client.get(current_url)
            if response is None:
                stats["pages_failed"] += 1
                self.logger.error("Skipping page after request failure: %s", current_url)
                current_url = None
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.select("article.product_pod")
            if not cards:
                self.logger.warning("No book cards found on %s", current_url)

            for card in cards:
                try:
                    title_node = card.select_one("h3 a")
                    price_node = card.select_one(".price_color")
                    availability_node = card.select_one(".availability")
                    rating_node = card.select_one(".star-rating")
                    link = title_node.get("href", "") if title_node else ""
                    source_url = urljoin(current_url, link)
                    rating_name = next(
                        (cls for cls in (rating_node.get("class", []) if rating_node else []) if cls in RATINGS),
                        None,
                    )
                    row = {
                        "source": self.source,
                        "source_url": source_url,
                        "name_or_title": title_node.get("title", "").strip() if title_node else "",
                        "category": None,
                        "price": price_node.get_text(" ", strip=True) if price_node else None,
                        "rating": RATINGS.get(rating_name) if rating_name else None,
                        "author": None,
                        "tags": None,
                        "description": None,
                        "availability": availability_node.get_text(" ", strip=True) if availability_node else None,
                        "author_url": None,
                    }
                    if self.include_details and source_url:
                        details = self._get_details(source_url)
                        if details is None:
                            stats["detail_pages_failed"] += 1
                        else:
                            row.update(details)
                    records.append(row)
                except Exception as exc:  # Keep one malformed card from stopping the page.
                    self.logger.exception("Failed to parse a book card on %s: %s", current_url, exc)

            next_node = soup.select_one("li.next a")
            current_url = urljoin(current_url, next_node.get("href")) if next_node else None

        return records, stats

    def _get_details(self, url: str) -> dict | None:
        if url in self._detail_cache:
            return self._detail_cache[url]
        response = self.client.get(url)
        if response is None:
            return None
        soup = BeautifulSoup(response.text, "html.parser")
        detail: dict = {}

        breadcrumb_links = soup.select("ul.breadcrumb li a")
        if breadcrumb_links:
            detail["category"] = breadcrumb_links[-1].get_text(" ", strip=True)

        description_marker = soup.select_one("#product_description")
        if description_marker:
            desc = description_marker.find_next("p")
            if desc:
                detail["description"] = desc.get_text(" ", strip=True)

        availability = soup.select_one(".product_page .availability")
        if availability:
            detail["availability"] = availability.get_text(" ", strip=True)

        rating = soup.select_one(".product_page .star-rating")
        if rating:
            rating_name = next((cls for cls in rating.get("class", []) if cls in RATINGS), None)
            detail["rating"] = RATINGS.get(rating_name)

        self._detail_cache[url] = detail
        return detail
