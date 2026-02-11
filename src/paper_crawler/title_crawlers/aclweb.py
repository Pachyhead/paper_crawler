from __future__ import annotations

import re

from bs4 import BeautifulSoup

from ..title import BasePaperTitleCrawler


class AclwebPaperTitleCrawler(BasePaperTitleCrawler):
    name = "aclweb"
    request_delay_seconds = 4.0
    _HOST_PATTERN = re.compile(r"^\d{4}\.aclweb\.org$")

    @classmethod
    def host_pattern(cls) -> re.Pattern[str]:
        return cls._HOST_PATTERN

    def extract_items(self, soup: BeautifulSoup, source_url: str) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        seen_titles: set[str] = set()

        title_nodes = soup.select("section.page__content ul li strong")

        for title_node in title_nodes:
            title = self.text(title_node)
            if not title:
                continue
            if title in seen_titles:
                continue
            seen_titles.add(title)
            items.append({"title": title})

        return items
