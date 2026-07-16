"""
loader.py
---------
End-to-end Sprint 1 ETL pipeline:
  1. Read all 12 raw Excel files (core files have a title row -> header=1)
  2. Normalise company_id and year columns
  3. Run all 16 DQ rule checks -> output/validation_failures.csv
  4. Reject CRITICAL rows (bad ticker / bad year / duplicate PK / orphan FK)
  5. Load everything into db/nifty100.db using db/schema.sql
  6. Write output/load_audit.csv with per-table row counts
"""
import re
import time
import sqlite3
from pathlib import Path

import pandas as pd

from src.etl.normaliser import normalize_ticker, normalize_year
from src.etl.validator import run_all_checks, dq02_annual_pk_uniqueness, dq03_fk_integrity

BASE = Path(__file__).resolve().parents[2]
DATA_DIR = BASE / "data" / "raw"
DB_PATH = BASE / "db" / "nifty100.db"
SCHEMA_PATH = BASE / "db" / "schema.sql"
OUTPUT_DIR = BASE / "output"

CORE_FILES = {  # header row index 1 (row 2 in Excel) -- these have a title row
    "companies": "companies.xlsx",
    "profitandloss": "profitandloss.xlsx",
    "balancesheet": "balancesheet.xlsx",
    "cashflow": "cashflow.xlsx",
    "analysis": "analysis.xlsx",
    "documents": "documents.xlsx",
    "prosandcons": "prosandcons.xlsx",
}
SUPP_FILES = {  # header row index 0 -- headers already on row 1
    "sectors": "sectors.xlsx",
    "stock_prices": "stock_prices.xlsx",
    "market_cap": "market_cap.xlsx",
    "financial_ratios": "financial_ratios.xlsx",
    "peer_groups": "peer_groups.xlsx",
}

YEAR_TABLES = {"profitandloss", "balancesheet", "cashflow", "market_cap", "financial_ratios"}


def read_raw_files() -> dict:
    frames = {}
    for name, fname in CORE_FILES.items():
        frames[name] = pd.read_excel(DATA_DIR / fname, header=1)
    for name, fname in SUPP_FILES.items():
        frames[name] = pd.read_excel(DATA_DIR / fname, header=0)
    # standardise documents.xlsx column name "Year" -> "year", "Annual_Report" -> "annual_report"
    frames["documents"] = frames["documents"].rename(
        columns={"Year": "year", "Annual_Report": "annual_report"})
    return frames


def _extract_month(raw) -> str:
    """Pull the month label out of a raw period string, e.g. 'Sep 2024' -> 'Sep'.
    Returns 'numeric' if the raw value has no month (already plain year)."""
    s = str(raw).strip()
    m = re.match(r"([A-Za-z]+)", s)
    return m.group(1) if m else "numeric"


def normalise_frames(frames: dict, audit_rows: list) -> dict:
    """Apply normalize_ticker/normalize_year to every table that has those columns.
    Rows that fail to normalise are dropped (CRITICAL, DQ-07/DQ-08) and logged.
    For year tables, we also keep the original reporting month in a helper
    column (_period_month) so that later dedup can tell a real fiscal
    year-end row apart from an interim/quarterly snapshot row that happens
    to fall in the same calendar year (e.g. 'Mar 2024' vs 'Sep 2024')."""
    clean = {}
    for table, df in frames.items():
        df = df.copy()
        rows_in = len(df)
        rejected = 0

        id_col = "company_id" if "company_id" in df.columns else ("id" if table == "companies" else None)
        if id_col:
            good_mask = []
            for val in df[id_col]:
                try:
                    normalize_ticker(val)
                    good_mask.append(True)
                except ValueError:
                    good_mask.append(False)
            rejected += (~pd.Series(good_mask)).sum()
            df = df[pd.Series(good_mask).values]
            df[id_col] = df[id_col].map(normalize_ticker)

        if table in YEAR_TABLES or (table == "documents"):
            good_mask = []
            for val in df["year"]:
                try:
                    normalize_year(val)
                    good_mask.append(True)
                except ValueError:
                    good_mask.append(False)
            rejected += (~pd.Series(good_mask)).sum()
            df = df[pd.Series(good_mask).values]
            if table in YEAR_TABLES:
                df["_period_month"] = df["year"].map(_extract_month)
            df["year"] = df["year"].map(normalize_year)

        clean[table] = df.reset_index(drop=True)
        audit_rows.append({"table": table, "stage": "normalise",
                            "rows_in": rows_in, "rows_out": len(df), "rejected": rejected})
    return clean


def dedupe_by_dominant_fiscal_month(df: pd.DataFrame) -> pd.DataFrame:
    """
    Some companies report on non-March fiscal year-ends (e.g. NESTLEIND,
    AMBUJACEM = December; SIEMENS = September). When a (company_id, year)
    collision happens because of a bonus interim snapshot row (e.g. an
    extra 'Sep 2024' row alongside the real 'Mar 2024' year-end row), we
    must NOT just keep-last -- we keep the row whose reporting month
    matches that company's own dominant/most common month, since that is
    the real annual figure. This avoids wrongly deleting December-FYE or
    September-FYE companies' legitimate data.
    """
    if "_period_month" not in df.columns:
        return df.drop_duplicates(subset=["company_id", "year"], keep="last")

    dominant_month = (
        df.groupby("company_id")["_period_month"]
        .agg(lambda s: s.value_counts().idxmax())
    )
    df = df.copy()
    df["_dominant_month"] = df["company_id"].map(dominant_month)
    df["_is_dominant"] = df["_period_month"] == df["_dominant_month"]

    # Prefer the dominant-month row on ties; fall back to last row otherwise.
    df = df.sort_values(["company_id", "year", "_is_dominant"])
    df = df.drop_duplicates(subset=["company_id", "year"], keep="last")
    return df.drop(columns=["_period_month", "_dominant_month", "_is_dominant"])


def drop_critical_violations(frames: dict, audit_rows: list) -> dict:
    """DQ-01/02/03: drop duplicate PKs and orphan FK rows before loading.
    Logs exactly how many rows were dropped and why, per table."""
    companies = frames["companies"]
    before = len(companies)
    frames["companies"] = companies.drop_duplicates(subset="id", keep="first")
    valid_ids = set(frames["companies"]["id"])
    audit_rows.append({"table": "companies", "stage": "dedupe_fk",
                        "rows_in": before, "rows_out": len(frames["companies"]),
                        "rejected": before - len(frames["companies"])})

    for table in ["profitandloss", "balancesheet", "cashflow", "financial_ratios"]:
        if table in frames:
            before = len(frames[table])
            after_dedup = dedupe_by_dominant_fiscal_month(frames[table])
            dedup_dropped = before - len(after_dedup)

            before_fk = len(after_dedup)
            after_fk = after_dedup[after_dedup["company_id"].isin(valid_ids)].reset_index(drop=True)
            fk_dropped = before_fk - len(after_fk)

            frames[table] = after_fk
            audit_rows.append({"table": table, "stage": "dedupe_fk",
                                "rows_in": before, "rows_out": len(after_fk),
                                "rejected": dedup_dropped + fk_dropped,
                                "note": f"{dedup_dropped} duplicate PK, {fk_dropped} orphan FK"})

    for table, df in frames.items():
        if table not in ["companies", "profitandloss", "balancesheet", "cashflow", "financial_ratios"] \
                and "company_id" in df.columns:
            before = len(df)
            after = df[df["company_id"].isin(valid_ids)].reset_index(drop=True)
            frames[table] = after
            audit_rows.append({"table": table, "stage": "dedupe_fk",
                                "rows_in": before, "rows_out": len(after),
                                "rejected": before - len(after), "note": "orphan FK"})

    return frames


def load_to_sqlite(frames: dict, audit_rows: list):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())

    table_col_map = {
        "companies": ["id", "company_logo", "company_name", "chart_link", "about_company",
                      "website", "nse_profile", "bse_profile", "face_value", "book_value",
                      "roce_percentage", "roe_percentage"],
        "profitandloss": ["id", "company_id", "year", "sales", "expenses", "operating_profit",
                           "opm_percentage", "other_income", "interest", "depreciation",
                           "profit_before_tax", "tax_percentage", "net_profit", "eps", "dividend_payout"],
        "balancesheet": ["id", "company_id", "year", "equity_capital", "reserves", "borrowings",
                          "other_liabilities", "total_liabilities", "fixed_assets", "cwip",
                          "investments", "other_asset", "total_assets"],
        "cashflow": ["id", "company_id", "year", "operating_activity", "investing_activity",
                     "financing_activity", "net_cash_flow"],
        "analysis": ["id", "company_id", "compounded_sales_growth", "compounded_profit_growth",
                     "stock_price_cagr", "roe"],
        "documents": ["id", "company_id", "year", "annual_report"],
        "prosandcons": ["id", "company_id", "pros", "cons"],
        "sectors": ["id", "company_id", "broad_sector", "sub_sector", "index_weight_pct",
                    "market_cap_category"],
        "stock_prices": ["id", "company_id", "date", "open_price", "high_price", "low_price",
                          "close_price", "volume", "adjusted_close"],
        "market_cap": ["id", "company_id", "year", "market_cap_crore", "enterprise_value_crore",
                        "pe_ratio", "pb_ratio", "ev_ebitda", "dividend_yield_pct"],
        "financial_ratios": ["id", "company_id", "year", "net_profit_margin_pct",
                              "operating_profit_margin_pct", "return_on_equity_pct", "debt_to_equity",
                              "interest_coverage", "asset_turnover", "free_cash_flow_cr", "capex_cr",
                              "earnings_per_share", "book_value_per_share", "dividend_payout_ratio_pct",
                              "total_debt_cr", "cash_from_operations_cr"],
        "peer_groups": ["id", "peer_group_name", "company_id", "is_benchmark"],
    }

    load_order = ["companies", "profitandloss", "balancesheet", "cashflow", "analysis",
                   "documents", "prosandcons", "sectors", "stock_prices", "market_cap",
                   "financial_ratios", "peer_groups"]

    for table in load_order:
        df = frames[table]
        cols = [c for c in table_col_map[table] if c in df.columns]
        t0 = time.time()
        df[cols].to_sql(table, conn, if_exists="append", index=False)
        runtime = time.time() - t0
        cur = conn.execute(f"SELECT COUNT(*) FROM {table}")
        rows_out = cur.fetchone()[0]
        audit_rows.append({"table": table, "stage": "load",
                            "rows_in": len(df), "rows_out": rows_out,
                            "rejected": 0, "runtime_s": round(runtime, 4)})

    fk_check = conn.execute("PRAGMA foreign_key_check;").fetchall()
    conn.commit()
    conn.close()
    return fk_check


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    audit_rows = []

    print("Step 1/5: Reading 12 raw Excel files...")
    frames = read_raw_files()

    print("Step 2/5: Normalising ticker + year fields...")
    frames = normalise_frames(frames, audit_rows)

    print("Step 3/5: Running 16 DQ rule checks...")
    violations = run_all_checks(frames)
    violations.to_csv(OUTPUT_DIR / "validation_failures.csv", index=False)
    n_critical = (violations["severity"] == "CRITICAL").sum() if len(violations) else 0
    print(f"   -> {len(violations)} total DQ issues found ({n_critical} CRITICAL)")

    print("Step 4/5: Dropping CRITICAL violations (dupes / orphan FKs) before load...")
    frames = drop_critical_violations(frames, audit_rows)

    print("Step 5/5: Loading into SQLite (nifty100.db)...")
    fk_check = load_to_sqlite(frames, audit_rows)

    audit_df = pd.DataFrame(audit_rows)
    audit_df.to_csv(OUTPUT_DIR / "load_audit.csv", index=False)

    print("\n=== DONE ===")
    print(f"DB written to: {DB_PATH}")
    print(f"FK check violations: {len(fk_check)} (should be 0)")
    print(f"Companies loaded: {len(frames['companies'])}")
    print("Audit log: output/load_audit.csv")
    print("DQ report: output/validation_failures.csv")


if __name__ == "__main__":
    main()
