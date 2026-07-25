"""
cagr.py
-------
CAGR = ((end/start)^(1/n) - 1) x 100
Only meaningful when start and end are both positive, so we handle
every other situation with a labeled reason instead of a fake number.
"""

FLAG_DECLINE_TO_LOSS = "DECLINE_TO_LOSS"   # was profitable, now isn't
FLAG_TURNAROUND = "TURNAROUND"              # was a loss, now profitable
FLAG_BOTH_NEGATIVE = "BOTH_NEGATIVE"        # loss at both ends
FLAG_ZERO_BASE = "ZERO_BASE"                # started at exactly 0
FLAG_INSUFFICIENT = "INSUFFICIENT"          # not enough years of data


def cagr(start_value, end_value, n_years):
    """Returns (value, flag). flag is None when the value is real."""
    if n_years is None or n_years <= 0:
        return None, FLAG_INSUFFICIENT

    if start_value == 0:
        return None, FLAG_ZERO_BASE

    if start_value > 0 and end_value > 0:
        value = ((end_value / start_value) ** (1 / n_years) - 1) * 100
        return value, None

    if start_value > 0 and end_value <= 0:
        return None, FLAG_DECLINE_TO_LOSS

    if start_value < 0 and end_value > 0:
        return None, FLAG_TURNAROUND

    return None, FLAG_BOTH_NEGATIVE


if __name__ == "__main__":
    print(cagr(100, 200, 5))     # expect (~14.87, None) -- normal growth
    print(cagr(100, -50, 3))     # expect (None, 'DECLINE_TO_LOSS')
    print(cagr(-100, 50, 3))     # expect (None, 'TURNAROUND')
    print(cagr(-100, -50, 3))    # expect (None, 'BOTH_NEGATIVE')
    print(cagr(0, 100, 3))       # expect (None, 'ZERO_BASE')