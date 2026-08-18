"""
batch_tearsheets.py
---------------------
Day 34: generates a tearsheet PDF for every company with 3+ years of
data. Companies with fewer than 3 years are skipped and logged, not
silently dropped or crashed on.
"""
import sqlite3
import pandas as pd

from src.reports.tearsheet import generate_tearsheet

conn = sqlite3.connect("db/nifty100.db")
companies = pd.read_sql("SELECT id FROM companies", conn)["id"].tolist()
year_counts = pd.read_sql("SELECT company_id, COUNT(DISTINCT year) as n_years FROM financial_ratios GROUP BY company_id", conn)
conn.close()

year_count_map = dict(zip(year_counts["company_id"], year_counts["n_years"]))

generated, skipped, failed = [], [], []

for ticker in companies:
    n_years = year_count_map.get(ticker, 0)
    if n_years < 3:
        skipped.append(dict(company_id=ticker, reason=f"only {n_years} years of data"))
        continue

    output_path = f"reports/tearsheets/{ticker}_tearsheet.pdf"
    try:
        success = generate_tearsheet(ticker, output_path)
        if success:
            generated.append(ticker)
        else:
            skipped.append(dict(company_id=ticker, reason="generate_tearsheet returned False"))
    except Exception as e:
        failed.append(dict(company_id=ticker, error=str(e)))

print(f"Generated: {len(generated)}")
print(f"Skipped: {len(skipped)}")
print(f"Failed (crashed): {len(failed)}")

pd.DataFrame(skipped).to_csv("output/skipped_tearsheets.csv", index=False)
print("\noutput/skipped_tearsheets.csv written")

if failed:
    print("\nCRASHES (need investigation):")
    for f in failed:
        print(" ", f)