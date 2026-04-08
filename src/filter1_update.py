import re

from sqlalchemy import update
from src.db_manager.database import engine, init_db

def mark_filtered_as_selected(title_list, table_name="EMNLP_2025"):
    if not title_list:
        return
    
    table = init_db(table_name)

    cleaned_titles = [re.sub(r'[^a-zA-Z0-9가-힣]', '', t).lower() for t in set(title_list)]

    stmt = (
        update(table)
        .where(table.c.cleaned_title.in_(cleaned_titles))
        .values(selected=1)
    )

    with engine.connect() as conn:
        conn.execute(stmt)
        conn.commit()