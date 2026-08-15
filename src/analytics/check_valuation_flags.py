from src.analytics.valuation import build_valuation_summary

df = build_valuation_summary()

print("Companies per sector:")
print(df.groupby("broad_sector").size().sort_values())
print()

print("Flag counts per sector:")
print(df.groupby(["broad_sector", "flag"]).size().unstack(fill_value=0))
print()

print("Discount companies -- how far below median are they, on average?")
discount = df[df["flag"] == "Discount"]
print(discount["pe_vs_sector_median_pct"].describe())
print()

print("Caution companies -- how far above median, on average?")
caution = df[df["flag"] == "Caution"]
print(caution["pe_vs_sector_median_pct"].describe())