from src.screener.engine import load_all_metrics

df = load_all_metrics()
print(f"Total companies: {len(df)}")

step1 = df[df["debt_to_equity"] == 0]
print(f"After debt_to_equity == 0: {len(step1)}")

step2 = step1[step1["return_on_equity_pct"] > 12]
print(f"After return_on_equity_pct > 12: {len(step2)}")

step3 = step2[step2["sales"] > 5000]
print(f"After sales > 5000: {len(step3)}")

print()
print("Companies with debt_to_equity == 0 (before other filters):")
print(step1[["company_id", "debt_to_equity", "return_on_equity_pct", "sales"]])