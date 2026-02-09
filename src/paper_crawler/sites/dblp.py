from __future__ import annotations

from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ..base import BaseCrawler


class Dblp(BaseCrawler):
    name = "dblp"
    request_delay_seconds = 4.0

    @classmethod
    def can_handle(cls, url: str) -> bool:
        hostname = (urlparse(url).hostname or "").lower().strip()
        if hostname.startswith("www."):
            hostname = hostname[4:]
        return hostname == "dblp.org"

    def extract_items(self, soup: BeautifulSoup, source_url: str):
        items: list[dict] = []
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
