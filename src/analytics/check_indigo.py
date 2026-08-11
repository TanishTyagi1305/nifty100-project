import sqlite3
conn = sqlite3.connect("db/nifty100.db")
row = conn.execute("""
    SELECT pat_cagr_5yr, revenue_cagr_5yr, debt_to_equity
    FROM financial_ratios WHERE company_id='INDIGO'
    AND year=(SELECT MAX(year) FROM financial_ratios)
""").fetchone()
print(row)
conn.close()