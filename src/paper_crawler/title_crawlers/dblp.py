from __future__ import annotations

import re

from bs4 import BeautifulSoup

from ..title import BasePaperTitleCrawler


class DblpPaperTitleCrawler(BasePaperTitleCrawler):
    name = "dblp"
    request_delay_seconds = 4.0
    _HOST_PATTERN = re.compile(r"^dblp\.org$")

    @classmethod
    def host_pattern(cls) -> re.Pattern[str]:
        return cls._HOST_PATTERN

    def extract_items(self, soup: BeautifulSoup, source_url: str) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        seen_titles: set[str] = set()

        # Preferred path for DBLP venue pages.
        title_nodes = soup.select("li.entry span.title")

        # Fallback selectors in case DBLP markup changes slightly.
        if not title_nodes:
            title_nodes = soup.select("cite span.title")
        if not title_nodes:
            title_nodes = soup.select("span.title")

        for title_node in title_nodes:
            title = self.text(title_node)
            if not title:
                continue
            if title in seen_titles:
                continue
            seen_titles.add(title)
            items.append({"title": title})

        return items
