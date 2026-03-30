from __future__ import annotations

import re
from abc import abstractmethod
import time
from typing import Tuple

from bs4 import BeautifulSoup

from paper_crawler.base import BasePaperCrawler
from utils.timing_logger import log_execution_time

class BasePaperDetailCrawler(BasePaperCrawler):
    """Abstract interface for extracting paper details from a detail URL."""

    @classmethod
    @abstractmethod
    def host_pattern(cls) -> re.Pattern[str]:
        """Return hostname-matching regex for detail crawling."""

    @abstractmethod
    def extract_detail(self, soup: BeautifulSoup, detail_url: str) -> Tuple[str, str]:
        """Return detail fields such as abstract/pdf_url for a single paper."""

    def crawl(self, url: str) -> Tuple[str, str]:
        with log_execution_time(
            "detail_fetch_parse_extract",
            log_path="logs/detail_crawler.log",
            logger_name="detail_crawler",
            context={"crawler": self.name, "url": url},
        ):
            time.sleep(0.1)
            html = self.fetch_html(url)
            soup = self.parse_html(html)
            detail = self.extract_detail(soup, url)
        return self.normalize_detail(detail)

    def normalize_detail(self, detail: Tuple[str, str]) -> Tuple[str, str]:
        return tuple(map(self._normalize_value, detail))
