import sqlite3

conn = sqlite3.connect("db/nifty100.db")

latest_year = conn.execute("SELECT MAX(year) FROM financial_ratios").fetchone()[0]
print(f"Latest year: {latest_year}")

avg_roe = conn.execute("""
    SELECT AVG(return_on_equity_pct) FROM financial_ratios
    WHERE year = ? AND return_on_equity_pct IS NOT NULL
""", (latest_year,)).fetchone()[0]
print(f"Average ROE: {avg_roe:.2f}%")

median_pe_rows = conn.execute("""
    SELECT pe_ratio FROM market_cap WHERE year = ? AND pe_ratio IS NOT NULL
    ORDER BY pe_ratio
""", (latest_year,)).fetchall()
pe_values = [r[0] for r in median_pe_rows]
median_pe = pe_values[len(pe_values)//2]
print(f"Median P/E (rough): {median_pe:.2f}")

total_companies = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
print(f"Total companies: {total_companies}")

debt_free = conn.execute("""
    SELECT COUNT(*) FROM financial_ratios
    WHERE year = ? AND debt_to_equity = 0
""", (latest_year,)).fetchone()[0]
print(f"Debt-free companies: {debt_free}")

conn.close()