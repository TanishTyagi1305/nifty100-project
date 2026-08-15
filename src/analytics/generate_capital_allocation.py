import sqlite3
import pandas as pd

from src.analytics.cashflow_kpis import capital_allocation_pattern

conn = sqlite3.connect("db/nifty100.db")
cf = pd.read_sql("SELECT * FROM cashflow", conn)
pnl = pd.read_sql("SELECT company_id, year, net_profit FROM profitandloss", conn)
conn.close()

df = cf.merge(pnl, on=["company_id", "year"], how="left")

results = []
for _, row in df.iterrows():
    cfo, cfi, cff = row["operating_activity"], row["investing_activity"], row["financing_activity"]
    if pd.isna(cfo) or pd.isna(cfi) or pd.isna(cff):
        continue

    cfo_s, cfi_s, cff_s, label = capital_allocation_pattern(cfo, cfi, cff)
    results.append(dict(
        company_id=row["company_id"], year=int(row["year"]),
        cfo_sign=cfo_s, cfi_sign=cfi_s, cff_sign=cff_s, pattern_label=label,
    ))

result_df = pd.DataFrame(results)
result_df.to_csv("output/capital_allocation.csv", index=False)
print(f"Wrote output/capital_allocation.csv with {len(result_df)} rows")
print()
print("Pattern distribution:")
print(result_df["pattern_label"].value_counts())