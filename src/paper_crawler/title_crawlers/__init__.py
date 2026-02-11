from __future__ import annotations

import inspect
from functools import lru_cache
from importlib import import_module
from pkgutil import iter_modules
from typing import Type

from ..title import BasePaperTitleCrawler


@lru_cache(maxsize=1)
def get_title_crawlers() -> list[Type[BasePaperTitleCrawler]]:
    """Auto-discover crawler classes under this package."""
    crawlers: list[Type[BasePaperTitleCrawler]] = []
    seen: set[Type[BasePaperTitleCrawler]] = set()

    for module_info in iter_modules(__path__):
        if module_info.name.startswith("_"):
            continue
        module = import_module(f"{__name__}.{module_info.name}")
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if obj is BasePaperTitleCrawler:
                continue
            if not issubclass(obj, BasePaperTitleCrawler):
                continue
            # Keep only classes declared in the module itself.
            if obj.__module__ != module.__name__:
                continue
            if obj in seen:
                continue
            seen.add(obj)
            crawlers.append(obj)

    # Deterministic order for first-match strategy.
    crawlers.sort(key=lambda crawler_cls: crawler_cls.__name__)
    return crawlers


for _crawler_cls in get_title_crawlers():
    globals()[_crawler_cls.__name__] = _crawler_cls

_exports = {"get_title_crawlers"}
_exports.update(crawler.__name__ for crawler in get_title_crawlers())

__all__ = sorted(_exports)
