from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from paper_crawler.factory import CrawlerFactory
from utils.csv_helper import save_titles_to_csv
from utils.timing_logger import log_execution_time

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Crawl paper titles and save them to CSV.",
    )
    parser.add_argument(
        "--url",
        default="https://dblp.org/db/conf/emnlp/emnlp2025.html",
        help="Target page URL to crawl.",
    )
    parser.add_argument(
        "--output",
        default="output/emnlp2025_titles.csv",
        help="Output CSV path.",
    )
    return parser.parse_args()


def main() -> int:
    with log_execution_time("crawl_and_save", log_path="logs/execution.log"):
        args = parse_args()
        crawler = CrawlerFactory.create(args.url)
        items = crawler.crawl(args.url)
        output_path = save_titles_to_csv(items, args.output)

    print(f"saved={output_path}")
    print(f"count={len(items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
