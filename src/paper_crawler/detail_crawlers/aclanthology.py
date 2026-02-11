from __future__ import annotations

import re

from bs4 import BeautifulSoup

from ..detail import BasePaperDetailCrawler

class AclanthologyPaperDetailCrawler(BasePaperDetailCrawler):
    name = "aclanthology"
    request_delay_seconds = 4.0
    _HOST_PATTERN = re.compile(r"^aclanthology\.org$")

    @classmethod
    def host_pattern(cls) -> re.Pattern[str]:
        return cls._HOST_PATTERN

    def extract_detail(self, soup: BeautifulSoup, detail_url: str) -> dict[str, str]:
        abstract = self.text(soup.select_one("div.card-body.acl-abstract > span")) or ""
        pdf_url = self.attr(soup.select_one("div.acl-paper-link-block a"), "href") or ""
        return {
            "abstract": abstract,
            "pdf_url": pdf_url,
        }
