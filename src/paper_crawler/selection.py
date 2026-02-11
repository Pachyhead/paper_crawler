from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol, TypeVar


class _SupportsCanHandle(Protocol):
    @classmethod
    def can_handle(cls, url: str) -> bool:
        ...


_CrawlerT = TypeVar("_CrawlerT", bound=_SupportsCanHandle)

SelectionStrategy = Callable[[str, Sequence[type[_CrawlerT]]], type[_CrawlerT] | None]


def first_match_selector(
    url: str,
    crawler_classes: Sequence[type[_CrawlerT]],
) -> type[_CrawlerT] | None:
    """Return the first crawler class that can handle the URL."""
    for crawler_class in crawler_classes:
        if crawler_class.can_handle(url):
            return crawler_class
    return None
