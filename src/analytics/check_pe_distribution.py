import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")
df = pd.read_sql("""
    SELECT company_id, pe_ratio FROM market_cap
    WHERE year = (SELECT MAX(year) FROM market_cap) AND pe_ratio IS NOT NULL
    ORDER BY pe_ratio DESC
""", conn)
conn.close()

print(f"Count: {len(df)}")
print(f"Proper median (pandas): {df['pe_ratio'].median():.2f}")
print(f"Mean: {df['pe_ratio'].mean():.2f}")
print()
print("Top 10 highest P/E (checking for outliers):")
print(df.head(10))
print()
print("Bottom 10 lowest P/E:")
print(df.tail(10))