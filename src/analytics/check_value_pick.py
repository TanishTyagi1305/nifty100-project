from src.screener.engine import load_all_metrics

df = load_all_metrics()
print(f"Total companies: {len(df)}")

step1 = df[df["pe_ratio"] < 20]
print(f"After pe_ratio < 20: {len(step1)}")

step2 = step1[step1["pb_ratio"] < 3.0]
print(f"After pb_ratio < 3.0: {len(step2)}")

step3 = step2[step2["debt_to_equity"] < 2.0]
print(f"After debt_to_equity < 2.0: {len(step3)}")

step4 = step3[step3["dividend_yield_pct"] > 1]
print(f"After dividend_yield_pct > 1: {len(step4)}")