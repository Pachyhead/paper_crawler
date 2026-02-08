from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup
from bs4.element import Tag

from .errors import FetchError, ParseError


class BaseCrawler(ABC):
    """Thin base crawler: shared networking/parsing/retry only."""

    name = "base"
    request_delay_seconds = 0.0
    default_timeout = 10.0
    default_retries = 2
    default_backoff_seconds = 0.5
    user_agent = "paper-crawler/0.1"

    def __init__(
        self,
        *,
        timeout: float | None = None,
        retries: int | None = None,
        backoff_seconds: float | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.request_delay_seconds = max(0.0, float(self.request_delay_seconds))
        self._last_request_at = 0.0
        self.timeout = timeout if timeout is not None else self.default_timeout
        self.retries = retries if retries is not None else self.default_retries
        self.backoff_seconds = (
            backoff_seconds
            if backoff_seconds is not None
            else self.default_backoff_seconds
        )
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def extract_items(self, soup: BeautifulSoup, source_url: str) -> list[dict[str, Any]]:
        """Site-specific parsing logic using direct bs4 code."""

    def crawl(self, url: str) -> list[dict[str, Any]]:
        html = self.fetch_html(url)
        soup = self.parse_html(html)
        items = self.extract_items(soup, url)
        return [self.normalize_item(item, source_url=url) for item in items]

    def fetch_html(self, url: str) -> str:
        last_error: Exception | None = None

        for attempt in range(self.retries + 1):
            try:
                self._apply_request_delay()
                request = Request(
                    url,
                    headers={"User-Agent": self.user_agent},
                )
                with urlopen(request, timeout=self.timeout) as response:
                    charset = response.headers.get_content_charset() or "utf-8"
                    body = response.read()
                    return body.decode(charset, errors="replace")
            except (HTTPError, URLError, TimeoutError, ValueError) as exc:
                last_error = exc
                is_final_try = attempt >= self.retries
                if is_final_try:
                    break

                sleep_time = self.backoff_seconds * (2**attempt)
                self.logger.warning(
                    "Fetch failed for %s (%s). Retry in %.2fs (%d/%d).",
                    url,
                    exc,
                    sleep_time,
                    attempt + 1,
                    self.retries + 1,
                )
                time.sleep(sleep_time)

        raise FetchError(f"Failed to fetch {url}") from last_error

    def _apply_request_delay(self) -> None:
        if self.request_delay_seconds <= 0:
            return

        now = time.monotonic()
        elapsed = now - self._last_request_at
        remaining = self.request_delay_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)
        self._last_request_at = time.monotonic()

    def parse_html(self, html: str) -> BeautifulSoup:
        try:
            return BeautifulSoup(html, "html.parser")
        except Exception as exc:  # pragma: no cover - parser errors are uncommon
            raise ParseError("Failed to parse HTML") from exc

    def text(self, node: Tag | None, default: str | None = None) -> str | None:
        if node is None:
            return default
        return node.get_text(strip=True)

    def attr(self, node: Tag | None, attr_name: str, default: str | None = None) -> str | None:
        if node is None:
            return default
        value = node.get(attr_name)
        if value is None:
            return default
        return str(value).strip()

    def absolute_url(self, base_url: str, href: str | None) -> str | None:
        if not href:
            return None
        return urljoin(base_url, href)

    def normalize_item(self, item: dict[str, Any], *, source_url: str) -> dict[str, Any]:
        normalized = {key: self._normalize_value(value) for key, value in item.items()}
        normalized["source_url"] = source_url
        normalized["crawler"] = self.name
        return normalized

    def _normalize_value(self, value: Any) -> Any:
        if isinstance(value, str):
            return " ".join(value.split())
        if isinstance(value, list):
            return [self._normalize_value(v) for v in value]
        if isinstance(value, dict):
            return {k: self._normalize_value(v) for k, v in value.items()}
        return value
