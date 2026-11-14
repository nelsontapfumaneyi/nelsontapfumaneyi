# BRD - Does holding ZiG pay? (UMFDOP 2026-11-13)

Nov 13, 2026 · Nelson Mwerenga

## Executive summary

Holding ZiG cash from launch (2024-04-08) to 2026-09-30 lost 49.4% of its USD value. The 27 Sep 2024 devaluation (13.9987 to 24.3902 ZWG per USD, a 42.6% loss) caused most of it.

Since January 2025 the result has reversed for term deposits. A return index at the best-quoted ZiG 3-month deposit rate gained +16.1% in USD terms over 21 months (8.9% a year; +14.8% if each 3-month term locks its rate), against 4.1% a year on the US 3-month T-bill. ZiG savings accounts and idle ZiG cash still trailed USD.

The decision rule is a required ZiG yield. A holder who already earns ZiG needs an effective 6.95% a year to match the T-bill at the 2026 depreciation pace. A USD holder converting for 12 months needs 12.43%, and for 3 months 30.63%, because the RBZ bid-ask round trip costs 4.9%.

The tail risk is a repeat devaluation. A 42.6% move inside a 12-month ZiGDTDF hold would leave ending wealth 38.6% below the T-bill alternative.

All figures are USD-adjusted, before tax and before bank fees, from the UMFDOP run of 2026-11-13 (result_findings.csv rows 0, 4, 12, 13, 14, 16), revised on 2026-11-14 after an external review corrected the required-yield formula and the stress-test units.

## Business problem

The RBZ wants ZiG balances held as savings, not just spent, and is building a short-term ZiG yield curve to get there. Holders will only keep ZiG if it earns more than USD after depreciation, inflation and conversion costs.

The trigger was the RBZ Governor's interview of 12 Nov 2026 ([Bloomberg](https://www.bloomberg.com/news/articles/2026-11-13/-usd-zwg-zimbabwe-moves-to-rebuild-local-bond-market-after-currency-turmoil)), where he set the aim of making ZiG a store of value. The first instrument, the ZiGDTDF 90-day bill, cleared at 10.98% on 4 Jun 2026 ([Herald](https://www.heraldonline.co.zw/rbz-moves-to-anchor-zig-as-store-of-value/)).

The mechanism is one formula: USD-adjusted return = (1 + ZiG yield) × (start rate / end rate) − 1. A higher curve lifts the yield; depreciation, the bid-ask spread and IMTT pull it down.

The stakes are material. ZiG deposits were about USD 1.07bn in Jun 2026, so each 1 pp of USD-adjusted return is worth about USD 10.7m a year to depositors (brief F12, derived).

## Stakeholders

Six groups act on this answer; corporate treasurers are the primary user of the dashboard.

| Stakeholder | Decision they make | What they use from this work |
| --- | --- | --- |
| Corporate treasurers | Hold surplus ZiG as cash, deposit or ZiGDTDF, or convert to USD | Required-yield table, loss-window risk, 2026 spreads |
| Pension funds and insurers | Allocate prescribed-asset ZiG holdings | Since-2025 returns by product, devaluation stress |
| Commercial banks | Price ZiG savings and term deposits; bid at ZiGDTDF auctions | Savings shortfall vs T-bill, gap to the 5% RBZ minimum |
| Asset managers | Design ZiG money-market funds for small investors | Product ranking, conversion-cost drag by holding period |
| Treasury (MoFED) | Revive the domestic debt market | Yield needed to attract USD holders |
| RBZ | Set ZiGDTDF rates and deposit-rate floors | Required yield, conversion-spread effect, holder risk profile |

## Scope

The analysis covers 2024-04-08 to 2026-09-30 for returns and runs to 2026-11-13 for exchange rates and the forward break-even.

| | In scope | Out of scope |
| --- | --- | --- |
| Instruments | ZiG cash; savings (min and max quoted); 3-month deposit (min and max); ZiGDTDF 90-day; USD cash; US 3-month T-bill | NNCDs; ZiG bonds; equities; bank USD deposit rates (no RBZ series) |
| Exchange rate | RBZ official interbank mid, bid and ask, daily | Parallel-market rate (no reliable series; sensitivity only) |
| Inflation | ZIMSTAT ZWG and USD CPI; US CPI (CPIAUCSL) | Weighted CPI as a deflator |
| Costs | RBZ bid-ask round trip (4.88%) | IMTT (2% on FX transactions); withholding tax on interest; bank fees |
| Methods | Monthly and cumulative returns, sub-period spreads, log bridge, required yield, Monte Carlo, rolling windows | Volume-weighted bank rates; forecasts of the ZiG rate |
| Outputs | Browser dashboard, Power BI report, Tableau story, this BRD, case study | Investment advice for any named client |

## Answers to the business questions

Three of four hypotheses held; the fourth (fewer than 20% of 90-day windows lose money since 2025) held only for the 3-month deposit at the top quoted rate.

| ID | Question | Answer | Key figure | Hypothesis | Confidence |
| --- | --- | --- | --- | --- | --- |
| BQ1 | What did each ZiG product return since launch, nominal, real and in USD? | Every ZiG product available at launch lost over 30% in USD; the FX effect (−68.1 log pts) swamped interest (at most +23 log pts). Since Jan 2025 interest-bearing products turned positive. | Cash −49.39%; top-rate 3-month index −36.09%; that index since Jan 2025 +16.08% (+14.83% with locked terms); ZiG cash real −49.56% | H1 and H1b supported | High |
| BQ2 | What spread did ZiG products earn over the US T-bill by sub-period? | Every product trailed before the devaluation. In 2025 and 2026 the 3-month index at the top rate beat the T-bill; savings did not. | 2026 to Sep: 3-month max +4.39 pp (+3.63 with locked terms); ZiGDTDF +8.76 pp (118 days); savings max −3.56 pp. 2025: 3-month max +5.18 pp | H2 supported | Medium (2026 is 9 months) |
| BQ3 | What ZiG yield beats USD, given depreciation, holding period and conversion cost? | Holders already earning ZiG need an effective 6.95%; converting USD holders need 12.43% for 12 months and 30.63% for 3 months. | ZiGDTDF ends ahead of the T-bill in 80.0% of simulated 12-month paths (fitted calm-month model, not a real-world probability); a repeat devaluation leaves ending wealth 38.59% below the T-bill | Supported (brief estimate 6.7 / 12.2 / 30.5%) | Medium |
| BQ4 | How often does a 90-day ZiG holding lose USD value, and how big is the tail? | Losses remain common for cash and savings since 2025, but are shallow; the full-window tail is the devaluation. | Share of losing 90-day windows since 2025: cash 40.69%, savings max 33.21%, 3-month min 27.01%, 3-month max 17.34%, ZiGDTDF 0% (29 windows). Worst since 2025: −5.96% (cash); worst overall: −52.01% | H4 rejected for cash, savings and 3-month min; supported for 3-month max | High |

Sources: result_findings.csv rows 0–20, result_metrics.csv rows 26–31, result_rolling.csv.

## Requirements

All twelve requirements are met. The browser dashboard and the Tableau story meet eleven each; FR-06 (return basis switch) is built in Power BI.

| ID | Requirement | Type | Priority | Met by |
| --- | --- | --- | --- | --- |
| FR-01 | Show the USD-adjusted return since launch for each ZiG product and the USD benchmarks | Functional | Must | Summary cards; value-of-holding line |
| FR-02 | Show the daily RBZ ZWG per USD rate with the 27 Sep 2024 devaluation marked | Functional | Must | FX line |
| FR-03 | Compare each product's annualised return with the US 3-month T-bill by sub-period (pp) | Functional | Must | Spread chart (P1, P3, P4) |
| FR-04 | Show the required ZiG yield by holding period (3, 6, 12 months) against current quoted rates | Functional | Must | Break-even chart with rate lines |
| FR-05 | Show the share of 90-day windows with a USD loss since 2025, by product | Functional | Must | Loss-window chart |
| FR-06 | Let the user switch return basis: USD-adjusted, USD-adjusted real, ZiG nominal, ZiG real | Functional | Should | Return basis slicer (Power BI, page FX and value) |
| FR-07 | List every finding with its number, unit, confidence and limits | Functional | Must | Findings table |
| NFR-01 | Every displayed figure traces to a result file and row | Traceability | Must | Tie-out table; source footers |
| NFR-02 | Exchange rates come from the RBZ official rate for each date; no hard-coded rates | Data quality | Must | `mart.v_fx_daily` |
| NFR-03 | Money columns carry an explicit currency (USD or ZWG); dates are ISO | Data standard | Must | DDL CHECK constraints |
| NFR-04 | BI tools read through a read-only role | Security | Must | `bi_reader` role on `mart` |
| NFR-05 | Only public data is published to Tableau Public | Confidentiality | Must | Sources are RBZ, ZIMSTAT, FRED, IMF; no client data |

## KPI definitions

All returns are measured in USD at the RBZ official mid rate unless the KPI says otherwise. S is ZWG per USD, r is the quoted annual ZiG rate and d is days.

```latex
R_{USD} = (1 + R_{ZWG}) \times \frac{S_{start}}{S_{end}} - 1
```

```latex
y_{required} = \frac{1 + r_{USD}}{(1 - e)(1 - c)^{1/T}} - 1
```

| KPI | Definition | Unit | Source |
| --- | --- | --- | --- |
| USD-adjusted return | ZiG return converted at the start and end RBZ mid rates, per the first formula | % | result_returns_monthly, result_subperiods |
| ZiG nominal return | Interest accrued daily at (1 + r × dm/365)^(1/dm) − 1, compounding monthly | % | result_returns_monthly |
| Real return | Nominal ZiG return deflated by ZIMSTAT ZWG CPI (Apr 2024 = 100) | % | result_returns_monthly |
| Cumulative USD index | Value of USD 100 placed on 2024-04-08, tracked monthly | index | result_returns_monthly |
| Spread vs T-bill | Annualised USD-adjusted return minus the annualised T-bill return over the same dates | pp p.a. | result_subperiods |
| T-bill yield | FRED DTB3 discount rate converted to bond-equivalent yield: 365d / (360 − 91d) | % p.a. | stg / core us_benchmark |
| Required ZiG yield | Second formula, effective annual: r_USD = T-bill yield (4.15%), e = annual loss in the ZiG's USD value (2.62%), c = round-trip cost, T = years held; rates on offer are converted to effective annual before comparison | % p.a. | result_scenarios |
| Round-trip conversion cost | 1 − bid / ask on the RBZ interbank rate; 4.88% at the latest date | % | run_parameters |
| Interest and FX effects | Log bridge: ln(1 + R_USD) = ln(1 + R_ZWG) + ln(S_start / S_end) | log pts | result_bridge |
| Loss-window share | Share of overlapping 30- or 90-day windows ending with a USD-adjusted loss | % of windows | result_rolling |
| Maximum drawdown | Largest peak-to-trough fall in the daily USD value | % | result_rolling |
| Share of simulated paths ahead of the T-bill | Share of 10,000 paths (seed 42; normal monthly log FX, μ = −0.0018, σ = 0.0160; each product compounds at its term) where the ZiG holding ends ahead; conditional on the model, not a real-world probability | % | result_scenarios |

## Data sources and lineage

Datasets D1 to D7 feed seven clean files, seven core tables and seven `mart` views; every dashboard visual reads a result file built from those views. Rows below are clean rows out, with rejects in brackets.

| ID | Dataset | Publisher | Clean file (rows) | Core table | Mart view |
| --- | --- | --- | --- | --- | --- |
| D1 + D7 | Daily interbank rate, bid and ask ([RBZ](https://www.rbz.co.zw/documents/Exchange_Rates/2026/November/RATES_13_NOVEMBER_2026.pdf)); 54 gap days filled from [First Capital Bank](https://www.firstcapitalbank.co.zw/wp-content/uploads/2025/12/Exchange-Rates-31-December-2025.pdf) | RBZ; FCB | fx_usd_zwg_daily (647 [1]) | core.fx_rate (temporal key) | v_fx_daily, v_fx_monthly |
| D2 | Monthly ZWE exchange rate, average and end of period | IMF (SDMX API) | fx_imf_monthly (60 [2]) | core.fact_fx_imf_monthly | v_fx_monthly (reconciliation) |
| D3 | Table 8.2 ZiG deposit rates ([xlsx](https://www.rbz.co.zw/documents/statistics/2026/August/Bank-Deposits-rates.xlsx)) | RBZ | deposit_rates_monthly (69 [0]) | core.fact_deposit_rate_monthly | v_deposit_rates_monthly |
| D4 | CPI, ZWG and USD ([Oct 2026 ZWG release](https://www.zimstat.co.zw/wp-content/uploads/Macro/Prices/CPI/2026/CPI_ZWG_10_2026.pdf)) | ZIMSTAT | cpi_observations (214), cpi_monthly (93, 4 imputed) | core.fact_cpi_observation, core.fact_cpi_monthly | v_cpi_monthly |
| D5 | DTB3, CPIAUCSL, SOFR ([FRED](https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTB3)) | Federal Reserve Bank of St. Louis | us_benchmarks (1,339 [59 blank holidays]) | core.fact_us_benchmark | v_us_benchmarks_monthly |
| D6 | ZiGDTDF auctions, taps, policy rates, deposit floors, launch and devaluation | RBZ via [Herald](https://www.heraldonline.co.zw/rbz-moves-to-anchor-zig-as-store-of-value/) and [NewsDay](https://www.newsday.co.zw/local-news/article/200056702/rbz-mops-up-liquidity-with-new-zig-bills) | rbz_events (12 [0]) | core.fact_rbz_event | v_rbz_events |
| D8 | Monetary aggregates; depository corporations survey | RBZ | Not loaded (context for the deposit-base estimate) | none | none |

All monthly inputs join in `mart.v_monthly_inputs`, which the Agent 4 extract (`05_agent4_extract.sql`) reads. Reconciliations: FCB equals RBZ on all 7 overlap days; the IMF month-end matches RBZ in 26 of 27 months (Feb 2026 differs by 0.0012%).

## Data model

PostgreSQL 18 database `umfdop` with four schemas: `stg` (raw loads), `core` (five dimensions, one temporal rate table, six facts), `mart` (seven read-only views) and `audit` (load log). Every fact table references `dim_date` and `dim_source`; facts that hold money or rates also reference `dim_currency`.

| Table | Grain | Key | Also references |
| --- | --- | --- | --- |
| core.dim_date | One calendar day | date_key | |
| core.dim_currency | One ISO currency (USD, ZWG) | currency_code (3 capitals, CHECK) | |
| core.dim_source | One publisher | source_id | |
| core.dim_price_index | One CPI series (ZWG, USD, Weighted, US) | index_code | dim_currency, dim_source |
| core.dim_series | One US benchmark series (DTB3, SOFR, CPIAUCSL) | series_id | dim_currency, dim_source |
| core.fx_rate | One rate type per currency over a validity range | (currency_code, rate_type, valid_at WITHOUT OVERLAPS) | dim_currency, dim_source |
| core.fact_fx_imf_monthly | Month × average or end of period | UNIQUE (period_start, transformation) | dim_date |
| core.fact_deposit_rate_monthly | Month × currency (savings and 3-month min and max) | UNIQUE (period_start, currency_code) | dim_date |
| core.fact_cpi_monthly | CPI series × month (imputed flag) | UNIQUE (index_code, period_start) | dim_price_index, dim_date |
| core.fact_cpi_observation | CPI series × month × release (revision history) | UNIQUE (index_code, period_start, published_in, role) | dim_price_index, dim_date |
| core.fact_us_benchmark | Series × observation date | UNIQUE (series_id, obs_date) | dim_series, dim_date |
| core.fact_rbz_event | Event date × type × instrument × tenor × currency | UNIQUE NULLS NOT DISTINCT on those five | dim_date |

The temporal key on `fx_rate` makes overlapping rate periods impossible, so a date can never carry two official rates. `mart.v_fx_daily` expands it to one row per calendar day and flags carried-forward weekend and holiday rates. Validation: 40 of 40 checks and negative tests pass (`03_validate.sql`, `04_negative_tests.sql`).

## Risks and controls

The largest risk to the conclusions is cost: excluded taxes and wider retail spreads make the converter case worse than shown. The calculations themselves are controlled: the return engine matches an independent SQL calculation to the last decimal (result_metrics row 0).

| Risk | Effect on results | Control in place | Residual |
| --- | --- | --- | --- |
| IMTT (2%), withholding tax on interest and bank fees not modelled | USD-adjusted returns and spreads are overstated, most for short holds | Stated on every finding; required-yield formula takes any cost c | High for converters |
| Retail FX spreads wider than the RBZ interbank bid-ask (4.88%) | Required yields for converters are understated | Scenario rows by conversion case | Medium |
| Bank deposit rates are quoted min and max ranges, not volume-weighted | True average returns probably sit between the min and max lines, but Table 8.2 shows savings minimums above maximums in Dec 2024, Jan 2025 and May 2026 | Both bounds reported for savings and 3-month deposits; anomalies flagged; the 3-month series is a return index, with a locked-term check in result_sensitivity.csv | Medium |
| ZiGDTDF history is 118 days; 10.98% (weighted average of accepted bids, range 10–25%) held constant and reinvested after the first maturity | 2026 ZiGDTDF spread (+8.76 pp) has low confidence | Confidence marked Low; later auction results listed as an open question | Medium |
| Monte Carlo assumes normal monthly FX moves fitted to 21 calm months | The 80.0% share of paths is conditional on the model and ignores devaluation jumps | Separate stress row: a repeat of the −42.6% move leaves ending wealth 38.59% below the T-bill | Medium |
| Parallel-market rate excluded | Realisable USD value may be lower than the official-rate result | Scope note; sensitivity offered (premium 16–21%) | Medium |
| 4 CPI months imputed from month-on-month rates | Real returns for those months are estimates | is_imputed flag in core and mart | Low |
| 33 business days with no RBZ or FCB rate (25 are public holidays) | Daily returns use the last official rate | Carried-forward flag in `mart.v_fx_daily`; FCB = RBZ on 7 of 7 overlap days | Low |
| IMF month-end differs from RBZ in Feb 2026 (0.0012%) | None material | Validation V10 with 0.01% tolerance; V10b pins the exception | Low |
| Single-source facts (Governor's aim; RBZ minimum deposit rates) | Context and the 5% savings floor may change | Register status `single_source` (MAC-012) pending the MPS PDF | Low |

## Recommendations

The analyst's recommendations follow from the results; they are decision rules, not investment advice for any named client.

1. **Treasurers already holding ZiG:** do not leave surplus ZiG idle or in savings accounts. Place it where the effective yield clears 6.95% a year, which in Sep 2026 meant the upper end of 3-month deposits (13.88% quoted, 14.62% effective) or ZiGDTDF (10.98% quoted, 11.44% effective).
2. **USD holders considering conversion:** at today's rates, of the holds tested only a 12-month conversion at the top 3-month rate (14.62% effective) clears the 12.43% hurdle. No current ZiG product clears the 30.63% hurdle for a 3-month hold.
3. **Size the devaluation tail before committing:** a repeat of the 27 Sep 2024 move inside a 12-month hold leaves ZiGDTDF ending wealth 38.59% below the T-bill alternative. Cap ZiG exposure at what the business can lose on that scale.
4. **Banks:** the top quoted savings rate (4.71%) sits below the 5% RBZ savings minimum reported for 2026 and trailed the T-bill by 3.56 pp. Pricing savings at or above the floor is the cheapest way to retain ZiG balances.
5. **RBZ and Treasury:** the conversion spread matters more than the curve for short holds. Halving the 4.88% round trip cuts the 3-month hurdle from 30.63% to 18.05% and the 12-month hurdle from 12.43% to 9.62% (sandbox calculation, run_parameters).
6. **Re-run monthly:** refresh rates, CPI and ZiGDTDF auction results, and re-check the 6.95% already-ZiG threshold against the latest depreciation pace.

## Acceptance criteria

All eight criteria are met. The Power BI report and the Tableau workbook both tie out to the Agent 4 results with zero difference on all 10 KPIs (2026-11-13).

| ID | Criterion | Evidence | Status |
| --- | --- | --- | --- |
| AC-01 | All database validation queries and negative tests pass | 40 of 40 (`03_validate.sql`, `04_negative_tests.sql`), approved at Step 3 | Met |
| AC-02 | Return engine matches an independent SQL calculation and the brief's tie-outs | result_metrics rows 0–7, all within rounding; the brief's required-yield tie-outs were replaced by an identity check after the 2026-11-14 correction | Met |
| AC-03 | Browser dashboard KPI cards equal result_findings (difference 0) | 8 of 8 cards read from the live page on 2026-11-13; on 2026-11-14 the findings and scenarios files were replaced and are byte-identical to the revised results (SHA-256 checked), so the two changed cards read 6.95 and 12.43 | Met |
| AC-04 | Browser dashboard passes its automated layout and data check | Check passed at 2026-11-13 20:33 UTC; the page wording was edited on 2026-11-14, so the check reruns the next time the page is opened | Met |
| AC-05 | Power BI build ties out on all 10 tie-out KPIs | 10 of 10 read from the built report `ZiG Returns.pbip` (Summary and FX pages), difference 0; re-tied 2026-11-14 after refresh (rows 12 and 13 read 6.95 and 12.43) | Met |
| AC-06 | Tableau story ties out on all 10 tie-out KPIs | 10 of 10 read from `ZiG Returns.twb` (sheets T1 to T3), difference 0; re-tied 2026-11-14 (T1 rows 12 and 13 read 6.95 and 12.43); not yet published to Tableau Public | Met |
| AC-07 | Only public data is published | Sources are RBZ, ZIMSTAT, IMF, FRED and press reports; no client data | Met |
| AC-08 | Every number in this BRD cites a result file and row or a register fact | Citations in each section | Met |

## Open questions

Seven gaps would tighten the answers; the first two change the converter case most.

- [ ] Which withholding tax rate applies to ZiG interest for each holder type? It is not modelled; add it as a register row after review by a registered tax practitioner.
- [ ] How should IMTT (2% on FX transactions, register TAX-008) enter the converter case: once per leg or once per round trip?
- [ ] What were the ZiGDTDF and NNCD auction results after June 2026? RBZ notices or a bank treasury desk could supply them.
- [ ] What USD deposit rates do commercial banks pay? No RBZ series was found; the T-bill and RBZ USD minimums stand in.
- [ ] How much wider than the RBZ interbank bid-ask are retail bank FX spreads?
- [ ] Is a reliable parallel-market rate series available for a sensitivity run (reported premium 16–21%)?
- [ ] Do the RBZ minimum deposit rates (5% ZiG savings, 7.5% ZiG time) appear in the 2026 Monetary Policy Statement PDF (register MAC-012)?

## Sources

- [RBZ daily interbank rates, 13 Nov 2026](https://www.rbz.co.zw/documents/Exchange_Rates/2026/November/RATES_13_NOVEMBER_2026.pdf), [8 Apr 2024](https://www.rbz.co.zw/documents/Exchange_Rates/2024/April/RATES_8_APRIL_2024.pdf) and [27 Sep 2024](https://www.rbz.co.zw/documents/Exchange_Rates/2024/September/RATES_27_SEPTEMBER_2024.pdf)
- [RBZ Table 8.2 bank deposit rates](https://www.rbz.co.zw/documents/statistics/2026/August/Bank-Deposits-rates.xlsx)
- [ZIMSTAT CPI ZWG, Oct 2026](https://www.zimstat.co.zw/wp-content/uploads/Macro/Prices/CPI/2026/CPI_ZWG_10_2026.pdf)
- [FRED DTB3](https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTB3)
- [IMF staff report, SMP first review (2026)](https://www.imf.org/-/media/files/publications/cr/2026/english/1zweea2026002.pdf)
- [First Capital Bank rates, 31 Dec 2025](https://www.firstcapitalbank.co.zw/wp-content/uploads/2025/12/Exchange-Rates-31-December-2025.pdf)
- [Bloomberg, 13 Nov 2026: Zimbabwe moves to rebuild local bond market](https://www.bloomberg.com/news/articles/2026-11-13/-usd-zwg-zimbabwe-moves-to-rebuild-local-bond-market-after-currency-turmoil)
- [Herald: RBZ moves to anchor ZiG as store of value](https://www.heraldonline.co.zw/rbz-moves-to-anchor-zig-as-store-of-value/); [Herald: 2026 monetary policy milestones](https://www.heraldonline.co.zw/single-digit-inflation-stable-exchange-rate-mark-2026-monetary-policy-milestones/); [Herald: policy rate cut to 27.5%](https://www.heraldonline.co.zw/rbz-cuts-policy-rate-to-275pc/)
- [NewsDay: RBZ mops up liquidity with new ZiG bills](https://www.newsday.co.zw/local-news/article/200056702/rbz-mops-up-liquidity-with-new-zig-bills)
- Pipeline files in this repository: `docs/` (brief and agent packs), `results/` (result tables), `sql/`, `scripts/`
