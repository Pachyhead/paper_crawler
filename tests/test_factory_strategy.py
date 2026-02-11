from __future__ import annotations

from collections.abc import Sequence
import re

from bs4 import BeautifulSoup

from paper_crawler.title import BasePaperTitleCrawler
from paper_crawler.factories.title_factory import TitleCrawlerFactory
from paper_crawler.selection import SelectionStrategy, first_match_selector


class AlwaysFirst(BasePaperTitleCrawler):
    name = "always-first"

    @classmethod
    def host_pattern(cls) -> re.Pattern[str]:
        return re.compile(r".+")

    def extract_items(self, soup: BeautifulSoup, source_url: str):
        return []


class AlwaysSecond(BasePaperTitleCrawler):
    name = "always-second"

    @classmethod
    def host_pattern(cls) -> re.Pattern[str]:
        return re.compile(r".+")

    def extract_items(self, soup: BeautifulSoup, source_url: str):
        return []


def pick_last_strategy(url: str, crawler_classes: Sequence[type[BasePaperTitleCrawler]]):
    for crawler_class in reversed(crawler_classes):
        if crawler_class.can_handle(url):
            return crawler_class
    return None


def test_factory_default_strategy_is_first_match():
    original_crawlers = list(TitleCrawlerFactory.crawler_classes)
    original_strategy: SelectionStrategy = TitleCrawlerFactory.selection_strategy
    try:
        TitleCrawlerFactory.crawler_classes = [AlwaysFirst, AlwaysSecond]
        TitleCrawlerFactory.set_strategy(first_match_selector)
        crawler = TitleCrawlerFactory.create("https://anything.test")
        assert isinstance(crawler, AlwaysFirst)
    finally:
        TitleCrawlerFactory.crawler_classes = original_crawlers
        TitleCrawlerFactory.set_strategy(original_strategy)


def test_factory_strategy_can_be_replaced():
    original_crawlers = list(TitleCrawlerFactory.crawler_classes)
    original_strategy: SelectionStrategy = TitleCrawlerFactory.selection_strategy
    try:
        TitleCrawlerFactory.crawler_classes = [AlwaysFirst, AlwaysSecond]
        TitleCrawlerFactory.set_strategy(pick_last_strategy)
        crawler = TitleCrawlerFactory.create("https://anything.test")
        assert isinstance(crawler, AlwaysSecond)
    finally:
        TitleCrawlerFactory.crawler_classes = original_crawlers
        TitleCrawlerFactory.set_strategy(original_strategy)
