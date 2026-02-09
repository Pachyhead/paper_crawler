from __future__ import annotations

from collections.abc import Callable, Sequence

from .base import BaseCrawler

SelectionStrategy = Callable[[str, Sequence[type[BaseCrawler]]], type[BaseCrawler] | None]


def first_match_selector(
    url: str,
    crawler_classes: Sequence[type[BaseCrawler]],
) -> type[BaseCrawler] | None:
    """Return the first crawler class that can handle the URL."""
    for crawler_class in crawler_classes:
        if crawler_class.can_handle(url):
            return crawler_class
    return None
