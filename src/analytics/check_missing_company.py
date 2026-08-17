import sqlite3
import pandas as pd
from src.analytics.cashflow_intelligence import build_cashflow_intelligence

conn = sqlite3.connect("db/nifty100.db")
all_companies = set(pd.read_sql("SELECT id FROM companies", conn)["id"].tolist())
conn.close()

result_df = build_cashflow_intelligence()
covered = set(result_df["company_id"].tolist())

missing = all_companies - covered
print("Missing company:", missing)