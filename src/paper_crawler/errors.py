class CrawlerError(Exception):
    """Base exception for crawler module."""


class FetchError(CrawlerError):
    """Raised when HTTP fetch fails after retries."""


class ParseError(CrawlerError):
    """Raised when HTML parsing fails."""


class UnsupportedSiteError(CrawlerError):
    """Raised when no crawler can handle a target URL."""
