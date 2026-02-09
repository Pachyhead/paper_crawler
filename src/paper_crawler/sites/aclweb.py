from __future__ import annotations

from bs4 import BeautifulSoup

from ..base import BaseCrawler


class Aclweb(BaseCrawler):
    name = "aclweb"
    request_delay_seconds = 4.0

    def extract_items(self, soup: BeautifulSoup, source_url: str):
        items: list[dict] = []
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
