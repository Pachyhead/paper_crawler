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
from paper_crawler.factory import CrawlerFactory
from utils.csv_helper import save_titles_to_csv

url = "https://dblp.org/db/conf/emnlp/emnlp2025.html"
items = CrawlerFactory.crawl(url)
save_titles_to_csv(items, "./output/emnlp2025_titles.csv")
```
