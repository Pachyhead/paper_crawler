from sqlalchemy import update

def mark_filtered_as_selected(engine, table, title_list):
    if not title_list:
        return

    unique_titles = list(set(title_list))

    stmt = (
        update(table)
        .where(table.c.title.in_(unique_titles))
        .values(selected=1)
    )

    with engine.connect() as conn:
        conn.execute(stmt)
        conn.commit()