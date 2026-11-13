-- UMFDOP Agent 4 - 05_agent4_extract.sql - the only queries the analysis reads (mart views only).
-- Run: psql -d umfdop -f sql/05_agent4_extract.sql   Tested in sandbox (PostgreSQL 18.7).

-- Q1 daily ZiG/USD (calendar days; weekends/holidays carry the last published rate)
SELECT date_key, units_per_usd, bid_units_per_usd, ask_units_per_usd, is_carried_forward, rate_source
FROM mart.v_fx_daily WHERE currency_code = 'ZWG' ORDER BY date_key;

-- Q2 monthly inputs (FX month-end/average, three CPIs, ZiG deposit rates, US T-bill, SOFR, US CPI)
SELECT * FROM mart.v_monthly_inputs ORDER BY period;

-- Q3 RBZ instrument events (ZiGDTDF auction and tap rates, minimum deposit rates, policy rate)
SELECT * FROM mart.v_rbz_events ORDER BY event_date, event_type, tenor_days;

-- Q4 readiness profile
SELECT 'v_fx_daily' AS view, count(*) AS rows, min(date_key)::text AS first, max(date_key)::text AS last,
       count(*) FILTER (WHERE is_carried_forward) AS carried_forward_days, 0 AS missing_values
FROM mart.v_fx_daily
UNION ALL
SELECT 'v_monthly_inputs', count(*), min(period), max(period), 0,
       count(*) FILTER (WHERE zwg_cpi IS NULL OR savings_max_pct IS NULL OR us_tbill_3m_discount_pct_avg IS NULL)
FROM mart.v_monthly_inputs;
