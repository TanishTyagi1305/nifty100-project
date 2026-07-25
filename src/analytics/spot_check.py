import sqlite3

conn = sqlite3.connect("db/nifty100.db")
cur = conn.cursor()

cur.execute("""
    SELECT p.year, p.net_profit, b.equity_capital, b.reserves, f.return_on_equity_pct
    FROM profitandloss p
    JOIN balancesheet b ON p.company_id = b.company_id AND p.year = b.year
    JOIN financial_ratios f ON p.company_id = f.company_id AND p.year = f.year
    WHERE p.company_id = 'TCS'
    ORDER BY p.year DESC LIMIT 1
""")
year, net_profit, equity, reserves, stored_roe = cur.fetchone()

manual_roe = net_profit / (equity + reserves) * 100
print(f"Year: {year}")
print(f"Stored ROE (from your code): {stored_roe:.4f}%")
print(f"Manual ROE (calculated here): {manual_roe:.4f}%")
print(f"Difference: {abs(stored_roe - manual_roe):.6f}")

conn.close()