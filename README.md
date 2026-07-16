# Nifty100 Financial Intelligence Platform

Data analytics project on Nifty 100 companies — financials, prices, ratios, sectors.

## Sprint 1 — Data Foundation (Done ✅)
Loaded and validated 12 source Excel files into a single SQLite database (`nifty100.db`)
with a 12-table schema, 16 automated data-quality rules, and full unit test coverage.

### How to run it yourself
```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
# place the 12 raw .xlsx files into data/raw/  (not committed to git — ask your mentor for them)
python -m src.etl.loader
pytest tests/ -v
```

### What's inside
| Path | What it is |
|---|---|
| `src/etl/normaliser.py` | Cleans ticker symbols and messy year formats |
| `src/etl/validator.py` | Implements the 16 Data Quality rules (DQ-01 to DQ-16) |
| `src/etl/loader.py` | End-to-end pipeline: read → clean → validate → load into SQLite |
| `db/schema.sql` | 12-table SQLite schema with PK/FK constraints |
| `tests/etl/` | 46 unit tests for the cleaning functions |
| `notebooks/exploratory_queries.sql` | 10 sample SQL queries against the loaded DB |
| `output/load_audit.csv` | Per-table row counts and rejection reasons from the last run |
| `output/validation_failures.csv` | Every DQ rule violation found, with severity |

### Exit criteria (all met)
- `SELECT COUNT(*) FROM companies` = 92
- `PRAGMA foreign_key_check` → 0 rows
- 46 unit tests passing
- Manual review of 5 companies completed

### Known data issues (flagged, not blocking)
- `companies.xlsx` is missing 7 real Nifty 100 companies (U–Z range) — their financial
  data exists in other files but can't be loaded until the source file is fixed.
- `opm_percentage` for COALINDIA and HINDALCO looks like a scale error in the source
  (flagged by DQ-05); use the computed OPM downstream instead.

## Sprint 2 — (upcoming)
TBD
