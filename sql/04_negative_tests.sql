-- UMFDOP Agent 3 - 04_negative_tests.sql - each bad insert must be rejected; every row should show PASS.
-- Run: psql -d umfdop -f sql/04_negative_tests.sql   Nothing is changed: each attempt is rolled back.
-- Tested in sandbox (PostgreSQL 18.7).
\pset footer off
CREATE TEMP TABLE neg_result (test text, expected_error text, got text);
DO $$
DECLARE
  t record;
  st text;
BEGIN
  FOR t IN SELECT * FROM (VALUES
    ('N1 overlapping ZWG rate period', '23P01',
     $q$INSERT INTO core.fx_rate (currency_code, valid_at, units_per_usd, flag_jump_gt_5pct, rate_source, source_id, source_file, loaded_at)
        VALUES ('ZWG', daterange('2026-11-12','2026-11-20'), 26.6, false, 'FCB_republished_RBZ_interbank', 'D7', 'test', now())$q$),
    ('N2 duplicate CPI month', '23505',
     $q$INSERT INTO core.fact_cpi_monthly (index_code, period_start, period_end, index_base, index_level, fill_method, is_imputed, source_id, source_file, loaded_at)
        VALUES ('ZWG', '2026-10-01', '2026-10-31', '2024-04=100', 198.63, 'reported_own_release', false, 'D4', 'test', now())$q$),
    ('N3 unknown currency code', '23503',
     $q$INSERT INTO core.fact_us_benchmark (series_id, obs_date, value, currency_code, source_id, source_file, loaded_at)
        VALUES ('DTB3', '2030-01-01', 4.0, 'ZWX', 'D5', 'test', now())$q$),
    ('N4 bid above mid', '23514',
     $q$INSERT INTO core.fx_rate (currency_code, valid_at, units_per_usd, bid_units_per_usd, ask_units_per_usd, flag_jump_gt_5pct, rate_source, source_id, source_file, loaded_at)
        VALUES ('ZWG', daterange('2030-01-01','2030-01-02'), 26.5, 27.0, 27.5, false, 'RBZ_interbank', 'D1', 'test', now())$q$),
    ('N5 ZWG deposit rate dated before the ZiG existed', '23514',
     $q$INSERT INTO core.fact_deposit_rate_monthly (period_start, period_end, currency_code, savings_min_pct, savings_max_pct, three_month_min_pct, three_month_max_pct,
        flag_savings_min_gt_max, flag_3m_min_gt_max, flag_same_as_prior_month, source_id, source_file, loaded_at)
        VALUES ('2023-01-01', '2023-01-31', 'ZWG', 4, 5, 7, 13, false, false, false, 'D3', 'test', now())$q$),
    ('N6 imputed flag inconsistent with fill method', '23514',
     $q$INSERT INTO core.fact_cpi_monthly (index_code, period_start, period_end, index_base, index_level, fill_method, is_imputed, source_id, source_file, loaded_at)
        VALUES ('ZWG', '2026-11-01', '2026-11-30', '2024-04=100', 199, 'chained_from_mom_1dp', false, 'D4', 'test', now())$q$)
  ) v(test, expected_error, sql) LOOP
    BEGIN
      EXECUTE t.sql;
      RAISE EXCEPTION 'undo' USING ERRCODE = 'P0001';   -- insert was accepted: force a rollback
    EXCEPTION WHEN OTHERS THEN
      GET STACKED DIAGNOSTICS st = RETURNED_SQLSTATE;
      INSERT INTO neg_result VALUES (t.test, t.expected_error, CASE WHEN st = 'P0001' THEN 'accepted' ELSE st END);
    END;
  END LOOP;
END $$;
SELECT test, expected_error, got, CASE WHEN got = expected_error THEN 'PASS' ELSE 'FAIL' END AS status FROM neg_result;
