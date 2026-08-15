import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Capital Allocation Map")


@st.cache_data(ttl=600)
def load_capital_data():
    return pd.read_csv("output/capital_allocation.csv")


df = load_capital_data()

# use each company's most recent year only, one box per company
latest = df.sort_values("year").groupby("company_id").tail(1)

st.write(f"Showing {len(latest)} companies across {latest['pattern_label'].nunique()} capital allocation patterns")

fig = px.treemap(
    latest, path=["pattern_label", "company_id"],
    color="pattern_label",
)
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Companies by Pattern")
selected_pattern = st.selectbox("Select a pattern to see its companies", sorted(latest["pattern_label"].unique()))
pattern_companies = latest[latest["pattern_label"] == selected_pattern]["company_id"].tolist()
st.write(pattern_companies)