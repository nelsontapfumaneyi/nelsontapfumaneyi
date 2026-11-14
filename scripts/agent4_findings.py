"""UMFDOP Agent 4 - build result_findings.csv from the result tables (every number traces to a results/ file).
Run after agent4_zig_returns.py:  python agent4_findings.py <run_dir>     Tested in sandbox.
"""
import sys
from pathlib import Path
import pandas as pd

R = (Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")) / "results"
sub = pd.read_csv(R / "result_subperiods.csv")
mon = pd.read_csv(R / "result_returns_monthly.csv")
roll = pd.read_csv(R / "result_rolling.csv")
scen = pd.read_csv(R / "result_scenarios.csv")
par = pd.to_numeric(pd.read_csv(R / "run_parameters.csv", index_col=0)["value"], errors="coerce")


def s(inst, per, col="usd_adjusted_return_pct"):
    return float(sub[(sub.instrument == inst) & (sub.subperiod == per)][col].iloc[0])


def real_cum(inst, col):
    g = mon[(mon.instrument == inst) & mon[col].notna()]
    return float(((1 + g[col] / 100).prod() - 1) * 100)


def rl(inst, h, regime, col):
    return float(roll[(roll.instrument == inst) & (roll.window_days == h) & (roll.regime == regime)][col].iloc[0])


def sc(text):
    return float(scen[scen.scenario == text]["p50"].iloc[0])


sensdf = pd.read_csv(R / "result_sensitivity.csv")


def sens(inst, measure):
    return float(sensdf[(sensdf.instrument == inst) & (sensdf.measure == measure)].locked_terms.iloc[0])


def mc(text):
    row = scen[scen.scenario == text].iloc[0]
    return row.p5, row.p50, row.p95, row.assumptions.split("P(behind T-bill)=")[1]


F = "P0 full window"; Y26 = "P4 2026 to Sep"; S25 = "P5 since 2025 (Jan 2025 to Sep 2026)"; Y25 = "P3 2025"
since = "windows starting 2025-01-01 or later"
c_lab = "RBZ bid-ask round trip 2026-11-13"
rows = [
    ("BQ1", "ZiG cash lost about half its USD value from launch (2024-04-08) to 2026-09-30",
     s("ZWG_cash", F), "% USD-adjusted", "High: exact calculation from RBZ daily rates; matches independent SQL",
     "Official mid rate; parallel-market rate not modelled"),
    ("BQ1", "A return index at the top quoted ZiG 3-month deposit rate lost over a third of its USD value since launch",
     s("ZWG_3m_deposit_max", F), "% USD-adjusted", "High for the index; it is a hypothetical strategy, not observed investor returns",
     f"Rate reset monthly, monthly compounding; locked 3-month terms give {sens('ZWG_3m_deposit_max', 'USD-adjusted return, P0 full window (%)'):.2f}%; quoted max rates, not volume-weighted"),
    ("BQ1", "FX effect since launch (same for every ZiG product) in log points; interest offsets at most 23 log points",
     float(pd.read_csv(R / "result_bridge.csv").query("step=='ZWG_cash: FX effect (log pts)'").amount.iloc[0]),
     "log pts", "High: bridge check row = 0", "Log decomposition; % equivalents in result_bridge.csv"),
    ("BQ1", "Real (ZWG CPI) return on ZiG cash, May 2024-Sep 2026", real_cum("ZWG_cash", "real_zwg_return_pct"), "% real",
     "High", "April 2024 excluded (CPI base month); 4 imputed CPI months flagged"),
    ("BQ1", "Since Jan 2025 the return index at the top quoted 3-month rate gained in USD terms",
     s("ZWG_3m_deposit_max", S25), "% USD-adjusted over 21 months", "High for the index",
     f"Locked 3-month terms give {sens('ZWG_3m_deposit_max', 'USD-adjusted return, P5 since 2025 (Jan 2025 to Sep 2026) (%)'):.2f}%; excludes conversion costs"),
    ("BQ1", "USD cash held in Zimbabwe lost real value too (ZIMSTAT USD CPI), May 2024-Sep 2026",
     real_cum("USD_cash", "usd_adjusted_real_return_pct"), "% real", "High", "Zimbabwe USD CPI, not US CPI"),
    ("BQ2", "2026 (to Sep): the top-rate 3-month index beat the US 3-month T-bill",
     s("ZWG_3m_deposit_max", Y26, "spread_vs_tbill_ann_pp"), "pp p.a.", "Medium: 9-month window",
     f"Locked 3-month terms give {sens('ZWG_3m_deposit_max', 'spread vs T-bill, P4 2026 to Sep (pp p.a.)'):.2f} pp; before conversion costs"),
    ("BQ2", "2026 (to Sep): ZiGDTDF 90-day (10.98%) beat the T-bill since its 4 June 2026 launch",
     s("ZWG_ZiGDTDF_90d", Y26, "spread_vs_tbill_ann_pp"), "pp p.a.", "Low: 118 days; ZiG firmed slightly in the window",
     "10.98% = weighted average of allotted bids (10%-25%); reinvested at the same rate after the first 90-day maturity; later auction results not available"),
    ("BQ2", "2026 (to Sep): ZiG savings (max quoted rate) lagged the T-bill",
     s("ZWG_savings_max", Y26, "spread_vs_tbill_ann_pp"), "pp p.a.", "Medium", "Quoted max savings rate"),
    ("BQ2", "2025: ZiG 3-month deposit max beat the T-bill; savings did not",
     s("ZWG_3m_deposit_max", Y25, "spread_vs_tbill_ann_pp"), "pp p.a.", "High", "Calendar 2025"),
    ("BQ2", "Pre-devaluation (Apr-Sep 2024) every ZiG product trailed the T-bill, even before the devaluation",
     s("ZWG_3m_deposit_max", "P1 pre-devaluation", "spread_vs_tbill_ann_pp"), "pp p.a.", "High", "5.5-month window"),
    ("BQ2", "ZiG depreciation in 2026 to 30 Sep (matches Bloomberg's 'almost 3%'; 2.1% to 12 Nov)",
     -s("ZWG_cash", Y26), "% vs USD", "High", "RBZ mid rate"),
    ("BQ3", "Required ZiG yield to match the T-bill for holders who already earn ZiG (2026 depreciation pace)",
     sc("required ZiG yield | no conversion (already earns ZiG) | 2026 realised depreciation | hold 12 months"), "% p.a.",
     "Medium: assumes 2026 depreciation pace continues", f"e={par['e_2026_ann_pct']:.2f}% p.a. to 13 Nov; r={par['r_usd_bey_oct2026_pct']:.2f}%"),
    ("BQ3", "Required yield for a USD holder who converts for 12 months (pays the RBZ bid-ask round trip)",
     sc(f"required ZiG yield | {c_lab} | 2026 realised depreciation | hold 12 months"), "% p.a.", "Medium",
     f"Round trip {par['c_latest_pct']:.2f}% at RBZ interbank bid/ask; retail spreads may be wider; IMTT excluded"),
    ("BQ3", "Required yield for a USD holder who converts for 3 months",
     sc(f"required ZiG yield | {c_lab} | 2026 realised depreciation | hold 3 months"), "% p.a.", "Medium",
     "Conversion cost dominates short holds"),
    ("BQ3", "Share of simulated 12-month paths in which ZiGDTDF at 10.98% ends ahead of the T-bill, already-ZiG holder (fitted calm-month model)",
     100 - 100 * float(mc("MC relative wealth vs T-bill | ZWG_ZiGDTDF_90d (10.98%) | 12m | no conversion")[3]), "% of simulated paths",
     "Low: conditional on a normal model fitted to 21 calm months; not a real-world probability", "Excludes devaluation jumps; see stress row"),
    ("BQ3", "Stress: a repeat of the 27 Sep 2024 devaluation inside a 12-month hold of ZiGDTDF leaves ending wealth below the T-bill alternative by",
     sc("stress: 27-Sep-2024 devaluation repeats within a 12m hold | ZWG_ZiGDTDF_90d (10.98%)"), "% relative wealth vs T-bill",
     "Scenario, not a forecast", "One-off -42.6% move as on 27 Sep 2024; percentage-point difference in result_scenarios.csv"),
    ("BQ4", "Share of 90-day windows since 2025 in which ZiG cash lost USD value",
     rl("ZWG_cash", 90, since, "share_loss_pct"), "% of windows", "High", f"{int(rl('ZWG_cash', 90, since, 'windows'))} overlapping windows"),
    ("BQ4", "Share of 90-day windows since 2025 in which the 3-month deposit (max) lost USD value",
     rl("ZWG_3m_deposit_max", 90, since, "share_loss_pct"), "% of windows", "High", "Overlapping windows; quoted max rate"),
    ("BQ4", "Worst 90-day USD-adjusted loss since 2025, ZiG cash (window starting 2026-04-10)",
     rl("ZWG_cash", 90, since, "worst_return_pct"), "%", "High", "Driven by the May 2026 move (-5.9% in the month)"),
    ("BQ4", "Worst 90-day USD-adjusted loss over the full window, ZiG cash (window starting 2024-08-05)",
     rl("ZWG_cash", 90, "all windows", "worst_return_pct"), "%", "High", "Includes the 27 Sep 2024 devaluation"),
]
out = pd.DataFrame(rows, columns=["question_id", "finding", "number", "unit", "confidence", "limits"])
out["number"] = out["number"].round(2)
out.to_csv(R / "result_findings.csv", index=False)
print(out[["question_id", "number", "unit", "finding"]].to_string(index=False))

# Hypothesis verdicts (from Agent 1's brief) appended to result_metrics.csv
met = pd.read_csv(R / "result_metrics.csv")
hyp = [
    ("BQ1", "H1 every launch-dated ZiG product worse than -30% USD-adjusted since launch (max of products)",
     max(s(i, F) for i in ["ZWG_cash", "ZWG_savings_min", "ZWG_savings_max", "ZWG_3m_deposit_min", "ZWG_3m_deposit_max"]), -30.0, None),
    ("BQ1", "H1b 3-month deposit (min rate) positive USD-adjusted since Jan 2025", s("ZWG_3m_deposit_min", S25), 0.0, True),
    ("BQ2", "H2 2026 spread vs T-bill, 3-month deposit max >= 3pp", s("ZWG_3m_deposit_max", Y26, "spread_vs_tbill_ann_pp"), 3.0, True),
    ("BQ2", "H2 2026 spread vs T-bill, savings max < 0 (does not beat USD)", s("ZWG_savings_max", Y26, "spread_vs_tbill_ann_pp"), 0.0, None),
    ("BQ4", "H4 share of 90-day loss windows since 2025 < 20%, ZiG cash", rl("ZWG_cash", 90, since, "share_loss_pct"), 20.0, None),
    ("BQ4", "H4 share of 90-day loss windows since 2025 < 20%, 3-month deposit max", rl("ZWG_3m_deposit_max", 90, since, "share_loss_pct"), 20.0, None),
]
for qid, name, val, thr, higher in hyp:
    ok = val >= thr if higher else val < thr
    met.loc[len(met)] = {"question_id": qid, "model": "hypothesis test", "metric": name, "value": round(val, 4),
                         "baseline_value": thr, "beats_baseline": bool(ok)}
met.to_csv(R / "result_metrics.csv", index=False)
print(met[met.model == "hypothesis test"][["metric", "value", "baseline_value", "beats_baseline"]].to_string(index=False))
