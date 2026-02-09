from __future__ import annotations

from .base import BaseCrawler
from .errors import UnsupportedSiteError
from .selection import SelectionStrategy, first_match_selector
from .sites import get_site_crawlers


class CrawlerFactory:
    """Create crawler instances from URL using a pluggable selection strategy."""

    crawler_classes: list[type[BaseCrawler]] = get_site_crawlers()
    selection_strategy: SelectionStrategy = first_match_selector

    @classmethod
    def create(cls, url: str, **crawler_kwargs) -> BaseCrawler:
        crawler_class = cls.selection_strategy(url, cls.crawler_classes)
        if crawler_class is None:
            raise UnsupportedSiteError(f"No crawler can handle URL: {url}")
        return crawler_class(**crawler_kwargs)

    @classmethod
    def crawl(cls, url: str, **crawler_kwargs):
        crawler = cls.create(url, **crawler_kwargs)
        return crawler.crawl(url)

    @classmethod
    def set_strategy(cls, strategy: SelectionStrategy) -> None:
        cls.selection_strategy = strategy
