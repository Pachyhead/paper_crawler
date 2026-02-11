from __future__ import annotations

import re

from bs4 import BeautifulSoup

from paper_crawler.detail import BasePaperDetailCrawler
from paper_crawler.factories.detail_factory import DetailCrawlerFactory
from paper_crawler.factories.title_factory import TitleCrawlerFactory
from paper_crawler.orchestrator import PaperCrawlOrchestrator
from paper_crawler.selection import SelectionStrategy, first_match_selector
from paper_crawler.title import BasePaperTitleCrawler


class FakeTitleCrawler(BasePaperTitleCrawler):
    name = "fake-title"

    @classmethod
    def host_pattern(cls) -> re.Pattern[str]:
        return re.compile(r"^list\.example\.com$")

    def extract_items(self, soup: BeautifulSoup, source_url: str) -> list[dict[str, str]]:
        return []

    def crawl(self, url: str) -> list[dict[str, str]]:
        return [
            {"title": "Paper A", "detail_url": "https://example.com/a"},
            {"title": "Paper B", "detail_url": "https://example.com/b"},
            {"title": "Paper C"},
        ]


class FakeDetailCrawler(BasePaperDetailCrawler):
    @classmethod
    def host_pattern(cls) -> re.Pattern[str]:
        return re.compile(r"^conf\.example\.com$")

    def extract_detail(self, soup: BeautifulSoup, detail_url: str) -> dict[str, str]:
        return {}

    def crawl(self, url: str) -> dict[str, str]:
        if url.endswith("/b"):
            raise RuntimeError("detail fetch failed")
        return {"abstract": f"abs:{url}", "pdf_url": f"{url}.pdf"}


def _set_factory_for_test() -> tuple[list[type[BasePaperTitleCrawler]], SelectionStrategy, list[type[BasePaperDetailCrawler]], SelectionStrategy]:
    original_title_crawlers = list(TitleCrawlerFactory.crawler_classes)
    original_title_strategy: SelectionStrategy = TitleCrawlerFactory.selection_strategy
    original_detail_crawlers = list(DetailCrawlerFactory.crawler_classes)
    original_detail_strategy: SelectionStrategy = DetailCrawlerFactory.selection_strategy

    TitleCrawlerFactory.crawler_classes = [FakeTitleCrawler]
    TitleCrawlerFactory.set_strategy(first_match_selector)
    DetailCrawlerFactory.crawler_classes = [FakeDetailCrawler]
    DetailCrawlerFactory.set_strategy(first_match_selector)

    return (
        original_title_crawlers,
        original_title_strategy,
        original_detail_crawlers,
        original_detail_strategy,
    )


def _restore_factory_after_test(
    original_title_crawlers: list[type[BasePaperTitleCrawler]],
    original_title_strategy: SelectionStrategy,
    original_detail_crawlers: list[type[BasePaperDetailCrawler]],
    original_detail_strategy: SelectionStrategy,
) -> None:
    TitleCrawlerFactory.crawler_classes = original_title_crawlers
    TitleCrawlerFactory.set_strategy(original_title_strategy)
    DetailCrawlerFactory.crawler_classes = original_detail_crawlers
    DetailCrawlerFactory.set_strategy(original_detail_strategy)


def test_orchestrator_enriches_details_with_skip_on_error():
    (
        original_title_crawlers,
        original_title_strategy,
        original_detail_crawlers,
        original_detail_strategy,
    ) = _set_factory_for_test()
    try:
        orchestrator = PaperCrawlOrchestrator(continue_on_detail_error=True)
        items = orchestrator.crawl(
            "https://list.example.com/papers",
            "https://conf.example.com/2026",
        )
    finally:
        _restore_factory_after_test(
            original_title_crawlers,
            original_title_strategy,
            original_detail_crawlers,
            original_detail_strategy,
        )

    assert items == [
        {
            "title": "Paper A",
            "abstract": "abs:https://example.com/a",
            "pdf_url": "https://example.com/a.pdf",
        },
        {
            "title": "Paper B",
            "abstract": "",
            "pdf_url": "",
        },
        {
            "title": "Paper C",
            "abstract": "",
            "pdf_url": "",
        },
    ]


def test_orchestrator_can_raise_on_detail_error():
    (
        original_title_crawlers,
        original_title_strategy,
        original_detail_crawlers,
        original_detail_strategy,
    ) = _set_factory_for_test()
    try:
        orchestrator = PaperCrawlOrchestrator(continue_on_detail_error=False)
        orchestrator.crawl(
            "https://list.example.com/papers",
            "https://conf.example.com/2026",
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError("Expected RuntimeError was not raised")
    finally:
        _restore_factory_after_test(
            original_title_crawlers,
            original_title_strategy,
            original_detail_crawlers,
            original_detail_strategy,
        )
