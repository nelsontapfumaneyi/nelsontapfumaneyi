-- UMFDOP Agent 3 - 02_load_cpi_observation.sql - load clean/cpi_observations.csv into core.fact_cpi_observation
-- Run from the run folder (it holds clean/):
--   psql -d umfdop -v ON_ERROR_STOP=1 -v expected_rows=<Agent 2 rows out> -f sql/02_load_cpi_observation.sql
-- Staging is reloaded; promotion and the audit row commit together or not at all. Tested in sandbox (PostgreSQL 18.7).
TRUNCATE stg.cpi_observations;
\copy stg.cpi_observations FROM 'clean/cpi_observations.csv' WITH (FORMAT csv, HEADER true)
BEGIN;
WITH ins AS (
    INSERT INTO core.fact_cpi_observation (index_code, period_start, published_in, role, index_level, index_base,
                                           source_id, source_file, loaded_at)
    SELECT cpi_type, (period || '-01')::date, (published_in || '-01')::date, role, index_level, index_base,
           source_id, source_file, loaded_at
    FROM stg.cpi_observations
    RETURNING 1
)
INSERT INTO audit.load_log (target_table, file_name, rows_agent2, rows_staged, rows_promoted)
SELECT 'core.fact_cpi_observation', 'cpi_observations.csv', :expected_rows,
       (SELECT count(*) FROM stg.cpi_observations), (SELECT count(*) FROM ins);
COMMIT;
