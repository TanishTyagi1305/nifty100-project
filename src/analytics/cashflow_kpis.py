"""
cashflow_kpis.py
----------------
Free Cash Flow, and an 8-pattern classifier based on the sign
(+ or -) of Operating / Investing / Financing cash flows.
"""


def free_cash_flow(operating_activity, investing_activity):
    """Negative FCF is a real, valid result -- it just means the company
    is investing heavily right now. We don't hide or block that."""
    return (operating_activity or 0) + (investing_activity or 0)


def _sign(x):
    if x is None:
        return "0"
    if x > 0:
        return "+"
    if x < 0:
        return "-"
    return "0"


def capital_allocation_pattern(cfo, cfi, cff):
    """Classifies a company-year based on the sign of (CFO, CFI, CFF)."""
    cfo_s, cfi_s, cff_s = _sign(cfo), _sign(cfi), _sign(cff)

    patterns = {
        ("+", "-", "-"): "Reinvestor",
        ("+", "+", "-"): "Liquidating Assets",
        ("-", "+", "+"): "Distress Signal",
        ("-", "-", "+"): "Growth Funded by Debt",
        ("+", "+", "+"): "Cash Accumulator",
        ("-", "-", "-"): "Pre-Revenue",
        ("+", "-", "+"): "Mixed",
    }
    label = patterns.get((cfo_s, cfi_s, cff_s), "Unclassified")
    return cfo_s, cfi_s, cff_s, label

def cfo_quality_score(avg_cfo, avg_pat):
    """avg_cfo / avg_pat, typically averaged over 5 years by the caller.
    Returns (ratio, label). Bands: >1.0 High Quality, 0.5-1.0 Moderate,
    <0.5 Accrual Risk."""
    if not avg_pat:
        return None, None
    ratio = avg_cfo / avg_pat
    if ratio > 1.0:
        label = "High Quality"
    elif ratio >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"
    return ratio, label


def capex_intensity(investing_activity, sales):
    """abs(investing_activity)/sales x 100. Labels: <3% Asset Light,
    3-8% Moderate, >8% Capital Intensive."""
    if not sales:
        return None, None
    pct = abs(investing_activity or 0) / sales * 100
    if pct < 3:
        label = "Asset Light"
    elif pct <= 8:
        label = "Moderate"
    else:
        label = "Capital Intensive"
    return pct, label


def fcf_conversion_pct(fcf, operating_profit):
    if not operating_profit:
        return None
    return (fcf / operating_profit) * 100


def is_distress_signal(cfo, cff):
    """CFO < 0 AND CFF > 0 -- raising cash from financing while operations burn cash."""
    if cfo is None or cff is None:
        return False
    return cfo < 0 and cff > 0


def is_deleveraging(cff, borrowings_this_year, borrowings_last_year):
    """CFF < 0 AND borrowings declining year-over-year -- actively paying down debt."""
    if cff is None or borrowings_this_year is None or borrowings_last_year is None:
        return False
    return cff < 0 and borrowings_this_year < borrowings_last_year

if __name__ == "__main__":
    print(free_cash_flow(100, -300))                    # expect -200
    print(capital_allocation_pattern(100, -50, -30))     # expect ('+','-','-','Reinvestor')
    print(capital_allocation_pattern(-50, 30, 40))       # expect ('-','+','+','Distress Signal')
    print(capital_allocation_pattern(200, 50, 30))       # expect ('+','+','+','Cash Accumulator')