import streamlit as st
import sqlite3
import pandas as pd
import requests

st.title("Annual Reports")

DB_PATH = "db/nifty100.db"


@st.cache_data(ttl=600)
def get_companies():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT id, company_name FROM companies", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_documents(ticker):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM documents WHERE company_id = ? ORDER BY year DESC", conn, params=[ticker])
    conn.close()
    return df


def check_url(url, timeout=3):
    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=True)
        return resp.status_code == 200
    except Exception:
        return False


companies = get_companies()
options = companies["id"] + " - " + companies["company_name"]
choice = st.selectbox("Search company", options=[""] + options.tolist())

if choice == "":
    st.info("Select a company to see its annual reports.")
    st.stop()

ticker = choice.split(" - ")[0]
docs = get_documents(ticker)

if len(docs) == 0:
    st.warning("No annual report records found for this company.")
    st.stop()

st.write(f"### Annual Reports — {ticker}")

for _, row in docs.iterrows():
    url = row.get("annual_report")
    year = row.get("year")
    if pd.isna(url) or not str(url).startswith("http"):
        st.write(f"**{year}** — Report unavailable")
        continue
    st.markdown(f"**{year}** — [View Report]({url})")