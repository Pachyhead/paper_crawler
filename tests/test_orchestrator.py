from __future__ import annotations

import re

from bs4 import BeautifulSoup

from paper_crawler.detail import BasePaperDetailCrawler
from paper_crawler.orchestrator import PaperCrawlOrchestrator
from paper_crawler.title import BasePaperTitleCrawler


class FakeTitleCrawler(BasePaperTitleCrawler):
    name = "fake-title"

    @classmethod
    def host_pattern(cls) -> re.Pattern[str]:
        return re.compile(r".+")

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
        return re.compile(r".+")

    def extract_detail(self, detail_url: str) -> dict[str, str]:
        if detail_url.endswith("/b"):
            raise RuntimeError("detail fetch failed")
        return {"abstract": f"abs:{detail_url}", "pdf_url": f"{detail_url}.pdf"}


def test_orchestrator_enriches_details_with_skip_on_error():
    orchestrator = PaperCrawlOrchestrator(
        title_crawler=FakeTitleCrawler(),
        detail_crawler=FakeDetailCrawler(),
        continue_on_detail_error=True,
    )
    items = orchestrator.crawl("https://example.com/list")

    assert items[0]["abstract"] == "abs:https://example.com/a"
    assert items[0]["pdf_url"] == "https://example.com/a.pdf"
    assert "abstract" not in items[1]
    assert items[2]["title"] == "Paper C"


def test_orchestrator_can_skip_detail_phase():
    orchestrator = PaperCrawlOrchestrator(
        title_crawler=FakeTitleCrawler(),
        detail_crawler=FakeDetailCrawler(),
    )
    items = orchestrator.crawl("https://example.com/list", include_detail=False)

    assert items == [
        {"title": "Paper A", "detail_url": "https://example.com/a"},
        {"title": "Paper B", "detail_url": "https://example.com/b"},
        {"title": "Paper C"},
    ]


def test_orchestrator_can_raise_on_detail_error():
    orchestrator = PaperCrawlOrchestrator(
        title_crawler=FakeTitleCrawler(),
        detail_crawler=FakeDetailCrawler(),
        continue_on_detail_error=False,
    )
    try:
        orchestrator.crawl("https://example.com/list")
    except RuntimeError:
        pass
    else:
        raise AssertionError("Expected RuntimeError was not raised")
