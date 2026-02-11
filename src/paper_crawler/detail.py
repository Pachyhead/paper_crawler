from __future__ import annotations

import re
from abc import abstractmethod

from bs4 import BeautifulSoup

from .base import BasePaperCrawler
from utils.timing_logger import log_execution_time


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
        with log_execution_time(
            "detail_fetch_parse_extract",
            log_path="logs/detail_crawler.log",
            logger_name="detail_crawler",
            context={"crawler": self.name, "url": url},
        ):
            html = self.fetch_html(url)
            soup = self.parse_html(html)
            detail = self.extract_detail(soup, url)
        return self.normalize_detail(detail, detail_url=url)

    def normalize_detail(self, detail: dict[str, str], *, detail_url: str) -> dict[str, str]:
        normalized = {key: self._normalize_value(str(value)) for key, value in detail.items()}
        normalized["detail_url"] = self._normalize_value(detail_url)
        normalized["detail_crawler"] = self._normalize_value(self.name)
        return normalized
