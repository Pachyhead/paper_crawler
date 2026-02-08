from __future__ import annotations

from bs4 import BeautifulSoup

from ..base import BaseCrawler


class ExampleStaticCrawler(BaseCrawler):
    name = "example-static"
    request_delay_seconds = 4.0

    def extract_items(self, soup: BeautifulSoup, source_url: str):
        items: list[dict] = []

        # Site-specific parsing intentionally uses raw bs4 selectors.
        for card in soup.select("article.paper-card"):
            title_node = card.select_one("h2.title")
            link_node = card.select_one("a.title-link")

            title = self.text(title_node)
            href = self.attr(link_node, "href")
            if not title or not href:
                continue

            author_nodes = card.select("span.author")
            authors = [self.text(node) for node in author_nodes if self.text(node)]

            item = {
                "title": title,
                "url": self.absolute_url(source_url, href),
                "authors": authors,
                "published_at": self.text(card.select_one("time.published-at")),
                "abstract": self.text(card.select_one("p.abstract")),
            }
            items.append(item)

        return items
