from __future__ import annotations

from urllib.parse import urlparse

from .base import BaseCrawler
from .errors import UnsupportedSiteError
from .sites import Dblp, ExampleStaticCrawler, Aclweb


class CrawlerFactory:
    """Create crawler instances from URL domain."""

    # Domain -> crawler class mapping
    domain_map = {
        "dblp.org": Dblp,
        "example.com": ExampleStaticCrawler,
        "2025.aclweb.org": Aclweb
    }

    @classmethod
    def create(cls, url: str, **crawler_kwargs) -> BaseCrawler:
        hostname = (urlparse(url).hostname or "").lower().strip()
        domain = cls._normalize_domain(hostname)
        crawler_class = cls.domain_map.get(domain)
        if crawler_class is None:
            raise UnsupportedSiteError(f"No crawler registered for domain: {domain}")
        return crawler_class(**crawler_kwargs)

    @classmethod
    def crawl(cls, url: str, **crawler_kwargs):
        crawler = cls.create(url, **crawler_kwargs)
        return crawler.crawl(url)

    @staticmethod
    def _normalize_domain(hostname: str) -> str:
        if hostname.startswith("www."):
            return hostname[4:]
        return hostname
