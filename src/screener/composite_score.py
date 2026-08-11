"""
composite_score.py
-------------------
0-100 composite quality score per company, built from 4 weighted
categories. Every metric is winsorised (capped at P10/P90) before
scaling, so one broken outlier can't distort everyone else's score.
"""
import sqlite3
import pandas as pd
import numpy as np


def winsorise_and_scale(series, higher_is_better=True):
    """Cap at 10th/90th percentile, then scale to 0-100."""
    s = series.copy()
    p10, p90 = s.quantile(0.10), s.quantile(0.90)
    s_clipped = s.clip(lower=p10, upper=p90)

    if p90 == p10:  # avoid divide-by-zero if everyone has the same value
        return pd.Series(50, index=s.index)

    scaled = (s_clipped - p10) / (p90 - p10) * 100
    if not higher_is_better:
        scaled = 100 - scaled
    return scaled


def compute_composite_scores():
    conn = sqlite3.connect("db/nifty100.db")
    df = pd.read_sql("""
        SELECT * FROM financial_ratios
        WHERE year = (SELECT MAX(year) FROM financial_ratios)
    """, conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    conn.close()

    df = df.merge(sectors, on="company_id", how="left")

    # Profitability (35%): ROE 15 + ROCE 10 + NPM 10 -- we don't have ROCE
    # stored in financial_ratios (only computed transiently in Sprint 2),
    # so for now we use ROE and NPM, reweighted proportionally (15+10=25 -> scale to 35)
    roe_score = winsorise_and_scale(df["return_on_equity_pct"])
    npm_score = winsorise_and_scale(df["net_profit_margin_pct"])
    profitability = (roe_score * 0.6 + npm_score * 0.4) * 0.35

    # Growth (20%): Revenue CAGR 10 + PAT CAGR 10
    rev_cagr_score = winsorise_and_scale(df["revenue_cagr_5yr"].fillna(df["revenue_cagr_5yr"].median()))
    pat_cagr_score = winsorise_and_scale(df["pat_cagr_5yr"].fillna(df["pat_cagr_5yr"].median()))
    growth = (rev_cagr_score * 0.5 + pat_cagr_score * 0.5) * 0.20

    # Cash Quality (30%): FCF positive flag as a simple proxy (full CFO/PAT
    # ratio + FCF CAGR would need more history than we're using here)
    fcf_positive = (df["free_cash_flow_cr"] > 0).astype(float) * 100
    cash_quality = fcf_positive * 0.30

    # Leverage (15%): D/E score (lower is better) + ICR risk (not flagged = good)
    de_score = winsorise_and_scale(df["debt_to_equity"].fillna(df["debt_to_equity"].median()), higher_is_better=False)
    icr_ok_score = (df["icr_risk_flag"] == 0).astype(float) * 100
    leverage = (de_score * 0.67 + icr_ok_score * 0.33) * 0.15

    df["composite_quality_score"] = profitability + growth + cash_quality + leverage

    # Sector-relative score: normalise within each broad_sector separately
    df["sector_relative_score"] = df.groupby("broad_sector")["composite_quality_score"].transform(
        lambda x: (x - x.min()) / (x.max() - x.min()) * 100 if x.max() > x.min() else 50
    )

    return df


if __name__ == "__main__":
    df = compute_composite_scores()
    print(df[["company_id", "composite_quality_score", "sector_relative_score"]]
          .sort_values("composite_quality_score", ascending=False).head(15))