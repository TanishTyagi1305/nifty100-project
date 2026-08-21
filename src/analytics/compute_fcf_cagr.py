"""
compute_fcf_cagr.py
--------------------
Computes FCF CAGR 5yr for all companies and updates financial_ratios.
This was deferred in Day 31 (documented as None/not-yet-computed) and
is now needed as a clustering feature on Day 36.
"""
import sqlite3
import pandas as pd
from src.analytics.cagr import cagr

conn = sqlite3.connect("db/nifty100.db")
try:
    conn.execute("ALTER TABLE financial_ratios ADD COLUMN fcf_cagr_5yr REAL")
    conn.commit()
    print("Added fcf_cagr_5yr column")
except Exception:
    pass  # column already exists, safe to ignore
ratios = pd.read_sql("SELECT company_id, year, free_cash_flow_cr FROM financial_ratios ORDER BY company_id, year", conn)

fcf_lookup = {}
for _, row in ratios.iterrows():
    fcf_lookup.setdefault(row["company_id"], {})[row["year"]] = row["free_cash_flow_cr"]

updates = []
for _, row in ratios.iterrows():
    cid, year = row["company_id"], row["year"]
    start = fcf_lookup.get(cid, {}).get(year - 5)
    end = row["free_cash_flow_cr"]
    if start is not None and end is not None:
        val, flag = cagr(start, end, 5)
    else:
        val, flag = None, "INSUFFICIENT"
    updates.append((val, cid, year))

for val, cid, year in updates:
    conn.execute("UPDATE financial_ratios SET fcf_cagr_5yr = ? WHERE company_id = ? AND year = ?", (val, cid, year))
conn.commit()

non_null = conn.execute("SELECT COUNT(fcf_cagr_5yr) FROM financial_ratios WHERE year = (SELECT MAX(year) FROM financial_ratios)").fetchone()[0]
print(f"fcf_cagr_5yr populated. Non-null for latest year: {non_null} / 92")
conn.close()