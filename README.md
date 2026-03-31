# paper_crawler

## Installation
```bash
# 프로젝트 디렉토리로 이동
python3 -m venv .venv
source .venv/bin/activate
pip3 install -e .
python3 main.py
```

## 세부 사용법
- 핵심 모듈
  - src/crawl_titles.py
    - crawl_titles() 매서드 실행 / 그냥 py 파일 실행도 가능
      - 현재는 https://dblp.org/db/conf/emnlp/emnlp2025.html 링크가 하드코딩되어 있음.
      - 주소 내 title명과 detail_url를 수집
  - src/filter1_update.py
    - mark_filtered_as_selected()
      - LLM을 통해 추출한 paper title들을 리스트 형태로 변환하여 mark_filtered_as_selected() 매서드에 인자로 전달
      - 해당되는 행의 selected 열을 0에서 1로 변경
  - src/crawl_detail.py
    - crawl_detail() 매서드 실행 / 그냥 py 파일 실행도 가능
      - 현재는 https://aclanthology.org/2025.emnlp-main.0/ 링크가 하드코딩되어 있음.
      - db의 selected가 1인 행을 대상으로 pdf의 abstract 및 pdf 다운 링크를 수집
