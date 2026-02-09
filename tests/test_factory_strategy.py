from __future__ import annotations

from collections.abc import Sequence

from bs4 import BeautifulSoup

from paper_crawler.base import BaseCrawler
from paper_crawler.factory import CrawlerFactory
from paper_crawler.selection import SelectionStrategy, first_match_selector


class AlwaysFirst(BaseCrawler):
    name = "always-first"

    @classmethod
    def can_handle(cls, url: str) -> bool:
        return True

    def extract_items(self, soup: BeautifulSoup, source_url: str):
        return []


class AlwaysSecond(BaseCrawler):
    name = "always-second"

    @classmethod
    def can_handle(cls, url: str) -> bool:
        return True

    def extract_items(self, soup: BeautifulSoup, source_url: str):
        return []


def pick_last_strategy(url: str, crawler_classes: Sequence[type[BaseCrawler]]):
    for crawler_class in reversed(crawler_classes):
        if crawler_class.can_handle(url):
            return crawler_class
    return None


def test_factory_default_strategy_is_first_match():
    original_crawlers = list(CrawlerFactory.crawler_classes)
    original_strategy: SelectionStrategy = CrawlerFactory.selection_strategy
    try:
        CrawlerFactory.crawler_classes = [AlwaysFirst, AlwaysSecond]
        CrawlerFactory.set_strategy(first_match_selector)
        crawler = CrawlerFactory.create("https://anything.test")
        assert isinstance(crawler, AlwaysFirst)
    finally:
        CrawlerFactory.crawler_classes = original_crawlers
        CrawlerFactory.set_strategy(original_strategy)


def test_factory_strategy_can_be_replaced():
    original_crawlers = list(CrawlerFactory.crawler_classes)
    original_strategy: SelectionStrategy = CrawlerFactory.selection_strategy
    try:
        CrawlerFactory.crawler_classes = [AlwaysFirst, AlwaysSecond]
        CrawlerFactory.set_strategy(pick_last_strategy)
        crawler = CrawlerFactory.create("https://anything.test")
        assert isinstance(crawler, AlwaysSecond)
    finally:
        CrawlerFactory.crawler_classes = original_crawlers
        CrawlerFactory.set_strategy(original_strategy)
