from __future__ import annotations

import inspect
from functools import lru_cache
from importlib import import_module
from pkgutil import iter_modules
from typing import Type

from ..detail import BasePaperDetailCrawler


@lru_cache(maxsize=1)
def get_detail_crawlers() -> list[Type[BasePaperDetailCrawler]]:
    """Auto-discover detail crawler classes under this package."""
    crawlers: list[Type[BasePaperDetailCrawler]] = []
    seen: set[Type[BasePaperDetailCrawler]] = set()

    for module_info in iter_modules(__path__):
        if module_info.name.startswith("_"):
            continue
        module = import_module(f"{__name__}.{module_info.name}")
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if obj is BasePaperDetailCrawler:
                continue
            if not issubclass(obj, BasePaperDetailCrawler):
                continue
            if obj.__module__ != module.__name__:
                continue
            if obj in seen:
                continue
            seen.add(obj)
            crawlers.append(obj)

    crawlers.sort(key=lambda crawler_cls: crawler_cls.__name__)
    return crawlers


for _crawler_cls in get_detail_crawlers():
    globals()[_crawler_cls.__name__] = _crawler_cls

_exports = {"get_detail_crawlers"}
_exports.update(crawler.__name__ for crawler in get_detail_crawlers())

__all__ = sorted(_exports)
