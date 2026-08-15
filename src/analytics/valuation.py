"""
valuation.py
------------
FCF Yield and overvaluation/discount flags, based on comparing each
company's P/E to its own sector's median P/E.
"""
import sqlite3
import pandas as pd


def compute_fcf_yield(fcf_cr, market_cap_crore):
    if not market_cap_crore:
        return None
    return (fcf_cr / market_cap_crore) * 100


def compute_valuation_flag(pe_ratio, sector_median_pe):
    if pe_ratio is None or sector_median_pe is None or sector_median_pe == 0:
        return "Fair"  # can't judge without a valid comparison, default to neutral
    if pe_ratio > sector_median_pe * 1.5:
        return "Caution"
    if pe_ratio < sector_median_pe * 0.7:
        return "Discount"
    return "Fair"


def build_valuation_summary():
    conn = sqlite3.connect("db/nifty100.db")
    ratios = pd.read_sql("""
        SELECT company_id, free_cash_flow_cr FROM financial_ratios
        WHERE year = (SELECT MAX(year) FROM financial_ratios)
    """, conn)
    market_cap = pd.read_sql("""
        SELECT * FROM market_cap WHERE year = (SELECT MAX(year) FROM market_cap)
    """, conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    companies = pd.read_sql("SELECT id AS company_id, company_name FROM companies", conn)
    conn.close()

    df = market_cap.merge(ratios, on="company_id", how="left")
    df = df.merge(sectors, on="company_id", how="left")
    df = df.merge(companies, on="company_id", how="left")

    sector_median_pe = df.groupby("broad_sector")["pe_ratio"].median()
    df["sector_median_pe"] = df["broad_sector"].map(sector_median_pe)

    df["fcf_yield_pct"] = df.apply(
        lambda r: compute_fcf_yield(r["free_cash_flow_cr"], r["market_cap_crore"]), axis=1)
    df["pe_vs_sector_median_pct"] = ((df["pe_ratio"] - df["sector_median_pe"]) / df["sector_median_pe"]) * 100
    df["flag"] = df.apply(
        lambda r: compute_valuation_flag(r["pe_ratio"], r["sector_median_pe"]), axis=1)

    return df


if __name__ == "__main__":
    df = build_valuation_summary()
    print(f"Total rows: {len(df)}")
    print()
    print("Flag distribution:")
    print(df["flag"].value_counts())
    print()
    print("Sample (5 rows):")
    print(df[["company_id", "pe_ratio", "sector_median_pe", "flag"]].head())