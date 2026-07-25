import sqlite3

conn = sqlite3.connect("db/nifty100.db")

new_columns = [
    "revenue_cagr_5yr REAL", "revenue_cagr_5yr_flag TEXT",
    "pat_cagr_5yr REAL", "pat_cagr_5yr_flag TEXT",
    "eps_cagr_5yr REAL", "eps_cagr_5yr_flag TEXT",
    "composite_quality_score REAL",
    "high_leverage_flag INTEGER",
    "icr_label TEXT", "icr_risk_flag INTEGER",
]

for col in new_columns:
    try:
        conn.execute(f"ALTER TABLE financial_ratios ADD COLUMN {col}")
        print(f"Added: {col}")
    except sqlite3.OperationalError as e:
        print(f"Skipped {col}: {e}")  # already exists, safe to ignore

conn.commit()
conn.close()