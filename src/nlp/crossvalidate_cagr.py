import sqlite3
import pandas as pd

parsed = pd.read_csv("output/analysis_parsed.csv")
# We only have a real computed equivalent for sales_growth (revenue_cagr_5yr) and
# profit_growth (pat_cagr_5yr) at the 5-year window -- stock_price_cagr and roe
# aren't directly comparable to anything we computed the same way.
parsed_5yr = parsed[parsed["period_years"] == 5]

conn = sqlite3.connect("db/nifty100.db")
computed = pd.read_sql("""
    SELECT company_id, revenue_cagr_5yr, pat_cagr_5yr FROM financial_ratios
    WHERE year = (SELECT MAX(year) FROM financial_ratios)
""", conn)
conn.close()

merged = parsed_5yr.merge(computed, on="company_id", how="left")

divergences = []
for _, row in merged.iterrows():
    if row["metric_type"] == "sales_growth" and pd.notna(row["revenue_cagr_5yr"]):
        diff = abs(row["value_pct"] - row["revenue_cagr_5yr"])
        if diff > 5:
            divergences.append({"company_id": row["company_id"], "metric": "sales_growth",
                                 "parsed": row["value_pct"], "computed": row["revenue_cagr_5yr"], "diff": diff})
    if row["metric_type"] == "profit_growth" and pd.notna(row["pat_cagr_5yr"]):
        diff = abs(row["value_pct"] - row["pat_cagr_5yr"])
        if diff > 5:
            divergences.append({"company_id": row["company_id"], "metric": "profit_growth",
                                 "parsed": row["value_pct"], "computed": row["pat_cagr_5yr"], "diff": diff})

div_df = pd.DataFrame(divergences)
print(f"Total 5yr comparisons checked: {len(merged)}")
print(f"Divergences > 5%: {len(div_df)}")
if len(div_df) > 0:
    print(div_df.sort_values("diff", ascending=False))