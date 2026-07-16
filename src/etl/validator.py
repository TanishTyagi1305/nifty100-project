"""
validator.py
------------
Implements the 16 Data Quality (DQ) rules from the project spec.
Each check function returns a list of violation dicts:
    {rule_id, table, company_id, year, field, issue, severity}
"""
import pandas as pd


def _v(rule_id, table, company_id, year, field, issue, severity):
    return dict(rule_id=rule_id, table=table, company_id=company_id,
                year=year, field=field, issue=issue, severity=severity)


def dq01_company_pk_uniqueness(companies: pd.DataFrame):
    violations = []
    dupes = companies[companies.duplicated("id", keep=False)]
    for _, row in dupes.iterrows():
        violations.append(_v("DQ-01", "companies", row["id"], None, "id",
                              "Duplicate company id", "CRITICAL"))
    return violations


def dq02_annual_pk_uniqueness(df: pd.DataFrame, table: str):
    violations = []
    dupes = df[df.duplicated(["company_id", "year"], keep=False)]
    for _, row in dupes.iterrows():
        violations.append(_v("DQ-02", table, row["company_id"], row["year"],
                              "company_id,year", "Duplicate (company_id, year)", "CRITICAL"))
    return violations


def dq03_fk_integrity(df: pd.DataFrame, table: str, valid_ids: set):
    violations = []
    orphans = df[~df["company_id"].isin(valid_ids)]
    for _, row in orphans.iterrows():
        violations.append(_v("DQ-03", table, row["company_id"], row.get("year"),
                              "company_id", "company_id not found in companies table", "CRITICAL"))
    return violations


def dq04_bs_balance(bs: pd.DataFrame):
    violations = []
    safe = bs[bs["total_assets"] != 0]
    ratio = (safe["total_assets"] - safe["total_liabilities"]).abs() / safe["total_assets"]
    bad = safe[ratio >= 0.01]
    for _, row in bad.iterrows():
        violations.append(_v("DQ-04", "balancesheet", row["company_id"], row["year"],
                              "total_assets/total_liabilities",
                              "Balance sheet does not balance within 1%", "WARNING"))
    return violations


def dq05_opm_crosscheck(pnl: pd.DataFrame):
    violations = []
    safe = pnl[pnl["sales"] != 0]
    computed = (safe["operating_profit"] / safe["sales"]) * 100
    diff = (safe["opm_percentage"] - computed).abs()
    bad = safe[diff >= 1]
    for _, row in bad.iterrows():
        violations.append(_v("DQ-05", "profitandloss", row["company_id"], row["year"],
                              "opm_percentage", "OPM does not match computed value (>1pt diff)", "WARNING"))
    return violations


def dq06_positive_sales(pnl: pd.DataFrame):
    violations = []
    bad = pnl[pnl["sales"] <= 0]
    for _, row in bad.iterrows():
        violations.append(_v("DQ-06", "profitandloss", row["company_id"], row["year"],
                              "sales", "Sales is zero or negative", "WARNING"))
    return violations


def dq09_net_cash_check(cf: pd.DataFrame):
    violations = []
    computed = cf["operating_activity"] + cf["investing_activity"] + cf["financing_activity"]
    diff = (cf["net_cash_flow"] - computed).abs()
    bad = cf[diff > 10]
    for _, row in bad.iterrows():
        violations.append(_v("DQ-09", "cashflow", row["company_id"], row["year"],
                              "net_cash_flow", "net_cash_flow does not equal CFO+CFI+CFF (>10cr diff)", "WARNING"))
    return violations


def dq10_nonneg_fixed_assets(bs: pd.DataFrame):
    violations = []
    bad = bs[bs["fixed_assets"] < 0]
    for _, row in bad.iterrows():
        violations.append(_v("DQ-10", "balancesheet", row["company_id"], row["year"],
                              "fixed_assets", "Negative fixed_assets", "WARNING"))
    return violations


def dq11_tax_rate_range(pnl: pd.DataFrame):
    violations = []
    bad = pnl[(pnl["tax_percentage"] < 0) | (pnl["tax_percentage"] > 60)]
    for _, row in bad.iterrows():
        violations.append(_v("DQ-11", "profitandloss", row["company_id"], row["year"],
                              "tax_percentage", "Tax rate outside 0-60% range", "WARNING"))
    return violations


def dq12_dividend_payout_cap(pnl: pd.DataFrame):
    violations = []
    bad = pnl[pnl["dividend_payout"] > 200]
    for _, row in bad.iterrows():
        violations.append(_v("DQ-12", "profitandloss", row["company_id"], row["year"],
                              "dividend_payout", "Dividend payout >200%, likely data-entry error", "WARNING"))
    return violations


def dq14_eps_sign_consistency(pnl: pd.DataFrame):
    violations = []
    bad = pnl[(pnl["net_profit"] > 0) & (pnl["eps"] <= 0)]
    for _, row in bad.iterrows():
        violations.append(_v("DQ-14", "profitandloss", row["company_id"], row["year"],
                              "eps", "eps <= 0 while net_profit > 0", "WARNING"))
    return violations


def dq16_coverage_check(pnl: pd.DataFrame):
    violations = []
    counts = pnl.groupby("company_id")["year"].nunique()
    thin = counts[counts < 5]
    for company_id, n in thin.items():
        violations.append(_v("DQ-16", "profitandloss", company_id, None,
                              "year", f"Only {n} years of P&L history (<5)", "WARNING"))
    return violations


def run_all_checks(frames: dict) -> pd.DataFrame:
    """
    frames: dict of table_name -> DataFrame, already normalised
    (company_id normalised, year normalised as int) for the tables
    that have those columns.
    Returns a DataFrame of all violations found (validation_failures.csv content).
    """
    all_violations = []
    companies = frames["companies"]
    valid_ids = set(companies["id"])

    all_violations += dq01_company_pk_uniqueness(companies)

    for table in ["profitandloss", "balancesheet", "cashflow", "financial_ratios"]:
        if table in frames:
            all_violations += dq02_annual_pk_uniqueness(frames[table], table)

    for table, df in frames.items():
        if table != "companies" and "company_id" in df.columns:
            all_violations += dq03_fk_integrity(df, table, valid_ids)

    if "balancesheet" in frames:
        all_violations += dq04_bs_balance(frames["balancesheet"])
        all_violations += dq10_nonneg_fixed_assets(frames["balancesheet"])

    if "profitandloss" in frames:
        pnl = frames["profitandloss"]
        all_violations += dq05_opm_crosscheck(pnl)
        all_violations += dq06_positive_sales(pnl)
        all_violations += dq11_tax_rate_range(pnl)
        all_violations += dq12_dividend_payout_cap(pnl)
        all_violations += dq14_eps_sign_consistency(pnl)
        all_violations += dq16_coverage_check(pnl)

    if "cashflow" in frames:
        all_violations += dq09_net_cash_check(frames["cashflow"])

    return pd.DataFrame(all_violations, columns=[
        "rule_id", "table", "company_id", "year", "field", "issue", "severity"
    ])
