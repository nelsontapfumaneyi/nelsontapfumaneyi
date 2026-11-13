-- UMFDOP Agent 3 - 02_load_rbz_event.sql - load clean/rbz_events.csv into core.fact_rbz_event
-- Run from the run folder (it holds clean/):
--   psql -d umfdop -v ON_ERROR_STOP=1 -v expected_rows=<Agent 2 rows out> -f sql/02_load_rbz_event.sql
-- Staging is reloaded; promotion and the audit row commit together or not at all. Tested in sandbox (PostgreSQL 18.7).
TRUNCATE stg.rbz_events;
\copy stg.rbz_events FROM 'clean/rbz_events.csv' WITH (FORMAT csv, HEADER true)
BEGIN;
WITH ins AS (
    INSERT INTO core.fact_rbz_event (event_date, event_type, instrument, tenor_days, currency_code, rate_pct, amount_zwg_m,
                                     source_url, status, source_id, source_file, loaded_at)
    SELECT event_date, event_type, instrument, tenor_days::integer, currency, rate_pct, amount_zwg_m, source_url, status,
           source_id, source_file, loaded_at
    FROM stg.rbz_events
    RETURNING 1
)
INSERT INTO audit.load_log (target_table, file_name, rows_agent2, rows_staged, rows_promoted)
SELECT 'core.fact_rbz_event', 'rbz_events.csv', :expected_rows,
       (SELECT count(*) FROM stg.rbz_events), (SELECT count(*) FROM ins);
COMMIT;
