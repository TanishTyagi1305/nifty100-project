"""
tearsheet.py
------------
2-page company tearsheet PDF using ReportLab.
Page 1: navy header, 6 KPI tiles, Revenue/Profit chart, ROE trend chart.
Page 2: Balance Sheet composition, Cash Flow waterfall, Pros/Cons (word-
wrapped), Capital Allocation badge.
"""
import os
import sqlite3
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas


def load_company_data(ticker):
    conn = sqlite3.connect("db/nifty100.db")
    company = pd.read_sql("SELECT * FROM companies WHERE id = ?", conn, params=[ticker])
    ratios = pd.read_sql("SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year", conn, params=[ticker])
    conn.close()
    return company, ratios


def draw_header(c, ticker, company_name):
    width, height = A4
    c.setFillColor(HexColor("#1a2b4c"))
    c.rect(0, height - 3 * cm, width, 3 * cm, fill=True, stroke=False)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 18)
    c.drawString(1.5 * cm, height - 1.5 * cm, company_name)
    c.setFont("Helvetica", 12)
    c.drawString(1.5 * cm, height - 2.2 * cm, ticker)


def draw_kpi_tiles(c, latest_ratios):
    width, height = A4
    tile_w, tile_h = 5.5 * cm, 2.5 * cm
    start_y = height - 5 * cm
    gap = 0.5 * cm
    tiles = [
        ("ROE", f"{latest_ratios.get('return_on_equity_pct'):.1f}%" if pd.notna(latest_ratios.get('return_on_equity_pct')) else "N/A"),
        ("Net Profit Margin", f"{latest_ratios.get('net_profit_margin_pct'):.1f}%" if pd.notna(latest_ratios.get('net_profit_margin_pct')) else "N/A"),
        ("D/E", f"{latest_ratios.get('debt_to_equity'):.2f}" if pd.notna(latest_ratios.get('debt_to_equity')) else "N/A"),
        ("Revenue CAGR 5yr", f"{latest_ratios.get('revenue_cagr_5yr'):.1f}%" if pd.notna(latest_ratios.get('revenue_cagr_5yr')) else "N/A"),
        ("FCF (Cr)", f"{latest_ratios.get('free_cash_flow_cr'):.0f}" if pd.notna(latest_ratios.get('free_cash_flow_cr')) else "N/A"),
        ("ICR", f"{latest_ratios.get('interest_coverage'):.1f}" if pd.notna(latest_ratios.get('interest_coverage')) else str(latest_ratios.get('icr_label') or "N/A")),
    ]
    for i, (label, value) in enumerate(tiles):
        row, col = divmod(i, 3)
        x = 1.5 * cm + col * (tile_w + gap)
        y = start_y - row * (tile_h + gap)
        c.setFillColor(HexColor("#f0f2f5"))
        c.rect(x, y - tile_h, tile_w, tile_h, fill=True, stroke=False)
        c.setFillColor(HexColor("#1a2b4c"))
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(x + tile_w / 2, y - tile_h / 2 + 0.3 * cm, value)
        c.setFont("Helvetica", 9)
        c.drawCentredString(x + tile_w / 2, y - tile_h / 2 - 0.4 * cm, label)


def make_revenue_profit_chart(ticker, pnl, save_path):
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.bar(pnl["year"] - 0.2, pnl["sales"], width=0.4, label="Sales")
    ax.bar(pnl["year"] + 0.2, pnl["net_profit"], width=0.4, label="Net Profit")
    ax.legend(fontsize=8)
    ax.set_title("Revenue & Net Profit (Cr)", fontsize=10)
    ax.tick_params(labelsize=7)
    plt.tight_layout()
    plt.savefig(save_path, dpi=120)
    plt.close(fig)


def make_roe_chart(ticker, ratios, save_path):
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.plot(ratios["year"], ratios["return_on_equity_pct"], marker="o", label="ROE %")
    ax.legend(fontsize=8)
    ax.set_title("ROE Trend", fontsize=10)
    ax.tick_params(labelsize=7)
    plt.tight_layout()
    plt.savefig(save_path, dpi=120)
    plt.close(fig)


def make_balance_sheet_chart(ticker, bs, save_path):
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.bar(bs["year"], bs["equity_capital"] + bs["reserves"], label="Equity")
    ax.bar(bs["year"], bs["borrowings"], bottom=bs["equity_capital"] + bs["reserves"], label="Borrowings")
    ax.bar(bs["year"], bs["other_liabilities"],
           bottom=bs["equity_capital"] + bs["reserves"] + bs["borrowings"], label="Other Liabilities")
    ax.legend(fontsize=7)
    ax.set_title("Balance Sheet Composition", fontsize=10)
    ax.tick_params(labelsize=7)
    plt.tight_layout()
    plt.savefig(save_path, dpi=120)
    plt.close(fig)


def make_cashflow_waterfall(ticker, latest_cf, save_path):
    labels = ["CFO", "CFI", "CFF", "Net Cash Flow"]
    values = [latest_cf.get("operating_activity") or 0, latest_cf.get("investing_activity") or 0,
              latest_cf.get("financing_activity") or 0, latest_cf.get("net_cash_flow") or 0]
    colors = ["green" if v >= 0 else "red" for v in values]
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.bar(labels, values, color=colors)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("Cash Flow Waterfall (Latest Year, Cr)", fontsize=10)
    ax.tick_params(labelsize=7)
    plt.tight_layout()
    plt.savefig(save_path, dpi=120)
    plt.close(fig)


def _wrap_text(text, max_chars):
    words = text.split()
    lines, current = [], ""
    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current = f"{current} {word}".strip()
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def generate_tearsheet(ticker, output_path):
    conn = sqlite3.connect("db/nifty100.db")
    company = pd.read_sql("SELECT * FROM companies WHERE id = ?", conn, params=[ticker])
    ratios = pd.read_sql("SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year", conn, params=[ticker])
    pnl = pd.read_sql("SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year", conn, params=[ticker])
    bs = pd.read_sql("SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year", conn, params=[ticker])
    cf = pd.read_sql("SELECT * FROM cashflow WHERE company_id = ? ORDER BY year", conn, params=[ticker])
    conn.close()

    if len(company) == 0 or len(ratios) == 0:
        return False

    company_name = company.iloc[0]["company_name"]
    latest_ratios = ratios.iloc[-1]

    os.makedirs("reports/tearsheets/_charts", exist_ok=True)
    chart1_path = f"reports/tearsheets/_charts/{ticker}_revprofit.png"
    chart2_path = f"reports/tearsheets/_charts/{ticker}_roe.png"
    make_revenue_profit_chart(ticker, pnl, chart1_path)
    make_roe_chart(ticker, ratios, chart2_path)

    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    draw_header(c, ticker, company_name)
    draw_kpi_tiles(c, latest_ratios)

    chart_y = height - 12 * cm
    c.drawImage(chart1_path, 1.5 * cm, chart_y, width=9 * cm, height=5.4 * cm, preserveAspectRatio=True)
    c.drawImage(chart2_path, 11 * cm, chart_y, width=9 * cm, height=5.4 * cm, preserveAspectRatio=True)

    c.showPage()

    try:
        all_generated = pd.read_csv("output/pros_cons_generated.csv")
        company_generated = all_generated[all_generated["company_id"] == ticker]
        pros_list = company_generated[company_generated["type"] == "pro"]["text"].tolist()
        cons_list = company_generated[company_generated["type"] == "con"]["text"].tolist()
    except FileNotFoundError:
        pros_list, cons_list = [], []

    try:
        capital_alloc_df = pd.read_csv("output/capital_allocation.csv")
        company_alloc = capital_alloc_df[capital_alloc_df["company_id"] == ticker].sort_values("year")
        capital_label = company_alloc.iloc[-1]["pattern_label"] if len(company_alloc) > 0 else "Unclassified"
    except FileNotFoundError:
        capital_label = "Unclassified"

    c.setFillColor(HexColor("#1a2b4c"))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1.5 * cm, height - 1.5 * cm, f"{ticker} - Page 2")

    if len(bs) > 0:
        bs_chart_path = f"reports/tearsheets/_charts/{ticker}_bs.png"
        make_balance_sheet_chart(ticker, bs, bs_chart_path)
        c.drawImage(bs_chart_path, 1.5 * cm, height - 9 * cm, width=9 * cm, height=5.4 * cm, preserveAspectRatio=True)

    if len(cf) > 0:
        cf_chart_path = f"reports/tearsheets/_charts/{ticker}_cf.png"
        make_cashflow_waterfall(ticker, cf.iloc[-1], cf_chart_path)
        c.drawImage(cf_chart_path, 11 * cm, height - 9 * cm, width=9 * cm, height=5.4 * cm, preserveAspectRatio=True)

    y = height - 10 * cm
    c.setFillColor(HexColor("#0a7a2e"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(1.5 * cm, y, "Pros")
    c.setFont("Helvetica", 8)
    y -= 0.5 * cm
    for pro_text in pros_list[:4]:
        wrapped = _wrap_text(pro_text, 55)
        for j, line in enumerate(wrapped):
            prefix = "- " if j == 0 else "  "
            c.drawString(1.7 * cm, y, prefix + line)
            y -= 0.4 * cm

    y -= 0.3 * cm
    c.setFillColor(HexColor("#a30000"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(1.5 * cm, y, "Cons")
    c.setFont("Helvetica", 8)
    y -= 0.5 * cm
    for con_text in cons_list[:4]:
        wrapped = _wrap_text(con_text, 55)
        for j, line in enumerate(wrapped):
            prefix = "- " if j == 0 else "  "
            c.drawString(1.7 * cm, y, prefix + line)
            y -= 0.4 * cm

    c.setFillColor(HexColor("#e8a33d"))
    c.rect(1.5 * cm, 1.5 * cm, 8 * cm, 1.2 * cm, fill=True, stroke=False)
    c.setFillColor(HexColor("#1a2b4c"))
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(5.5 * cm, 1.9 * cm, f"Capital Allocation: {capital_label}")

    c.showPage()
    c.save()
    return True


if __name__ == "__main__":
    success = generate_tearsheet("TCS", "reports/tearsheets/TCS_v3.pdf")
    print("Generated:" if success else "Failed:", "reports/tearsheets/TCS_v3.pdf")