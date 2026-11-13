-- UMFDOP Agent 3 - 02_load_us_benchmark.sql - load clean/us_benchmarks.csv into core.fact_us_benchmark
-- Run from the run folder (it holds clean/):
--   psql -d umfdop -v ON_ERROR_STOP=1 -v expected_rows=<Agent 2 rows out> -f sql/02_load_us_benchmark.sql
-- Staging is reloaded; promotion and the audit row commit together or not at all. Tested in sandbox (PostgreSQL 18.7).
TRUNCATE stg.us_benchmarks;
\copy stg.us_benchmarks FROM 'clean/us_benchmarks.csv' WITH (FORMAT csv, HEADER true)
BEGIN;
WITH ins AS (
    INSERT INTO core.fact_us_benchmark (series_id, obs_date, value, currency_code, source_id, source_file, loaded_at)
    SELECT series_id, obs_date, value, currency, source_id, source_file, loaded_at
    FROM stg.us_benchmarks
    RETURNING 1
)
INSERT INTO audit.load_log (target_table, file_name, rows_agent2, rows_staged, rows_promoted)
SELECT 'core.fact_us_benchmark', 'us_benchmarks.csv', :expected_rows,
       (SELECT count(*) FROM stg.us_benchmarks), (SELECT count(*) FROM ins);
COMMIT;
