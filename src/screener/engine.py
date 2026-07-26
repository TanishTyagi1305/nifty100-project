import sqlite3
import pandas as pd


def load_latest_ratios():
    """Pull the most recent year's financial_ratios row for every company."""
    conn = sqlite3.connect("db/nifty100.db")
    df = pd.read_sql("""
        SELECT * FROM financial_ratios
        WHERE year = (SELECT MAX(year) FROM financial_ratios)
    """, conn)
    conn.close()
    return df


def filter_by_roe_min(df, roe_min):
    """Keep only companies with ROE above the given threshold, and
    exclude implausible ROE values (>200%) which are known data errors."""
    return df[(df["return_on_equity_pct"] > roe_min) & (df["return_on_equity_pct"] < 200)]


if __name__ == "__main__":
    df = load_latest_ratios()
    print(f"Total companies (latest year): {len(df)}")

    filtered = filter_by_roe_min(df, roe_min=15)
    print(f"Companies with ROE > 15%: {len(filtered)}")
    print(filtered[["company_id", "return_on_equity_pct"]].sort_values("return_on_equity_pct", ascending=False).head(10))