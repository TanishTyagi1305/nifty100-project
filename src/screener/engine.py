import sqlite3
import yaml
import pandas as pd


def load_config():
    with open("config/screener_config.yaml") as f:
        return yaml.safe_load(f)


def load_all_metrics():
    """Join financial_ratios, market_cap, and profitandloss for the latest
    year, so every one of the 15 filterable metrics is in one DataFrame."""
    conn = sqlite3.connect("db/nifty100.db")

    fr = pd.read_sql("""
        SELECT * FROM financial_ratios
        WHERE year = (SELECT MAX(year) FROM financial_ratios)
    """, conn)
    mc = pd.read_sql("""
        SELECT * FROM market_cap
        WHERE year = (SELECT MAX(year) FROM market_cap)
    """, conn)
    pnl = pd.read_sql("""
        SELECT * FROM profitandloss
        WHERE year = (SELECT MAX(year) FROM profitandloss)
    """, conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    conn.close()

    df = fr.merge(mc, on=["company_id", "year"], how="left", suffixes=("", "_mc"))
    df = df.merge(pnl, on=["company_id", "year"], how="left", suffixes=("", "_pnl"))
    df = df.merge(sectors, on="company_id", how="left")
    return df


def apply_filters(df, config):
    """Apply every threshold in config to the DataFrame, one at a time.
    Each filter is skipped if that key isn't present in the config."""
    result = df.copy()

    if "roe_min" in config:
        result = result[(result["return_on_equity_pct"] > config["roe_min"]) &
                         (result["return_on_equity_pct"] < 200)]

    if "de_max" in config:
        is_financials = result["broad_sector"] == "Financials"
        passes_de = result["debt_to_equity"] < config["de_max"]
        result = result[is_financials | passes_de]

    if "fcf_min" in config:
        result = result[result["free_cash_flow_cr"] > config["fcf_min"]]

    if "revenue_cagr_5yr_min" in config:
        result = result[result["revenue_cagr_5yr"] > config["revenue_cagr_5yr_min"]]

    if "pat_cagr_5yr_min" in config:
        result = result[result["pat_cagr_5yr"] > config["pat_cagr_5yr_min"]]

    if "opm_min" in config:
        result = result[result["opm_percentage"] > config["opm_min"]]

    if "pe_max" in config:
        result = result[result["pe_ratio"] < config["pe_max"]]

    if "pb_max" in config:
        result = result[result["pb_ratio"] < config["pb_max"]]

    if "dividend_yield_min" in config:
        result = result[result["dividend_yield_pct"] > config["dividend_yield_min"]]

    if "icr_min" in config:
        is_debt_free = result["icr_label"] == "Debt Free"
        passes_icr = result["interest_coverage"] > config["icr_min"]
        result = result[is_debt_free | passes_icr]

    if "market_cap_min" in config:
        result = result[result["market_cap_crore"] > config["market_cap_min"]]

    if "net_profit_min" in config:
        result = result[result["net_profit"] > config["net_profit_min"]]

    if "eps_cagr_5yr_min" in config:
        result = result[result["eps_cagr_5yr"] > config["eps_cagr_5yr_min"]]

    if "asset_turnover_min" in config:
        result = result[result["asset_turnover"] > config["asset_turnover_min"]]

    if "sales_min" in config:
        result = result[result["sales"] > config["sales_min"]]

    if "composite_quality_score" in result.columns:
        return result.sort_values("composite_quality_score", ascending=False)
    return result


if __name__ == "__main__":
    config = load_config()
    df = load_all_metrics()
    print(f"Total companies (latest year): {len(df)}")

    running = df.copy()
    for key in config:
        before = len(running)
        running = apply_filters(running, {key: config[key]})
        after = len(running)
        print(f"After applying '{key}' ({config[key]}): {before} -> {after}")

    print(f"\nFinal count: {len(running)}")
    print("\nFinal companies:")
    print(running[["company_id", "return_on_equity_pct", "debt_to_equity", "pat_cagr_5yr", "pb_ratio"]])