"""
peer.py
-------
Computes percentile rank for each company, within its own peer group,
across 10 key metrics. D/E is inverted since lower debt is better.
"""
import sqlite3
import pandas as pd

METRICS = [
    "return_on_equity_pct", "net_profit_margin_pct", "debt_to_equity",
    "free_cash_flow_cr", "pat_cagr_5yr", "revenue_cagr_5yr",
    "eps_cagr_5yr", "interest_coverage", "asset_turnover",
]
# D/E is the one metric where LOWER is better -- percentile needs inverting
INVERT_METRICS = {"debt_to_equity"}


def load_data():
    conn = sqlite3.connect("db/nifty100.db")
    ratios = pd.read_sql("""
        SELECT * FROM financial_ratios
        WHERE year = (SELECT MAX(year) FROM financial_ratios)
    """, conn)
    peer_groups = pd.read_sql("SELECT company_id, peer_group_name FROM peer_groups", conn)
    conn.close()
    return ratios, peer_groups


def compute_percentiles():
    ratios, peer_groups = load_data()
    df = ratios.merge(peer_groups, on="company_id", how="left")

    results = []
    for group_name, group_df in df.groupby("peer_group_name"):
        for metric in METRICS:
            valid = group_df[group_df[metric].notna()]
            if len(valid) < 2:
                continue  # can't rank with fewer than 2 companies

            ranks = valid[metric].rank(pct=True)  # 0.0 to 1.0, higher value = higher rank
            if metric in INVERT_METRICS:
                ranks = 1 - ranks

            for company_id, pct_rank, value in zip(valid["company_id"], ranks, valid[metric]):
                results.append(dict(
                    company_id=company_id, peer_group_name=group_name,
                    metric=metric, value=value, percentile_rank=pct_rank,
                    year=int(group_df["year"].iloc[0]),
                ))

    # companies with no peer group at all
    no_group = df[df["peer_group_name"].isna()]["company_id"].unique()
    if len(no_group) > 0:
        print(f"No peer group assigned for {len(no_group)} companies: {list(no_group)}")

    return pd.DataFrame(results)


if __name__ == "__main__":
    result_df = compute_percentiles()

    conn = sqlite3.connect("db/nifty100.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS peer_percentiles (
            company_id TEXT, peer_group_name TEXT, metric TEXT,
            value REAL, percentile_rank REAL, year INTEGER
        )
    """)
    conn.execute("DELETE FROM peer_percentiles")
    result_df.to_sql("peer_percentiles", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()

    print(f"\npeer_percentiles table populated: {len(result_df)} rows")

    print("\nIT Services group, ROE percentile ranks:")
    it_roe = result_df[(result_df["peer_group_name"] == "IT Services") &
                        (result_df["metric"] == "return_on_equity_pct")]
    print(it_roe[["company_id", "value", "percentile_rank"]].sort_values("value", ascending=False))