import pandas as pd
from src.analytics.valuation import build_valuation_summary

df = build_valuation_summary()

summary_cols = ["company_id", "company_name", "broad_sector", "pe_ratio", "pb_ratio",
                 "ev_ebitda", "fcf_yield_pct", "sector_median_pe", "pe_vs_sector_median_pct", "flag"]
df[summary_cols].to_excel("output/valuation_summary.xlsx", index=False)
print(f"output/valuation_summary.xlsx written: {len(df)} rows")

flagged = df[df["flag"].isin(["Caution", "Discount"])]
flagged[summary_cols].to_csv("output/valuation_flags.csv", index=False)
print(f"output/valuation_flags.csv written: {len(flagged)} rows")