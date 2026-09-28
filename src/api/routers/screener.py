import sqlite3
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from src.screener.engine import load_all_metrics, apply_filters

router = APIRouter()
DB = "db/nifty100.db"


@router.get("/screener")
def screener(
    min_roe: Optional[float] = None,
    max_de: Optional[float] = None,
    min_fcf: Optional[float] = None,
    sector: Optional[str] = None,
    min_rev_cagr_5yr: Optional[float] = None,
    min_pat_cagr_5yr: Optional[float] = None,
    max_pe: Optional[float] = None,
):
    try:
        df = load_all_metrics()
        config = {}
        if min_roe is not None:
            config["roe_min"] = min_roe
        if max_de is not None:
            config["de_max"] = max_de
        if min_fcf is not None:
            config["fcf_min"] = min_fcf
        if min_rev_cagr_5yr is not None:
            config["revenue_cagr_5yr_min"] = min_rev_cagr_5yr
        if min_pat_cagr_5yr is not None:
            config["pat_cagr_5yr_min"] = min_pat_cagr_5yr
        if max_pe is not None:
            config["pe_max"] = max_pe

        result = apply_filters(df, config)

        if sector:
            result = result[result["broad_sector"] == sector]

        cols = ["company_id", "broad_sector", "return_on_equity_pct", "debt_to_equity",
                "free_cash_flow_cr", "revenue_cagr_5yr", "pat_cagr_5yr", "composite_quality_score"]
        available = [c for c in cols if c in result.columns]
        return result[available].fillna("N/A").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sectors")
def list_sectors():
    conn = sqlite3.connect(DB)
    df = pd.read_sql("""
        SELECT s.broad_sector, COUNT(DISTINCT s.company_id) as company_count,
               AVG(f.return_on_equity_pct) as median_roe,
               AVG(f.debt_to_equity) as median_de
        FROM sectors s
        LEFT JOIN financial_ratios f ON s.company_id = f.company_id
            AND f.year = (SELECT MAX(year) FROM financial_ratios)
        GROUP BY s.broad_sector
    """, conn)
    conn.close()
    return df.fillna("N/A").to_dict(orient="records")


@router.get("/sectors/{sector}/companies")
def sector_companies(sector: str):
    conn = sqlite3.connect(DB)
    rows = conn.execute("""
        SELECT s.company_id, c.company_name, s.broad_sector, s.sub_sector
        FROM sectors s
        JOIN companies c ON s.company_id = c.id
        WHERE s.broad_sector = ?
    """, (sector,)).fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail=f"Sector '{sector}' not found")
    return [dict(company_id=r[0], company_name=r[1], broad_sector=r[2], sub_sector=r[3]) for r in rows]


@router.get("/peers/{group_name}")
def peer_group(group_name: str):
    conn = sqlite3.connect(DB)
    rows = conn.execute("""
        SELECT pp.company_id, pp.metric, pp.value, pp.percentile_rank
        FROM peer_percentiles pp
        WHERE pp.peer_group_name = ?
    """, (group_name,)).fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail=f"Peer group '{group_name}' not found")
    return [dict(company_id=r[0], metric=r[1], value=r[2], percentile_rank=r[3]) for r in rows]


@router.get("/portfolio/stats")
def portfolio_stats():
    df = pd.read_csv("output/portfolio_stats.csv", index_col=0)
    return df.fillna("N/A").to_dict()


@router.get("/market-cap/{ticker}")
def market_cap(ticker: str):
    conn = sqlite3.connect(DB)
    rows = conn.execute("""
        SELECT * FROM market_cap WHERE company_id = ? ORDER BY year
    """, (ticker,)).fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No market cap data for '{ticker}'")
    cols = [d[0] for d in conn.execute("PRAGMA table_info(market_cap)").fetchall()]
    return [dict(zip(cols, r)) for r in rows]