import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.title("Company Profile")

DB_PATH = "db/nifty100.db"


@st.cache_data(ttl=600)
def get_all_companies():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT id, company_name FROM companies", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_company_detail(ticker):
    conn = sqlite3.connect(DB_PATH)
    company = pd.read_sql("SELECT * FROM companies WHERE id = ?", conn, params=[ticker])
    sector = pd.read_sql("SELECT * FROM sectors WHERE company_id = ?", conn, params=[ticker])
    ratios = pd.read_sql("SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year", conn, params=[ticker])
    pnl = pd.read_sql("SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year", conn, params=[ticker])
    proscons = pd.read_sql("SELECT * FROM prosandcons WHERE company_id = ?", conn, params=[ticker])
    conn.close()
    return company, sector, ratios, pnl, proscons


all_companies = get_all_companies()

# Search box with autocomplete via selectbox
options = all_companies["id"] + " - " + all_companies["company_name"]
choice = st.selectbox("Search company (name or ticker)", options=[""] + options.tolist())

if choice == "":
    st.info("Start typing a company name or ticker above to see its profile.")
    st.stop()

ticker = choice.split(" - ")[0]
company, sector, ratios, pnl, proscons = get_company_detail(ticker)

if len(company) == 0:
    st.warning("Ticker not found — please try another")
    st.stop()

# Company card
c = company.iloc[0]
s = sector.iloc[0] if len(sector) else None
st.subheader(f"{c['company_name']} ({ticker})")
if s is not None:
    st.caption(f"{s['broad_sector']} · {s['sub_sector']}")
st.write(c.get("about_company", "No description available."))

st.divider()

# 6 KPI tiles -- latest year
if len(ratios) == 0:
    st.warning("No financial ratio data available for this company.")
else:
    latest = ratios.sort_values("year").iloc[-1]
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)
    col1.metric("ROE", f"{latest['return_on_equity_pct']:.1f}%" if pd.notna(latest['return_on_equity_pct']) else "N/A")
    col2.metric("Net Profit Margin", f"{latest['net_profit_margin_pct']:.1f}%" if pd.notna(latest['net_profit_margin_pct']) else "N/A")
    col3.metric("D/E", f"{latest['debt_to_equity']:.2f}" if pd.notna(latest['debt_to_equity']) else "N/A")
    col4.metric("Revenue CAGR 5yr", f"{latest['revenue_cagr_5yr']:.1f}%" if pd.notna(latest['revenue_cagr_5yr']) else "N/A")
    col5.metric("FCF (Cr)", f"{latest['free_cash_flow_cr']:.0f}" if pd.notna(latest['free_cash_flow_cr']) else "N/A")
    col6.metric("ICR", f"{latest['interest_coverage']:.1f}" if pd.notna(latest['interest_coverage']) else (latest['icr_label'] or "N/A"))

    st.divider()

    # Revenue / Net Profit bar chart
    st.subheader("Revenue & Net Profit (10yr)")
    fig1 = go.Figure()
    fig1.add_bar(x=pnl["year"], y=pnl["sales"], name="Sales")
    fig1.add_bar(x=pnl["year"], y=pnl["net_profit"], name="Net Profit")
    st.plotly_chart(fig1, use_container_width=True)

    st.divider()

    # ROE / ROCE dual-axis (ROCE not stored, showing ROE only if that's all we have)
    st.subheader("ROE Trend (10yr)")
    fig2 = go.Figure()
    fig2.add_scatter(x=ratios["year"], y=ratios["return_on_equity_pct"], mode="lines+markers", name="ROE")
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# Pros and cons
st.subheader("Pros & Cons")
if len(proscons) > 0:
    pros_text = proscons.iloc[0].get("pros", "")
    cons_text = proscons.iloc[0].get("cons", "")
    col_a, col_b = st.columns(2)
    with col_a:
        for line in str(pros_text).split(";"):
            if line.strip():
                st.success(f"✔ {line.strip()}")
    with col_b:
        for line in str(cons_text).split(";"):
            if line.strip():
                st.error(f"✘ {line.strip()}")
else:
    st.write("No pros/cons data available.")