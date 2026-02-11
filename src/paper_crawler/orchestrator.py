from __future__ import annotations

import logging

from .factories.detail_factory import DetailCrawlerFactory
from .factories.title_factory import TitleCrawlerFactory
import time

class PaperCrawlOrchestrator:
    """
    Orchestrate title/detail crawling through factories.

    Flow:
    1. Build title crawler from titles_url
    2. Build detail crawler from conference_url
    3. Merge to final schema: {title, abstract, pdf_url}
    """

    def __init__(
        self,
        *,
        title_factory: type[TitleCrawlerFactory] = TitleCrawlerFactory,
        detail_factory: type[DetailCrawlerFactory] = DetailCrawlerFactory,
        logger: logging.Logger | None = None,
        continue_on_detail_error: bool = True,
    ) -> None:
        self.title_factory = title_factory
        self.detail_factory = detail_factory
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.continue_on_detail_error = continue_on_detail_error

    def crawl(
        self,
        titles_url: str,
        conference_url: str,
        *,
        detail_url_field: str = "detail_url",
    ) -> list[dict[str, str]]:
        title_crawler = self.title_factory.create(titles_url)
        detail_crawler = self.detail_factory.create(conference_url)
        title_items = title_crawler.crawl(titles_url)
        return self._compose_final_items(
            title_items,
            detail_crawler=detail_crawler,
            detail_url_field=detail_url_field,
        )

    def _compose_final_items(
        self,
        title_items: list[dict[str, str]],
        *,
        detail_crawler,
        detail_url_field: str,
    ) -> list[dict[str, str]]:
        results: list[dict[str, str]] = []
        for i, item in enumerate(title_items):
            title = item.get("title", "")
            detail_url = item.get(detail_url_field)

            abstract = ""
            pdf_url = ""

            if not isinstance(detail_url, str) or not detail_url or i > 40:
                results.append(
                    {
                        "title": title,
                        "abstract": abstract,
                        "pdf_url": pdf_url,
                    }
                )
                continue

            try:
                time.sleep(0.1)
                detail_fields = detail_crawler.crawl(detail_url)
                abstract = detail_fields.get("abstract", "")
                pdf_url = detail_fields.get("pdf_url", "")
            except Exception as exc:
                if not self.continue_on_detail_error:
                    raise
                self.logger.warning(
                    "Detail extraction failed for %s (%s). Use empty values.",
                    detail_url,
                    exc,
                )
            results.append(
                {
                    "title": title,
                    "abstract": abstract,
                    "pdf_url": pdf_url,
                }
            )

        return results
