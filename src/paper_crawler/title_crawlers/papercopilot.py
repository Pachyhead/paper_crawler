from __future__ import annotations

import re

from bs4 import BeautifulSoup

from paper_crawler.title import BasePaperTitleCrawler


class PaperCopilotPaperTitleCrawler(BasePaperTitleCrawler):
    name = "papercopilot"
    request_delay_seconds = 4.0
    _HOST_PATTERN = re.compile(r"^papercopilot\.com$")

    @classmethod
    def host_pattern(cls) -> re.Pattern[str]:
        return cls._HOST_PATTERN

    def extract_items(self, soup: BeautifulSoup, source_url: str) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        seen_titles: set[str] = set()

        table = soup.select_one("table#paperlist")
        breakpoint()
        for tr in table.select("tr"):
            tds = tr.find_all("td", recursive=False)  
            a  = tds[1].find("a")                              
            title = self.text(a)
            if not title:
                continue
            if title in seen_titles:
                continue
            seen_titles.add(title)
            items.append({"title": title})

        return items
