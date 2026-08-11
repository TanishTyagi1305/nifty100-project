import sqlite3
conn = sqlite3.connect("db/nifty100.db")
row = conn.execute("""
    SELECT company_id, composite_quality_score FROM financial_ratios
    WHERE year = (SELECT MAX(year) FROM financial_ratios) LIMIT 10
""").fetchall()
for r in row:
    print(r)

count = conn.execute("""
    SELECT COUNT(composite_quality_score) FROM financial_ratios
    WHERE year = (SELECT MAX(year) FROM financial_ratios)
""").fetchone()[0]
print(f"\nNon-null composite_quality_score: {count} / 92")
conn.close()