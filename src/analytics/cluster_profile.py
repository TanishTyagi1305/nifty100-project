"""
cluster_profile.py
-------------------
Day 37: profiles each cluster, generates a correlation heatmap,
flags outliers (Z-score > 3), and computes portfolio-wide percentile stats.
"""
import sqlite3
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import os

FEATURES = ["return_on_equity_pct", "debt_to_equity", "revenue_cagr_5yr",
            "fcf_cagr_5yr", "operating_profit_margin_pct"]

KPI_COLS = ["return_on_equity_pct", "net_profit_margin_pct", "debt_to_equity",
            "revenue_cagr_5yr", "pat_cagr_5yr", "eps_cagr_5yr",
            "interest_coverage", "asset_turnover", "free_cash_flow_cr",
            "operating_profit_margin_pct"]


def load_data():
    conn = sqlite3.connect("db/nifty100.db")
    ratios = pd.read_sql("""
        SELECT * FROM financial_ratios
        WHERE year = (SELECT MAX(year) FROM financial_ratios)
    """, conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    conn.close()
    df = ratios.merge(sectors, on="company_id", how="left")
    clusters = pd.read_csv("output/cluster_labels.csv")
    df = df.merge(clusters[["company_id", "cluster_id", "cluster_name"]], on="company_id", how="left")
    return df


def profile_clusters(df):
    print("=== Cluster Profiles (Mean of each feature) ===")
    profile = df.groupby(["cluster_id", "cluster_name"])[FEATURES].agg(["mean", "median"])
    print(profile.round(2))
    print()
    print("=== Companies per cluster ===")
    for cid in sorted(df["cluster_id"].dropna().unique()):
        name = df[df["cluster_id"] == cid]["cluster_name"].iloc[0]
        companies = df[df["cluster_id"] == cid]["company_id"].tolist()
        print(f"Cluster {int(cid)} ({name}): {companies}")
    print()


def generate_correlation_heatmap(df):
    corr = df[KPI_COLS].corr()
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", ax=ax, annot_kws={"size": 7})
    ax.set_title("Pearson Correlation — 10 KPIs across 92 companies", fontsize=12)
    plt.tight_layout()
    plt.savefig("reports/correlation_heatmap.png", dpi=120)
    plt.close(fig)
    print("reports/correlation_heatmap.png saved")


def detect_outliers(df):
    outliers = []
    for sector, sector_df in df.groupby("broad_sector"):
        for col in FEATURES:
            vals = sector_df[col].dropna()
            if len(vals) < 3:
                continue
            z_scores = (sector_df[col] - vals.mean()) / vals.std()
            flagged = sector_df[z_scores.abs() > 3]
            for _, row in flagged.iterrows():
                outliers.append(dict(
                    company_id=row["company_id"], broad_sector=sector,
                    metric=col, value=row[col],
                    z_score=round(z_scores[row.name], 2),
                ))
    outlier_df = pd.DataFrame(outliers)
    outlier_df.to_csv("output/outlier_report.csv", index=False)
    print(f"output/outlier_report.csv written: {len(outlier_df)} outliers flagged")
    return outlier_df


def compute_portfolio_stats(df):
    stats = df[KPI_COLS].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9])
    stats.to_csv("output/portfolio_stats.csv")
    print("output/portfolio_stats.csv written")


if __name__ == "__main__":
    os.makedirs("reports", exist_ok=True)
    df = load_data()
    profile_clusters(df)
    generate_correlation_heatmap(df)
    outliers = detect_outliers(df)
    compute_portfolio_stats(df)
    if len(outliers) > 0:
        print("\nSample outliers:")
        print(outliers.head(5))