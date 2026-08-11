import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")
df = pd.read_sql("SELECT * FROM peer_groups", conn)
conn.close()

print(f"Total rows: {len(df)}")
print(f"Distinct peer groups: {df['peer_group_name'].nunique()}")
print()
print(df.groupby("peer_group_name")["company_id"].apply(list))