# Agent 1 - Data Request & Context Brief
Date: 2026-11-13   Topic: Does holding ZiG pay? Real and USD-adjusted returns on ZiG since April 2024   Industry: Banking and finance (treasury, pension funds, capital markets)

## 1. Trigger
- Agent 1 Feed of 2026-11-13, candidate A, built on item 1 (RBZ plans a short-term ZiG yield curve). Items 3 (RBZ rate) and 6 to 8 were used as context.
- Kept: items 1 and 3. Dropped: 6 items (2, 4, 5, 6, 7, 8). They are not relevant to this question. Items 2 (growth) and 6/7 (gold) stay in the feed for candidates B and C.

## 2. Verified facts
| # | Fact | Value | Source (URL) | As of | Status |
|---|---|---|---|---|---|
| F1 | Governor's stated aim: make the ZiG "a store of value" and develop a short-term ZiG yield curve | Interview in Johannesburg, Thu 12 Nov | https://www.bloomberg.com/news/articles/2026-11-13/-usd-zwg-zimbabwe-moves-to-rebuild-local-bond-market-after-currency-turmoil | 2026-11-13 | single_source (Bloomberg; Streamline is a rewrite of it) |
| F2 | RBZ official interbank rate, USD | 12 Nov: bid 25.8762, ask 27.2032, mid 26.5397 ZWG. 13 Nov: bid 25.9214, ask 27.2508, mid 26.5861 | https://www.rbz.co.zw/documents/Exchange_Rates/2026/November/RATES_12_NOVEMBER_2026.pdf ; .../RATES_13_NOVEMBER_2026.pdf | 2026-11-13 | verified (primary) |
| F3 | ZiG launch rate | Mid 13.5616 ZiG per USD on 8 Apr 2024 (bid 13.2226, ask 13.9006) | https://www.rbz.co.zw/documents/Exchange_Rates/2024/April/RATES_8_APRIL_2024.pdf | 2024-04-08 | verified (primary) |
| F4 | ZiG close 2025 (YTD baseline) | 25.9807. RBZ has no file for 30-31 Dec 2025, so this comes from First Capital Bank's republished interbank rate and the IMF programme rate (25.98) | https://www.firstcapitalbank.co.zw/wp-content/uploads/2025/12/Exchange-Rates-31-December-2025.pdf ; https://www.imf.org/-/media/files/publications/cr/2026/english/1zweea2026002.pdf | 2025-12-31 | verified (IMF + bank) |
| F5 | ZWG CPI (Apr 2024 = 100) | 198.63 Oct 2026; 198.25 Sep 2026; y/y 4.3%; m/m 0.2% | https://www.zimstat.co.zw/wp-content/uploads/Macro/Prices/CPI/2026/CPI_ZWG_10_2026.pdf | 2026-10 | verified (primary) |
| F6 | USD CPI (Jun 2022 = 100); Weighted CPI (Apr 2024 = 100) | USD 126.11 Oct 2026; Weighted 131.32 Sep 2026 | CPI_USD_10_2026.pdf ; CPI_Weighted_09_2026.pdf (same ZIMSTAT folder) | 2026-10 | verified (primary) |
| F7 | Average commercial-bank ZiG deposit rates (RBZ Table 8.2), Sep 2026 | Savings 4.35-4.71%; 3-month 7.88-13.88% (series Apr 2024 to Sep 2026) | https://www.rbz.co.zw/documents/statistics/2026/August/Bank-Deposits-rates.xlsx | 2026-09 | verified (primary) |
| F8 | RBZ prescribed minimum deposit rates (2026 MPS) | Savings 5% ZiG, 2.5% USD; time 7.5% ZiG, 4% USD | https://www.heraldonline.co.zw/single-digit-inflation-stable-exchange-rate-mark-2026-monetary-policy-milestones/ | 2026-02-27 | single_source |
| F9 | Inaugural ZiGDTDF auction (90-day), 4 Jun 2026 | Offer ZiG 500m; bids 391.6m; allotted 331.6m; weighted average rate 10.98% | https://www.heraldonline.co.zw/rbz-moves-to-anchor-zig-as-store-of-value/ ; IMF staff report (ZiG 330m at about 11%; ZiG 110m at 8% for 30 days) | 2026-06 | verified |
| F10 | ZiGDTDF tap offers | 30/60/90 days at 8/9/11% p.a. | https://www.newsday.co.zw/local-news/article/200056702/rbz-mops-up-liquidity-with-new-zig-bills ; https://equityaxis.net/post/19143/2026/6/rbz-launches-second-round-of-zig-bills | 2026-06 | verified (2 secondary) |
| F11 | Bank Policy Rate | 27.5% from 28 Sep 2026; MPC will keep issuing ZiGDTDF to build a short-term yield curve | https://www.heraldonline.co.zw/rbz-cuts-policy-rate-to-275pc/ | 2026-09-28 | verified (register MAC-001) |
| F12 | Reserves and ZiG deposit cover | USD 1.7bn, about 1.7 months' import cover (end-Jul, Mid-Term MPS). Above USD 2bn, about 2 months (Sep, MPC). Reserves about 1.5x total ZiG deposits (Jun 2026) | https://www.newsday.co.zw/business/article/200059480/rbz-cuts-policy-rate-as-inflation-eases ; https://www.heraldonline.co.zw/rbz-cuts-policy-rate-to-275pc/ ; https://www.heraldonline.co.zw/gold-holdings-surge-past-45-tonnes/ | 2026-09 | Jul: verified; Sep and cover ratio: single_source |
| F13 | US 3-month T-bill (DTB3); SOFR | 4.12% (10 Nov 2026); 3.90% (12 Nov 2026) | https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTB3 ; ...?id=SOFR | 2026-11-12 | verified (primary) |

## 3. Business context
Threat/opportunity: The RBZ wants ZiG balances to be held, not just spent. Holders will only do that if ZiG instruments earn more than USD alternatives after depreciation, inflation and conversion costs. The record is split. Since launch, ZiG cash has lost half its USD value. In 2026, short-term ZiG paper has beaten US T-bills by about 4 pp.
Who is affected: corporate treasurers, pension funds and insurers holding prescribed assets, banks (ZiG deposit pricing and ZiGDTDF bidding), asset managers pooling small investors, and Treasury (domestic debt-market revival).
Mechanism: USD-adjusted return = (1 + ZiG yield) x (start rate / end rate) - 1. The yield curve raises the ZiG yield. Depreciation, the bid-ask spread and IMTT reduce the result.
Horizon: the backward-looking analysis covers Apr 2024 to Nov 2026. The forward-looking break-even covers the first 3 to 12 months of the yield curve (2027 Budget on 19 Nov; next MPC).

First-order size (calculations run in Python in the sandbox):
1. Since launch: ZiG 1 was worth 1/13.5616 = USD 0.07374 on 8 Apr 2024 and 1/26.5397 = USD 0.03768 on 12 Nov 2026. That is a USD loss of 48.9%. ZWG CPI went from 100 to 198.63, so purchasing power fell 49.7%. Both figures are before interest.
2. 2026 YTD (31 Dec 2025 to 12 Nov 2026, 316 days): ZWG per USD rose from 25.9807 to 26.5397 (+2.15%), so the ZiG lost 2.1% against the USD. Annualised, that is 2.49%.
3. USD-adjusted annualised return in 2026 = (1 + r) / 1.0249 - 1:
   - ZiGDTDF 90-day at 11%: 8.3%. Real (ZWG CPI 4.3%): 6.4%.
   - 3-month deposit at 13.88% (max): 11.1%. At 7.88% (min): 5.3%.
   - Savings at 4.71% (max): 2.2%.
   - Benchmark: US 3-month T-bill at 4.12%. Instruments beat it by about +4.2 pp; savings fall short by about -1.9 pp.
4. Break-even depreciation for 11% ZiG paper against the T-bill: 1.11/1.0412 - 1 = 6.6% a year.
5. Conversion cost: the RBZ spread on 12 Nov was (27.2032 - 25.8762)/26.5397 = 5.0% of mid. Converting USD to ZiG at the bid and back at the ask loses 1 - 25.8762/27.2032 = 4.9%. At the 2026 advantage of 11% paper (1.0830/1.0412 = +4.0% a year), that takes ln(1/0.951)/ln(1.0401), about 1.3 years, to recover, before IMTT (2% on FX transactions, register TAX-008).
6. Exposure: ZiG deposits are about USD 1.6bn / 1.5 = USD 1.07bn (Jun 2026, derived from F12). Each 1 pp of USD-adjusted return is worth about USD 10.7m a year to ZiG depositors. If the whole base earned savings-type rates, the cost against T-bills would be about 1.9 pp, or about USD 20m a year. This is an upper bound because the product mix is unknown.

## 4. Business questions
| ID | Question | KPI | Hypothesis |
|---|---|---|---|
| BQ1 | Month by month since Apr 2024, what nominal, real and USD-adjusted return did ZiG cash, ZiG savings, ZiG 3-month deposits (min and max) and ZiGDTDF paper earn? | Monthly and cumulative return (%) by instrument; real return deflated by ZWG CPI | Cumulative USD-adjusted return since launch is worse than -30% for every ZiG product (the 27 Sep 2024 devaluation of -42.6% dominates), but 3-month deposits are positive from Jan 2025 |
| BQ2 | By sub-period (pre-devaluation, devaluation, Oct 2024 to Dec 2025, 2026 YTD), what spread did ZiG products earn over USD alternatives? | Spread (pp) vs US 3m T-bill and vs RBZ minimum USD time-deposit rate (4%) | In 2026, ZiG 3-month max and ZiGDTDF beat USD by 3 pp or more; ZiG savings rates do not |
| BQ3 | What ZiG yield does the new short-term curve need to beat USD at a given expected depreciation e, holding period T (years) and round-trip conversion cost c? | Required yield y = (1 + r_USD)(1 + e) / (1 - c)^(1/T) - 1; break-even depreciation e* | At 2026 values (r = 4.12%, e = 2.5%, c = 4.9%), holders who already earn ZiG need about 6.7%; a USD holder who converts needs about 12% for a 12-month hold and about 30% for a 3-month hold |
| BQ4 | How often does a 30- or 90-day ZiG holding end with a USD-adjusted loss, and how large is the tail? | Share of rolling windows with a loss; worst 90-day loss; max drawdown | Losses cluster in Sep-Oct 2024; since 2025, under 20% of 90-day windows lose money |

**Revision, 2026-11-14 (after an external review):** the BQ3 formula above is right when e is the annual rise in ZiG per US dollar, as in Section 3 (2.49%), so the hypothesis values stand. Agent 4 measured e as the annual loss in the ZiG's US-dollar value (2.62% to 13 Nov), for which the matching form is y = (1 + r_USD) / ((1 - e)(1 - c)^(1/T)) - 1. Using the first form with that e understated the hurdles slightly; Agent 4's corrected results are 6.95%, 12.43% and 30.63% (Agent 4 pack, Section 6). No register fact changes.

## 5. Data discovery log
| Need | Candidates searched (tier) | Chosen | Why | Fallbacks |
|---|---|---|---|---|
| N1 Daily ZiG/USD official rate | RBZ daily PDFs (T1); First Capital Bank daily PDFs (T1 bank, secondary); IMF ER monthly API (T2); AllRatesToday API / Hugging Face archive (T4); Trading Economics (T4, paid) | RBZ daily PDFs | Primary, daily, bid/ask/mid, free | FCB PDFs for gap days (FCB 14 Aug mid 26.5673 matches the RBZ mid reported in the press); IMF ER for monthly reconciliation; AllRatesToday history is paid |
| N2 ZiG deposit rates | RBZ Table 8.2 xlsx (T1); IMF IFS deposit rate (T2, not confirmed for ZWG); Trading Economics deposit rate (T4, RBZ-sourced, paid download); FCB indicative ZWG money-market rates (T1 bank); World Bank WDI FR.INR.DPST (T2, annual, too coarse) | RBZ Table 8.2 | Primary, Excel, monthly, ZiG only from Apr 2024 | Trading Economics; FCB quotes |
| N3 RBZ instrument yields (ZiGDTDF, NNCD) and policy events | RBZ notices (T1, archive page not found); IMF staff report Jul 2026 (T2); Herald, NewsDay, equityaxis (secondary) | Hand-built event table (D6) | No downloadable series exists | Ask RBZ Financial Markets for auction results |
| N4 Inflation | ZIMSTAT CPI PDFs: ZWG, USD, Weighted (T1); IMF CPI dataflow (T2, ZWG basis not confirmed); RBZ Monthly Economic Review (T1); Trading Economics (T4) | ZIMSTAT PDFs | Primary; stable URL pattern, tested | Trading Economics; RBZ MER |
| N5 USD benchmark and USD inflation | FRED DTB3, SOFR, CPIAUCSL (T3, CSV); RBZ prescribed USD minimum rates (T1); FCB USD money-market quotes (T1 bank); ZIMSTAT USD CPI (T1) | FRED DTB3 + CPIAUCSL; ZIMSTAT USD CPI | Free CSV, daily, tested | SOFR; RBZ USD minimum rates |
| N6 Size of ZiG deposit base | RBZ monetary statistics xlsx (T1); RBZ reserve-cover statements (secondary); IMF staff report (about 80% of deposits are USD) | RBZ Monetary_Aggregates_.xlsx (to confirm it splits ZiG and FCA deposits) | Primary Excel | Derived estimate in Section 3 |
| N7 Parallel-market rate | equityaxis weekly updates (premium averaged 20.7% in Aug 2026); IMF staff report (gap about 16%); street-rate sites | Not requested | No reliable time series; low reliability | Sensitivity only (open question) |

## 6. Datasets requested
| ID | Dataset | Source and location | Access | Period / granularity | Fields needed | Licence / cost | Priority |
|---|---|---|---|---|---|---|---|
| D1 | RBZ daily interbank rates | rbz.co.zw/documents/Exchange_Rates/<YYYY>/<Month>/RATES_<D or DD>_<MONTH>_<YYYY>.pdf | PDF per day (script) | 2024-04-08 to 2026-11-13, business days | rate_date, currency, bid, ask, mid (ZWG per USD) | Free | Must |
| D2 | IMF ER monthly ZWE | api.imf.org SDMX 2.1, IMF.STA,ER | API (XML) | 2024-01 to latest (2026-06) | period, USD per ZWG, average (PA_RT) and end-of-period (EOP_RT) | Free | Must |
| D3 | RBZ Table 8.2 ZiG deposit rates | rbz.co.zw > Research > Markets > Interest Rates > Bank-Deposits-rates.xlsx (sheet "T8.2 ") | Excel | 2024-04 to 2026-09, monthly | month, savings min/max, 3-month min/max | Free | Must |
| D4 | ZIMSTAT CPI | zimstat.co.zw/wp-content/uploads/Macro/Prices/CPI/<YYYY>/CPI_<ZWG/USD/Weighted>_<MM>_<YYYY>.pdf | PDF per month | 2024-04 to 2026-10 | index level, m/m %, y/y % | Free | Must (ZWG, USD); Nice (Weighted) |
| D5 | FRED: DTB3, CPIAUCSL (Must); SOFR (Nice) | fred.stlouisfed.org/graph/fredgraph.csv?id=<ID> | CSV | 2024-04 to latest; daily / monthly | date, value | Free (public domain US data) | Must |
| D6 | RBZ instrument and policy events | Hand-built CSV (starter in Section 7) | CSV | 2024-04 to 2026-11 | event_date, type, tenor, currency, rate, amount, source_url, status | Free | Must |
| D7 | FCB daily rate PDFs for RBZ gap days | firstcapitalbank.co.zw/forex-reports | PDF per day | Gap days in D1 log only | date, interbank mid | Free | Nice |
| D8 | RBZ monetary aggregates (ZiG vs FCA deposits) | rbz.co.zw > Monetary & Financial Statistics > Monetary_Aggregates_.xlsx, Depository_Corporations_Survey_.xlsx | Excel | 2024-04 to latest | month, ZiG deposits, FCA deposits | Free | Nice |

## 7. How to get the data
1. **D1** (Python 3, tested in sandbox on 2025-12-29 to 2026-01-05): `python get_rbz_daily_rates.py 2024-04-08 2026-11-13 D1_rbz_daily_rates`. The script is saved in the project (`umfdop/scripts/get_rbz_daily_rates.py`). It tries both file-name patterns, saves `RBZ_RATES_<date>.pdf` and writes `D1_download_log.csv`. Expect gaps (missing in testing: 2024-04-15, 2025-12-30, 2025-12-31). Upload the PDFs as a zip, plus the log.
2. **D2** (browser or curl, tested): `https://api.imf.org/external/sdmx/2.1/data/IMF.STA,ER/ZWE.USD_XDC.PA_RT.M?startPeriod=2024-01` and the same URL with `EOP_RT`. Save as `D2_imf_er_pa.xml` and `D2_imf_er_eop.xml`. Values are USD per ZWG; invert them.
3. **D3** (tested): rbz.co.zw > Research > Markets > Interest Rates > "Bank Deposits rates". The current link is `https://www.rbz.co.zw/documents/statistics/2026/August/Bank-Deposits-rates.xlsx`; the folder changes each release, so take the link from the page. Save as `D3_rbz_bank_deposit_rates.xlsx`.
4. **D4** (pattern tested for Apr, Sep and Oct 2026): `https://www.zimstat.co.zw/wp-content/uploads/Macro/Prices/CPI/2026/CPI_ZWG_10_2026.pdf`. Loop over `ZWG`, `USD` and `Weighted`, months 04/2024 to 10/2026 (93 files). Zip them as `D4_zimstat_cpi.zip` and note any 404s.
5. **D5** (tested): `https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTB3&cosd=2024-04-01`. Repeat with `CPIAUCSL` (use `cosd=2024-03-01`) and `SOFR`. Save as `D5_fred_<id>.csv`.
6. **D6**: save this starter as `D6_rbz_events.csv` and add any further ZiGDTDF/NNCD results you find:
```
event_date,event_type,instrument,tenor_days,currency,rate_pct,amount_zwg_m,source_url,status
2024-04-08,launch,ZiG introduction (mid 13.5616),,ZWG,,,https://www.rbz.co.zw/documents/Exchange_Rates/2024/April/RATES_8_APRIL_2024.pdf,verified
2024-09-27,devaluation,ZiG mid 13.9987 (26 Sep) to 24.3902 (27 Sep): -42.6% vs USD,,ZWG,,,https://www.rbz.co.zw/documents/Exchange_Rates/2024/September/RATES_27_SEPTEMBER_2024.pdf,verified
2026-02-27,min_deposit_rate,savings,,ZWG,5.0,,https://www.heraldonline.co.zw/single-digit-inflation-stable-exchange-rate-mark-2026-monetary-policy-milestones/,single_source
2026-02-27,min_deposit_rate,savings,,USD,2.5,,https://www.heraldonline.co.zw/single-digit-inflation-stable-exchange-rate-mark-2026-monetary-policy-milestones/,single_source
2026-02-27,min_deposit_rate,time deposit,,ZWG,7.5,,https://www.heraldonline.co.zw/single-digit-inflation-stable-exchange-rate-mark-2026-monetary-policy-milestones/,single_source
2026-02-27,min_deposit_rate,time deposit,,USD,4.0,,https://www.heraldonline.co.zw/single-digit-inflation-stable-exchange-rate-mark-2026-monetary-policy-milestones/,single_source
2026-06-04,zigdtdf_auction,ZiGDTDF,90,ZWG,10.98,331.6,https://www.heraldonline.co.zw/rbz-moves-to-anchor-zig-as-store-of-value/,verified
2026-06-10,zigdtdf_tap,ZiGDTDF,30,ZWG,8.0,,https://www.newsday.co.zw/local-news/article/200056702/rbz-mops-up-liquidity-with-new-zig-bills,verified
2026-06-10,zigdtdf_tap,ZiGDTDF,60,ZWG,9.0,,https://www.newsday.co.zw/local-news/article/200056702/rbz-mops-up-liquidity-with-new-zig-bills,verified
2026-06-10,zigdtdf_tap,ZiGDTDF,90,ZWG,11.0,,https://www.newsday.co.zw/local-news/article/200056702/rbz-mops-up-liquidity-with-new-zig-bills,verified
2026-06-15,policy_rate,Bank Policy Rate,,ZWG,30.0,,https://www.heraldonline.co.zw/rbz-slashes-policy-rate-to-30-percent-in-first-cut-since-zig-launch/,verified
2026-09-28,policy_rate,Bank Policy Rate,,ZWG,27.5,,https://www.heraldonline.co.zw/rbz-cuts-policy-rate-to-275pc/,verified
```
7. **D7** (only for dates logged as `missing` in D1): open firstcapitalbank.co.zw > Resources > Forex Reports and download the PDF for each date.
8. **D8**: rbz.co.zw > Research > Markets > Monetary & Financial Statistics. Download `Monetary_Aggregates_.xlsx` and `Depository_Corporations_Survey_.xlsx`.

## 8. Register updates (CSV lines)
```
MAC-002,Macro,ZiG year-on-year inflation,4.3% (Oct 2026); ZWG CPI 198.63 (Apr 2024=100),2026-10,2026-11-13,verified,primary,https://www.zimstat.co.zw/wp-content/uploads/Macro/Prices/CPI/2026/CPI_ZWG_10_2026.pdf,UPGRADED to primary (ZIMSTAT PDF read). m/m 0.2%
MAC-006,Macro,Weighted CPI index level,131.32 (Sept 2026; base April 2024 = 100),2026-09,2026-11-13,verified,primary,https://www.zimstat.co.zw/wp-content/uploads/Macro/Prices/CPI/2026/CPI_Weighted_09_2026.pdf,VERIFIED: v4.2 value confirmed in ZIMSTAT PDF
MAC-007,Macro,ZiG/USD exchange rate,Use the RBZ official interbank rate for each transaction date,daily,2026-11-13,rule,primary,https://www.rbz.co.zw/documents/Exchange_Rates/2026/November/RATES_13_NOVEMBER_2026.pdf,"Latest verified: mid 26.5861 (bid 25.9214; ask 27.2508) on 2026-11-13. File names vary (zero-padded or not) and some days have no file. Never hard-code a rate"
MAC-008,Macro,Real GDP growth,8.3% (2025); 5.0% projected (2026),2026,2026-11-13,verified,primary (IMF staff report),https://www.imf.org/-/media/files/publications/cr/2026/english/1zweea2026002.pdf,UPGRADED: IMF SMP first-review staff report (28 Jul 2026)
MAC-009,Macro,Foreign reserves backing ZiG,Above USD 2 billion (Sept 2026); about 2 months' import cover,2026-09,2026-11-13,single_source,secondary (RBZ MPC quoted),https://www.heraldonline.co.zw/rbz-cuts-policy-rate-to-275pc/,"RESOLVED feed flag: not a conflict. USD 1.7bn (about 1.7 months) is the end-Jul figure from the Mid-Term MPS (verified: Chronicle + NewsDay). Reserves include gold. Reserves about 1.5x ZiG deposits (Jun 2026)"
MAC-010,Macro,ZiG share of national payment system transactions,43% (Jan-Aug 2026),2026-08,2026-11-13,single_source,secondary (Treasury quoted),https://allafrica.com/stories/202610200234.html,Herald quotes the RBZ Governor at 45% as of May 2026: https://www.heraldonline.co.zw/zig-gains-ground-nationally/
MAC-011,Macro,ZiG introduction rate,ZiG 13.5616 per USD (mid) on 8 April 2024,2024-04-08,2026-11-13,verified,primary,https://www.rbz.co.zw/documents/Exchange_Rates/2024/April/RATES_8_APRIL_2024.pdf,VERIFIED: bid 13.2226; ask 13.9006
MAC-012,Macro,RBZ prescribed minimum deposit rates,Savings 5% ZiG / 2.5% USD; time deposits 7.5% ZiG / 4% USD,2026-02-27,2026-11-13,single_source,secondary,https://www.heraldonline.co.zw/single-digit-inflation-stable-exchange-rate-mark-2026-monetary-policy-milestones/,NEW. Confirm in the 2026 MPS PDF
MAC-013,Macro,ZiGDTDF inaugural 90-day auction,Weighted average 10.98%; ZiG 331.6m allotted of ZiG 391.6m bids (ZiG 500m offer),2026-06-04,2026-11-13,verified,secondary + IMF,https://www.heraldonline.co.zw/rbz-moves-to-anchor-zig-as-store-of-value/,NEW. IMF staff report: ZiG 330m at about 11% (90d); ZiG 110m at 8% (30d)
MAC-014,Macro,ZiGDTDF tap rates,30d 8%; 60d 9%; 90d 11% p.a.,2026-06,2026-11-13,verified,secondary (2),https://www.newsday.co.zw/local-news/article/200056702/rbz-mops-up-liquidity-with-new-zig-bills,NEW. Later auction results not found
MAC-015,Macro,ZiG/USD close 2025,25.9807 ZWG per USD,2025-12-31,2026-11-13,verified,IMF programme rate + bank,https://www.firstcapitalbank.co.zw/wp-content/uploads/2025/12/Exchange-Rates-31-December-2025.pdf,NEW. No RBZ file for 30-31 Dec 2025. YTD baseline
MAC-016,Macro,Average ZiG deposit rates (RBZ Table 8.2),Savings 4.35-4.71%; 3-month 7.88-13.88% (Sep 2026),2026-09,2026-11-13,verified,primary,https://www.rbz.co.zw/documents/statistics/2026/August/Bank-Deposits-rates.xlsx,"NEW. Range of rates quoted by banks, not volume-weighted. Below the 5% savings minimum (MAC-012)"
DAT-004,Data,RBZ daily rate PDF naming,RATES_<D or DD>_<MONTH>_<YYYY>.pdf under /documents/Exchange_Rates/<YYYY>/<Month>/,2024-04,2026-11-13,verified,tested (sandbox),https://www.rbz.co.zw/documents/Exchange_Rates/2026/November/RATES_13_NOVEMBER_2026.pdf,"NEW. Both padded and unpadded names occur; no file on 2024-04-15, 2025-12-30, 2025-12-31"
```

## 9. Assumptions and open questions
- The USD-adjusted return uses the RBZ mid rate. Conversions at bid and ask are a separate scenario (spread about 5% of mid). Withholding tax on interest is not modelled; add it as a register row before use. IMTT is per TAX-007/008.
- Bloomberg says the ZiG weakened "almost 3%" in 2026. The RBZ mid gives 2.1% YTD to 12 Nov (2.6% at 31 Aug). Bloomberg may use another rate or date.
- RBZ Table 8.2 gives min/max quoted ranges, not volume-weighted rates. Data-quality flags for Agent 2: savings min > max in Dec 2024, Jan 2025 and May 2026; Jan 2025 repeats Dec 2024; rows before Apr 2024 are ZWL and must be excluded.
- IMF ER flags for Agent 2: it returns a spurious `2027-M03` observation (it duplicates 2026-M03); Apr 2024 average 13.40 is below the launch rate (a part-month effect); data stops at 2026-M06.
- DTB3 is quoted on a discount basis. Agent 4 converts it to bond-equivalent yield.
- No RBZ table of commercial-bank USD deposit rates was found. Proxies: RBZ USD minimums (2.5% / 4%) and US T-bills.
- ZiGDTDF and NNCD results after June 2026 were not found. Do you have the RBZ auction notices, or can you get them from a bank treasury desk?
- The parallel-market rate is excluded (no reliable series). Agent 4 can run it as a sensitivity (premium 16-21%).

## 10. Handoff to Agent 2
Upload: D1 (`D1_rbz_daily_rates.zip` + `D1_download_log.csv`), D2 (`D2_imf_er_pa.xml`, `D2_imf_er_eop.xml`), D3 (`D3_rbz_bank_deposit_rates.xlsx`), D4 (`D4_zimstat_cpi.zip`), D5 (`D5_fred_DTB3.csv`, `D5_fred_CPIAUCSL.csv`, optional `D5_fred_SOFR.csv`), D6 (`D6_rbz_events.csv`). Optional: D7 (FCB gap-day PDFs), D8 (RBZ monetary aggregates xlsx).

Pipeline: Step 1 of 5 - Agent 1 - Waiting for: files D1-D6 uploaded (D7-D8 optional)
