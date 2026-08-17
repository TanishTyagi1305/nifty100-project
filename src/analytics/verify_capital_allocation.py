import sqlite3
import pandas as pd

df = pd.read_csv("output/capital_allocation.csv")
print(f"Total rows: {len(df)}")
print(f"Distinct companies: {df['company_id'].nunique()}")

conn = sqlite3.connect("db/nifty100.db")
total_companies = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
conn.close()
print(f"Total companies in database: {total_companies}")

covered = set(df["company_id"].unique())
conn = sqlite3.connect("db/nifty100.db")
all_ids = set(pd.read_sql("SELECT id FROM companies", conn)["id"].tolist())
conn.close()
missing = all_ids - covered
print(f"Companies with ZERO capital allocation rows: {missing}")