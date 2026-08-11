import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")
df = pd.read_sql("""
    SELECT company_id, value, percentile_rank FROM peer_percentiles
    WHERE peer_group_name = 'FMCG' AND metric = 'return_on_equity_pct'
    ORDER BY value DESC
""", conn)
conn.close()
print(df)