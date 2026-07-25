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


if __name__ == "__main__":
    print(free_cash_flow(100, -300))                    # expect -200
    print(capital_allocation_pattern(100, -50, -30))     # expect ('+','-','-','Reinvestor')
    print(capital_allocation_pattern(-50, 30, 40))       # expect ('-','+','+','Distress Signal')
    print(capital_allocation_pattern(200, 50, 30))       # expect ('+','+','+','Cash Accumulator')