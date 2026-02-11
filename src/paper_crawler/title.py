from __future__ import annotations

import re
from abc import abstractmethod

from bs4 import BeautifulSoup

from .base import BasePaperCrawler


class BasePaperTitleCrawler(BasePaperCrawler):
    """Base class for crawlers that extract title list pages."""

    @classmethod
    @abstractmethod
    def host_pattern(cls) -> re.Pattern[str]:
        """Return hostname-matching regex for title crawling."""

    @abstractmethod
    def extract_items(self, soup: BeautifulSoup, source_url: str) -> list[dict[str, str]]:
        """Extract list-level paper items from parsed HTML."""

    def crawl(self, url: str) -> list[dict[str, str]]:
        html = self.fetch_html(url)
        soup = self.parse_html(html)
        items = self.extract_items(soup, url)
        return [self.normalize_item(item, source_url=url) for item in items]
