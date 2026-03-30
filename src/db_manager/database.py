from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, Boolean
from config import PROJECT_ROOT

engine = create_engine(f'sqlite:///{PROJECT_ROOT}/papers_data.db')
metadata = MetaData()

def init_db(table_name): 
    # 함수 내부에서 Table 객체를 생성하여 이름을 부여합니다.
    new_table = Table(
        table_name, metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('title', String, nullable=False),
        Column('detail_url', String, unique=True, nullable=False),
        Column('abstract', Text, nullable=True),
        Column('pdf_link', String, nullable=True),
        Column('selected', Boolean, server_default='0', nullable=False),
        extend_existing=True # 이미 메모리에 해당 이름의 객체가 있어도 덮어쓰도록 설정
    )
    
    # 실제로 DB 파일에 테이블을 생성합니다.
    metadata.create_all(engine)
    
    # 생성된 테이블 객체(리모컨)를 반환하여 밖에서 쓸 수 있게 합니다.
    return new_table