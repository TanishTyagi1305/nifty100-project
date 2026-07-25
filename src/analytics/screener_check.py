import sqlite3

conn = sqlite3.connect("db/nifty100.db")
cur = conn.cursor()

cur.execute("""
    SELECT DISTINCT company_id
    FROM financial_ratios
    WHERE year = (SELECT MAX(year) FROM financial_ratios)
    AND return_on_equity_pct > 15
    AND return_on_equity_pct < 200
    AND debt_to_equity < 1
""")
companies = [row[0] for row in cur.fetchall()]
print(f"Count: {len(companies)}")
print("Companies:", sorted(companies))

conn.close()