from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine("postgresql+psycopg://postgres:pg@localhost:5433/postgres")

with engine.begin() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))

for f in sorted(Path("data/olist").glob("*.csv")):
    table = f.stem.replace("olist_", "").replace("_dataset", "")
    df = pd.read_csv(f)
    rows_per_chunk = 65_535 // len(df.columns) - 1   # stay under Postgres' parameter limit
    df.to_sql(table, engine, schema="raw", if_exists="replace",
            index=False, chunksize=rows_per_chunk, method="multi")
    print(f"{table:40} {len(df):>10,} rows")

        
    
    