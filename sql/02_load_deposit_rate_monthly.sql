-- UMFDOP Agent 3 - 02_load_deposit_rate_monthly.sql - load clean/deposit_rates_monthly.csv into core.fact_deposit_rate_monthly
-- Run from the run folder (it holds clean/):
--   psql -d umfdop -v ON_ERROR_STOP=1 -v expected_rows=<Agent 2 rows out> -f sql/02_load_deposit_rate_monthly.sql
-- Staging is reloaded; promotion and the audit row commit together or not at all. Tested in sandbox (PostgreSQL 18.7).
TRUNCATE stg.deposit_rates_monthly;
\copy stg.deposit_rates_monthly FROM 'clean/deposit_rates_monthly.csv' WITH (FORMAT csv, HEADER true)
BEGIN;
WITH ins AS (
    INSERT INTO core.fact_deposit_rate_monthly (period_start, period_end, currency_code, savings_min_pct, savings_max_pct,
           three_month_min_pct, three_month_max_pct, flag_savings_min_gt_max, flag_3m_min_gt_max, flag_same_as_prior_month,
           source_id, source_file, loaded_at)
    SELECT period_start, period_end, currency, savings_min_pct, savings_max_pct, three_month_min_pct, three_month_max_pct,
           flag_savings_min_gt_max, flag_3m_min_gt_max, flag_same_as_prior_month, source_id, source_file, loaded_at
    FROM stg.deposit_rates_monthly
    RETURNING 1
)
INSERT INTO audit.load_log (target_table, file_name, rows_agent2, rows_staged, rows_promoted)
SELECT 'core.fact_deposit_rate_monthly', 'deposit_rates_monthly.csv', :expected_rows,
       (SELECT count(*) FROM stg.deposit_rates_monthly), (SELECT count(*) FROM ins);
COMMIT;
