import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")
df = pd.read_sql("""
    SELECT company_id, year, pat_cagr_5yr, pat_cagr_5yr_flag
    FROM financial_ratios
    WHERE year = (SELECT MAX(year) FROM financial_ratios)
    ORDER BY pat_cagr_5yr DESC
""", conn)
conn.close()

print(df.head(15))
print()
print("How many rows have a real (non-null) pat_cagr_5yr value?")
print(df["pat_cagr_5yr"].notna().sum(), "out of", len(df))
print()
print("Flag value counts (why it's None, when it is):")
print(df["pat_cagr_5yr_flag"].value_counts())