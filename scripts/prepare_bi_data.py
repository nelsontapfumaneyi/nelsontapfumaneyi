"""Prepare BI-ready copies of the Agent 4 result tables for Power BI and Tableau (UMFDOP, 2026-11-13 ZiG returns).

Run (Python 3, pandas):  python3 prepare_bi_data.py <results_dir> <fx_daily_csv> <out_dir>
  results_dir  folder with result_*.csv from agent4_zig_returns.py / agent4_findings.py
  fx_daily_csv export of mart.v_fx_daily (date_key, zwg_per_usd, is_carried_forward, rate_source)
  out_dir      e.g. Documents/UMFDOP/zig-returns-2026-11-13/data
Adds helper columns only (no figures change): findings.row_id, returns_monthly.period_date,
subperiods label/order, scenario parts, and three small dimension files.
"""
import os
import sys

import pandas as pd

RES, FX, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
p = lambda n: os.path.join(RES, n)

f = pd.read_csv(p("result_findings.csv"))
f.insert(0, "row_id", range(len(f)))  # row_id = CSV row number, used by every BI tool's KPI cards
f.to_csv(os.path.join(OUT, "findings.csv"), index=False)

r = pd.read_csv(p("result_returns_monthly.csv"))
r.insert(2, "period_date", r["period"] + "-01")
r.to_csv(os.path.join(OUT, "returns_monthly.csv"), index=False)

s = pd.read_csv(p("result_subperiods.csv"))
LAB = {"P0 full window": "Full window", "P1 pre-devaluation": "Apr-Sep 2024", "P2 devaluation and aftermath": "Sep-Dec 2024",
       "P3 2025": "2025", "P4 2026 to Sep": "2026 to Sep", "P5 since 2025 (Jan 2025 to Sep 2026)": "Since Jan 2025"}
s.insert(2, "subperiod_label", s["subperiod"].map(LAB))
s.insert(3, "subperiod_order", s["subperiod"].str.slice(1, 2).astype(int))
assert s["subperiod_label"].notna().all(), "unmapped subperiod"
s.to_csv(os.path.join(OUT, "subperiods.csv"), index=False)

ro = pd.read_csv(p("result_rolling.csv"))
ro["window_days"] = ro["window_days"].astype("Int64")  # drawdown rows stay blank
ro.to_csv(os.path.join(OUT, "rolling.csv"), index=False)

sc = pd.read_csv(p("result_scenarios.csv"))
parts = sc["scenario"].str.split(r" \| ", regex=True)


def conv(x):
    if x[0].startswith("required"):
        return "Already holds ZiG" if x[1].startswith("no conversion") else "Converts US$ and back"
    if x[0].startswith("MC"):
        return "Already holds ZiG" if x[3] == "no conversion" else "Converts US$ and back"
    return ""


def hold(x):
    if x[0].startswith("required"):
        return x[3].replace("hold ", "")
    if x[0].startswith("MC"):
        return {"3m": "3 months", "12m": "12 months"}[x[2]]
    return "12 months"


sc.insert(2, "kind", parts.str[0])
sc.insert(3, "conversion_case", parts.apply(conv))
sc.insert(4, "depreciation_case", parts.apply(lambda x: x[2] if x[0].startswith("required") else ""))
sc.insert(5, "hold_label", parts.apply(hold))
sc.insert(6, "hold_months", sc["hold_label"].str.extract(r"(\d+)")[0].astype(int))
sc.insert(7, "instrument", parts.apply(lambda x: x[1].split(" ")[0] if not x[0].startswith("required") else ""))
sc.to_csv(os.path.join(OUT, "scenarios.csv"), index=False)

fx = pd.read_csv(FX)
if not pd.api.types.is_bool_dtype(fx["is_carried_forward"]):  # psql exports booleans as t/f
    fx["is_carried_forward"] = fx["is_carried_forward"].astype(str).map({"t": True, "f": False, "True": True, "False": False})
fx.to_csv(os.path.join(OUT, "fx_daily.csv"), index=False)

pd.DataFrame([("ZWG_cash", "ZiG cash", "ZWG", 1), ("ZWG_savings_min", "ZiG savings (lowest rate)", "ZWG", 2),
              ("ZWG_savings_max", "ZiG savings (top rate)", "ZWG", 3), ("ZWG_3m_deposit_min", "ZiG 3-month index (lowest rate)", "ZWG", 4),
              ("ZWG_3m_deposit_max", "ZiG 3-month index (top rate)", "ZWG", 5), ("ZWG_ZiGDTDF_90d", "RBZ ZiGDTDF 90-day bill", "ZWG", 6),
              ("USD_cash", "USD cash", "USD", 7), ("USD_tbill_3m", "US 3-month T-bill", "USD", 8)],
             columns=["instrument", "label", "currency_held", "sort"]).to_csv(os.path.join(OUT, "dim_instrument.csv"), index=False)

d = pd.DataFrame({"Date": pd.date_range("2024-04-01", "2026-12-31")})
d["Year"], d["MonthNumber"] = d["Date"].dt.year, d["Date"].dt.month
d["YearMonth"], d["MonthLabel"] = d["Date"].dt.strftime("%Y-%m"), d["Date"].dt.strftime("%b %Y")
d["Date"] = d["Date"].dt.strftime("%Y-%m-%d")
d.to_csv(os.path.join(OUT, "dim_date.csv"), index=False)

pd.DataFrame({"basis": ["USD-adjusted", "USD-adjusted real", "ZiG nominal", "ZiG real"], "order": [1, 2, 3, 4]}).to_csv(
    os.path.join(OUT, "return_basis.csv"), index=False)

for n in sorted(os.listdir(OUT)):
    if n.endswith(".csv"):
        print(n, len(pd.read_csv(os.path.join(OUT, n))))
