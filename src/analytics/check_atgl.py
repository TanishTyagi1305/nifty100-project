import sqlite3
conn = sqlite3.connect("db/nifty100.db")
cf_count = conn.execute("SELECT COUNT(*) FROM cashflow WHERE company_id='ATGL'").fetchone()[0]
pnl_count = conn.execute("SELECT COUNT(*) FROM profitandloss WHERE company_id='ATGL'").fetchone()[0]
print(f"ATGL cashflow rows: {cf_count}")
print(f"ATGL profitandloss rows: {pnl_count}")
conn.close()