from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from paper_crawler.factories.detail_factory import DetailCrawlerFactory
from utils.timing_logger import get_file_logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run ACL Anthology detail crawler for a single URL.",
    )
    parser.add_argument(
        "--url",
        required=True,
    )
    return parser.parse_args()


def run(url: str) -> dict[str, str]:
    detail_logger = get_file_logger(
        log_path="logs/detail_crawler.log",
        logger_name="detail_crawler",
    )
    crawler = DetailCrawlerFactory.create(url, logger=detail_logger)
    return crawler.crawl(url)


def main() -> int:
    args = parse_args()
    try:
        result = run(args.url)
    except Exception as exc:
        print(f"error={exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
