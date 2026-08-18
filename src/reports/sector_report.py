"""
sector_report.py
------------------
Day 34: one PDF per broad_sector (11 total). Each PDF: a summary page
with sector median KPIs, plus a list of all companies in that sector
with 8 metrics each.
"""
import os
import sqlite3
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas


def load_sector_data():
    conn = sqlite3.connect("db/nifty100.db")
    ratios = pd.read_sql("""
        SELECT * FROM financial_ratios WHERE year = (SELECT MAX(year) FROM financial_ratios)
    """, conn)
    sectors = pd.read_sql("SELECT * FROM sectors", conn)
    companies = pd.read_sql("SELECT id, company_name FROM companies", conn)
    conn.close()

    df = ratios.merge(sectors, on="company_id", how="inner")
    df = df.merge(companies, left_on="company_id", right_on="id", how="left")
    return df


def generate_sector_pdf(sector_name, sector_df, output_path):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    c.setFillColor(HexColor("#1a2b4c"))
    c.rect(0, height - 2.5 * cm, width, 2.5 * cm, fill=True, stroke=False)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1.5 * cm, height - 1.6 * cm, f"{sector_name} — Sector Report")

    medians = sector_df[["return_on_equity_pct", "debt_to_equity", "net_profit_margin_pct",
                          "revenue_cagr_5yr"]].median()
    c.setFillColor(HexColor("#000000"))
    c.setFont("Helvetica-Bold", 11)
    y = height - 3.5 * cm
    c.drawString(1.5 * cm, y, "Sector Median KPIs")
    c.setFont("Helvetica", 9)
    y -= 0.6 * cm
    for label, value in [("Median ROE", f"{medians['return_on_equity_pct']:.1f}%"),
                          ("Median D/E", f"{medians['debt_to_equity']:.2f}"),
                          ("Median NPM", f"{medians['net_profit_margin_pct']:.1f}%"),
                          ("Median Revenue CAGR 5yr", f"{medians['revenue_cagr_5yr']:.1f}%")]:
        c.drawString(1.7 * cm, y, f"{label}: {value}")
        y -= 0.45 * cm

    y -= 0.5 * cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(1.5 * cm, y, f"Companies in {sector_name} ({len(sector_df)})")
    y -= 0.5 * cm

    c.setFont("Helvetica-Bold", 7)
    headers = ["Ticker", "ROE%", "D/E", "NPM%", "RevCAGR%", "PATCAGR%", "ICR", "FCF(Cr)"]
    x_positions = [1.5, 4, 6, 8, 10.5, 13, 15.5, 17.5]
    for h, x in zip(headers, x_positions):
        c.drawString(x * cm, y, h)
    y -= 0.4 * cm

    c.setFont("Helvetica", 7)
    for _, row in sector_df.sort_values("company_id").iterrows():
        if y < 2 * cm:
            c.showPage()
            y = height - 2 * cm
            c.setFont("Helvetica", 7)

        values = [
            row["company_id"],
            f"{row['return_on_equity_pct']:.1f}" if pd.notna(row['return_on_equity_pct']) else "N/A",
            f"{row['debt_to_equity']:.2f}" if pd.notna(row['debt_to_equity']) else "N/A",
            f"{row['net_profit_margin_pct']:.1f}" if pd.notna(row['net_profit_margin_pct']) else "N/A",
            f"{row['revenue_cagr_5yr']:.1f}" if pd.notna(row['revenue_cagr_5yr']) else "N/A",
            f"{row['pat_cagr_5yr']:.1f}" if pd.notna(row['pat_cagr_5yr']) else "N/A",
            f"{row['interest_coverage']:.1f}" if pd.notna(row['interest_coverage']) else "N/A",
            f"{row['free_cash_flow_cr']:.0f}" if pd.notna(row['free_cash_flow_cr']) else "N/A",
        ]
        for v, x in zip(values, x_positions):
            c.drawString(x * cm, y, str(v))
        y -= 0.4 * cm

    c.save()


if __name__ == "__main__":
    os.makedirs("reports/sector", exist_ok=True)
    df = load_sector_data()

    sectors = sorted(df["broad_sector"].dropna().unique())
    print(f"Generating {len(sectors)} sector PDFs...")

    for sector_name in sectors:
        sector_df = df[df["broad_sector"] == sector_name]
        safe_name = sector_name.replace(" ", "_").replace("&", "and")
        output_path = f"reports/sector/{safe_name}_report.pdf"
        generate_sector_pdf(sector_name, sector_df, output_path)
        print(f"  {sector_name}: {len(sector_df)} companies -> {output_path}")

    print("\nDone.")