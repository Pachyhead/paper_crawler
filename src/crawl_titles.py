import sys
from pathlib import Path
from typing import TypedDict

from config import PROJECT_ROOT
from paper_crawler.factories.title_factory import TitleCrawlerFactory
from db_manager.database import engine, init_db

class ConferenceTarget(TypedDict):
    name: str
    url: str

# 이 리스트에 크롤링할 컨퍼런스를 추가하면 순차적으로 실행됩니다.
TARGET_CONFERENCES: list[ConferenceTarget] = [
    {
        "name": "EMNLP_2025",
        "url": "https://dblp.org/db/conf/emnlp/emnlp2025.html",
    },
    # {
    #     "name": "ICLR_2025",
    #     "url": "https://papercopilot.com/paper-list/iclr-paper-list/iclr-2025-paper-list/",
    # },
    # {   "name": "AAAI_2025",
    #     "url": "https://papercopilot.com/paper-list/aaai-paper-list/aaai-2025-paper-list/",
    # }
    #{
    #    "name": "acl_2025",
    #    "url": "https://2025.aclweb.org/program/find_papers/",
    #}
]

## OUTPUT_TXT = PROJECT_ROOT / "outputs" / "title_results.txt"

def crawl_urls(conferences: list[ConferenceTarget])->None:
    results: dict[str, list[dict[str, str]]] = {}

    for conference in conferences:
        name = conference["name"]
        url = conference["url"]
        try:
            items = TitleCrawlerFactory.crawl(url)
            # items = pd.DataFrame(['title', 'detail_url'])
            
            table = init_db(name)
            try:
                items.to_sql(table.name, con=engine, if_exists='append', index=False)
            except Exception as e:
                print(f"데이터 저장 중 에러 발생 (중복 가능성): {e}")
            print(f"ok conference={name} url={url} count={len(items)}")
        except Exception as exc:
            results[name] = []
            print(f"failed conference={name} url={url} error={exc}", file=sys.stderr)

def crawl_detail() -> int:
    if not TARGET_CONFERENCES:
        print("TARGET_CONFERENCES is empty", file=sys.stderr)
        return 1

    crawl_urls(TARGET_CONFERENCES)
    return 0

if __name__ == "__main__":
    raise SystemExit(crawl_detail())
