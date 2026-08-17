"""
capital_allocation_report.py
-------------------------------
Day 32: distribution summary for the latest year, plus a report of
which companies changed capital allocation pattern year-over-year.
ATGL is excluded (no cashflow data, documented in Day 31/32 checks).
"""
import pandas as pd

df = pd.read_csv("output/capital_allocation.csv")

# --- Distribution summary for latest year ---
latest_year = df["year"].max()
latest = df[df["year"] == latest_year]

print(f"Capital allocation pattern distribution ({latest_year}):")
print(latest["pattern_label"].value_counts())
print()

# --- Pattern changes year-over-year ---
df_sorted = df.sort_values(["company_id", "year"])
df_sorted["prev_pattern"] = df_sorted.groupby("company_id")["pattern_label"].shift(1)
df_sorted["prev_year"] = df_sorted.groupby("company_id")["year"].shift(1)

changes = df_sorted[
    df_sorted["prev_pattern"].notna() &
    (df_sorted["pattern_label"] != df_sorted["prev_pattern"])
].copy()

changes = changes[["company_id", "prev_year", "prev_pattern", "year", "pattern_label"]]
changes.columns = ["company_id", "from_year", "from_pattern", "to_year", "to_pattern"]
changes.to_csv("output/pattern_changes.csv", index=False)

print(f"output/pattern_changes.csv written: {len(changes)} pattern changes detected")
print()
print("Sample of changes:")
print(changes.head(10))