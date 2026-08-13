"""
app.py
------
Main Streamlit entry point. Streamlit auto-discovers every file in
pages/ and adds it to the sidebar navigation automatically -- this
file just sets shared page config that applies across the whole app.
"""
import streamlit as st

st.set_page_config(
    page_title="Nifty 100 Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Nifty 100 Analytics")
st.write("Use the sidebar to navigate between screens.")
st.write("This scaffold is working if you can see this text with no errors above it.")