from __future__ import annotations

import re

from bs4 import BeautifulSoup

from ..title import BasePaperTitleCrawler


class ExampleStaticPaperTitleCrawler(BasePaperTitleCrawler):
    name = "example-static"
    request_delay_seconds = 4.0
    _HOST_PATTERN = re.compile(r"^example\.com$")

    @classmethod
    def host_pattern(cls) -> re.Pattern[str]:
        return cls._HOST_PATTERN

    def extract_items(self, soup: BeautifulSoup, source_url: str) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []

        # Site-specific parsing intentionally uses raw bs4 selectors.
        for card in soup.select("article.paper-card"):
            title_node = card.select_one("h2.title")
            link_node = card.select_one("a.title-link")

            title = self.text(title_node)
            href = self.attr(link_node, "href")
            if not title or not href:
                continue

            author_nodes = card.select("span.author")
            authors = [author for node in author_nodes if (author := self.text(node))]
            url = self.absolute_url(source_url, href)
            if not url:
                continue

            item = {
                "title": title,
                "url": url,
                "authors": ", ".join(authors),
                "published_at": self.text(card.select_one("time.published-at")) or "",
                "abstract": self.text(card.select_one("p.abstract")) or "",
            }
            items.append(item)

        return items
