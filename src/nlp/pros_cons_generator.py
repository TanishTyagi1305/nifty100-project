"""
pros_cons_generator.py
------------------------
12 pro rules + 12 con rules, each checking financial_ratios/profitandloss/
balancesheet/cashflow history for a specific pattern and generating a
sentence + confidence score (0-100). Only rules with confidence > 60
make it into the final output.
"""
import sqlite3
import pandas as pd


def load_company_history(company_id, conn):
    """All years of data for one company, needed to check 'sustained for
    N years' and 'declining for N years' style rules."""
    ratios = pd.read_sql("SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year", conn, params=[company_id])
    pnl = pd.read_sql("SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year", conn, params=[company_id])
    bs = pd.read_sql("SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year", conn, params=[company_id])
    cf = pd.read_sql("SELECT * FROM cashflow WHERE company_id = ? ORDER BY year", conn, params=[company_id])
    sector = pd.read_sql("SELECT broad_sector FROM sectors WHERE company_id = ?", conn, params=[company_id])
    broad_sector = sector.iloc[0]["broad_sector"] if len(sector) else None
    return ratios, pnl, bs, cf, broad_sector


# ---------------- PRO RULES 1-6 ----------------

def pro_rule_1_high_roe(ratios):
    """ROE > 20% sustained for 3+ years."""
    last3 = ratios.tail(3)
    if len(last3) < 3:
        return None
    if (last3["return_on_equity_pct"] > 20).all():
        return dict(rule_id="PRO-01", text="Consistently high return on equity above 20% demonstrates exceptional capital efficiency", confidence_pct=90)
    return None


def pro_rule_2_fcf_positive(ratios):
    """FCF positive for 5+ consecutive years."""
    last5 = ratios.tail(5)
    if len(last5) < 5:
        return None
    if (last5["free_cash_flow_cr"] > 0).all():
        return dict(rule_id="PRO-02", text="Strong free cash flow generation over 5 years signals healthy business fundamentals", confidence_pct=85)
    return None


def pro_rule_3_debt_free(ratios):
    """D/E = 0 in latest year."""
    if len(ratios) == 0:
        return None
    latest = ratios.iloc[-1]
    if latest["debt_to_equity"] == 0:
        return dict(rule_id="PRO-03", text="Debt-free balance sheet provides financial flexibility and eliminates interest burden", confidence_pct=95)
    return None


def pro_rule_4_revenue_cagr(ratios):
    """Revenue CAGR > 15% over 5 years."""
    if len(ratios) == 0:
        return None
    latest = ratios.iloc[-1]
    if pd.notna(latest["revenue_cagr_5yr"]) and latest["revenue_cagr_5yr"] > 15:
        return dict(rule_id="PRO-04", text="Revenue growing at above 15% CAGR over 5 years reflects strong business momentum", confidence_pct=85)
    return None


def pro_rule_5_high_opm(pnl):
    """OPM > 25% in latest year."""
    if len(pnl) == 0:
        return None
    latest = pnl.iloc[-1]
    if pd.notna(latest["opm_percentage"]) and latest["opm_percentage"] > 25:
        return dict(rule_id="PRO-05", text="Operating profit margin above 25% indicates strong pricing power and cost discipline", confidence_pct=80)
    return None


def pro_rule_6_pat_cagr(ratios):
    """PAT CAGR > 20% over 5 years."""
    if len(ratios) == 0:
        return None
    latest = ratios.iloc[-1]
    if pd.notna(latest["pat_cagr_5yr"]) and latest["pat_cagr_5yr"] > 20:
        return dict(rule_id="PRO-06", text="Net profit compounding at above 20% over 5 years creates significant shareholder value", confidence_pct=85)
    return None


# ---------------- PRO RULES 7-12 ----------------

def pro_rule_7_high_icr(ratios):
    """ICR > 10 OR Debt Free label."""
    if len(ratios) == 0:
        return None
    latest = ratios.iloc[-1]
    if latest.get("icr_label") == "Debt Free":
        return dict(rule_id="PRO-07", text="Very high interest coverage ratio reflects negligible financial stress from debt servicing", confidence_pct=90)
    if pd.notna(latest["interest_coverage"]) and latest["interest_coverage"] > 10:
        return dict(rule_id="PRO-07", text="Very high interest coverage ratio reflects negligible financial stress from debt servicing", confidence_pct=90)
    return None


def pro_rule_8_dividend_fcf(ratios, market_cap_row):
    """Dividend Yield > 2% AND FCF positive."""
    if len(ratios) == 0 or market_cap_row is None:
        return None
    latest = ratios.iloc[-1]
    div_yield = market_cap_row.get("dividend_yield_pct")
    if pd.notna(div_yield) and div_yield > 2 and pd.notna(latest["free_cash_flow_cr"]) and latest["free_cash_flow_cr"] > 0:
        return dict(rule_id="PRO-08", text="Consistent dividend yield above 2% backed by positive free cash flow", confidence_pct=80)
    return None


def pro_rule_9_eps_cagr(ratios):
    """EPS CAGR > 15% over 5 years."""
    if len(ratios) == 0:
        return None
    latest = ratios.iloc[-1]
    if pd.notna(latest["eps_cagr_5yr"]) and latest["eps_cagr_5yr"] > 15:
        return dict(rule_id="PRO-09", text="Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding", confidence_pct=85)
    return None


def pro_rule_10_roe_improving(ratios):
    """ROE improving for 3 consecutive years (each year higher than the last)."""
    last3 = ratios.tail(3)
    if len(last3) < 3:
        return None
    values = last3["return_on_equity_pct"].tolist()
    if pd.notna(values).all() and values[0] < values[1] < values[2]:
        return dict(rule_id="PRO-10", text="Return on equity improving for 3 consecutive years shows strengthening business quality", confidence_pct=75)
    return None


def pro_rule_11_operating_leverage(ratios):
    """Revenue CAGR > 0 but PAT CAGR > Revenue CAGR (profits growing faster than revenue)."""
    if len(ratios) == 0:
        return None
    latest = ratios.iloc[-1]
    rev_cagr, pat_cagr = latest.get("revenue_cagr_5yr"), latest.get("pat_cagr_5yr")
    if pd.notna(rev_cagr) and pd.notna(pat_cagr) and rev_cagr > 0 and pat_cagr > rev_cagr:
        return dict(rule_id="PRO-11", text="Revenue growing slower than profits shows improving operating leverage and scale benefits", confidence_pct=70)
    return None


def pro_rule_12_self_sustaining_growth(bs):
    """Total assets growing while borrowings decline, over the last 3 years."""
    last3 = bs.tail(3)
    if len(last3) < 3:
        return None
    assets_growing = last3["total_assets"].is_monotonic_increasing
    debt_declining = last3["borrowings"].is_monotonic_decreasing
    if assets_growing and debt_declining:
        return dict(rule_id="PRO-12", text="Growing asset base funded by internal accruals reflects self-sustaining growth", confidence_pct=75)
    return None


if __name__ == "__main__":
    conn = sqlite3.connect("db/nifty100.db")

    test_ticker = "TCS"
    ratios, pnl, bs, cf, sector = load_company_history(test_ticker, conn)
    market_cap_row = pd.read_sql("SELECT * FROM market_cap WHERE company_id = ? ORDER BY year DESC LIMIT 1",
                                   conn, params=[test_ticker])
    mc_row = market_cap_row.iloc[0] if len(market_cap_row) else None

    rules_to_test = [
        pro_rule_1_high_roe(ratios), pro_rule_2_fcf_positive(ratios), pro_rule_3_debt_free(ratios),
        pro_rule_4_revenue_cagr(ratios), pro_rule_5_high_opm(pnl), pro_rule_6_pat_cagr(ratios),
        pro_rule_7_high_icr(ratios), pro_rule_8_dividend_fcf(ratios, mc_row), pro_rule_9_eps_cagr(ratios),
        pro_rule_10_roe_improving(ratios), pro_rule_11_operating_leverage(ratios), pro_rule_12_self_sustaining_growth(bs),
    ]

    print(f"{test_ticker} -- All 12 pro rules:")
    fired = 0
    for r in rules_to_test:
        if r:
            fired += 1
            print(" ", r)
    print(f"\n{fired} of 12 pro rules fired for {test_ticker}")

    conn.close()