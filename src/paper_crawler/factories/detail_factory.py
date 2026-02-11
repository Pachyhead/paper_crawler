from __future__ import annotations

from typing import Any

from ..detail import BasePaperDetailCrawler
from ..detail_crawlers import get_detail_crawlers
from ..errors import UnsupportedSiteError
from ..selection import SelectionStrategy, first_match_selector


class DetailCrawlerFactory:
    """Create detail crawler instances from detail URL."""

    crawler_classes: list[type[BasePaperDetailCrawler]] = get_detail_crawlers()
    selection_strategy: SelectionStrategy = first_match_selector

    @classmethod
    def create(cls, detail_url: str, **crawler_kwargs: Any) -> BasePaperDetailCrawler:
        crawler_class = cls.selection_strategy(detail_url, cls.crawler_classes)
        if crawler_class is None:
            raise UnsupportedSiteError(f"No detail crawler can handle URL: {detail_url}")
        return crawler_class(**crawler_kwargs)

    @classmethod
    def crawl(cls, detail_url: str, **crawler_kwargs: Any) -> dict[str, str]:
        crawler = cls.create(detail_url, **crawler_kwargs)
        return crawler.crawl(detail_url)

    @classmethod
    def set_strategy(cls, strategy: SelectionStrategy) -> None:
        cls.selection_strategy = strategy
