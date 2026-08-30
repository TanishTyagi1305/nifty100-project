"""
main.py
-------
FastAPI application entry point. Sprint 6, Day 38.
All endpoints are under /api/v1 prefix.
"""
import time
import sqlite3
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Nifty100 Analytics API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

START_TIME = time.time()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round(time.time() - start, 3)
    print(f"{request.method} {request.url.path} -> {response.status_code} ({duration}s)")
    return response


@app.get("/api/v1/health")
def health():
    conn = sqlite3.connect("db/nifty100.db")
    tables = ["companies", "profitandloss", "balancesheet", "cashflow",
              "financial_ratios", "sectors", "stock_prices", "market_cap",
              "peer_groups", "peer_percentiles"]
    row_counts = {}
    for t in tables:
        try:
            row_counts[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except Exception:
            row_counts[t] = "table not found"
    conn.close()
    return {
        "status": "ok",
        "db_row_counts": row_counts,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "version": "1.0.0",
    }