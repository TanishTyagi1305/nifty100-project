# Nifty100 Financial Intelligence Platform

Data analytics project on Nifty 100 companies — financials, ratios, screener, peer comparison, and an interactive dashboard, built from 12 raw Excel files through 4 sprints.

---

## Quick Start

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
# place the 12 raw .xlsx files into data/raw/ (not committed to git — ask your mentor for them)

python -m src.etl.loader                     # Sprint 1: build the database
python -m src.analytics.compute_ratios        # Sprint 2: compute financial ratios
python -m src.analytics.generate_capital_allocation  # Sprint 2/3: capital allocation patterns
python -m src.analytics.peer                  # Sprint 3: peer percentile rankings
python -m src.screener.composite_score        # Sprint 3: composite quality scores
python -m src.screener.export_excel           # Sprint 3: screener_output.xlsx
python -m src.reports.peer_comparison_excel   # Sprint 3: peer_comparison.xlsx
python -m src.reports.radar                   # Sprint 3: radar charts
python -m src.analytics.export_valuation      # Sprint 4: valuation_summary.xlsx

streamlit run src/dashboard/app.py            # Sprint 4: launch the dashboard
pytest tests/ -v                              # run all tests
```

---

## Sprint 1 — Data Foundation ✅
Loaded and validated 12 source Excel files into a single SQLite database (`nifty100.db`) with a 12-table schema, 16 automated data-quality rules, and full unit test coverage.

**What's inside**
| Path | What it is |
|---|---|
| `src/etl/normaliser.py` | Cleans ticker symbols and messy year formats |
| `src/etl/validator.py` | Implements the 16 Data Quality rules (DQ-01 to DQ-16) |
| `src/etl/loader.py` | End-to-end pipeline: read → clean → validate → load into SQLite |
| `db/schema.sql` | 12-table SQLite schema with PK/FK constraints |
| `tests/etl/` | Unit tests for the cleaning functions |
| `notebooks/exploratory_queries.sql` | 10 sample SQL queries against the loaded DB |
| `output/load_audit.csv` | Per-table row counts and rejection reasons |
| `output/validation_failures.csv` | Every DQ rule violation found, with severity |

**Known data issues (flagged, not fixable in code)**
- `companies.xlsx` is missing 7 real Nifty 100 companies (ULTRACEMCO, UNIONBANK, UNITDSPR, VEDL, WIPRO, ZOMATO, ZYDUSLIFE) — their financial data exists elsewhere but can't be loaded until the source file is fixed. This caps every downstream row count (financial_ratios, valuation, etc.) below what the original specs assumed.

---

## Sprint 2 — Financial Ratio Engine ✅
Computes 50+ KPIs (profitability, leverage, CAGR, cash flow) for all companies across all available years.

**What's inside**
| Path | What it is |
|---|---|
| `src/analytics/ratios.py` | Profitability, leverage, and efficiency ratio formulas |
| `src/analytics/cagr.py` | CAGR engine with all 6 edge-case handlers (turnaround, decline-to-loss, zero-base, etc.) |
| `src/analytics/cashflow_kpis.py` | Free Cash Flow, CFO quality, CapEx intensity, capital allocation pattern classifier |
| `src/analytics/compute_ratios.py` | Runs the full ratio engine and populates `financial_ratios` |
| `output/ratio_edge_cases.log` / `_summary.log` | Every ROE anomaly vs. source data, categorized |
| `tests/kpi/` | Unit tests for every formula (39+ tests) |

**Real data problems found and fixed**
- **BEL, HAL, LICI, LT, PNB, INDIGO** — 41 rows of impossible ROE values (up to 4744%) traced to broken `reserves` figures in the source balance sheet data. Nulled out at the source (`src/analytics/fix_impossible_roe.py`), plus a `<200%` sanity guard applied downstream wherever ROE is used.
- **TCS's source `roe_percentage`** (0.52) is a clear decimal/unit error — real ROE is ~50%, confirmed independently by our own computation.
- `book_value_per_share`, `pat_cagr_5yr`, `eps_cagr_5yr`, and `dividend_payout_ratio_pct` were at various points silently left blank in `compute_ratios.py` — caught each time by checking non-null counts per column, not just row counts.

---

## Sprint 3 — Screener + Peer Engine ✅
A configurable financial screener (15 metrics, 6 presets) and a peer percentile ranking system across 11 industry groups.

**What's inside**
| Path | What it is |
|---|---|
| `config/screener_config.yaml` | Editable threshold config for all 15 filterable metrics |
| `src/screener/engine.py` | Core filter engine — joins financial_ratios/market_cap/profitandloss, applies thresholds |
| `src/screener/presets.py` / `turnaround.py` | The 6 named presets (Quality Compounder, Value Pick, Growth Accelerator, Dividend Champion, Debt-Free Blue Chip, Turnaround Watch) |
| `src/screener/composite_score.py` | 0–100 composite quality score, P10/P90 winsorised, sector-relative |
| `src/screener/export_excel.py` | `output/screener_output.xlsx` — 6 color-coded sheets |
| `src/analytics/peer.py` | Peer percentile ranking across 11 groups, 9 metrics (D/E inverted) |
| `src/reports/peer_comparison_excel.py` | `output/peer_comparison.xlsx` — 11 sheets, percentile colors, benchmark highlight |
| `src/reports/radar.py` | 92 individual radar charts (peer group overlay, or Nifty 100 average fallback) |
| `tests/screener/` | Unit tests for filter logic, D/E Financials-sector exception, Debt Free = infinite ICR |

**Real bugs found and fixed**
- `pat_cagr_5yr` / `eps_cagr_5yr` — never actually computed in Sprint 2 despite the database columns existing; caught when a PAT CAGR filter returned 0 companies.
- `dividend_payout_ratio_pct` — completely missing from the ratio engine's output; caught when Dividend Champion returned 0 companies.
- `composite_quality_score` was calculated but never saved to the database — silently broke the Phase 3 Excel sort order and every radar chart's Composite axis until a stray "Mean of empty slice" warning led to the fix.
- `apply_filters()` secretly assumed `composite_quality_score` always existed — only surfaced when real unit tests ran it against small, hand-built test data instead of the always-complete real database.

**Documented, non-bug findings**
- Value Pick (P/B<3.0) and Debt-Free Blue Chip genuinely return only 2 companies each — this basket of companies trades at real, premium valuations (confirmed via P/B and P/E distributions), not a data error.

---

## Sprint 4 — Streamlit Dashboard + Valuation ✅
An 8-screen interactive dashboard, plus a sector-relative valuation module.

**Run it**
```bash
streamlit run src/dashboard/app.py
```
Opens at `http://localhost:8501`.

**The 8 screens**
| Screen | What it shows |
|---|---|
| Home | 6 market-wide KPI tiles, sector donut chart, top-5 companies by composite score |
| Company Profile | Search any of the 92 companies — KPIs, 10yr revenue/profit chart, ROE trend, pros/cons |
| Screener | 10 live sliders + 6 one-click presets (reuses Sprint 3's filter engine exactly) |
| Peer Comparison | Radar chart vs peer group average, full group KPI table with benchmark highlighted |
| Trend Analysis | Overlay up to 3 metrics on one 10-year chart with YoY % change labels |
| Sector Analysis | Bubble chart (Revenue x ROE x Market Cap) per sector, plus median KPI bars |
| Capital Allocation Map | Treemap of all 92 companies by capital allocation pattern, click to drill in |
| Annual Reports | Search a company, see clickable annual report links by year |

**What's inside**
| Path | What it is |
|---|---|
| `src/dashboard/app.py` | Main entry point, page config |
| `src/dashboard/pages/` | The 8 screen files |
| `src/dashboard/utils/db.py` | Shared, cached (`@st.cache_data`) data loader used by every screen |
| `src/analytics/valuation.py` | FCF yield + sector-relative P/E overvaluation/discount flags |
| `output/valuation_summary.xlsx` | All 92 companies with valuation multiples and flags |
| `output/valuation_flags.csv` | Only the Caution/Discount flagged companies (44 rows) |

**Real bugs found and fixed**
- `pages/` folder was created in the wrong location relative to `app.py` — Streamlit silently showed no sidebar navigation instead of erroring.
- `output/capital_allocation.csv` had gone missing during earlier rebuild sessions and was never regenerated — caught by a `FileNotFoundError` on the Capital Allocation screen.
- `capital_allocation_pattern()`'s function signature had drifted from an earlier draft during rebuilds — caught by checking the real file instead of assuming.

**Documented, non-bug findings**
- `sectors.broad_sector` uses different naming ("Information Technology") than `peer_groups.peer_group_name` ("IT Services") for a similar grouping.
- Valuation flags: "Discount" naturally outnumbers "Caution" (30 vs 14) — explained by the spec's own asymmetric thresholds (0.7x vs 1.5x sector median), not a data issue.
- Annual Report links are not live-checked for 404s on page load — would make the screen too slow for 92 companies; a documented tradeoff, not an oversight.

---

## Known Limitations (carried across all sprints)
- **`companies.xlsx` is missing 7 real Nifty 100 companies** (Sprint 1 finding) — this caps every downstream table below the row counts originally specced (e.g. `financial_ratios` sits at 1073 rows, not the targeted 1,100+). Needs a source-data fix from whoever owns the raw files, not a code fix.
- Several source columns (`roe_percentage`, `roce_percentage`, some `opm_percentage` values for banks) contain known anomalies — always prefer the computed values in `financial_ratios` for analysis; the source columns are useful for display/reference only.

## Project Structure
```
nifty100-project/
├── data/raw/              # 12 source Excel files (not committed)
├── db/                    # schema.sql, nifty100.db
├── config/                # screener_config.yaml
├── src/
│   ├── etl/                # Sprint 1: loader, normaliser, validator
│   ├── analytics/           # Sprint 2-4: ratios, cagr, cashflow_kpis, peer, valuation
│   ├── screener/             # Sprint 3: engine, presets, composite_score
│   ├── reports/               # Sprint 3: radar charts, peer_comparison_excel
│   └── dashboard/              # Sprint 4: Streamlit app + 8 pages
├── tests/                  # unit tests, mirrors src/ structure
├── notebooks/              # exploratory_queries.sql
├── output/                 # generated CSVs, Excel reports
└── reports/radar_charts/   # 92 generated PNG radar charts
```