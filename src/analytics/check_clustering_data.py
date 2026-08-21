import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")
df = pd.read_sql("""
    SELECT company_id, return_on_equity_pct, debt_to_equity,
           revenue_cagr_5yr, operating_profit_margin_pct
    FROM financial_ratios
    WHERE year = (SELECT MAX(year) FROM financial_ratios)
""", conn)
conn.close()

print(f"Total rows: {len(df)}")
print(f"\nNon-null counts per feature:")
print(df.notna().sum())
print(f"\nSample:")
print(df.head(5))