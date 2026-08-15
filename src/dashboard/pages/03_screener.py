import streamlit as st
import sys
sys.path.insert(0, ".")  # so we can import from src/screener the same way our scripts do

from src.screener.engine import load_all_metrics, apply_filters
from src.screener.presets import PRESETS

st.title("Screener")

df = load_all_metrics()

# preset buttons -- clicking one fills session_state, which the sliders read from
st.write("**Presets**")
preset_cols = st.columns(len(PRESETS) + 1)
for i, name in enumerate(PRESETS):
    if preset_cols[i].button(name):
        st.session_state.update(PRESETS[name])
if preset_cols[-1].button("Reset"):
    for key in ["roe_min", "de_max", "fcf_min", "revenue_cagr_5yr_min", "pat_cagr_5yr_min",
                "opm_min", "pe_max", "pb_max", "dividend_yield_min", "icr_min"]:
        st.session_state.pop(key, None)

st.sidebar.write("**Filter Thresholds**")
roe_min = st.sidebar.slider("ROE min (%)", 0, 100, st.session_state.get("roe_min", 0))
de_max = st.sidebar.slider("D/E max", 0.0, 10.0, st.session_state.get("de_max", 10.0))
fcf_min = st.sidebar.slider("FCF min (Cr)", -5000, 20000, st.session_state.get("fcf_min", -5000))
rev_cagr_min = st.sidebar.slider("Revenue CAGR 5yr min (%)", -20, 50, st.session_state.get("revenue_cagr_5yr_min", -20))
pat_cagr_min = st.sidebar.slider("PAT CAGR 5yr min (%)", -20, 100, st.session_state.get("pat_cagr_5yr_min", -20))
opm_min = st.sidebar.slider("OPM min (%)", 0, 60, st.session_state.get("opm_min", 0))
pe_max = st.sidebar.slider("P/E max", 0, 100, st.session_state.get("pe_max", 100))
pb_max = st.sidebar.slider("P/B max", 0.0, 20.0, st.session_state.get("pb_max", 20.0))
div_yield_min = st.sidebar.slider("Dividend Yield min (%)", 0.0, 5.0, st.session_state.get("dividend_yield_min", 0.0))
icr_min = st.sidebar.slider("ICR min", 0.0, 20.0, st.session_state.get("icr_min", 0.0))

config = {
    "roe_min": roe_min, "de_max": de_max, "fcf_min": fcf_min,
    "revenue_cagr_5yr_min": rev_cagr_min, "pat_cagr_5yr_min": pat_cagr_min,
    "opm_min": opm_min, "pe_max": pe_max, "pb_max": pb_max,
    "dividend_yield_min": div_yield_min, "icr_min": icr_min,
}

result = apply_filters(df, config)

st.write(f"### {len(result)} companies match your filters")

display_cols = ["company_id", "broad_sector", "composite_quality_score",
                 "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr",
                 "pe_ratio", "pb_ratio"]
st.dataframe(result[display_cols], use_container_width=True, hide_index=True)

csv = result[display_cols].to_csv(index=False)
st.download_button("Download CSV", csv, file_name="screener_results.csv", mime="text/csv")