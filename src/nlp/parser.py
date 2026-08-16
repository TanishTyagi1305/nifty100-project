"""
parser.py
---------
Parses text fields in analysis.xlsx like "10 Years: 21%" into
structured (period_years, value_pct) pairs, using regex.

Real data has more formats than the simple spec example:
  "10 Years: 21%"      -> period=10, value=21.0
  "5 Years          14%" (no colon, extra spaces) -> period=5, value=14.0
  "1 Year: -2%"         (singular, negative value) -> period=1, value=-2.0
  "TTM: 43%"            (Trailing Twelve Months, no year number) -> period=0 (special case), value=43.0
  "Last Year: 12%"      (no year number)          -> period=1 (treated as 1yr), value=12.0
"""
import re
import sqlite3
import pandas as pd

# Matches "10 Years: 21%", "5 Years 14%", "1 Year: -2%" -- handles singular/plural,
# optional colon, variable whitespace, and negative values.
YEAR_PATTERN = re.compile(r"(\d+)\s*Years?:?\s*(-?[\d.]+)%")

# Matches "TTM: 43%" or "TTM 43%" -- no year number, treated as period=0 (a marker,
# not a real multi-year figure)
TTM_PATTERN = re.compile(r"TTM:?\s*(-?[\d.]+)%")

# Matches "Last Year: 12%" -- treated as a 1-year figure
LAST_YEAR_PATTERN = re.compile(r"Last Year:?\s*(-?[\d.]+)%")


def parse_metric_text(raw_text):
    """
    Returns (period_years, value_pct) or (None, None) if nothing matched.
    period_years=0 is used as a special marker for TTM (not a real N-year period).
    """
    if raw_text is None:
        return None, None
    s = str(raw_text).strip()

    m = YEAR_PATTERN.search(s)
    if m:
        return int(m.group(1)), float(m.group(2))

    m = TTM_PATTERN.search(s)
    if m:
        return 0, float(m.group(1))  # 0 = TTM marker

    m = LAST_YEAR_PATTERN.search(s)
    if m:
        return 1, float(m.group(1))

    return None, None


def parse_analysis_table():
    conn = sqlite3.connect("db/nifty100.db")
    df = pd.read_sql("SELECT * FROM analysis", conn)
    conn.close()

    METRIC_COLUMNS = {
        "compounded_sales_growth": "sales_growth",
        "compounded_profit_growth": "profit_growth",
        "stock_price_cagr": "stock_price_cagr",
        "roe": "roe",
    }

    results = []
    failures = []

    for _, row in df.iterrows():
        for col, metric_type in METRIC_COLUMNS.items():
            raw = row.get(col)
            period, value = parse_metric_text(raw)
            if period is None:
                if raw is not None and str(raw).strip():
                    failures.append({"company_id": row["company_id"], "column": col, "raw_text": raw})
                continue
            results.append({
                "company_id": row["company_id"], "metric_type": metric_type,
                "period_years": period, "value_pct": value,
            })

    return pd.DataFrame(results), pd.DataFrame(failures)


if __name__ == "__main__":
    parsed, failures = parse_analysis_table()
    parsed.to_csv("output/analysis_parsed.csv", index=False)
    failures.to_csv("output/parse_failures.csv", index=False)

    print(f"Parsed {len(parsed)} rows -> output/analysis_parsed.csv")
    print(f"Failed to parse {len(failures)} rows -> output/parse_failures.csv")
    if len(failures) > 0:
        print("\nSample failures:")
        print(failures.head(10))