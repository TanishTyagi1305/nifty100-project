"""
portfolio_summary.py
---------------------
Day 35: one page per company, alphabetical by ticker, with top 6 KPIs
and trend arrows (up/down/flat vs prior year).
"""
import os
import sqlite3
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas


def trend_arrow(current, previous):
    if current is None or previous is None or previous == 0:
        return "-"
    pct_change = ((current - previous) / abs(previous)) * 100
    if abs(pct_change) <= 2:
        return "right"
    return "up" if pct_change > 0 else "down"


def arrow_symbol(direction):
    return {"up": "^ UP", "down": "v DN", "right": "= FL", "-": "  --"}.get(direction, "--")


def load_portfolio_data():
    conn = sqlite3.connect("db/nifty100.db")
    ratios = pd.read_sql("SELECT * FROM financial_ratios ORDER BY company_id, year", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)
    companies = pd.read_sql("SELECT id, company_name FROM companies ORDER BY id", conn)
    conn.close()
    return ratios, sectors, companies


def generate_portfolio_summary():
    os.makedirs("reports/portfolio", exist_ok=True)
    ratios, sectors, companies = load_portfolio_data()

    c = canvas.Canvas("reports/portfolio/portfolio_summary.pdf", pagesize=A4)
    width, height = A4

    for _, company_row in companies.iterrows():
        ticker = company_row["id"]
        company_name = company_row["company_name"]

        company_ratios = ratios[ratios["company_id"] == ticker].sort_values("year")
        sector_row = sectors[sectors["company_id"] == ticker]
        sector = sector_row.iloc[0]["broad_sector"] if len(sector_row) else "Unknown"

        if len(company_ratios) == 0:
            continue

        latest = company_ratios.iloc[-1]
        prior = company_ratios.iloc[-2] if len(company_ratios) >= 2 else None

        # navy header
        c.setFillColor(HexColor("#1a2b4c"))
        c.rect(0, height - 2.5 * cm, width, 2.5 * cm, fill=True, stroke=False)
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont("Helvetica-Bold", 14)
        c.drawString(1.5 * cm, height - 1.5 * cm, f"{company_name} ({ticker})")
        c.setFont("Helvetica", 10)
        c.drawString(1.5 * cm, height - 2.1 * cm, sector)

        # 6 KPI tiles with trend arrows
        KPIS = [
            ("ROE (%)", "return_on_equity_pct"),
            ("Net Profit Margin (%)", "net_profit_margin_pct"),
            ("D/E", "debt_to_equity"),
            ("Revenue CAGR 5yr (%)", "revenue_cagr_5yr"),
            ("FCF (Cr)", "free_cash_flow_cr"),
            ("Interest Coverage", "interest_coverage"),
        ]

        tile_w, tile_h = 5.5 * cm, 2.8 * cm
        gap = 0.5 * cm
        start_y = height - 4 * cm

        for i, (label, col) in enumerate(KPIS):
            row_i, col_i = divmod(i, 3)
            x = 1.5 * cm + col_i * (tile_w + gap)
            y = start_y - row_i * (tile_h + gap)

            current_val = latest.get(col)
            prior_val = prior.get(col) if prior is not None else None
            direction = trend_arrow(current_val, prior_val)
            arrow = arrow_symbol(direction)

            val_str = f"{current_val:.1f}" if pd.notna(current_val) else "N/A"

            c.setFillColor(HexColor("#f0f2f5"))
            c.rect(x, y - tile_h, tile_w, tile_h, fill=True, stroke=False)

            c.setFillColor(HexColor("#1a2b4c"))
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(x + tile_w / 2, y - tile_h / 2 + 0.5 * cm, val_str)

            arrow_color = HexColor("#0a7a2e") if direction == "up" else (HexColor("#a30000") if direction == "down" else HexColor("#555555"))
            c.setFillColor(arrow_color)
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(x + tile_w / 2, y - tile_h / 2, arrow)

            c.setFillColor(HexColor("#555555"))
            c.setFont("Helvetica", 8)
            c.drawCentredString(x + tile_w / 2, y - tile_h / 2 - 0.5 * cm, label)

        c.showPage()

    c.save()
    print("reports/portfolio/portfolio_summary.pdf written")


if __name__ == "__main__":
    generate_portfolio_summary()