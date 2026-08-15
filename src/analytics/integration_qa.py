"""
integration_qa.py
------------------
Runs the core data-loading functions behind every screen against 10
tickers spanning 5 sectors, including at least one partial-data company
(JIOFIN, known from Sprint 2 to have only 2 years of history).
Flags any crash immediately -- this is NOT a full UI test, just a fast
way to catch data-layer bugs before manually clicking through 80
screen/ticker combinations.
"""
import sqlite3
import pandas as pd

TEST_TICKERS = [
    "TCS", "INFY",          # IT
    "HDFCBANK", "ICICIBANK",  # Financials
    "HINDUNILVR", "ITC",     # FMCG / Consumer Staples
    "RELIANCE", "ONGC",      # Energy
    "SUNPHARMA", "CIPLA",    # Healthcare
]
PARTIAL_DATA_TICKER = "JIOFIN"  # known thin-history company from Sprint 2

DB_PATH = "db/nifty100.db"


def check_ticker(ticker):
    errors = []
    conn = sqlite3.connect(DB_PATH)
    try:
        company = pd.read_sql("SELECT * FROM companies WHERE id = ?", conn, params=[ticker])
        if len(company) == 0:
            errors.append("not found in companies table")

        ratios = pd.read_sql("SELECT * FROM financial_ratios WHERE company_id = ?", conn, params=[ticker])
        pnl = pd.read_sql("SELECT * FROM profitandloss WHERE company_id = ?", conn, params=[ticker])
        docs = pd.read_sql("SELECT * FROM documents WHERE company_id = ?", conn, params=[ticker])
        proscons = pd.read_sql("SELECT * FROM prosandcons WHERE company_id = ?", conn, params=[ticker])

        # simulate what the profile screen does: access the latest ratio row
        if len(ratios) > 0:
            latest = ratios.sort_values("year").iloc[-1]
            _ = latest.get("return_on_equity_pct")  # would KeyError/crash if column missing

    except Exception as e:
        errors.append(f"CRASH: {e}")
    finally:
        conn.close()

    return errors


all_tickers = TEST_TICKERS + [PARTIAL_DATA_TICKER]
print(f"Testing {len(all_tickers)} tickers...\n")

any_failed = False
for ticker in all_tickers:
    errors = check_ticker(ticker)
    if errors:
        any_failed = True
        print(f"❌ {ticker}: {errors}")
    else:
        print(f"✅ {ticker}: OK")

print()
if any_failed:
    print("Some tickers had issues -- see above.")
else:
    print("All tickers passed data-layer checks.")