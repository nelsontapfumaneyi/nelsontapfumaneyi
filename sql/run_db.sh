#!/usr/bin/env bash
# UMFDOP Agent 3 - full database build, load and validation. Run from the run folder (the one holding clean/ and sql/).
# Usage: DB=umfdop bash sql/run_db.sh        (add PGPORT/PGHOST/PGUSER to the environment as needed)
set -euo pipefail
DB=${DB:-umfdop}
P="psql -d $DB -v ON_ERROR_STOP=1 -q"
$P -f sql/01_ddl.sql
# Reference rates first, then facts. expected_rows = Agent 2 rows out (run log 2026-11-13).
$P -v expected_rows=647  -f sql/02_load_fx_rate.sql
$P -v expected_rows=60   -f sql/02_load_fx_imf_monthly.sql
$P -v expected_rows=69   -f sql/02_load_deposit_rate_monthly.sql
$P -v expected_rows=93   -f sql/02_load_cpi_monthly.sql
$P -v expected_rows=214  -f sql/02_load_cpi_observation.sql
$P -v expected_rows=1339 -f sql/02_load_us_benchmark.sql
$P -v expected_rows=12   -f sql/02_load_rbz_event.sql
psql -d "$DB" -f sql/03_validate.sql
psql -d "$DB" -f sql/04_negative_tests.sql
