from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from typing import Optional

import requests
from requests import Response


@dataclass
class HttpClient:
    timeout: float = 20.0
    retries: int = 3
    backoff_factor: float = 0.5
    delay: float = 0.2
    user_agent: str = "Realisieren-Technologies-Scraper/1.0"

    def __post_init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})
        self.logger = logging.getLogger(self.__class__.__name__)
        self._last_request_at = 0.0

    def get(self, url: str) -> Optional[Response]:
        if self.delay > 0:
            elapsed = time.monotonic() - self._last_request_at
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)

        for attempt in range(self.retries + 1):
            try:
                self.logger.debug("GET %s (attempt %s)", url, attempt + 1)
                response = self.session.get(url, timeout=self.timeout)
                self._last_request_at = time.monotonic()
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                self._last_request_at = time.monotonic()
                if attempt >= self.retries:
                    self.logger.error("Request failed permanently: %s | %s", url, exc)
                    return None
                sleep_for = self.backoff_factor * (2**attempt) + random.uniform(0, 0.2)
                self.logger.warning("Request failed: %s | retrying in %.2fs", exc, sleep_for)
                time.sleep(sleep_for)
        return None
