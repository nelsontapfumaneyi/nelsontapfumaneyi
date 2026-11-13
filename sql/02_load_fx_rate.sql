-- UMFDOP Agent 3 - 02_load_fx_rate.sql - load clean/fx_usd_zwg_daily.csv into core.fx_rate
-- Run from the run folder (it holds clean/):
--   psql -d umfdop -v ON_ERROR_STOP=1 -v expected_rows=<Agent 2 rows out> -f sql/02_load_fx_rate.sql
-- Staging is reloaded; promotion and the audit row commit together or not at all. Tested in sandbox (PostgreSQL 18.7).
TRUNCATE stg.fx_usd_zwg_daily;
\copy stg.fx_usd_zwg_daily FROM 'clean/fx_usd_zwg_daily.csv' WITH (FORMAT csv, HEADER true)
BEGIN;
WITH ins AS (
    INSERT INTO core.fx_rate (currency_code, rate_type, valid_at, units_per_usd, bid_units_per_usd, ask_units_per_usd,
                              pct_change_mid_pct, flag_jump_gt_5pct, rate_source, source_id, source_file, loaded_at)
    SELECT quote_currency, 'RBZ official',
           daterange(rate_date, coalesce(lead(rate_date) OVER (ORDER BY rate_date), rate_date + 1), '[)'),
           mid, bid, ask, pct_change_mid, flag_jump_gt_5pct, rate_source, source_id, source_file, loaded_at
    FROM stg.fx_usd_zwg_daily
    WHERE base_currency = 'USD'
    RETURNING 1
)
INSERT INTO audit.load_log (target_table, file_name, rows_agent2, rows_staged, rows_promoted)
SELECT 'core.fx_rate', 'fx_usd_zwg_daily.csv', :expected_rows,
       (SELECT count(*) FROM stg.fx_usd_zwg_daily), (SELECT count(*) FROM ins);
COMMIT;
