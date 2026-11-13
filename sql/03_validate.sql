-- UMFDOP Agent 3 - 03_validate.sql - every row should show status = PASS
-- Run: psql -d umfdop -f sql/03_validate.sql     Tested in sandbox (PostgreSQL 18.7).
\pset footer off
WITH last_load AS (
    SELECT DISTINCT ON (target_table) * FROM audit.load_log ORDER BY target_table, load_id DESC
),
checks(check_name, expected, actual) AS (
    -- V1-V2: row counts per load
    SELECT 'V1 staged = Agent 2 rows out: ' || target_table, rows_agent2::text, rows_staged::text FROM last_load
    UNION ALL
    SELECT 'V2 promoted = staged: ' || target_table, rows_staged::text, rows_promoted::text FROM last_load
    UNION ALL
    -- V3: totals by currency, staging vs core
    SELECT 'V3 FX sum of mid by currency (stg vs core)',
           (SELECT round(sum(mid), 4)::text FROM stg.fx_usd_zwg_daily WHERE quote_currency = 'ZWG'),
           (SELECT round(sum(units_per_usd), 4)::text FROM core.fx_rate WHERE currency_code = 'ZWG' AND NOT is_deleted)
    UNION ALL
    SELECT 'V3 deposit-rate totals by currency (stg vs core)',
           (SELECT string_agg(currency || '=' || s, ';' ORDER BY currency) FROM
              (SELECT currency, round(sum(savings_min_pct + savings_max_pct + three_month_min_pct + three_month_max_pct), 4) s
               FROM stg.deposit_rates_monthly GROUP BY 1) a),
           (SELECT string_agg(currency_code || '=' || s, ';' ORDER BY currency_code) FROM
              (SELECT currency_code, round(sum(savings_min_pct + savings_max_pct + three_month_min_pct + three_month_max_pct), 4) s
               FROM core.fact_deposit_rate_monthly WHERE NOT is_deleted GROUP BY 1) b)
    UNION ALL
    SELECT 'V3 CPI index totals by index (stg vs core)',
           (SELECT string_agg(cpi_type || '=' || s, ';' ORDER BY cpi_type) FROM
              (SELECT cpi_type, round(sum(index_level), 2) s FROM stg.cpi_monthly GROUP BY 1) a),
           (SELECT string_agg(index_code || '=' || s, ';' ORDER BY index_code) FROM
              (SELECT index_code, round(sum(index_level), 2) s FROM core.fact_cpi_monthly WHERE NOT is_deleted GROUP BY 1) b)
    UNION ALL
    SELECT 'V3 US benchmark totals by series (stg vs core)',
           (SELECT string_agg(series_id || '=' || s, ';' ORDER BY series_id) FROM
              (SELECT series_id, round(sum(value), 4) s FROM stg.us_benchmarks GROUP BY 1) a),
           (SELECT string_agg(series_id || '=' || s, ';' ORDER BY series_id) FROM
              (SELECT series_id, round(sum(value), 4) s FROM core.fact_us_benchmark WHERE NOT is_deleted GROUP BY 1) b)
    UNION ALL
    -- V4: no ZWG month without an exchange rate
    SELECT 'V4 months 2024-04..2026-10 without a ZWG/USD month-end rate', '0',
           (SELECT count(*)::text FROM mart.v_monthly_inputs WHERE period BETWEEN '2024-04' AND '2026-10' AND zwg_per_usd_eop IS NULL)
    UNION ALL
    -- V5: dates outside dim_date (staging, all date columns)
    SELECT 'V5 staged dates outside dim_date', '0', (SELECT count(*)::text FROM (
              SELECT rate_date d FROM stg.fx_usd_zwg_daily UNION ALL SELECT period_start FROM stg.fx_imf_monthly
              UNION ALL SELECT period_start FROM stg.deposit_rates_monthly UNION ALL SELECT period_start FROM stg.cpi_monthly
              UNION ALL SELECT obs_date FROM stg.us_benchmarks UNION ALL SELECT event_date FROM stg.rbz_events) x
              LEFT JOIN core.dim_date dd ON dd.date_key = x.d WHERE dd.date_key IS NULL)
    UNION ALL
    -- V6-V9: daily FX view
    SELECT 'V6 v_fx_daily: one row per calendar day 2024-04-08..2026-11-13',
           ((DATE '2026-11-13' - DATE '2024-04-08') + 1)::text,
           (SELECT count(DISTINCT date_key)::text || CASE WHEN count(*) = count(DISTINCT date_key) THEN '' ELSE ' (duplicates)' END
            FROM mart.v_fx_daily)
    UNION ALL
    SELECT 'V7 weekdays carried forward (no published rate)', '33',
           (SELECT count(*)::text FROM mart.v_fx_daily WHERE is_weekday AND is_carried_forward)
    UNION ALL
    SELECT 'V8 FCB-sourced days (bid/ask null by rule R4)', '54',
           (SELECT count(*)::text FROM core.fx_rate WHERE rate_source = 'FCB_republished_RBZ_interbank' AND bid_units_per_usd IS NULL)
    UNION ALL
    SELECT 'V9 tie-out mids 2024-04-08 | 2024-09-27 | 2025-12-31 | 2026-11-13', '13.5616|24.3902|25.9807|26.5861',
           (SELECT string_agg(trim(to_char(units_per_usd, 'FM999990.0000')), '|' ORDER BY date_key) FROM mart.v_fx_daily
            WHERE date_key IN ('2024-04-08', '2024-09-27', '2025-12-31', '2026-11-13'))
    UNION ALL
    -- V10: RBZ month-end equals IMF end-of-period (Agent 2 reconciliation rule)
    -- Tolerance 0.01%: extraction errors (dropped digits) move a rate by 10% or more; IMF rounding moves it by < 0.01%.
    SELECT 'V10 complete months where RBZ month-end differs from IMF EOP by > 0.01%', '0',
           (SELECT count(*)::text FROM mart.v_fx_monthly
            WHERE is_complete_month AND imf_eop_units_per_usd IS NOT NULL
              AND abs(eop_units_per_usd / imf_eop_units_per_usd - 1) > 0.0001)
    UNION ALL
    -- Known exception: IMF Feb 2026 EOP 25.7730 vs RBZ sheet of 2026-02-27 25.7733 (checked against the PDF). A new month here fails.
    SELECT 'V10b months with any month-end difference > 0.0001 ZWG (known: 2026-02)', '2026-02',
           (SELECT coalesce(string_agg(period, ',' ORDER BY period), 'none') FROM mart.v_fx_monthly
            WHERE is_complete_month AND imf_eop_units_per_usd IS NOT NULL AND abs(eop_units_per_usd - imf_eop_units_per_usd) > 0.0001)
    UNION ALL
    SELECT 'V11 months compared with IMF EOP', '27',
           (SELECT count(*)::text FROM mart.v_fx_monthly WHERE is_complete_month AND imf_eop_units_per_usd IS NOT NULL)
    UNION ALL
    -- V12-V14: contract business rules
    SELECT 'V12 CPI rows | imputed | null levels', '93|4|0',
           (SELECT count(*) || '|' || count(*) FILTER (WHERE is_imputed) || '|' || count(*) FILTER (WHERE index_level IS NULL)
            FROM core.fact_cpi_monthly)
    UNION ALL
    SELECT 'V13 tie-out CPI ZWG 2026-10 | Weighted 2026-09 | USD 2026-10', '198.63|131.32|126.11',
           (SELECT string_agg(index_level::text, '|' ORDER BY ord) FROM (
              SELECT index_level, 1 ord FROM core.fact_cpi_monthly WHERE index_code = 'ZWG' AND period_start = '2026-10-01'
              UNION ALL SELECT index_level, 2 FROM core.fact_cpi_monthly WHERE index_code = 'Weighted' AND period_start = '2026-09-01'
              UNION ALL SELECT index_level, 3 FROM core.fact_cpi_monthly WHERE index_code = 'USD' AND period_start = '2026-10-01') t)
    UNION ALL
    SELECT 'V14 ZWG deposit-rate months (2024-04..2026-09) | min>max flags', '30|3',
           (SELECT count(*) || '|' || count(*) FILTER (WHERE flag_savings_min_gt_max OR flag_3m_min_gt_max)
            FROM core.fact_deposit_rate_monthly WHERE currency_code = 'ZWG')
    UNION ALL
    SELECT 'V15 IMF rows labelled ZWG before 2024-04 or ZWL after', '0',
           (SELECT count(*)::text FROM core.fact_fx_imf_monthly
            WHERE (currency_code = 'ZWG') <> (period_start >= DATE '2024-04-01'))
    UNION ALL
    SELECT 'V16 CPI observations: periods stated with conflicting levels', '0',
           (SELECT count(*)::text FROM (SELECT index_code, period_start FROM core.fact_cpi_observation
            GROUP BY 1, 2 HAVING max(index_level) - min(index_level) > 0.005) r)
    UNION ALL
    SELECT 'V17 monthly inputs 2024-04..2026-10 with all three CPI levels', '31',
           (SELECT count(*)::text FROM mart.v_monthly_inputs WHERE period BETWEEN '2024-04' AND '2026-10'
            AND zwg_cpi IS NOT NULL AND zim_usd_cpi IS NOT NULL AND weighted_cpi IS NOT NULL)
    UNION ALL
    SELECT 'V18 bi_reader can read mart and cannot read core',  'mart=t core=f',
           'mart=' || has_table_privilege('bi_reader', 'mart.v_fx_daily', 'SELECT')::text
           || ' core=' || has_table_privilege('bi_reader', 'core.fx_rate', 'SELECT')::text
)
SELECT check_name, expected, actual,
       CASE WHEN expected = actual
              OR (expected = 'mart=t core=f' AND actual = 'mart=true core=false') THEN 'PASS' ELSE 'FAIL' END AS status
FROM checks;
