from __future__ import annotations

import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .http_client import HttpClient


class QuotesToScrape:
    source = "Quotes to Scrape"
    start_url = "https://quotes.toscrape.com/page/1/"

    def __init__(self, client: HttpClient, include_author_details: bool = True) -> None:
        self.client = client
        self.include_author_details = include_author_details
        self.logger = logging.getLogger(self.__class__.__name__)
        self._author_cache: dict[str, dict] = {}

    def scrape(self, max_pages: int = 0) -> tuple[list[dict], dict]:
        records: list[dict] = []
        stats = {"pages_requested": 0, "pages_failed": 0, "author_pages_failed": 0}
        current_url = self.start_url

        while current_url and (max_pages <= 0 or stats["pages_requested"] < max_pages):
            stats["pages_requested"] += 1
            response = self.client.get(current_url)
            if response is None:
                stats["pages_failed"] += 1
                self.logger.error("Skipping page after request failure: %s", current_url)
                break

            soup = BeautifulSoup(response.text, "html.parser")
            quote_nodes = soup.select("div.quote")
            if not quote_nodes:
                self.logger.warning("No quote blocks found on %s", current_url)

            for quote in quote_nodes:
                try:
                    text_node = quote.select_one("span.text")
                    author_node = quote.select_one("small.author")
                    author_link = quote.select_one("span a")
                    tags = [tag.get_text(" ", strip=True) for tag in quote.select("div.tags a.tag")]
                    author_url = urljoin(current_url, author_link.get("href", "")) if author_link else None

                    row = {
                        "source": self.source,
                        "source_url": current_url,
                        "name_or_title": text_node.get_text(" ", strip=True) if text_node else "",
                        "category": None,
                        "price": None,
                        "rating": None,
                        "author": author_node.get_text(" ", strip=True) if author_node else None,
                        "tags": tags,
                        "description": None,
                        "availability": None,
                        "author_url": author_url,
                    }

                    if self.include_author_details and author_url:
                        details = self._get_author_details(author_url)
                        if details is None:
                            stats["author_pages_failed"] += 1
                        else:
                            row.update(details)
                    records.append(row)
                except Exception as exc:
                    self.logger.exception("Failed to parse quote on %s: %s", current_url, exc)

            next_node = soup.select_one("nav li.next a")
            current_url = urljoin(current_url, next_node.get("href")) if next_node else None

        return records, stats

    def _get_author_details(self, url: str) -> dict | None:
        if url in self._author_cache:
            return self._author_cache[url]
        response = self.client.get(url)
        if response is None:
            return None
        soup = BeautifulSoup(response.text, "html.parser")
        detail: dict = {}
        description = soup.select_one(".author-description")
        if description:
            detail["description"] = description.get_text(" ", strip=True)
        self._author_cache[url] = detail
        return detail
