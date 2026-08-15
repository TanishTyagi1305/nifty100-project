import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go

st.title("Peer Comparison")

DB_PATH = "db/nifty100.db"


@st.cache_data(ttl=600)
def load_peer_data():
    conn = sqlite3.connect(DB_PATH)
    peer_groups = pd.read_sql("SELECT * FROM peer_groups", conn)
    ratios = pd.read_sql("""
        SELECT * FROM financial_ratios
        WHERE year = (SELECT MAX(year) FROM financial_ratios)
    """, conn)
    companies = pd.read_sql("SELECT id, company_name FROM companies", conn)
    conn.close()
    return peer_groups, ratios, companies


peer_groups, ratios, companies = load_peer_data()

group_names = sorted(peer_groups["peer_group_name"].unique())
selected_group = st.selectbox("Select peer group", group_names)

group_companies = peer_groups[peer_groups["peer_group_name"] == selected_group]
group_data = ratios.merge(group_companies, on="company_id")
group_data = group_data.merge(companies, left_on="company_id", right_on="id")

if len(group_data) == 0:
    st.warning("No data available for this peer group.")
    st.stop()

selected_company = st.selectbox("Select company for radar chart", group_data["company_id"].tolist())

# Radar chart: selected company vs peer group average
AXES = ["return_on_equity_pct", "net_profit_margin_pct", "debt_to_equity",
        "free_cash_flow_cr", "pat_cagr_5yr", "revenue_cagr_5yr", "composite_quality_score"]
AXIS_LABELS = ["ROE", "NPM", "D/E", "FCF", "PAT CAGR", "Rev CAGR", "Composite"]

norm = group_data.copy()
for col in AXES:
    lo, hi = norm[col].min(), norm[col].max()
    if hi > lo:
        norm[col + "_scaled"] = (norm[col] - lo) / (hi - lo) * 100
    else:
        norm[col + "_scaled"] = 50

company_row = norm[norm["company_id"] == selected_company].iloc[0]
peer_avg = norm[[c + "_scaled" for c in AXES]].mean()

fig = go.Figure()
fig.add_trace(go.Scatterpolar(
    r=[company_row[c + "_scaled"] for c in AXES], theta=AXIS_LABELS,
    fill="toself", name=selected_company))
fig.add_trace(go.Scatterpolar(
    r=[peer_avg[c + "_scaled"] for c in AXES], theta=AXIS_LABELS,
    fill="toself", name="Peer Average", opacity=0.5))
fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader(f"{selected_group} — Full Group Comparison")

is_benchmark_col = group_data.get("is_benchmark")
display_cols = ["company_id", "company_name", "return_on_equity_pct", "debt_to_equity",
                 "pat_cagr_5yr", "composite_quality_score"]

def highlight_benchmark(row):
    if row.get("is_benchmark"):
        return ["background-color: gold"] * len(row)
    return [""] * len(row)

styled = group_data[display_cols + ["is_benchmark"]].style.apply(highlight_benchmark, axis=1)
st.dataframe(styled, use_container_width=True, hide_index=True, column_config={"is_benchmark": None})