"""
presets.py
----------
6 named threshold combinations, built on top of engine.py's
apply_filters() function. Each preset is just a different config dict.
"""
from src.screener.engine import load_all_metrics, apply_filters

PRESETS = {
    "Quality Compounder": {
        "roe_min": 15, "de_max": 1.0, "fcf_min": 0, "revenue_cagr_5yr_min": 10,
    },
    "Value Pick": {
        "pe_max": 20, "pb_max": 3.0, "de_max": 2.0, "dividend_yield_min": 1,
    },
    "Growth Accelerator": {
        "pat_cagr_5yr_min": 20, "revenue_cagr_5yr_min": 15, "de_max": 2.0,
    },
    "Dividend Champion": {
        "dividend_yield_min": 2, "fcf_min": 0,
        # dividend_payout_max isn't in engine.py yet -- added as a special case below
    },
    "Debt-Free Blue Chip": {
        "roe_min": 12, "sales_min": 5000,
        # de == 0 exactly is a special case, handled below, not a normal "max" filter
    },
}


def run_preset(name):
    df = load_all_metrics()

    if name == "Debt-Free Blue Chip":
        # D/E must be EXACTLY 0 (truly debt-free), not just "low" -- apply_filters
        # only supports max/min thresholds, so this one needs a direct check here.
        result = apply_filters(df, PRESETS[name])
        result = result[result["debt_to_equity"] == 0]
        return result

    if name == "Dividend Champion":
        result = apply_filters(df, PRESETS[name])
        result = result[result["dividend_payout_ratio_pct"] < 80]
        return result

    return apply_filters(df, PRESETS[name])


if __name__ == "__main__":
    for name in PRESETS:
        result = run_preset(name)
        print(f"{name}: {len(result)} companies")
        print(result["company_id"].tolist())
        print()