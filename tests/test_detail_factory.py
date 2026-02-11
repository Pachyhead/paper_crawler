from __future__ import annotations

import re

from paper_crawler.detail import BasePaperDetailCrawler
from paper_crawler.factories.detail_factory import DetailCrawlerFactory
from paper_crawler.errors import UnsupportedSiteError
from paper_crawler.selection import SelectionStrategy, first_match_selector


class DetailA(BasePaperDetailCrawler):
    @classmethod
    def host_pattern(cls) -> re.Pattern[str]:
        return re.compile(r"^a\.example\.com$")

    def extract_detail(self, detail_url: str) -> dict[str, str]:
        return {"abstract": "A"}


class DetailAny(BasePaperDetailCrawler):
    @classmethod
    def host_pattern(cls) -> re.Pattern[str]:
        return re.compile(r".+")

    def extract_detail(self, detail_url: str) -> dict[str, str]:
        return {"abstract": "ANY"}


def pick_last_strategy(url: str, crawler_classes: list[type[BasePaperDetailCrawler]]):
    for crawler_class in reversed(crawler_classes):
        if crawler_class.can_handle(url):
            return crawler_class
    return None


def test_detail_factory_first_match():
    original_crawlers = list(DetailCrawlerFactory.crawler_classes)
    original_strategy: SelectionStrategy = DetailCrawlerFactory.selection_strategy
    try:
        DetailCrawlerFactory.crawler_classes = [DetailA, DetailAny]
        DetailCrawlerFactory.set_strategy(first_match_selector)
        crawler = DetailCrawlerFactory.create("https://a.example.com/detail/1")
        assert isinstance(crawler, DetailA)
    finally:
        DetailCrawlerFactory.crawler_classes = original_crawlers
        DetailCrawlerFactory.set_strategy(original_strategy)


def test_detail_factory_strategy_replaceable():
    original_crawlers = list(DetailCrawlerFactory.crawler_classes)
    original_strategy: SelectionStrategy = DetailCrawlerFactory.selection_strategy
    try:
        DetailCrawlerFactory.crawler_classes = [DetailA, DetailAny]
        DetailCrawlerFactory.set_strategy(pick_last_strategy)
        crawler = DetailCrawlerFactory.create("https://a.example.com/detail/1")
        assert isinstance(crawler, DetailAny)
    finally:
        DetailCrawlerFactory.crawler_classes = original_crawlers
        DetailCrawlerFactory.set_strategy(original_strategy)


def test_detail_factory_raises_when_unmatched():
    original_crawlers = list(DetailCrawlerFactory.crawler_classes)
    original_strategy: SelectionStrategy = DetailCrawlerFactory.selection_strategy
    try:
        DetailCrawlerFactory.crawler_classes = [DetailA]
        DetailCrawlerFactory.set_strategy(first_match_selector)
        try:
            DetailCrawlerFactory.create("https://unknown.example.com/detail/1")
        except UnsupportedSiteError:
            pass
        else:
            raise AssertionError("Expected UnsupportedSiteError was not raised")
    finally:
        DetailCrawlerFactory.crawler_classes = original_crawlers
        DetailCrawlerFactory.set_strategy(original_strategy)
