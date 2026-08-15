import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go

st.title("Trend Analysis")

DB_PATH = "db/nifty100.db"


@st.cache_data(ttl=600)
def get_companies():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT id, company_name FROM companies", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_ratios_history(ticker):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year", conn, params=[ticker])
    conn.close()
    return df


companies = get_companies()
options = companies["id"] + " - " + companies["company_name"]
choice = st.selectbox("Search company", options=[""] + options.tolist())

if choice == "":
    st.info("Select a company to see its trends.")
    st.stop()

ticker = choice.split(" - ")[0]
df = get_ratios_history(ticker)

if len(df) == 0:
    st.warning("No data available for this company.")
    st.stop()

METRIC_OPTIONS = {
    "ROE (%)": "return_on_equity_pct",
    "Net Profit Margin (%)": "net_profit_margin_pct",
    "D/E": "debt_to_equity",
    "Revenue CAGR 5yr (%)": "revenue_cagr_5yr",
    "PAT CAGR 5yr (%)": "pat_cagr_5yr",
    "Free Cash Flow (Cr)": "free_cash_flow_cr",
}

selected_metrics = st.multiselect("Select up to 3 metrics to overlay",
                                   list(METRIC_OPTIONS.keys()),
                                   default=["ROE (%)"], max_selections=3)

if not selected_metrics:
    st.info("Select at least one metric.")
    st.stop()

fig = go.Figure()
for metric_label in selected_metrics:
    col = METRIC_OPTIONS[metric_label]
    series = df[col]

    yoy_pct = series.pct_change() * 100
    text_labels = [f"{v:+.1f}%" if pd.notna(v) else "" for v in yoy_pct]

    fig.add_trace(go.Scatter(
        x=df["year"], y=series, mode="lines+markers+text",
        text=text_labels, textposition="top center", name=metric_label,
    ))

fig.update_layout(title=f"{ticker} — 10 Year Trend", xaxis_title="Year")
st.plotly_chart(fig, use_container_width=True)