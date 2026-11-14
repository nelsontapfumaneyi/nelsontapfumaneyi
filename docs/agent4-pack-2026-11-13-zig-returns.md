# Agent 4 - Analytics Pack
Inputs: Agent 3 validation (34 of 34 checks and 6 of 6 negative tests PASS, 2026-11-13, approved by Nelson); BQ1-BQ4 from `umfdop/briefs/agent1-brief-2026-11-13-zig-returns.md`.
Mode: autonomous. Run in Claude's workspace against PostgreSQL 18.7, reading `mart` views only.
Code (tested in sandbox; Python 3.13, pandas 3.0.5, numpy 2.5.3, psycopg 3.3.9, seed 42):
- `umfdop/sql/05_agent4_extract.sql`
- `umfdop/scripts/agent4_zig_returns.py`
- `umfdop/scripts/agent4_findings.py`

Note: during this step the sandbox database was rebuilt as UTF8 (it had defaulted to SQL_ASCII, which returns text as bytes to Python). The Agent 3 validation was re-run: still 40 of 40 PASS. When you create the database locally, use `CREATE DATABASE umfdop ENCODING 'UTF8' TEMPLATE template0`.

## 1. Method plan
| Question | Method | Baseline | Data used (mart view) | Readiness check |
|---|---|---|---|---|
| BQ1 Monthly nominal, real and USD-adjusted returns by ZiG product | Daily wealth-index engine; exact log bridge (interest effect + FX effect = total) | USD cash (0%) and US 3-month T-bill; identity checks | v_fx_daily, v_monthly_inputs, v_rbz_events | 950 of 950 FX days; deposit rates end 2026-09, so the window is **2024-04-08 to 2026-09-30** |
| BQ2 Spread vs USD alternatives by sub-period | Sub-period point-to-point returns, annualised; spread in pp | T-bill (bond-equivalent yield of DTB3) and USD cash | same | 6 sub-periods; ZiGDTDF only from 2026-06-04 |
| BQ3 Yield the curve needs; break-even | Scenario grid y = (1+r)/((1-e)(1-c)^(1/T)) - 1, e = annual loss in the ZiG's USD value (corrected 2026-11-14); effective annual rates on offer; Monte Carlo of ending wealth relative to the T-bill (10,000 runs, compounding at each product's term); devaluation stress | Current-state values: r = 4.15% (Oct 2026 BEY), e = 2.62% p.a. (2026 to 13 Nov), c = 4.88% (RBZ bid/ask, 13 Nov) | same | Monte Carlo inputs from 21 calm months (Jan 2025 to Sep 2026) |
| BQ4 How often 30/90-day holdings lose USD value; tail | Rolling windows on the daily panel; maximum drawdown | USD cash (never loses nominal USD) and T-bill | same | 816 to 876 windows per product (ZiGDTDF: 29 to 89) |

No predictive model was fitted. The questions are descriptive and what-if, so the simplest exact method was used and is checked by identities (Section 3).

Return conventions:
- Quoted % p.a. rates accrue daily and compound monthly: a full month earns r × days/365.
- USD-adjusted return = ZWG return × (start rate / end rate), using the RBZ mid rate; weekends carry Friday's rate.
- The real ZWG return is deflated by the ZWG CPI; the USD-adjusted real return is deflated by the ZIMSTAT USD CPI.
- 3-month deposits are approximated as monthly accrual at each month's quoted rate (no lock-in modelled).
- ZiGDTDF is held at the inaugural 10.98% (no later auction results were found).

## 2. Code
### SQL extraction (`05_agent4_extract.sql`)
- Q1 `mart.v_fx_daily`
- Q2 `mart.v_monthly_inputs`
- Q3 `mart.v_rbz_events`
- Q4 readiness profile

### KNIME workflow (Analytics Platform 5.x)
| # | Node | Configuration | Purpose |
|---|---|---|---|
| 1 | PostgreSQL Connector | db `umfdop`, login role with `bi_reader` | Connection |
| 2 | DB Query Reader (x3) | Q1, Q2 and Q3 from `05_agent4_extract.sql` | Extract |
| 3 | String Manipulation | `period = substr(date_key,0,7)` | Month key |
| 4 | Joiner | v_fx_daily left-join v_monthly_inputs on period | Attach monthly rates |
| 5 | Lag Column | `units_per_usd`, lag 1 | Previous day's rate |
| 6 | Math Formula | `fx_factor = lag/units_per_usd`; `ln_g = ln(1 + r/100*dm/365)/dm` per instrument | Daily factors |
| 7 | Moving Aggregation | Cumulative sum of `ln(fx_factor)` and `ln_g` | Log wealth |
| 8 | Math Formula | `wealth_usd = exp(cum_ln_g + cum_ln_fx)` | USD-adjusted index |
| 9 | Row Filter + GroupBy | Month ends; first/last per sub-period | BQ1 and BQ2 tables |
| 10 | Python Script | `monte_carlo` from agent4_templates.py and the rolling-window block | BQ3 Monte Carlo, BQ4 |
| 11 | CSV Writer | `results/` | Output |

### Python
`agent4_zig_returns.py` produces the returns, sub-periods, scenarios, rolling windows and metrics. `agent4_findings.py` builds the findings and the hypothesis verdicts from the result tables, so every number traces to a file. Both were tested in the sandbox.

## 3. Results and validation
| Check | Value | Expected | Verdict |
|---|---|---|---|
| ZiG cash USD return, daily engine vs independent SQL | -49.390405% | -49.390405% | PASS |
| Brief tie-out: ZiG cash to 2026-11-12 | -48.9% | -48.9% | PASS |
| Brief tie-out: 2026 YTD to 12 Nov | -2.1% | -2.1% | PASS |
| Required-yield identity (1+y)^T (1-e)^T (1-c) = (1+r)^T (replaces the brief's required-yield tie-out, which used the same reciprocal error) | 2e-16 | 0 | PASS |
| Bridge check rows (effects minus total) | 0 | 0 | PASS |
| Monthly returns compound to the cumulative index | 5e-14 | 0 | PASS |
| A full month earns r × days/365 | 1.140822% | 1.140822% | PASS |
| Monte Carlo | 10,000 runs, seed 42, inputs from 21 analysed months | Template standard | PASS |
| Required yield with e = c = 0 equals the T-bill rate | 4.149215% | 4.149215% | PASS |

Hypotheses (from the brief):
| Hypothesis | Result | Verdict |
|---|---|---|
| H1: every launch-dated ZiG product is worse than -30% USD-adjusted since launch | The best product (top-rate 3-month index) reached -36.1% (-36.7% with locked terms) | Supported |
| H1b: 3-month deposits are positive from Jan 2025 | Min rate +8.3%, max rate +16.1% | Supported |
| H2: in 2026, the 3-month max and ZiGDTDF beat USD by 3 pp or more; savings do not | 3-month max +4.4 pp; ZiGDTDF +8.8 pp; savings -3.6 pp | Supported (ZiGDTDF window short) |
| H3: required yield about 6.7% / about 12% (12-month converter) / about 30% (3-month converter) | 6.95% / 12.43% / 30.63% (corrected; first reported 6.9% / 12.4% / 30.5%) | Supported |
| H4: fewer than 20% of 90-day windows since 2025 lose money | ZiG cash 40.7%, savings max 33.2%, 3-month min 27.0%, 3-month max 17.3% (19.3% with locked terms), ZiGDTDF 0% | Rejected for cash and savings; supported only for the 3-month max and ZiGDTDF |

## 4. Findings
| Question | What we found | How sure | What it means | Limits |
|---|---|---|---|---|
| BQ1 | From 2024-04-08 to 2026-09-30, ZiG cash lost **49.4%** of its USD value. Savings lost 44.0-44.3%; 3-month deposits lost 36.1% (max rate) to 40.9% (min rate). The FX effect is -68.1 log points for every product; interest offsets at most 23.3. In real ZWG terms, cash lost 49.6% (May 2024 to Sep 2026). | High (exact; identities hold) | Since launch, no ZiG product available at launch preserved USD value. The 27 Sep 2024 devaluation (-42.6% in one day; -44.3% in September 2024) dominates everything. | Official mid rate; quoted maximum rates; no taxes, fees or IMTT |
| BQ1 | Since Jan 2025 the picture flips: the 3-month return index gained +16.1% (max rate; +14.8% with locked terms) and +8.3% (min rate; +7.9% locked) USD-adjusted over 21 months; ZiG cash lost 3.7%. | High | A post-2025 holder of term ZiG did better than USD cash. | The window starts after the devaluation |
| BQ1 | USD cash held in Zimbabwe also lost 15.3% in real terms (ZIMSTAT USD CPI); the T-bill lost 6.1% in real terms. | High | "Hold USD" is not a free benchmark either. | Zimbabwe USD CPI basket |
| BQ2 | Annualised spread vs the T-bill: pre-devaluation, 3-month max -6.3 pp. 2025: 3-month max +5.2 pp; savings max -0.9 pp. 2026 to September: 3-month max +4.4 pp (+3.6 locked); ZiGDTDF +8.8 pp; savings max -3.6 pp; ZiG cash -7.9 pp. | High (ZiGDTDF: low, 118 days) | Term ZiG instruments beat USD in 2025-26; savings products do not. The new yield curve is competing against savings rates that lose to USD. | Before conversion costs |
| BQ2 | ZiG depreciation in 2026 was 3.0% to 30 Sep (this is Bloomberg's "almost 3%") and 2.1% to 12 Nov. | High | Resolves the brief's open question: the Bloomberg figure is measured to end-September. | RBZ mid |
| BQ3 | To match the T-bill at the 2026 depreciation pace (effective annual): **6.95%** for holders who already earn ZiG; **12.43%** for a USD holder converting for 12 months; **30.63%** for 3 months. Effective rates on offer: ZiGDTDF 11.44% and 3-month max 14.62% clear the first hurdle; only the 3-month max clears the 12-month converter hurdle; savings (4.81%) clear neither. | Medium (assumes the 2026 depreciation pace) | The curve can win existing ZiG balances at about 7-11%. It cannot pull in USD for short tenors while the RBZ round trip costs 4.9%. | RBZ interbank spread; retail spreads are likely wider; IMTT excluded |
| BQ3 | Simulation (fitted calm-month model): ZiGDTDF at 10.98% ends ahead of the T-bill over 12 months in **80.0%** of paths without conversion and 46.4% with it; median ending wealth +4.8% and -0.5% relative to the T-bill. These are shares of model paths, not real-world probabilities. A repeat of the Sep 2024 devaluation leaves ending wealth **38.6%** below the T-bill (40.2 percentage points). | Low-Medium (normal FX moves fitted to 21 calm months) | The ZiG return premium is compensation for jump risk that the calm-regime numbers do not show. | No jump process; see the stress row |
| BQ4 | Since 2025, 90-day holdings lost USD value in 40.7% of windows for ZiG cash, 33.2% for savings max, 27.0% for 3-month min, 17.3% for 3-month max and 0% for ZiGDTDF (29 windows). The worst 90-day loss since 2025 was -6.0% (cash, windows starting April 2026; May 2026 moved -5.9%). Over the full window the worst was -52.0% and the maximum drawdown -53.9%. | High | Only the higher-yield term products keep the loss frequency under 1 in 5. | Overlapping windows; ZiGDTDF sample short |

## 5. Result tables for Agent 5 (`results/`)
| File | Rows | Content |
|---|---|---|
| result_returns_monthly.csv | 214 | BQ1: month × instrument; rate, nominal, FX effect, USD-adjusted, real, USD real, cumulative index |
| result_bridge.csv | 30 | BQ1: interest, FX, total and check row per ZiG product |
| result_subperiods.csv | 45 | BQ2: sub-period × instrument; return, annualised, T-bill, spreads |
| result_scenarios.csv | 51 | BQ3: required-yield grid (32), effective rates on offer (3), simulation of relative wealth (12), stress (2) and stress payback (2); p5/p50/p95 |
| result_sensitivity.csv | 22 | Robustness: 3-month index vs locked 3-month terms, by sub-period, plus the 90-day loss share |
| result_rolling.csv | 40 | BQ4: loss frequency, share below the T-bill, worst window, drawdown |
| result_metrics.csv | 32 | Validation checks (VAL), key returns vs the T-bill baseline (BQ2), hypothesis verdicts. In this file, `beats_baseline` means check passed / hypothesis supported |
| result_findings.csv | 21 | Findings with number, unit, confidence and limits |
| run_parameters.csv | 9 | e, c, r, Monte Carlo parameters, ZiGDTDF rate and start |

## 6. Revision, 2026-11-14 (external review)
An external review of the published report raised five points; all were confirmed and corrected in `agent4_zig_returns.py` and `agent4_findings.py`, and the run was repeated (all validation checks pass).
1. Required yield: the formula used (1+e) while e is the annual loss in the ZiG's USD value. Corrected to 1+y = (1+r)/((1-e)(1-c)^(1/T)): 6.95 / 12.43 / 18.20 / 30.63% (was 6.88 / 12.36 / 18.12 / 30.54%); 15.72% at 10% depreciation (was 14.56%). Rates on offer are now converted to effective annual (14.62 / 11.44 / 4.81%).
2. Stress: now ending wealth relative to the T-bill, (1+R_zig)/(1+R_tbill)-1: -38.59% ZiGDTDF, -36.84% 3-month max (was a -40.45 pp difference). Payback from compounded relative growth: 6.0 and 11.1 years.
3. Simulation: holdings compound at each product's term (was simple interest over the hold); output is relative wealth and the share of paths behind the T-bill, described as conditional on the model. ZiGDTDF 12-month, no conversion: 80.0% of paths ahead (was 77.9%).
4. The 3-month series is labelled a return index; result_sensitivity.csv adds locked 3-month terms (since 2025 +14.83% vs +16.08%; 2026 spread +3.63 vs +4.39 pp; 90-day loss share 19.34% vs 17.34%).
5. Wording qualified: products available at launch; tested horizons rather than a universal threshold; ZiGDTDF 10.98% = weighted average of accepted bids (10-25%), reinvested after the first maturity; savings min > max in Dec 2024, Jan 2025 and May 2026 disclosed; loss windows overlap.

Pipeline: Step 4 of 5 - Agent 4 - Revised 2026-11-14 after external review
