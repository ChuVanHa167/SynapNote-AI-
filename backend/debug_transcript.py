from sqlalchemy import create_engine, MetaData, Table, select

engine = create_engine("mysql+pymysql://root:@localhost:3306/synapnote_ai")
metadata = MetaData()
meetings = Table('meetings', metadata, autoload_with=engine)

with engine.connect() as conn:
    stmt = select(meetings).order_by(meetings.c.id.desc())
    results = conn.execute(stmt).fetchall()
    print(f"{'ID':<40} | {'Status':<15} | {'Transcript Len':<15}")
    print("-" * 75)
    for row in results:
        t_len = len(row.transcript) if row.transcript else 0
        print(f"{row.id:<40} | {row.status:<15} | {t_len:<15}")
