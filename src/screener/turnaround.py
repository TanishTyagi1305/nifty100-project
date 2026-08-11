"""
turnaround.py
-------------
Turnaround Watch preset: Revenue CAGR 3yr > 10%, FCF positive in the
latest year, and D/E declining year-over-year (this year's D/E < last
year's D/E for the same company).
"""
import sqlite3
import pandas as pd

from src.analytics.cagr import cagr


def load_de_history():
    """{company_id: {year: debt_to_equity}} for every company/year."""
    conn = sqlite3.connect("db/nifty100.db")
    df = pd.read_sql("SELECT company_id, year, debt_to_equity, free_cash_flow_cr FROM financial_ratios", conn)
    conn.close()

    de_lookup = {}
    for _, row in df.iterrows():
        de_lookup.setdefault(row["company_id"], {})[row["year"]] = row["debt_to_equity"]
    return df, de_lookup


def is_de_declining(company_id, latest_year, de_lookup):
    """True if this year's D/E is lower than last year's, for this company."""
    this_year_de = de_lookup.get(company_id, {}).get(latest_year)
    last_year_de = de_lookup.get(company_id, {}).get(latest_year - 1)
    if this_year_de is None or last_year_de is None:
        return False  # can't compare without both years
    return this_year_de < last_year_de


def run_turnaround_watch():
    conn = sqlite3.connect("db/nifty100.db")
    pnl = pd.read_sql("SELECT company_id, year, sales FROM profitandloss", conn)
    conn.close()

    df, de_lookup = load_de_history()
    latest_year = df["year"].max()
    latest = df[df["year"] == latest_year].copy()

    # Revenue 3yr CAGR lookup
    sales_lookup = {}
    for _, row in pnl.iterrows():
        sales_lookup.setdefault(row["company_id"], {})[row["year"]] = row["sales"]

    results = []
    for _, row in latest.iterrows():
        cid = row["company_id"]

        start_sales = sales_lookup.get(cid, {}).get(latest_year - 3)
        end_sales = sales_lookup.get(cid, {}).get(latest_year)
        if start_sales is None or end_sales is None:
            continue
        rev_cagr_3yr, flag = cagr(start_sales, end_sales, 3)
        if rev_cagr_3yr is None or rev_cagr_3yr <= 10:
            continue

        if row["free_cash_flow_cr"] is None or row["free_cash_flow_cr"] <= 0:
            continue

        if not is_de_declining(cid, latest_year, de_lookup):
            continue

        results.append(cid)

    return results


if __name__ == "__main__":
    companies = run_turnaround_watch()
    print(f"Turnaround Watch: {len(companies)} companies")
    print(companies)