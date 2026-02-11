from paper_crawler.detail import BasePaperDetailCrawler
from paper_crawler.title import BasePaperTitleCrawler


def test_title_base_redeclares_host_pattern():
    assert "host_pattern" in BasePaperTitleCrawler.__dict__


def test_detail_base_redeclares_host_pattern():
    assert "host_pattern" in BasePaperDetailCrawler.__dict__
