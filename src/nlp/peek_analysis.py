import sqlite3

conn = sqlite3.connect("db/nifty100.db")
rows = conn.execute("""
    SELECT company_id, compounded_sales_growth, compounded_profit_growth, stock_price_cagr, roe
    FROM analysis LIMIT 10
""").fetchall()
for r in rows:
    print(r)
conn.close()