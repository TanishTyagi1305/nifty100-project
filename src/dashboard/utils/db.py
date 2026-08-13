"""
db.py
-----
Shared, cached data loader for the Streamlit dashboard. Every screen
should call these functions instead of writing its own SQL -- keeps
all 8 screens consistent and avoids repeating query logic.
"""
import sqlite3
import pandas as pd
import streamlit as st

DB_PATH = "db/nifty100.db"


@st.cache_data(ttl=600)
def get_companies():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM companies", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_ratios(ticker=None, year=None):
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM financial_ratios WHERE 1=1"
    params = []
    if ticker:
        query += " AND company_id = ?"
        params.append(ticker)
    if year:
        query += " AND year = ?"
        params.append(year)
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_pl(ticker):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year", conn, params=[ticker])
    conn.close()
    return df


if __name__ == "__main__":
    # Quick sanity check -- NOT run through Streamlit, just plain Python,
    # so we can verify the queries work before wiring them into a screen.
    companies = get_companies()
    print(f"get_companies(): {len(companies)} rows")

    ratios = get_ratios(ticker="TCS")
    print(f"get_ratios('TCS'): {len(ratios)} rows")

    pl = get_pl("TCS")
    print(f"get_pl('TCS'): {len(pl)} rows")