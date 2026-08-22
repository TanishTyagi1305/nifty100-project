"""
clustering.py
-------------
KMeans clustering of 92 companies into 5 archetypes using 5 financial
features. Missing values are imputed with sector medians before scaling.
"""
import sqlite3
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import os

FEATURES = ["return_on_equity_pct", "debt_to_equity", "revenue_cagr_5yr",
            "fcf_cagr_5yr", "operating_profit_margin_pct"]

CLUSTER_NAMES = {
    0: "Broad Market Core",
    1: "High-Margin Defensives",
    2: "High-ROE Quality Compounders",
    3: "Unique Outlier",
    4: "High-Growth Financials",
}


def load_features():
    conn = sqlite3.connect("db/nifty100.db")
    df = pd.read_sql("""
        SELECT f.company_id, f.return_on_equity_pct, f.debt_to_equity,
               f.revenue_cagr_5yr, f.fcf_cagr_5yr, f.operating_profit_margin_pct
        FROM financial_ratios f
        WHERE f.year = (SELECT MAX(year) FROM financial_ratios)
    """, conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    conn.close()
    df = df.merge(sectors, on="company_id", how="left")
    return df


def impute_with_sector_median(df):
    """Replace missing values with the sector median for each feature.
    If a whole sector has no data for a feature, fall back to the
    overall median across all companies."""
    df = df.copy()
    for feature in FEATURES:
        sector_medians = df.groupby("broad_sector")[feature].transform("median")
        global_median = df[feature].median()
        df[feature] = df[feature].fillna(sector_medians).fillna(global_median)
    return df


def generate_elbow_plot(X_scaled):
    os.makedirs("reports", exist_ok=True)
    inertias = []
    for k in range(2, 11):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)
        inertias.append(km.inertia_)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(range(2, 11), inertias, marker="o")
    ax.axvline(x=5, color="red", linestyle="--", label="k=5 (chosen)")
    ax.set_xlabel("Number of clusters (k)")
    ax.set_ylabel("Inertia")
    ax.set_title("KMeans Elbow Plot")
    ax.legend()
    plt.tight_layout()
    plt.savefig("reports/elbow_plot.png", dpi=120)
    plt.close(fig)
    print("reports/elbow_plot.png saved")


def run_clustering():
    df = load_features()
    df = impute_with_sector_median(df)

    X = df[FEATURES].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    generate_elbow_plot(X_scaled)

    km = KMeans(n_clusters=5, random_state=42, n_init=10)
    df["cluster_id"] = km.fit_predict(X_scaled)

    centroids = km.cluster_centers_
    distances = []
    for i, row in enumerate(X_scaled):
        centroid = centroids[df["cluster_id"].iloc[i]]
        dist = np.linalg.norm(row - centroid)
        distances.append(dist)
    df["distance_from_centroid"] = distances

    df["cluster_name"] = df["cluster_id"].map(CLUSTER_NAMES)

    output = df[["company_id", "cluster_id", "cluster_name", "distance_from_centroid"]]
    output.to_csv("output/cluster_labels.csv", index=False)
    print(f"output/cluster_labels.csv written: {len(output)} rows")

    print("\nCluster distribution:")
    print(df.groupby(["cluster_id", "cluster_name"]).size())

    return df


if __name__ == "__main__":
    df = run_clustering()
    print("\nSample per cluster:")
    for cid in sorted(df["cluster_id"].unique()):
        companies = df[df["cluster_id"] == cid]["company_id"].tolist()[:5]
        print(f"  Cluster {cid} ({CLUSTER_NAMES[cid]}): {companies}")