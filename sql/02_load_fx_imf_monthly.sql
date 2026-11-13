-- UMFDOP Agent 3 - 02_load_fx_imf_monthly.sql - load clean/fx_imf_monthly.csv into core.fact_fx_imf_monthly
-- Run from the run folder (it holds clean/):
--   psql -d umfdop -v ON_ERROR_STOP=1 -v expected_rows=<Agent 2 rows out> -f sql/02_load_fx_imf_monthly.sql
-- Staging is reloaded; promotion and the audit row commit together or not at all. Tested in sandbox (PostgreSQL 18.7).
TRUNCATE stg.fx_imf_monthly;
\copy stg.fx_imf_monthly FROM 'clean/fx_imf_monthly.csv' WITH (FORMAT csv, HEADER true)
BEGIN;
WITH ins AS (
    INSERT INTO core.fact_fx_imf_monthly (period_start, period_end, transformation, currency_code, usd_per_unit,
                                          local_per_usd, flag_partial_zig_month, source_id, source_file, loaded_at)
    SELECT period_start, period_end, transformation, currency, usd_per_unit, local_per_usd, flag_partial_zig_month,
           source_id, source_file, loaded_at
    FROM stg.fx_imf_monthly
    RETURNING 1
)
INSERT INTO audit.load_log (target_table, file_name, rows_agent2, rows_staged, rows_promoted)
SELECT 'core.fact_fx_imf_monthly', 'fx_imf_monthly.csv', :expected_rows,
       (SELECT count(*) FROM stg.fx_imf_monthly), (SELECT count(*) FROM ins);
COMMIT;
