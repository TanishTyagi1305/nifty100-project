import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

st.title("Sector Analysis")

DB_PATH = "db/nifty100.db"


@st.cache_data(ttl=600)
def load_sector_data():
    conn = sqlite3.connect(DB_PATH)
    ratios = pd.read_sql("""
        SELECT * FROM financial_ratios WHERE year = (SELECT MAX(year) FROM financial_ratios)
    """, conn)
    pnl = pd.read_sql("""
        SELECT company_id, sales FROM profitandloss WHERE year = (SELECT MAX(year) FROM profitandloss)
    """, conn)
    market_cap = pd.read_sql("""
        SELECT company_id, market_cap_crore FROM market_cap WHERE year = (SELECT MAX(year) FROM market_cap)
    """, conn)
    sectors = pd.read_sql("SELECT * FROM sectors", conn)
    companies = pd.read_sql("SELECT id, company_name FROM companies", conn)
    conn.close()

    df = ratios.merge(pnl, on="company_id", how="left")
    df = df.merge(market_cap, on="company_id", how="left")
    df = df.merge(sectors, on="company_id", how="left")
    df = df.merge(companies, left_on="company_id", right_on="id", how="left")
    return df


df = load_sector_data()

sector_names = sorted(df["broad_sector"].dropna().unique())
selected_sector = st.selectbox("Select sector", sector_names)

sector_df = df[df["broad_sector"] == selected_sector].dropna(
    subset=["sales", "return_on_equity_pct", "market_cap_crore"])

if len(sector_df) == 0:
    st.warning("Not enough data to plot this sector.")
    st.stop()

st.subheader(f"{selected_sector} — Revenue vs ROE")
fig = px.scatter(
    sector_df, x="sales", y="return_on_equity_pct",
    size="market_cap_crore", color="sub_sector",
    hover_name="company_name",
    labels={"sales": "Revenue (Cr)", "return_on_equity_pct": "ROE (%)"},
)
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader(f"{selected_sector} — Median KPIs")
medians = sector_df[["return_on_equity_pct", "net_profit_margin_pct", "debt_to_equity",
                      "revenue_cagr_5yr"]].median()
fig2 = px.bar(x=medians.index, y=medians.values, labels={"x": "Metric", "y": "Median Value"})
st.plotly_chart(fig2, use_container_width=True)