import sqlite3

conn = sqlite3.connect("db/nifty100.db")
cur = conn.cursor()

cur.execute("""
    SELECT p.year, p.net_profit, b.equity_capital, b.reserves
    FROM profitandloss p
    JOIN balancesheet b ON p.company_id = b.company_id AND p.year = b.year
    WHERE p.company_id = 'TCS'
    ORDER BY p.year DESC LIMIT 3
""")
for row in cur.fetchall():
    print(row)

conn.close()