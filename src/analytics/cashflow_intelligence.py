"""
cashflow_intelligence.py
--------------------------
Day 31: runs CFO quality, CapEx intensity, distress/deleveraging flags,
and capital allocation pattern for all 92 companies, using their
latest year of data. Companies with no cashflow data at all (e.g. ATGL)
are still included with an honest "No cashflow data" label rather than
silently dropped or given fabricated numbers.
"""
import sqlite3
import pandas as pd

from src.analytics.cashflow_kpis import (
    cfo_quality_score, capex_intensity, fcf_conversion_pct,
    is_distress_signal, is_deleveraging, capital_allocation_pattern
)


def build_cashflow_intelligence():
    conn = sqlite3.connect("db/nifty100.db")
    cf = pd.read_sql("SELECT * FROM cashflow ORDER BY company_id, year", conn)
    pnl = pd.read_sql("SELECT * FROM profitandloss ORDER BY company_id, year", conn)
    bs = pd.read_sql("SELECT * FROM balancesheet ORDER BY company_id, year", conn)
    ratios = pd.read_sql("""
        SELECT company_id, revenue_cagr_5yr, free_cash_flow_cr FROM financial_ratios
        WHERE year = (SELECT MAX(year) FROM financial_ratios)
    """, conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    companies = pd.read_sql("SELECT id FROM companies", conn)["id"].tolist()
    conn.close()

    results = []
    for company_id in companies:
        cf_hist = cf[cf["company_id"] == company_id]
        pnl_hist = pnl[pnl["company_id"] == company_id]
        bs_hist = bs[bs["company_id"] == company_id]

        sector_row = sectors[sectors["company_id"] == company_id]
        sector = sector_row.iloc[0]["broad_sector"] if len(sector_row) else None

        if len(cf_hist) == 0 or len(pnl_hist) == 0:
            results.append(dict(
                company_id=company_id, sector=sector,
                cfo_quality_score=None, cfo_quality_label="No cashflow data",
                capex_intensity_pct=None, capex_label="No cashflow data",
                fcf_cagr_5yr=None, fcf_conversion_pct=None,
                distress_flag=False, deleveraging_flag=False,
                capital_allocation_label="No cashflow data",
            ))
            continue

        # 5yr average CFO/PAT for quality score
        cf_last5 = cf_hist.tail(5)
        pnl_last5 = pnl_hist.tail(5)
        merged5 = cf_last5.merge(pnl_last5[["year", "net_profit"]], on="year", how="inner")
        cfo_ratio, cfo_label = (None, None)
        if len(merged5) > 0:
            avg_cfo = merged5["operating_activity"].mean()
            avg_pat = merged5["net_profit"].mean()
            cfo_ratio, cfo_label = cfo_quality_score(avg_cfo, avg_pat)

        latest_cf = cf_hist.iloc[-1]
        latest_pnl = pnl_hist.iloc[-1]

        capex_pct, capex_label = capex_intensity(latest_cf["investing_activity"], latest_pnl["sales"])
        fcf = (latest_cf["operating_activity"] or 0) + (latest_cf["investing_activity"] or 0)
        fcf_conv = fcf_conversion_pct(fcf, latest_pnl["operating_profit"])

        distress = is_distress_signal(latest_cf["operating_activity"], latest_cf["financing_activity"])

        deleveraging = False
        if len(bs_hist) >= 2:
            latest_bs = bs_hist.iloc[-1]
            prev_bs = bs_hist.iloc[-2]
            deleveraging = is_deleveraging(latest_cf["financing_activity"],
                                            latest_bs["borrowings"], prev_bs["borrowings"])

        cfo_s, cfi_s, cff_s, pattern_label = capital_allocation_pattern(
            latest_cf["operating_activity"], latest_cf["investing_activity"], latest_cf["financing_activity"])

        # fcf_cagr_5yr is not computed anywhere else in the project yet
        # (Sprint 2's CAGR engine covers Revenue/PAT/EPS, not FCF specifically)
        # -- left as None rather than fabricated, documented here honestly.
        fcf_cagr_5yr = None

        results.append(dict(
            company_id=company_id, sector=sector,
            cfo_quality_score=cfo_ratio, cfo_quality_label=cfo_label,
            capex_intensity_pct=capex_pct, capex_label=capex_label,
            fcf_cagr_5yr=fcf_cagr_5yr, fcf_conversion_pct=fcf_conv,
            distress_flag=distress, deleveraging_flag=deleveraging,
            capital_allocation_label=pattern_label,
        ))

    return pd.DataFrame(results)


if __name__ == "__main__":
    df = build_cashflow_intelligence()
    df.to_excel("output/cashflow_intelligence.xlsx", index=False)
    print(f"output/cashflow_intelligence.xlsx written: {len(df)} rows")
    print()
    print("CFO quality label distribution:")
    print(df["cfo_quality_label"].value_counts())
    print()
    print("Distress flags:", df["distress_flag"].sum())
    print("Deleveraging flags:", df["deleveraging_flag"].sum())

    distress_companies = df[df["distress_flag"] == True]
    distress_companies.to_csv("output/distress_alerts.csv", index=False)
    print(f"\noutput/distress_alerts.csv written: {len(distress_companies)} rows")