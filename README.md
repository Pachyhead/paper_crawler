# paper_crawler

## 1. 파일구조

```text
paper_crawler/
  main.py
  requirements.txt
  src/
    paper_crawler/
      base.py
      errors.py
      factory.py
      sites/
        dblp.py
        example_static.py
  utils/
    csv_helper.py
    timing_logger.py
  tests/
```

## 2. requirements 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. main.py 실행

```bash
python main.py --url "~~~" --output "~~~"
```

## 4. 세부 사용법
```python
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from paper_crawler.factory import CrawlerFactory
from utils.csv_helper import save_titles_to_csv
from utils.timing_logger import log_execution_time

url = "https://dblp.org/db/conf/emnlp/emnlp2025.html"
with log_execution_time(
    "crawl_and_save",
    log_path="./logs/execution.log",
    logger_name="crawler_timer",
    context={"url": url},
):
    items = CrawlerFactory.crawl(url)
    save_titles_to_csv(items, "./output/emnlp2025_titles.csv")
```

- `logger_name`: 로거 식별자(내부 구분용)입니다.
- `context`: 로그에 추가할 정보입니다. 예: `url=https://...`
