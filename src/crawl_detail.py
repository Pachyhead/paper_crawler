import sys
from pathlib import Path
from typing import Tuple

from config import PROJECT_ROOT
from paper_crawler.factories.detail_factory import DetailCrawlerFactory
from paper_crawler.detail import BasePaperDetailCrawler
from sqlalchemy import create_engine, Engine, text
import pandas as pd

# dblp -> aclanthology

def for_test(table_name: str, engine: Engine):
    with engine.begin() as conn:
    # 서브쿼리(Subquery)를 사용하여 첫 10개의 ID를 찾고, 그 줄만 업데이트합니다.
        query = text(f"""
            UPDATE {table_name}
            SET selected = 1
            WHERE id IN (
                SELECT id FROM {table_name}
                ORDER BY id
                LIMIT 10
            )
        """)
        conn.execute(query)

def read_table(table_name: str) -> Tuple[pd.DataFrame, Engine]:
    engine = create_engine(f'sqlite:///{PROJECT_ROOT}/papers_data.db')
    df = pd.read_sql(table_name, con=engine)

    return (df, engine)

def process(df: pd.DataFrame, detail_crawler: BasePaperDetailCrawler) -> pd.DataFrame:
    mask = df['selected'] == 1
    
    # 수정 1: 선택된 행이 있을 때만 크롤링을 진행하여 에러 방지
    if mask.any(): 
        df.loc[mask, "abstract"], df.loc[mask, "pdf_link"] = zip(*df.loc[mask, "detail_url"].map(detail_crawler.crawl))
        print(f"{mask.sum()}개의 논문 상세 정보를 수집했습니다.")
    else:
        print("선택된(selected=True) 논문이 없습니다.")
        
    return df

def update_database(df: pd.DataFrame, table_name: str, engine: Engine):
    """
    수정 2: to_sql(append) 대신 직접 UPDATE 명령을 수행하는 함수 추가
    """
    mask = df['selected'] == 1
    update_data = df[mask] # 수집이 완료된 행만 추려냅니다.
    
    if update_data.empty:
        return

    with engine.begin() as conn: # 트랜잭션 시작 (안전한 저장)
        for _, row in update_data.iterrows():
            # detail_url을 기준으로 해당 논문을 찾아 abstract와 pdf_link를 덮어씁니다.
            query = text(f"""
                UPDATE {table_name}
                SET abstract = :abstract, pdf_link = :pdf_link
                WHERE detail_url = :detail_url
            """)
            conn.execute(query, {
                "abstract": row['abstract'],
                "pdf_link": row['pdf_link'],
                "detail_url": row['detail_url']
            }) 
    print("데이터베이스 업데이트가 완료되었습니다.")

def crawl_titles():
    df, engine = read_table(table_name="EMNLP_2025")
    conference_url = "https://aclanthology.org/2025.emnlp-main.0/"
    detail_crawler = DetailCrawlerFactory.create(conference_url)
    for_test("EMNLP_2025", engine)
    process(df, detail_crawler)
    update_database(df, "EMNLP_2025", engine)

if __name__ == "__main__":
    raise SystemExit(crawl_titles())