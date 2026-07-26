import sqlite3

conn = sqlite3.connect("db/nifty100.db")
for table in ["financial_ratios", "market_cap", "profitandloss"]:
    cols = [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    print(f"{table}: {cols}")
conn.close()