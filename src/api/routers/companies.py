import sqlite3
import os
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from typing import Optional

router = APIRouter()
DB = "db/nifty100.db"


def get_conn():
    return sqlite3.connect(DB)


@router.get("/companies")
def list_companies(sector: Optional[str] = None, search: Optional[str] = None):
    conn = get_conn()
    query = """
        SELECT c.id, c.company_name, s.broad_sector, s.sub_sector,
               c.roce_percentage, c.roe_percentage
        FROM companies c
        LEFT JOIN sectors s ON c.id = s.company_id
        WHERE 1=1
    """
    params = []
    if sector:
        query += " AND s.broad_sector = ?"
        params.append(sector)
    if search:
        query += " AND (c.id LIKE ? OR c.company_name LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(id=r[0], company_name=r[1], broad_sector=r[2],
                 sub_sector=r[3], roce_pct=r[4], roe_pct=r[5]) for r in rows]


@router.get("/companies/{ticker}")
def get_company(ticker: str):
    conn = get_conn()
    company = conn.execute("SELECT * FROM companies WHERE id = ?", (ticker,)).fetchone()
    if not company:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")
    cols = [d[0] for d in conn.execute("PRAGMA table_info(companies)").fetchall()]
    result = dict(zip(cols, company))

    ratios = conn.execute("""
        SELECT * FROM financial_ratios WHERE company_id = ?
        ORDER BY year DESC LIMIT 1
    """, (ticker,)).fetchone()
    if ratios:
        ratio_cols = [d[0] for d in conn.execute("PRAGMA table_info(financial_ratios)").fetchall()]
        result["latest_ratios"] = dict(zip(ratio_cols, ratios))

    conn.close()
    return result


@router.get("/companies/{ticker}/pl")
def get_pl(ticker: str, from_year: Optional[int] = None, to_year: Optional[int] = None):
    conn = get_conn()
    query = "SELECT * FROM profitandloss WHERE company_id = ?"
    params = [ticker]
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
    query += " ORDER BY year"
    rows = conn.execute(query, params).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No P&L data for '{ticker}'")
    cols = [d[0] for d in conn.execute("PRAGMA table_info(profitandloss)").fetchall()]
    conn.close()
    return [dict(zip(cols, r)) for r in rows]


@router.get("/companies/{ticker}/bs")
def get_bs(ticker: str, from_year: Optional[int] = None, to_year: Optional[int] = None):
    conn = get_conn()
    query = "SELECT * FROM balancesheet WHERE company_id = ?"
    params = [ticker]
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
    query += " ORDER BY year"
    rows = conn.execute(query, params).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No balance sheet data for '{ticker}'")
    cols = [d[0] for d in conn.execute("PRAGMA table_info(balancesheet)").fetchall()]
    conn.close()
    return [dict(zip(cols, r)) for r in rows]


@router.get("/companies/{ticker}/cashflow")
def get_cashflow(ticker: str, from_year: Optional[int] = None, to_year: Optional[int] = None):
    conn = get_conn()
    query = "SELECT * FROM cashflow WHERE company_id = ?"
    params = [ticker]
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
    query += " ORDER BY year"
    rows = conn.execute(query, params).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No cash flow data for '{ticker}'")
    cols = [d[0] for d in conn.execute("PRAGMA table_info(cashflow)").fetchall()]
    conn.close()
    return [dict(zip(cols, r)) for r in rows]


@router.get("/companies/{ticker}/ratios")
def get_ratios(ticker: str, year: Optional[int] = None):
    conn = get_conn()
    query = "SELECT * FROM financial_ratios WHERE company_id = ?"
    params = [ticker]
    if year:
        query += " AND year = ?"
        params.append(year)
    query += " ORDER BY year"
    rows = conn.execute(query, params).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No ratio data for '{ticker}'")
    cols = [d[0] for d in conn.execute("PRAGMA table_info(financial_ratios)").fetchall()]
    conn.close()
    return [dict(zip(cols, r)) for r in rows]


@router.get("/companies/{ticker}/tearsheet")
def get_tearsheet(ticker: str):
    path = f"reports/tearsheets/{ticker}_tearsheet.pdf"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Tearsheet for '{ticker}' not found")
    return FileResponse(path, media_type="application/pdf",
                        filename=f"{ticker}_tearsheet.pdf")