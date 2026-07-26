import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")
df = pd.read_sql("""
    SELECT company_id, year, pb_ratio
    FROM market_cap
    WHERE year = (SELECT MAX(year) FROM market_cap)
    ORDER BY pb_ratio DESC
""", conn)
conn.close()

print(df.head(20))
print()
print("How many rows have pb_ratio < 5?", (df["pb_ratio"] < 5).sum(), "out of", len(df))
print("How many rows have a non-null pb_ratio?", df["pb_ratio"].notna().sum(), "out of", len(df))