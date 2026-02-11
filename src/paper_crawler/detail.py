from __future__ import annotations

import re
from abc import abstractmethod

from bs4 import BeautifulSoup

from .base import BasePaperCrawler


class BasePaperDetailCrawler(BasePaperCrawler):
    """Abstract interface for extracting paper details from a detail URL."""

    @classmethod
    @abstractmethod
    def host_pattern(cls) -> re.Pattern[str]:
        """Return hostname-matching regex for detail crawling."""

    @abstractmethod
    def extract_detail(self, soup: BeautifulSoup, detail_url: str) -> dict[str, str]:
        """Return detail fields such as abstract/pdf_url for a single paper."""

    def crawl(self, url: str) -> dict[str, str]:
        html = self.fetch_html(url)
        soup = self.parse_html(html)
        detail = self.extract_detail(soup, url)
        return self.normalize_detail(detail, detail_url=url)

    def normalize_detail(self, detail: dict[str, str], *, detail_url: str) -> dict[str, str]:
        normalized = {key: self._normalize_value(str(value)) for key, value in detail.items()}
        normalized["detail_url"] = self._normalize_value(detail_url)
        normalized["detail_crawler"] = self._normalize_value(self.name)
        return normalized
