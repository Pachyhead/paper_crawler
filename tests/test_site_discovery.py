from paper_crawler.factories.title_factory import TitleCrawlerFactory
from paper_crawler.title_crawlers import (
    AclwebPaperTitleCrawler,
    DblpPaperTitleCrawler,
    ExampleStaticPaperTitleCrawler,
    get_title_crawlers,
)


def test_site_auto_discovery_contains_known_crawlers():
    discovered = get_title_crawlers()
    assert AclwebPaperTitleCrawler in discovered
    assert DblpPaperTitleCrawler in discovered
    assert ExampleStaticPaperTitleCrawler in discovered


def test_factory_uses_discovered_crawlers_by_default():
    assert AclwebPaperTitleCrawler in TitleCrawlerFactory.crawler_classes
    assert DblpPaperTitleCrawler in TitleCrawlerFactory.crawler_classes
    assert ExampleStaticPaperTitleCrawler in TitleCrawlerFactory.crawler_classes
