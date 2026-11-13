# Agent 2 - Ingestion and Cleaning Pack
Brief: 2026-11-13, Does holding ZiG pay? (`umfdop/briefs/agent1-brief-2026-11-13-zig-returns.md`)
Mode: autonomous. Claude fetched the data and ran the pipeline in its own workspace; Nelson reviews and approves.
Scripts (all tested in sandbox): `umfdop/scripts/fetch_zig_returns.py`, `fetch_zig_returns_pass2.py`, `clean_zig_returns.py`

## 1. File inventory
| ID | Requested dataset | Received | Status |
|---|---|---|---|
| D1 | RBZ daily interbank rates | 593 PDFs covering 680 business days (2024-04-08 to 2026-11-13) | Received with gaps (see D7) |
| D2 | IMF ER monthly, ZWE | 2 XML files (average, end of period), 31 obs each | Received |
| D3 | RBZ Table 8.2 deposit rates | `Bank-Deposits-rates.xlsx`, sheet `T8.2 ` | Received |
| D4 | ZIMSTAT CPI (ZWG, USD, Weighted) | 78 of 93 PDFs; 13 of these were found under irregular file names | Received with gaps (filled, see R11) |
| D5 | FRED DTB3, CPIAUCSL, SOFR | 3 CSV files | Received |
| D6 | RBZ events | 12 rows, built from the brief's verified facts | Received |
| D7 | FCB PDFs for RBZ gap days | 55 PDFs for gap days plus 8 overlap-day PDFs for reconciliation | Received |
| D8 | RBZ monetary aggregates | 2 workbooks | Profiled only. Not needed for BQ1-BQ4, so not cleaned |

There are 33 business days with no rate from either RBZ or FCB. 25 of them are public holidays. The other 8 are working days: 2024-04-12, 2024-05-02, 2024-05-03, 2024-05-13, 2024-07-24, 2024-07-26, 2025-04-29 and 2026-09-15.

## 2. Data profile
- **D1:** Each file is one page. The date header appears in 4 formats ("Monday, 12 November 2026", "07 January 2025", "Monday, January 5, 2026", "Monday, 24 February, 2025"). The currency label changes over time (ZIG, then ZiG, then ZWG). The USD row reads INDICES 1/1/1.0000, then ZWG bid, ask and mid, mostly to 4 decimals (a trailing zero is sometimes dropped). The PDF text contains padding spaces inside numbers (for example "1 3.2226"), so text-based parsing breaks.
- **D7:** The date is in the form "15-Apr-2024". The RBZ interbank mid is printed in a side panel. FCB's own buy and sell rates are wider retail rates and are not used.
- **D2:** SDMX XML, in USD per national currency unit. Periods before 2024-04 are ZWL. Data runs to 2026-06, plus one spurious 2027-03 observation.
- **D3:** Monthly from 2021-01 to 2026-09. A year row is followed by month rows. A "*" marks ZiG rows (2024-04 onwards). There are 4 rate columns in % per year (savings min and max, 3-month min and max). Some cells hold more decimals than are displayed (for example 3.541667). 15 structural rows (titles and footnotes) are skipped.
- **D4:** The first page states the index for the month, the previous month and usually the same month a year earlier. Page 2 has a 13-month month-on-month table rounded to 0.1. The ZWG and Weighted indices have base April 2024 = 100; the USD index has base June 2022 = 100.
- **D5:** FRED CSV files, with a blank value on non-trading days. DTB3 is quoted on a discount basis.
- **D6:** 12 rows and 9 columns.

## 3. Issues found
| ID | File | Column | Issue | Rows affected | Severity |
|---|---|---|---|---|---|
| I1 | D1 | bid/ask/mid | Text extraction splits numbers | 593 files | High (fixed by R1) |
| I2 | D1 | header date | 4 date formats | 176 files | Medium (fixed by R2) |
| I3 | D1/D7 | rate_date | 33 business days have no rate | 33 days | Medium (left missing; Agent 3 forward-fills in the mart) |
| I4 | D1 | - | No RBZ file on some days (for example 2025-12-30 and 2025-12-31) | 54 days | Medium (filled from FCB, R4) |
| I5 | D7 | header date | The file named 29 Apr 2025 contains the 28 Apr 2025 sheet | 1 | Medium (rejected) |
| I6 | D1 | mid | +74.2% move on 2024-09-27 (devaluation) | 1 | Low (flagged, kept) |
| I7 | D2 | period | 2027-03 observation | 2 | Low (rejected) |
| I8 | D2 | period average | June 2026 IMF average is 26.424, but every RBZ daily mid that month is between 26.69 and 26.89 | 1 | Low (IMF-side; RBZ carried) |
| I9 | D2, D3 | currency | Rows before Apr 2024 are ZWL | 3 IMF rows, 39 D3 rows | Medium (currency column added) |
| I10 | D3 | savings min/max | Minimum is higher than maximum in 2024-12, 2025-01 and 2026-05 | 3 | Medium (flagged) |
| I11 | D3 | all rates | The month repeats the prior month (2025-03, 2025-12) | 2 | Low (flagged) |
| I12 | D4 | index_level | 15 of 93 type-months have no own release | 15 | Medium (filled per R11; 4 imputed and flagged) |
| I13 | D5 | value | Blank on non-trading days | 59 | Low (rejected as no_observation) |
| I14 | D5 | DTB3 | Quoted on a discount basis | All DTB3 rows | Low (unit labelled; Agent 4 converts) |

## 4. Cleaning rules
| Rule | File | Column | Issue | Rule | Rationale |
|---|---|---|---|---|---|
| R1 | D1 | bid/ask/mid | Split numbers | Rebuild the USD row from character positions (cells split on gaps over 3 pt, spaces removed inside a cell); take the last 3 cells | Robust across all vintages |
| R2 | D1/D7 | header date | Mixed formats | Parse all formats; reject the row if the header date differs from the file date | Catches mislabelled files |
| R3 | D1 | bid/ask/mid | Validity | Reject unless bid < mid < ask and abs(mid - (bid+ask)/2) <= 0.0005 | Catches parse errors |
| R4 | D7 | mid | RBZ gap days | Use the FCB-republished RBZ interbank mid only where RBZ has no file; bid and ask stay null; `rate_source` = FCB_republished_RBZ_interbank | FCB matches RBZ exactly on the 7 overlap days |
| R5 | D1/D7 | mid | Large move | `flag_jump_gt_5pct` when the daily change exceeds 5%; never delete | Outliers are flagged |
| R6 | D1/D7 | rate_date | No rate | Leave missing; no fill in the clean file | Fill is a mart-layer rule |
| R7 | D2 | period | Future period | Reject periods after the run month | Spurious observation |
| R8 | D2/D3 | currency | ZWL vs ZWG | `currency` = ZWL before 2024-04 (D3: by the "*" marker; rejected if the marker and period disagree) | Never mix currencies |
| R9 | D2 | rate | Quote direction | Keep `usd_per_unit` as reported and add `local_per_usd` = 1/x | Matches the RBZ quote convention |
| R10 | D3 | rates | Inconsistent ranges | Flags `flag_savings_min_gt_max`, `flag_3m_min_gt_max`, `flag_same_as_prior_month`; values kept | Source issue, not a parse error |
| R11 | D4 | index_level | Missing release | Fill order: own release, then the next month's release (prior-month level), then the release 12 months later, then chain from the 0.1-dp month-on-month table (`is_imputed` = true). The weighted index for 2024-04 is 100 by base definition | Exact values first; imputation flagged |
| R12 | D4 | index_level | Revisions | Keep every level statement in `cpi_observations.csv`; list any period stated twice with different values in `recon_cpi_revisions.csv` | Don't pick silently (0 found) |
| R13 | D5 | value | Blank days | Reject with `no_observation` | Not data |
| R14 | All | - | Lineage | `source_id`, `source_file` and `loaded_at` on every row; ISO dates; snake_case | Contract |

## 5. Reconciliation
- **FCB vs RBZ (7 overlap days):** difference 0.0000 on every day.
- **RBZ daily vs IMF monthly (27 months):** end-of-period values are identical in 26 of 27 months. In Feb 2026 the IMF figure is 25.7730 against 25.7733 on the RBZ sheet of 2026-02-27 (0.0012%; RBZ checked against the PDF; corrected at Step 3). Period averages agree within ±0.2%, except 2026-06 (-1.38%, an IMF-side anomaly; I8).
- **CPI:** 214 level statements with 0 conflicting revisions. Computed year-on-year rates for Oct 2026 match the ZIMSTAT releases (ZWG 4.27 vs 4.3; USD 3.22 vs 3.2; Weighted 3.51 vs 3.5).
- **Tie-out to verified brief figures:** 16 of 16 pass. Examples: mid 13.5616 (2024-04-08), 24.3902 (2024-09-27), 25.9807 (2025-12-31), 26.5397 (2026-11-12) and 26.5861 (2026-11-13); ZWG CPI 198.63 (Oct 2026); 3-month maximum rate 13.88% (Sep 2026); DTB3 4.12 (2026-11-10).

## 6. KNIME node sequence (Analytics Platform 5.x)
| # | Node | Configuration | Purpose |
|---|---|---|---|
| 1 | Python Script | Runs the `parse_rbz`, `parse_fcb` and `parse_cpi` functions from `clean_zig_returns.py` over the PDF folders; outputs 3 tables | PDF extraction (KNIME has no reliable native PDF table reader) |
| 2 | Rule Engine | R2 and R3 checks producing `reject_reason` | Validation |
| 3 | Row Splitter | `reject_reason` is empty | Clean vs rejects |
| 4 | Concatenate + Duplicate Row Filter | Key `rate_date`; keep RBZ over FCB | R4 |
| 5 | Lag Column + Math Formula | `mid/lag(mid)-1`; Rule Engine for `flag_jump_gt_5pct` | R5 |
| 6 | XML Reader + XPath | `//Obs/@TIME_PERIOD`, `//Obs/@OBS_VALUE` | D2 |
| 7 | Excel Reader + Rule Engine + Row Filter | Sheet `T8.2 `; month rows only; currency from the "*" marker | D3, R8, R10 |
| 8 | CSV Reader + Row Filter | FRED files; drop blank values | D5, R13 |
| 9 | Table Validator | Types and allowed values per the contract | Contract check |
| 10 | CSV Writer | `clean/` and `rejects/` | Output |

## 7. Python script
`umfdop/scripts/clean_zig_returns.py`, tested in sandbox (Python 3, pandas 3.0.5, pdfplumber 0.11.10). It is idempotent: two runs produce identical output (11 files compared, 0 differences). Run with `python clean_zig_returns.py <run_dir>`.

## 8. Data contract (for Agent 3)
| File | Grain | Key | Columns (type, unit, nullable) |
|---|---|---|---|
| `fx_usd_zwg_daily.csv` (647 rows) | One business day with a published rate | PK `rate_date` | `rate_date` date; `base_currency` 'USD'; `quote_currency` 'ZWG'; `bid`, `ask` numeric(12,4) ZWG per USD, nullable (null on FCB rows); `mid` numeric(12,4) > 0, not null; `pct_change_mid` numeric %, nullable on the first row; `flag_jump_gt_5pct` bool; `rate_source` {RBZ_interbank, FCB_republished_RBZ_interbank}; lineage |
| `fx_imf_monthly.csv` (60) | Month x transformation | PK (`period`, `transformation`) | `period` YYYY-MM; `period_start`, `period_end` date; `transformation` {period_average, end_of_period}; `currency` {ZWL, ZWG}; `usd_per_unit`, `local_per_usd` numeric; `flag_partial_zig_month` bool; lineage |
| `deposit_rates_monthly.csv` (69) | Month | PK `period` | `period`; `period_start`, `period_end`; `currency` {ZWL, ZWG}; `savings_min_pct`, `savings_max_pct`, `three_month_min_pct`, `three_month_max_pct` numeric % p.a., not null; 3 boolean flags; lineage |
| `cpi_observations.csv` (214) | One level statement in one release | PK (`cpi_type`, `period`, `published_in`, `role`) | `cpi_type` {ZWG, USD, Weighted}; `period`; `index_level` numeric; `role` {current, prior_month, prior_year}; `published_in` YYYY-MM; `index_base` nullable; lineage |
| `cpi_monthly.csv` (93) | CPI type x month, 2024-04 to 2026-10 | PK (`cpi_type`, `period`) | `index_level` numeric, not null; `index_base` {2024-04=100, 2022-06=100}; `mom_pct`, `yoy_pct` numeric, nullable; `fill_method`; `is_imputed` bool; lineage |
| `us_benchmarks.csv` (1,339) | Series x observation date | PK (`series_id`, `obs_date`) | `series_id` {DTB3, SOFR, CPIAUCSL}; `value` numeric; `unit`; `frequency` {daily, monthly}; `currency` 'USD'; lineage |
| `rbz_events.csv` (12) | One event | Surrogate key; natural key (`event_date`, `event_type`, `instrument`, `tenor_days`, `currency`) with nullable `tenor_days` | `rate_pct`, `amount_zwg_m`, `tenor_days` nullable numeric; `status` {verified, single_source}; `source_url` |

Foreign keys: a date dimension built by Agent 3 joins `fx.rate_date`, `us_benchmarks.obs_date` and `rbz_events.event_date`; a month dimension joins `period` in `cpi_monthly`, `deposit_rates_monthly` and `fx_imf_monthly`. The daily exchange-rate mart view must forward-fill the 33 no-rate days and add an `is_carried_forward` flag.

## 9. Run log (evidence)
| File | Rows in | Rows out | Rejected | Output |
|---|---|---|---|---|
| D1+D7 | 648 | 647 | 1 | `fx_usd_zwg_daily.csv` |
| D2 | 62 | 60 | 2 | `fx_imf_monthly.csv` |
| D3 | 69 | 69 | 0 | `deposit_rates_monthly.csv` |
| D4 | 78 | 78 | 0 | `cpi_observations.csv`, then `cpi_monthly.csv` (93) |
| D5 | 1,398 | 1,339 | 59 | `us_benchmarks.csv` |
| D6 | 12 | 12 | 0 | `rbz_events.csv` |

In every file, rows in = rows out + rejected (asserted in the script).

Pipeline: Step 2 of 5 - Agent 2 - Waiting for: Nelson's approval of this pack
