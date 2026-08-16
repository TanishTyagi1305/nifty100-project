import pandas as pd
df = pd.read_csv("output/analysis_parsed.csv")
print(f"Total rows: {len(df)}")
print(df.head(15))
print()
print("period_years distribution:")
print(df["period_years"].value_counts())