import sqlite3
import pandas as pd

from src.analytics.ratios import (
    net_profit_margin, operating_profit_margin, return_on_equity,
    return_on_capital_employed, debt_to_equity, interest_coverage_ratio,
    asset_turnover, high_leverage_flag, icr_risk_flag
)
from src.analytics.cagr import cagr
from src.analytics.cashflow_kpis import free_cash_flow

conn = sqlite3.connect("db/nifty100.db")

pnl = pd.read_sql("SELECT * FROM profitandloss", conn)
bs = pd.read_sql("SELECT * FROM balancesheet", conn)
cf = pd.read_sql("SELECT * FROM cashflow", conn)
sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)

df = pnl.merge(bs, on=["company_id", "year"], how="left", suffixes=("", "_bs"))
df = df.merge(cf, on=["company_id", "year"], how="left", suffixes=("", "_cf"))
df = df.merge(sectors, on="company_id", how="left")

# lookup tables {company_id: {year: value}} for CAGR -- Revenue, PAT, and EPS
sales_lookup = {}
pat_lookup = {}
eps_lookup = {}
for _, row in pnl.iterrows():
    sales_lookup.setdefault(row["company_id"], {})[row["year"]] = row["sales"]
    pat_lookup.setdefault(row["company_id"], {})[row["year"]] = row["net_profit"]
    eps_lookup.setdefault(row["company_id"], {})[row["year"]] = row["eps"]

results = []
for _, row in df.iterrows():
    npm = net_profit_margin(row["net_profit"], row["sales"])
    opm = operating_profit_margin(row["operating_profit"], row["sales"])
    roe = return_on_equity(row["net_profit"], row.get("equity_capital"), row.get("reserves"))
    de = debt_to_equity(row.get("borrowings"), row.get("equity_capital"), row.get("reserves"))
    icr, icr_label = interest_coverage_ratio(row["operating_profit"], row["other_income"], row["interest"])
    at = asset_turnover(row["sales"], row.get("total_assets"))
    fcf = free_cash_flow(row.get("operating_activity"), row.get("investing_activity"))

    roce_ebit = (row["operating_profit"] or 0) + (row["other_income"] or 0)
    roce = return_on_capital_employed(roce_ebit, row.get("equity_capital"), row.get("reserves"), row.get("borrowings"))
    hl_flag = high_leverage_flag(de, row.get("broad_sector"))
    icr_risk = icr_risk_flag(icr)

    # Revenue CAGR (5yr, ending at this row's year)
    start_sales = sales_lookup.get(row["company_id"], {}).get(row["year"] - 5)
    end_sales = row["sales"]
    if start_sales is not None:
        rev_cagr, rev_flag = cagr(start_sales, end_sales, 5)
    else:
        rev_cagr, rev_flag = None, "INSUFFICIENT"

    # PAT (net profit) CAGR (5yr)
    pat_start = pat_lookup.get(row["company_id"], {}).get(row["year"] - 5)
    pat_end = row["net_profit"]
    if pat_start is not None:
        pat_cagr_val, pat_flag = cagr(pat_start, pat_end, 5)
    else:
        pat_cagr_val, pat_flag = None, "INSUFFICIENT"

    # EPS CAGR (5yr)
    eps_start = eps_lookup.get(row["company_id"], {}).get(row["year"] - 5)
    eps_end = row["eps"]
    if eps_start is not None:
        eps_cagr_val, eps_flag = cagr(eps_start, eps_end, 5)
    else:
        eps_cagr_val, eps_flag = None, "INSUFFICIENT"

    results.append(dict(
        company_id=row["company_id"], year=int(row["year"]),
        net_profit_margin_pct=npm, operating_profit_margin_pct=opm,
        return_on_equity_pct=roe, debt_to_equity=de,
        interest_coverage=icr, icr_label=icr_label, asset_turnover=at,
        free_cash_flow_cr=fcf,
        revenue_cagr_5yr=rev_cagr, revenue_cagr_5yr_flag=rev_flag,
        pat_cagr_5yr=pat_cagr_val, pat_cagr_5yr_flag=pat_flag,
        eps_cagr_5yr=eps_cagr_val, eps_cagr_5yr_flag=eps_flag,
        high_leverage_flag=int(hl_flag), icr_risk_flag=int(icr_risk),
    ))

results_df = pd.DataFrame(results)

conn.execute("DELETE FROM financial_ratios")
results_df.to_sql("financial_ratios", conn, if_exists="append", index=False)
conn.commit()

count = conn.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0]
print(f"Done. financial_ratios now has {count} rows.")

flagged = conn.execute("SELECT COUNT(*) FROM financial_ratios WHERE high_leverage_flag=1").fetchone()[0]
print(f"Companies flagged high leverage: {flagged} / {count}")

pat_populated = conn.execute("SELECT COUNT(*) FROM financial_ratios WHERE pat_cagr_5yr IS NOT NULL").fetchone()[0]
print(f"Rows with a real pat_cagr_5yr value: {pat_populated} / {count}")

# ---------------- cross-check against source data ----------------

companies = pd.read_sql("SELECT id, roce_percentage, roe_percentage FROM companies", conn)
check_df = results_df.merge(companies, left_on="company_id", right_on="id", how="left")
check_df = check_df.merge(sectors, on="company_id", how="left")

edge_log = []
for _, r in check_df.iterrows():
    if pd.notna(r.get("roe_percentage")) and pd.notna(r.get("return_on_equity_pct")):
        diff = abs((r["return_on_equity_pct"] or 0) - r["roe_percentage"])
        if diff > 5:
            category = "data source issue" if (r["roe_percentage"] < 5 or abs(r["return_on_equity_pct"]) > 200) else "version difference"
            edge_log.append(
                f"[{category}] {r['company_id']} {r['year']}: ROE - "
                f"computed={r['return_on_equity_pct']:.2f} vs source={r['roe_percentage']:.2f}, "
                f"diff={diff:.2f}"
            )

with open("output/ratio_edge_cases.log", "w") as f:
    f.write(f"Ratio Edge Case Log (all years) - {len(edge_log)} entries\n")
    f.write("=" * 60 + "\n")
    for line in edge_log:
        f.write(line + "\n")
print(f"ratio_edge_cases.log written: {len(edge_log)} entries")

latest_year = check_df["year"].max()
latest_only = check_df[check_df["year"] == latest_year]

summary_log = []
for _, r in latest_only.iterrows():
    if pd.notna(r.get("roe_percentage")) and pd.notna(r.get("return_on_equity_pct")):
        diff = abs((r["return_on_equity_pct"] or 0) - r["roe_percentage"])
        if diff > 5:
            category = "data source issue" if (r["roe_percentage"] < 5 or abs(r["return_on_equity_pct"]) > 200) else "version difference"
            summary_log.append(
                f"[{category}] {r['company_id']} ({latest_year}): ROE - "
                f"computed={r['return_on_equity_pct']:.2f} vs source={r['roe_percentage']:.2f}, "
                f"diff={diff:.2f}"
            )

with open("output/ratio_edge_cases_summary.log", "w") as f:
    f.write(f"Ratio Edge Case Summary (latest year only: {latest_year}) - {len(summary_log)} entries\n")
    f.write("=" * 60 + "\n")
    for line in summary_log:
        f.write(line + "\n")
print(f"ratio_edge_cases_summary.log written: {len(summary_log)} entries")

conn.close()