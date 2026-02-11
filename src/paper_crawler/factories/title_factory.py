from __future__ import annotations

from typing import Any

from ..errors import UnsupportedSiteError
from ..selection import SelectionStrategy, first_match_selector
from ..title import BasePaperTitleCrawler
from ..title_crawlers import get_title_crawlers


class TitleCrawlerFactory:
    """Create title crawler instances from URL."""

    crawler_classes: list[type[BasePaperTitleCrawler]] = get_title_crawlers()
    selection_strategy: SelectionStrategy = first_match_selector

    @classmethod
    def create(cls, url: str, **crawler_kwargs: Any) -> BasePaperTitleCrawler:
        crawler_class = cls.selection_strategy(url, cls.crawler_classes)
        if crawler_class is None:
            raise UnsupportedSiteError(f"No title crawler can handle URL: {url}")
        return crawler_class(**crawler_kwargs)

    @classmethod
    def crawl(cls, url: str, **crawler_kwargs: Any) -> list[dict[str, str]]:
        crawler = cls.create(url, **crawler_kwargs)
        return crawler.crawl(url)

    @classmethod
    def set_strategy(cls, strategy: SelectionStrategy) -> None:
        cls.selection_strategy = strategy
