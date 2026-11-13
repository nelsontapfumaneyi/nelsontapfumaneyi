-- UMFDOP Agent 3 - 02_load_cpi_monthly.sql - load clean/cpi_monthly.csv into core.fact_cpi_monthly
-- Run from the run folder (it holds clean/):
--   psql -d umfdop -v ON_ERROR_STOP=1 -v expected_rows=<Agent 2 rows out> -f sql/02_load_cpi_monthly.sql
-- Staging is reloaded; promotion and the audit row commit together or not at all. Tested in sandbox (PostgreSQL 18.7).
TRUNCATE stg.cpi_monthly;
\copy stg.cpi_monthly FROM 'clean/cpi_monthly.csv' WITH (FORMAT csv, HEADER true)
BEGIN;
WITH ins AS (
    INSERT INTO core.fact_cpi_monthly (index_code, period_start, period_end, index_base, index_level, mom_pct, yoy_pct,
                                       fill_method, is_imputed, source_id, source_file, loaded_at)
    SELECT cpi_type, period_start, period_end, index_base, index_level, mom_pct, yoy_pct, fill_method, is_imputed,
           source_id, source_file, loaded_at
    FROM stg.cpi_monthly
    RETURNING 1
)
INSERT INTO audit.load_log (target_table, file_name, rows_agent2, rows_staged, rows_promoted)
SELECT 'core.fact_cpi_monthly', 'cpi_monthly.csv', :expected_rows,
       (SELECT count(*) FROM stg.cpi_monthly), (SELECT count(*) FROM ins);
COMMIT;
