from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from paper_crawler.orchestrator import PaperCrawlOrchestrator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Paper Crawler Orchestrator",
    )
    parser.add_argument(
        "--titles-url",
        default='https://dblp.org/db/conf/emnlp/emnlp2025.html',
    )
    parser.add_argument(
        "--conference-url",
        default='https://aclanthology.org/2025.emnlp-main.1'
    )
    parser.add_argument(
        "--output-json",
        default="outputs/papers.json",
        help="Path to save crawl result as JSON.",
    )
    return parser.parse_args()


def run(titles_url: str, conference_url: str) -> list[dict[str, str]]:
    orchest = PaperCrawlOrchestrator()
    return orchest.crawl(titles_url, conference_url)


def save_result_json(result: list[dict[str, str]], output_json: str) -> Path:
    output_path = Path(output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def main() -> int:
    args = parse_args()
    try:
        result = run(args.titles_url, args.conference_url)
    except Exception as exc:
        print(f"error={exc}", file=sys.stderr)
        return 1

    output_path = save_result_json(result, args.output_json)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"saved_json={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
