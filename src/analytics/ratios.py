"""
ratios.py
---------
Profitability, leverage, and efficiency ratio functions.
Every function returns None where the formula is mathematically undefined
(division by zero, negative denominator, etc.) instead of crashing or
guessing -- except where 0 is the genuinely correct answer (debt-free
companies have a real D/E of 0, not a "missing" D/E).
"""


# ---------------- Profitability ratios ----------------

def net_profit_margin(net_profit, sales):
    if not sales:
        return None
    return (net_profit / sales) * 100


def operating_profit_margin(operating_profit, sales):
    if not sales:
        return None
    return (operating_profit / sales) * 100


def return_on_equity(net_profit, equity_capital, reserves):
    denom = (equity_capital or 0) + (reserves or 0)
    if denom <= 0:
        return None
    return (net_profit / denom) * 100


def return_on_capital_employed(ebit, equity_capital, reserves, borrowings):
    denom = (equity_capital or 0) + (reserves or 0) + (borrowings or 0)
    if denom <= 0:
        return None
    return (ebit / denom) * 100


def return_on_assets(net_profit, total_assets):
    if not total_assets:
        return None
    return (net_profit / total_assets) * 100


# ---------------- Leverage & efficiency ratios ----------------

def debt_to_equity(borrowings, equity_capital, reserves):
    """0 (not None) if borrowings = 0 -- debt-free is a valid, real answer."""
    denom = (equity_capital or 0) + (reserves or 0)
    if not borrowings:
        return 0.0
    if denom <= 0:
        return None
    return borrowings / denom


def high_leverage_flag(de_ratio, broad_sector):
    """True if D/E > 5 -- but skip this flag for Financials sector,
    since banks are naturally high-leverage, that's normal for them."""
    if de_ratio is None or broad_sector == "Financials":
        return False
    return de_ratio > 5


def interest_coverage_ratio(operating_profit, other_income, interest):
    """Returns (value, label). If interest = 0, value is None and label is 'Debt Free'."""
    if not interest:
        return None, "Debt Free"
    icr = (operating_profit + (other_income or 0)) / interest
    return icr, None


def icr_risk_flag(icr):
    """True if ICR < 1.5 -- company may struggle to cover interest payments."""
    if icr is None:
        return False
    return icr < 1.5


def asset_turnover(sales, total_assets):
    if not total_assets:
        return None
    return sales / total_assets


if __name__ == "__main__":
    print("Net Profit Margin:", net_profit_margin(100, 1000))
    print("Return on Equity:", return_on_equity(100, 500, 500))
    print("Debt to Equity (debt-free):", debt_to_equity(0, 500, 500))
    print("High Leverage Flag (Materials, D/E=6):", high_leverage_flag(6.0, "Materials"))
    print("High Leverage Flag (Financials, D/E=6):", high_leverage_flag(6.0, "Financials"))
    print("ICR (interest=0):", interest_coverage_ratio(200, 10, 0))
    print("ICR Risk Flag (icr=1.2):", icr_risk_flag(1.2))