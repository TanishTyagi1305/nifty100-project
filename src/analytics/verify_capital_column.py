import pandas as pd
df = pd.read_excel("output/cashflow_intelligence.xlsx")
print("capital_allocation_label" in df.columns)
print(df[["company_id", "capital_allocation_label"]].head(10))