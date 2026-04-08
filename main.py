from crawl_titles import crawl_titles
from crawl_detail import crawl_detail
from Filtering import filter_titles
from filter1_update import mark_filtered_as_selected
from db_manager.database import engine, init_db, Table, Engine, text

# llm이 처리할 부분
def pseudo_function() -> list[str]:
    pass

# def load_table(table_name: str = "EMNLP_2025") -> Table:
#     table = init_db(table_name)

#     return table

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

if __name__ == "__main__":
    # https://dblp.org/db/conf/emnlp/emnlp2025.html paper title list 수집
    crawl_titles()

    # LLM filtering 후 결과를 리스트로 저장
    title_list: list[str] = filter_titles()

    # 매칭된 paper title list를 바탕으로 해당되는 행의 selected 속성을 0 -> 1 변환
    mark_filtered_as_selected(title_list=title_list)

    # for test
    for_test(table_name="EMNLP_2025", engine=engine)

    print("Detail Crawl Start.")
    # selected가 1인 행을 대상으로 https://aclanthology.org/ 에서 abstract와 pdf 다운로드 링크를 수집
    crawl_detail()