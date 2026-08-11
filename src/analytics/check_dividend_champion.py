from src.screener.engine import load_all_metrics

df = load_all_metrics()
print(f"Total companies: {len(df)}")

step1 = df[df["dividend_yield_pct"] > 2]
print(f"After dividend_yield_pct > 2: {len(step1)}")

step2 = step1[step1["free_cash_flow_cr"] > 0]
print(f"After free_cash_flow_cr > 0: {len(step2)}")

step3 = step2[step2["dividend_payout_ratio_pct"] < 80]
print(f"After dividend_payout_ratio_pct < 80: {len(step3)}")

print()
print("Let's look at dividend_payout_ratio_pct values for companies passing steps 1-2:")
print(step2[["company_id", "dividend_yield_pct", "dividend_payout_ratio_pct"]].sort_values("dividend_payout_ratio_pct"))