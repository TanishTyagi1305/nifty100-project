"""
radar.py
--------
8-axis radar chart per company: the company's own values as a filled
polygon, its peer group average as a dashed overlay. Falls back to a
simpler comparison for companies with no peer group.
"""
import sqlite3
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

AXES = ["return_on_equity_pct", "net_profit_margin_pct", "debt_to_equity",
        "free_cash_flow_cr", "pat_cagr_5yr", "revenue_cagr_5yr", "composite_quality_score"]
AXIS_LABELS = ["ROE", "NPM", "D/E (inv)", "FCF", "PAT CAGR", "Rev CAGR", "Composite"]


def normalise_for_radar(df):
    out = df.copy()
    for col in AXES:
        s = out[col].fillna(out[col].median())
        lo, hi = s.quantile(0.05), s.quantile(0.95)
        if hi == lo:
            out[col + "_scaled"] = 50
            continue
        scaled = ((s.clip(lo, hi) - lo) / (hi - lo)) * 100
        if col == "debt_to_equity":
            scaled = 100 - scaled
        out[col + "_scaled"] = scaled
    return out


def plot_radar(company_id, company_row, peer_avg_row, save_path):
    values = [company_row[c + "_scaled"] for c in AXES]
    peer_values = [peer_avg_row[c + "_scaled"] for c in AXES]

    angles = np.linspace(0, 2 * np.pi, len(AXES), endpoint=False).tolist()
    values += values[:1]
    peer_values += peer_values[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.plot(angles, values, color="tab:blue", linewidth=2, label=company_id)
    ax.fill(angles, values, color="tab:blue", alpha=0.25)
    ax.plot(angles, peer_values, color="gray", linewidth=1.5, linestyle="dashed", label="Peer Avg")

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(AXIS_LABELS, fontsize=10)
    ax.set_yticklabels([])
    ax.set_title(company_id, fontsize=14)
    ax.legend(loc="upper right", bbox_to_anchor=(1.2, 1.1))

    plt.tight_layout()
    plt.savefig(save_path, dpi=120)
    plt.close(fig)


if __name__ == "__main__":
    conn = sqlite3.connect("db/nifty100.db")
    ratios = pd.read_sql("""
        SELECT * FROM financial_ratios
        WHERE year = (SELECT MAX(year) FROM financial_ratios)
    """, conn)
    peer_groups = pd.read_sql("SELECT company_id, peer_group_name FROM peer_groups", conn)
    conn.close()

    df = ratios.merge(peer_groups, on="company_id", how="left")
    df = normalise_for_radar(df)

    tcs_row = df[df["company_id"] == "TCS"].iloc[0]
    peer_group_name = tcs_row["peer_group_name"]
    peer_rows = df[df["peer_group_name"] == peer_group_name]
    peer_avg = peer_rows[[c + "_scaled" for c in AXES]].mean()

    plot_radar("TCS", tcs_row, peer_avg, "reports/radar_charts/TCS_radar.png")
    print("Saved: reports/radar_charts/TCS_radar.png")