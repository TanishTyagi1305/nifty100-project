import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

st.title("Home")

DB_PATH = "db/nifty100.db"


@st.cache_data(ttl=600)
def load_home_data():
    conn = sqlite3.connect(DB_PATH)
    latest_year = conn.execute("SELECT MAX(year) FROM financial_ratios").fetchone()[0]

    ratios = pd.read_sql(f"SELECT * FROM financial_ratios WHERE year = {latest_year}", conn)
    market_cap = pd.read_sql(f"SELECT * FROM market_cap WHERE year = {latest_year}", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    companies = pd.read_sql("SELECT id, company_name FROM companies", conn)

    conn.close()
    return latest_year, ratios, market_cap, sectors, companies


latest_year, ratios, market_cap, sectors, companies = load_home_data()

st.caption(f"Showing data for fiscal year {latest_year}")

# 6 KPI tiles
col1, col2, col3 = st.columns(3)
col4, col5, col6 = st.columns(3)

col1.metric("Average ROE", f"{ratios['return_on_equity_pct'].mean():.1f}%")
col2.metric("Median P/E", f"{market_cap['pe_ratio'].median():.1f}")
col3.metric("Median D/E", f"{ratios['debt_to_equity'].median():.2f}")
col4.metric("Total Companies", len(companies))
col5.metric("Median Revenue CAGR 5yr", f"{ratios['revenue_cagr_5yr'].median():.1f}%")
col6.metric("Debt-Free Companies", int((ratios['debt_to_equity'] == 0).sum()))

st.divider()

# Sector breakdown donut chart
st.subheader("Companies by Sector")
sector_counts = sectors["broad_sector"].value_counts().reset_index()
sector_counts.columns = ["Sector", "Count"]
fig = px.pie(sector_counts, names="Sector", values="Count", hole=0.5)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# Top 5 by composite score
st.subheader("Top 5 Companies by Composite Quality Score")
top5 = ratios.merge(companies, left_on="company_id", right_on="id")
top5 = top5[["company_id", "company_name", "composite_quality_score"]].dropna()
top5 = top5.sort_values("composite_quality_score", ascending=False).head(5)
st.dataframe(top5, use_container_width=True, hide_index=True)