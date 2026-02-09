from paper_crawler.factory import CrawlerFactory
from paper_crawler.sites import Aclweb, Dblp, ExampleStaticCrawler, get_site_crawlers


def test_site_auto_discovery_contains_known_crawlers():
    discovered = get_site_crawlers()
    assert Aclweb in discovered
    assert Dblp in discovered
    assert ExampleStaticCrawler in discovered


def test_factory_uses_discovered_crawlers_by_default():
    assert Aclweb in CrawlerFactory.crawler_classes
    assert Dblp in CrawlerFactory.crawler_classes
    assert ExampleStaticCrawler in CrawlerFactory.crawler_classes
