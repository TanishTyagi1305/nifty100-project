def trend_arrow(current, previous):
    """Returns an arrow character based on % change from previous to current.
    Flat (within 2%) -> right arrow. Up -> up arrow. Down -> down arrow."""
    if current is None or previous is None or previous == 0:
        return "-"
    pct_change = ((current - previous) / abs(previous)) * 100
    if abs(pct_change) <= 2:
        return "→"
    return "↑" if pct_change > 0 else "↓"


# quick predictions before checking real data
print(trend_arrow(110, 100))   # 10% up -> expect ↑
print(trend_arrow(90, 100))    # 10% down -> expect ↓
print(trend_arrow(100.5, 100)) # 0.5% up -> expect → (flat)
print(trend_arrow(None, 100))  # missing data -> expect -