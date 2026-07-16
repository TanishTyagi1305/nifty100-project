-- exploratory_queries.sql
-- 10 sanity/exploration queries against nifty100.db (Sprint 1 wrap-up)

-- 1. How many companies per sector?
SELECT broad_sector, COUNT(*) AS n_companies
FROM sectors GROUP BY broad_sector ORDER BY n_companies DESC;

-- 2. Top 10 companies by latest year sales
SELECT company_id, year, sales
FROM profitandloss
WHERE year = (SELECT MAX(year) FROM profitandloss)
ORDER BY sales DESC LIMIT 10;

-- 3. Companies with negative equity (equity_capital + reserves <= 0)
SELECT company_id, year, equity_capital, reserves
FROM balancesheet
WHERE (equity_capital + reserves) <= 0;

-- 4. Average OPM% by sector (latest year)
SELECT s.broad_sector, ROUND(AVG(p.opm_percentage), 2) AS avg_opm
FROM profitandloss p
JOIN sectors s ON p.company_id = s.company_id
WHERE p.year = (SELECT MAX(year) FROM profitandloss)
GROUP BY s.broad_sector ORDER BY avg_opm DESC;

-- 5. Companies with fewer than 5 years of P&L history (DQ-16 flag list)
SELECT company_id, COUNT(DISTINCT year) AS n_years
FROM profitandloss GROUP BY company_id HAVING n_years < 5;

-- 6. Balance sheets that don't balance within 1% (DQ-04 flagged rows)
SELECT company_id, year, total_assets, total_liabilities,
       ROUND(ABS(total_assets-total_liabilities)*100.0/total_assets, 3) AS pct_diff
FROM balancesheet
WHERE total_assets != 0
  AND ABS(total_assets-total_liabilities)*1.0/total_assets >= 0.01;

-- 7. Latest market cap ranking (top 10)
SELECT company_id, year, market_cap_crore
FROM market_cap
WHERE year = (SELECT MAX(year) FROM market_cap)
ORDER BY market_cap_crore DESC LIMIT 10;

-- 8. Average stock closing price trend for one company (e.g. TCS) by year
SELECT strftime('%Y', date) AS yr, ROUND(AVG(close_price), 2) AS avg_close
FROM stock_prices WHERE company_id = 'TCS'
GROUP BY yr ORDER BY yr;

-- 9. Companies with dividend payout over 100% (possible red flag)
SELECT company_id, year, dividend_payout
FROM profitandloss WHERE dividend_payout > 100
ORDER BY dividend_payout DESC;

-- 10. Row counts across all 12 tables (final load summary)
SELECT 'companies' AS tbl, COUNT(*) AS n FROM companies
UNION ALL SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL SELECT 'analysis', COUNT(*) FROM analysis
UNION ALL SELECT 'documents', COUNT(*) FROM documents
UNION ALL SELECT 'prosandcons', COUNT(*) FROM prosandcons
UNION ALL SELECT 'sectors', COUNT(*) FROM sectors
UNION ALL SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL SELECT 'market_cap', COUNT(*) FROM market_cap
UNION ALL SELECT 'financial_ratios', COUNT(*) FROM financial_ratios
UNION ALL SELECT 'peer_groups', COUNT(*) FROM peer_groups;
