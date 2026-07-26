import sqlite3

conn = sqlite3.connect("db/nifty100.db")
cur = conn.cursor()

cur.execute("""
    SELECT company_id, year, return_on_equity_pct
    FROM financial_ratios
    WHERE return_on_equity_pct > 200
""")
bad_rows = cur.fetchall()
print(f"Found {len(bad_rows)} rows with implausible ROE (>200%):")
for row in bad_rows:
    print(" ", row)

cur.execute("""
    UPDATE financial_ratios
    SET return_on_equity_pct = NULL
    WHERE return_on_equity_pct > 200
""")
conn.commit()
print(f"\nNulled out {cur.rowcount} rows.")

conn.close()