import sqlite3

conn = sqlite3.connect("db/nifty100.db")
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print("Tables found:", tables)

for t in ["companies", "profitandloss", "balancesheet", "cashflow", "financial_ratios"]:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"{t}: {cur.fetchone()[0]} rows")
    except Exception as e:
        print(f"{t}: NOT FOUND ({e})")

# check if the Sprint 2 CAGR columns exist yet
cur.execute("PRAGMA table_info(financial_ratios)")
cols = [row[1] for row in cur.fetchall()]
print()
print("financial_ratios columns:", cols)
print("Has revenue_cagr_5yr column?", "revenue_cagr_5yr" in cols)

conn.close()