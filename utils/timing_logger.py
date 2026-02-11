from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


def get_file_logger(
    *,
    log_path: str | Path,
    logger_name: str = "execution_timer",
    level: int = logging.INFO,
) -> logging.Logger:
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    resolved_path = path.resolve()

    logger = logging.getLogger(f"{logger_name}:{resolved_path}")
    logger.setLevel(level)
    logger.propagate = False

    has_target_handler = any(
        isinstance(handler, logging.FileHandler)
        and Path(handler.baseFilename).resolve() == resolved_path
        for handler in logger.handlers
    )
    if not has_target_handler:
        handler = logging.FileHandler(resolved_path, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        )
        logger.addHandler(handler)

    return logger


@contextmanager
def log_execution_time(
    block_name: str,
    *,
    log_path: str | Path = "logs/execution.log",
    logger_name: str = "execution_timer",
    level: int = logging.INFO,
    logger: logging.Logger | None = None,
    context: dict[str, Any] | None = None,
) -> Iterator[None]:
    """
    Measure block execution time and append it to a log file.

    Example:
        with log_execution_time("crawl_emnlp"):
            run_crawler()
    """
    target_logger = logger or get_file_logger(
        log_path=log_path,
        logger_name=logger_name,
        level=level,
    )
    start = time.perf_counter()
    status = "success"
    error_text = ""
    try:
        yield
    except Exception as exc:
        status = "failed"
        error_text = f"{type(exc).__name__}:{exc}"
        raise
    finally:
        elapsed = time.perf_counter() - start
        message = f"{block_name} status={status} elapsed_sec={elapsed:.4f}"
        if context:
            context_text = " ".join(
                f"{key}={value}" for key, value in sorted(context.items())
            )
            message = f"{message} | {context_text}"
        if error_text:
            message = f"{message} | error={error_text}"

        log_level = level if status == "success" else logging.ERROR
        target_logger.log(log_level, message)
