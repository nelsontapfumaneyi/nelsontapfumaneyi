"""UMFDOP Agent 4 - Does holding ZiG pay? (BQ1-BQ4, brief 2026-11-13)
Python 3.10+, pandas 2.x/3.x, numpy, psycopg 3. Reads mart views only (sql/05_agent4_extract.sql).
Run:  UMFDOP_DSN="dbname=umfdop port=5433" python agent4_zig_returns.py <run_dir>
Writes <run_dir>/results/*.csv and prints the run log. Seed fixed (42). Tested in sandbox.

Return conventions (stated, not hidden):
- Quoted annual rates (% p.a., simple) accrue daily and compound monthly: daily factor = (1 + r*dm/365)^(1/dm),
  where dm = days in the calendar month. A full month therefore earns exactly r*dm/365.
- USD-adjusted return = ZWG return x (start ZWG/USD rate / end ZWG/USD rate). RBZ mid rate; weekends carry Friday.
- Real ZWG return deflates by the ZIMSTAT ZWG CPI; USD-adjusted real return deflates by the ZIMSTAT USD CPI.
- US T-bill: monthly average DTB3 (discount basis) converted to bond-equivalent yield, 91-day bill:
  BEY = 365*d / (360 - 91*d).
- The 3-month deposit series are hypothetical return indices at the published (RBZ Table 8.2) rates: the rate is
  re-read every month and interest compounds monthly; no term is locked. result_sensitivity.csv repeats the
  headline figures with locked 3-month terms (rate fixed at placement, simple interest, reinvested at maturity).
- ZiGDTDF: 10.98% is the weighted average of allotted bids at the 4 June 2026 auction (accepted bids 10%-25%).
  Holding it past the first 90-day maturity assumes reinvestment at the same rate.

Revision 2026-11-14 (external review): required yield uses e = annual loss in the USD value of the ZiG, so
1+y = (1+r)/((1-e)(1-c)^(1/T)) (was (1+r)(1+e)/(1-c)^(1/T), which treats e as growth in ZiG per USD).
Stress and Monte Carlo results are now relative wealth vs the T-bill, (1+R_zig)/(1+R_tbill)-1, with the
percentage-point difference kept in the assumptions. Simulated holdings compound at each product's term.
"""
import math, os, sys
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
import psycopg

RUN = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
OUT = RUN / "results"
DSN = os.environ.get("UMFDOP_DSN", "dbname=umfdop")
SEED = 42
START, END, EXT_END = date(2024, 4, 8), date(2026, 9, 30), date(2026, 11, 13)
SUBPERIODS = {  # (from, to): returns measured from the close of 'from' to the close of 'to'
    "P0 full window": (date(2024, 4, 8), END),
    "P1 pre-devaluation": (date(2024, 4, 8), date(2024, 9, 26)),
    "P2 devaluation and aftermath": (date(2024, 9, 26), date(2024, 12, 31)),
    "P3 2025": (date(2024, 12, 31), date(2025, 12, 31)),
    "P4 2026 to Sep": (date(2025, 12, 31), END),
    "P5 since 2025 (Jan 2025 to Sep 2026)": (date(2024, 12, 31), END),
}


def q(sql):
    with psycopg.connect(DSN) as con, con.cursor() as cur:
        cur.execute(sql)
        cols = [c.name for c in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=cols)


# ------------------------------------------------------------------ data (mart views only)
fx = q("SELECT date_key, units_per_usd, bid_units_per_usd, ask_units_per_usd, is_carried_forward, rate_source "
       "FROM mart.v_fx_daily WHERE currency_code = 'ZWG' ORDER BY date_key")
mi = q("SELECT * FROM mart.v_monthly_inputs ORDER BY period")
ev = q("SELECT * FROM mart.v_rbz_events ORDER BY event_date")
fx["date_key"] = pd.to_datetime(fx["date_key"])
for c in ("units_per_usd", "bid_units_per_usd", "ask_units_per_usd"):
    fx[c] = fx[c].astype(float)
S = fx.set_index("date_key")["units_per_usd"]
num = [c for c in mi.columns if c not in ("period", "period_start", "fx_complete_month") and not c.endswith("imputed")
       and c != "flag_savings_min_gt_max"]
mi[num] = mi[num].astype(float)
mi = mi.set_index("period")

dtdf = ev[(ev.event_type == "zigdtdf_auction") & (ev.tenor_days == 90)].iloc[0]
DTDF_START, DTDF_RATE = pd.Timestamp(dtdf.event_date), float(dtdf.rate_pct)


def bey(d_pct):
    d = d_pct / 100
    return 100 * 365 * d / (360 - 91 * d)


mi["tbill_bey_pct"] = bey(mi["us_tbill_3m_discount_pct_avg"])

INSTRUMENTS = {  # name: (currency held, rate column or constant, first date)
    "ZWG_cash": ("ZWG", 0.0, START),
    "ZWG_savings_min": ("ZWG", "savings_min_pct", START),
    "ZWG_savings_max": ("ZWG", "savings_max_pct", START),
    "ZWG_3m_deposit_min": ("ZWG", "three_month_min_pct", START),
    "ZWG_3m_deposit_max": ("ZWG", "three_month_max_pct", START),
    "ZWG_ZiGDTDF_90d": ("ZWG", DTDF_RATE, DTDF_START.date()),
    "USD_cash": ("USD", 0.0, START),
    "USD_tbill_3m": ("USD", "tbill_bey_pct", START),
}

# ------------------------------------------------------------------ daily wealth panel
def daily_panel(end, only=None):
    days = pd.date_range(START, end, freq="D")
    s = S.reindex(days)
    assert s.notna().all(), "gap in v_fx_daily"
    fx_factor = (s.shift(1) / s).fillna(1.0)          # USD value change of 1 ZWG, day over day
    per = days.strftime("%Y-%m")
    dm = days.days_in_month.to_numpy()
    panel = {"date": days, "zwg_per_usd": s.to_numpy(), "fx_factor": fx_factor.to_numpy()}
    for name, (ccy, rate, first) in INSTRUMENTS.items():
        if only and name not in only:
            continue
        r = np.full(len(days), float(rate)) if not isinstance(rate, str) else mi[rate].reindex(per).to_numpy()
        held = days >= pd.Timestamp(first)
        g = np.where(held, (1 + r / 100 * dm / 365) ** (1 / dm), 1.0)
        g[days == pd.Timestamp(first)] = 1.0          # day 0 = purchase at the close
        if np.isnan(g).any():
            raise ValueError(f"{name}: missing rate inside window")
        nom = np.cumprod(g)
        usd = nom * (np.cumprod(fx_factor.to_numpy()) if ccy == "ZWG" else 1.0)
        if ccy == "ZWG":                               # rebase USD value to the instrument's own start
            usd = usd / usd[np.argmax(held)] * nom[np.argmax(held)] if held.any() else usd
        panel[f"{name}__rate"] = np.where(held, r, np.nan)
        panel[f"{name}__nom"] = nom
        panel[f"{name}__usd"] = np.where(held, usd, np.nan)
    return pd.DataFrame(panel).set_index("date")


P = daily_panel(END)
names = list(INSTRUMENTS)


def ret(series, d0, d1):
    a, b = series.get(pd.Timestamp(d0)), series.get(pd.Timestamp(d1))
    return np.nan if (a is None or b is None or pd.isna(a) or pd.isna(b)) else b / a - 1


def ann(r, d0, d1):
    days = (pd.Timestamp(d1) - pd.Timestamp(d0)).days
    return np.nan if pd.isna(r) or days <= 0 else (1 + r) ** (365 / days) - 1


# ------------------------------------------------------------------ BQ1 monthly returns
cpi = mi[["zwg_cpi", "zim_usd_cpi", "weighted_cpi"]]
month_ends = [d for d in P.index if d.is_month_end] or []
rows = []
for name in names:
    ccy = INSTRUMENTS[name][0]
    first = pd.Timestamp(INSTRUMENTS[name][2])
    prev = first
    for me in month_ends:
        if me < first or me <= prev:
            continue
        per = me.strftime("%Y-%m")
        prev_per = (me - pd.offsets.MonthEnd(1)).strftime("%Y-%m")
        nom = P.loc[me, f"{name}__nom"] / P.loc[prev, f"{name}__nom"] - 1
        usd = P.loc[me, f"{name}__usd"] / P.loc[prev, f"{name}__usd"] - 1
        fxe = (P.loc[prev, "zwg_per_usd"] / P.loc[me, "zwg_per_usd"] - 1) if ccy == "ZWG" else 0.0
        partial = prev.strftime("%Y-%m") == per or prev != (me - pd.offsets.MonthEnd(1))
        z_inf = cpi.loc[per, "zwg_cpi"] / cpi.loc[prev_per, "zwg_cpi"] - 1 if prev_per in cpi.index and not partial else np.nan
        u_inf = cpi.loc[per, "zim_usd_cpi"] / cpi.loc[prev_per, "zim_usd_cpi"] - 1 if prev_per in cpi.index and not partial else np.nan
        rows.append({"question_id": "BQ1", "period": per, "instrument": name, "currency_held": ccy,
                     "days": (me - prev).days, "partial_month": partial,
                     "rate_pct_pa": P.loc[me, f"{name}__rate"],
                     "nominal_return_pct": 100 * nom if ccy == "ZWG" else np.nan,
                     "fx_effect_pct": 100 * fxe,
                     "usd_adjusted_return_pct": 100 * usd,
                     "real_zwg_return_pct": 100 * ((1 + nom) / (1 + z_inf) - 1) if ccy == "ZWG" else np.nan,
                     "usd_adjusted_real_return_pct": 100 * ((1 + usd) / (1 + u_inf) - 1),
                     "cum_usd_index": P.loc[me, f"{name}__usd"] / P.loc[first, f"{name}__usd"] * 100,
                     "zwg_cpi_imputed": bool(mi.loc[per, "zwg_cpi_imputed"]) if per in mi.index else None})
        prev = me
monthly = pd.DataFrame(rows)

# BQ1 bridge: cumulative USD-adjusted log return = interest effect + FX effect (exact)
bridge = []
for name in [n for n in names if INSTRUMENTS[n][0] == "ZWG"]:
    d0 = pd.Timestamp(INSTRUMENTS[name][2]); d1 = pd.Timestamp(END)
    interest = math.log(P.loc[d1, f"{name}__nom"] / P.loc[d0, f"{name}__nom"])
    fxlog = math.log(P.loc[d0, "zwg_per_usd"] / P.loc[d1, "zwg_per_usd"])
    total = math.log(P.loc[d1, f"{name}__usd"] / P.loc[d0, f"{name}__usd"])
    for step, amt in (("interest effect (log pts)", interest), ("FX effect (log pts)", fxlog),
                      ("total USD-adjusted (log pts)", total), ("check: effects minus total (must be 0)", interest + fxlog - total),
                      ("total USD-adjusted (% simple)", math.exp(total) - 1)):
        bridge.append({"step": f"{name}: {step}", "amount": round(100 * amt, 6), "currency": "USD",
                       "period_from": d0.date().isoformat(), "period_to": d1.date().isoformat(),
                       "question_id": "BQ1", "instrument": name})
bridge = pd.DataFrame(bridge)

# ------------------------------------------------------------------ BQ2 sub-period spreads vs USD
sub = []
for label, (d0, d1) in SUBPERIODS.items():
    tb = ret(P["USD_tbill_3m__usd"], d0, d1)
    for name in names:
        first = INSTRUMENTS[name][2]
        a = max(d0, first)
        if a >= d1:
            continue
        r = ret(P[f"{name}__usd"], a, d1)
        tb_a = ret(P["USD_tbill_3m__usd"], a, d1)
        sub.append({"question_id": "BQ2", "subperiod": label, "instrument": name, "from": a.isoformat(), "to": d1.isoformat(),
                    "days": (d1 - a).days, "usd_adjusted_return_pct": 100 * r, "annualised_pct": 100 * ann(r, a, d1),
                    "tbill_return_pct": 100 * tb_a, "tbill_annualised_pct": 100 * ann(tb_a, a, d1),
                    "spread_vs_tbill_ann_pp": 100 * (ann(r, a, d1) - ann(tb_a, a, d1)),
                    "spread_vs_usd_cash_ann_pp": 100 * ann(r, a, d1),
                    "instrument_start_later": a != d0})
sub = pd.DataFrame(sub)

# ------------------------------------------------------------------ BQ3 required yield and scenarios
rbz = fx[fx.rate_source == "RBZ_interbank"].copy()
rbz["round_trip_cost"] = 1 - rbz["bid_units_per_usd"] / rbz["ask_units_per_usd"]
last_rbz = rbz.iloc[-1]
c_latest = float(last_rbz["round_trip_cost"])
c_2026 = float(rbz[rbz.date_key >= "2026-01-01"]["round_trip_cost"].mean())
e_2026 = -ann(ret(1 / S, date(2025, 12, 31), EXT_END), date(2025, 12, 31), EXT_END)  # realised ZWG depreciation p.a., to latest rate
r_usd = float(mi.loc["2026-10", "tbill_bey_pct"]) / 100                         # latest complete month
scen = []


def required(r, e, c, T):
    """Effective annual ZiG yield y that leaves a ZiG holder level with the T-bill after T years.
    r = T-bill effective annual rate; e = annual loss in the USD value of the ZiG (S0/S1 = 1-e per year);
    c = round-trip conversion cost paid once over the hold. Identity: (1+y)^T (1-e)^T (1-c) = (1+r)^T."""
    return (1 + r) / ((1 - e) * (1 - c) ** (1 / T)) - 1


def effective_annual(quoted_pct, term_years):
    """Effective annual rate of a quoted simple rate paid at the end of each term and reinvested."""
    return (1 + quoted_pct / 100 * term_years) ** (1 / term_years) - 1


TERMS = {"ZWG_ZiGDTDF_90d": 90 / 365, "ZWG_3m_deposit_max": 0.25, "ZWG_3m_deposit_min": 0.25,
         "ZWG_savings_max": 1 / 12, "ZWG_savings_min": 1 / 12}


for c_label, c in (("no conversion (already earns ZiG)", 0.0), (f"RBZ bid-ask round trip {last_rbz.date_key.date()}", c_latest)):
    for e_label, e in (("0% depreciation", 0.0), ("2026 realised depreciation", e_2026), ("5% depreciation", 0.05),
                       ("10% depreciation", 0.10)):
        for T_label, T in (("1 month", 1 / 12), ("3 months", 0.25), ("6 months", 0.5), ("12 months", 1.0)):
            y = required(r_usd, e, c, T)
            scen.append({"question_id": "BQ3", "scenario": f"required ZiG yield | {c_label} | {e_label} | hold {T_label}",
                         "assumptions": f"r_usd={r_usd:.4%} (DTB3 BEY Oct 2026); e={e:.4%}; c={c:.4%}; T={T:g}y",
                         "p5": 100 * y, "p50": 100 * y, "p95": 100 * y, "unit": "% p.a."})

for inst, quoted in (("ZWG_3m_deposit_max", float(mi.loc["2026-09", "three_month_max_pct"])),
                     ("ZWG_ZiGDTDF_90d", DTDF_RATE),
                     ("ZWG_savings_max", float(mi.loc["2026-09", "savings_max_pct"]))):
    ea = 100 * effective_annual(quoted, TERMS[inst])
    scen.append({"question_id": "BQ3", "scenario": f"effective annual rate on offer | {inst}",
                 "assumptions": f"quoted {quoted:.2f}% simple per term; term {TERMS[inst]:.4f}y; reinvested at the same rate",
                 "p5": ea, "p50": ea, "p95": ea, "unit": "% p.a. effective"})

# Monte Carlo: USD wealth of ZiG paper relative to the T-bill, calm regime (2025-2026 monthly FX moves).
# Conditional on the fitted model (normal monthly log moves, no jumps); not a validated real-world probability.
eom = S[S.index.is_month_end]
lchg = np.log(eom.shift(1) / eom).dropna()                                      # + = ZWG appreciation
calm = lchg[lchg.index >= "2025-01-31"]
calm = calm[calm.index <= pd.Timestamp(END)]
mu_m, sd_m = float(calm.mean()), float(calm.std(ddof=1))
rng = np.random.default_rng(SEED)
RUNS = 10_000
mc_rows = []
for inst, key, y_pa in (("ZWG_ZiGDTDF_90d (10.98%)", "ZWG_ZiGDTDF_90d", DTDF_RATE / 100),
                        ("ZWG_3m_deposit_max (Sep 2026 13.88%)", "ZWG_3m_deposit_max", float(mi.loc["2026-09", "three_month_max_pct"]) / 100),
                        ("ZWG_savings_max (Sep 2026 4.71%)", "ZWG_savings_max", float(mi.loc["2026-09", "savings_max_pct"]) / 100)):
    tau = TERMS[key]
    for T_m in (3, 12):
        growth = (1 + y_pa * tau) ** ((T_m / 12) / tau)                        # rolled at the product's own term
        tb = (1 + r_usd) ** (T_m / 12)
        for c_label, c in (("no conversion", 0.0), ("with round trip", c_latest)):
            fxlog = rng.normal(mu_m * T_m, sd_m * math.sqrt(T_m), RUNS)
            wealth = growth * np.exp(fxlog) * (1 - c)                          # USD wealth per USD-equivalent placed
            rel = wealth / tb - 1                                               # relative wealth vs T-bill
            pp = (wealth - 1) - (tb - 1)                                        # percentage-point difference
            p5, p50, p95 = np.percentile(rel * 100, [5, 50, 95])
            mc_rows.append({"question_id": "BQ3", "scenario": f"MC relative wealth vs T-bill | {inst} | {T_m}m | {c_label}",
                            "assumptions": f"monthly log FX ~ N({mu_m:.5f}, {sd_m:.5f}) from {len(calm)} months Jan 2025-Sep 2026; "
                                           f"{RUNS} runs; seed {SEED}; conditional on this model; "
                                           f"median pp difference={np.median(pp) * 100:.2f}; P(behind T-bill)={np.mean(rel < 0):.3f}",
                            "p5": p5, "p50": p50, "p95": p95, "unit": "% relative wealth vs T-bill"})
    # stress: replay of the 27 Sep 2024 one-day move inside a 12-month hold
dev = float(S[pd.Timestamp("2024-09-26")] / S[pd.Timestamp("2024-09-27")])
for inst, key, y_pa in (("ZWG_ZiGDTDF_90d (10.98%)", "ZWG_ZiGDTDF_90d", DTDF_RATE / 100),
                        ("ZWG_3m_deposit_max (13.88%)", "ZWG_3m_deposit_max", float(mi.loc["2026-09", "three_month_max_pct"]) / 100)):
    zig = (1 + y_pa * TERMS[key]) ** (1 / TERMS[key]) * dev                    # 12-month hold, rolled at its term
    rel = 100 * (zig / (1 + r_usd) - 1)
    pp = 100 * ((zig - 1) - r_usd)
    sub_row = sub[(sub.instrument == key) & (sub.subperiod == "P4 2026 to Sep")].iloc[0]
    pace = (1 + sub_row.annualised_pct / 100) / (1 + sub_row.tbill_annualised_pct / 100)   # 2026 relative growth p.a.
    years = math.log(1 / (1 + rel / 100)) / math.log(pace) if pace > 1 else float("nan")
    mc_rows.append({"question_id": "BQ3", "scenario": f"stress: 27-Sep-2024 devaluation repeats within a 12m hold | {inst}",
                    "assumptions": f"one-off FX factor {dev:.4f} (13.9987 -> 24.3902); no conversion cost; "
                                   f"ZiG return {100 * (zig - 1):.2f}%; pp difference vs T-bill {pp:.2f}",
                    "p5": rel, "p50": rel, "p95": rel, "unit": "% relative wealth vs T-bill"})
    mc_rows.append({"question_id": "BQ3", "scenario": f"stress recovery: years at the 2026 relative pace to regain the shortfall | {inst}",
                    "assumptions": f"relative growth p.a. = (1+{sub_row.annualised_pct:.2f}%)/(1+{sub_row.tbill_annualised_pct:.2f}%) (2026 to Sep)",
                    "p5": years, "p50": years, "p95": years, "unit": "years"})
scenarios = pd.concat([pd.DataFrame(scen), pd.DataFrame(mc_rows)], ignore_index=True)

# ------------------------------------------------------------------ BQ4 rolling windows
roll = []
for name in names:
    w = P[f"{name}__usd"].dropna()
    tbw = P["USD_tbill_3m__usd"].reindex(w.index)
    for h in (30, 90):
        r = (w.shift(-h) / w - 1).dropna()
        rt = (tbw.shift(-h) / tbw - 1).reindex(r.index)
        for regime, mask in (("all windows", r.index >= w.index[0]), ("windows starting 2025-01-01 or later", r.index >= "2025-01-01")):
            rr, rtt = r[mask], rt[mask]
            if len(rr) == 0:
                continue
            roll.append({"question_id": "BQ4", "instrument": name, "window_days": h, "regime": regime, "windows": len(rr),
                         "share_loss_pct": 100 * float((rr < 0).mean()),
                         "share_below_tbill_pct": 100 * float((rr < rtt).mean()),
                         "worst_return_pct": 100 * float(rr.min()), "worst_window_start": rr.idxmin().date().isoformat(),
                         "median_return_pct": 100 * float(rr.median()), "best_return_pct": 100 * float(rr.max())})
    dd = (w / w.cummax() - 1).min()
    roll.append({"question_id": "BQ4", "instrument": name, "window_days": None, "regime": "max drawdown, full window",
                 "windows": len(w), "share_loss_pct": None, "share_below_tbill_pct": None,
                 "worst_return_pct": 100 * float(dd), "worst_window_start": (w / w.cummax() - 1).idxmin().date().isoformat(),
                 "median_return_pct": None, "best_return_pct": None})
rolling = pd.DataFrame(roll)

# ------------------------------------------------------------------ robustness: locked 3-month terms (review 2026-11-14)
def locked_nominal(rate_col, start, end, term_months=3):
    """ZWG value of 1 ZWG placed at the close of `start` in consecutive 3-month terms. Each term locks the
    quoted rate of the month it starts in; simple interest accrues by day within the term and is reinvested
    at maturity. A value inside a term includes accrued interest."""
    days = pd.date_range(start, end, freq="D")
    out = np.empty(len(days))
    t0, principal = pd.Timestamp(start), 1.0
    mat = t0 + pd.DateOffset(months=term_months)
    rate = float(mi.loc[t0.strftime("%Y-%m"), rate_col]) / 100
    for i, d in enumerate(days):
        if d >= mat:
            principal *= 1 + rate * (mat - t0).days / 365
            t0, mat = mat, mat + pd.DateOffset(months=term_months)
            rate = float(mi.loc[t0.strftime("%Y-%m"), rate_col]) / 100
        out[i] = principal * (1 + rate * (d - t0).days / 365)
    return pd.Series(out, index=days)


sens = []
for key, col in (("ZWG_3m_deposit_max", "three_month_max_pct"), ("ZWG_3m_deposit_min", "three_month_min_pct")):
    for label in ("P0 full window", "P1 pre-devaluation", "P3 2025", "P4 2026 to Sep", "P5 since 2025 (Jan 2025 to Sep 2026)"):
        d0, d1 = SUBPERIODS[label]
        nomv = locked_nominal(col, d0, d1)
        r_locked = nomv.iloc[-1] * float(S[pd.Timestamp(d0)] / S[pd.Timestamp(d1)]) - 1
        base = sub[(sub.instrument == key) & (sub.subperiod == label)].iloc[0]
        tb_a = base.tbill_annualised_pct
        sens.append({"instrument": key, "measure": f"USD-adjusted return, {label} (%)", "index_method": base.usd_adjusted_return_pct,
                     "locked_terms": 100 * r_locked, "difference": 100 * r_locked - base.usd_adjusted_return_pct})
        sens.append({"instrument": key, "measure": f"spread vs T-bill, {label} (pp p.a.)", "index_method": base.spread_vs_tbill_ann_pp,
                     "locked_terms": 100 * ann(r_locked, d0, d1) - tb_a, "difference": 100 * ann(r_locked, d0, d1) - tb_a - base.spread_vs_tbill_ann_pp})
    # 90-day windows from 2025: a fresh deposit locked at the entry month's rate, valued after 90 days
    starts = pd.date_range("2025-01-01", pd.Timestamp(END) - pd.Timedelta(days=90), freq="D")
    rl90 = np.array([(1 + float(mi.loc[d.strftime("%Y-%m"), col]) / 100 * 90 / 365) * float(S[d] / S[d + pd.Timedelta(days=90)]) - 1
                     for d in starts])
    idx = [x for x in roll if x["instrument"] == key and x["window_days"] == 90 and x["regime"] == "windows starting 2025-01-01 or later"][0]
    sens.append({"instrument": key, "measure": "share of 90-day windows since 2025 with a USD loss (%)", "index_method": idx["share_loss_pct"],
                 "locked_terms": 100 * float((rl90 < 0).mean()), "difference": 100 * float((rl90 < 0).mean()) - idx["share_loss_pct"]})
sensitivity = pd.DataFrame(sens)

# ------------------------------------------------------------------ validation checks
def check(name, value, expected, tol):
    return {"question_id": "VAL", "model": "return engine", "metric": name, "value": value, "baseline_value": expected,
            "beats_baseline": bool(abs(value - expected) <= tol)}

P_ext = daily_panel(EXT_END, only=["ZWG_cash"])
cash_ext = ret(P_ext["ZWG_cash__usd"], date(2024, 4, 8), date(2026, 11, 12))
ytd_ext = ret(P_ext["ZWG_cash__usd"], date(2025, 12, 31), date(2026, 11, 12))
sql_cash = float(q("SELECT (SELECT units_per_usd FROM mart.v_fx_daily WHERE date_key='2024-04-08') / "
                   "(SELECT units_per_usd FROM mart.v_fx_daily WHERE date_key='2026-09-30') - 1 AS r").r[0])
chk = [
    check("ZWG cash USD return 2024-04-08..2026-09-30: daily engine vs independent SQL", 100 * ret(P["ZWG_cash__usd"], START, END), 100 * sql_cash, 1e-9),
    check("Brief tie-out: ZWG cash USD return to 2026-11-12 (brief -48.9%)", round(100 * cash_ext, 1), -48.9, 0.05),
    check("Brief tie-out: ZWG cash USD return 2026 YTD to 12 Nov (brief -2.1%)", round(100 * ytd_ext, 1), -2.1, 0.05),
    check("Required-yield identity: (1+y)^T (1-e)^T (1-c) = (1+r)^T, 3m hold with round trip (max abs diff)",
          max(abs((1 + required(r_usd, e_2026, c, T)) ** T * (1 - e_2026) ** T * (1 - c) - (1 + r_usd) ** T)
              for c in (0.0, c_latest) for T in (1 / 12, 0.25, 0.5, 1.0)), 0.0, 1e-12),
    check("Required yield with no depreciation, cost or hold effect equals the T-bill rate", 100 * required(r_usd, 0, 0, 1), 100 * r_usd, 1e-9),
    check("Bridge check rows: max |effects - total| (log pts)", float(bridge[bridge.step.str.contains("check")].amount.abs().max()), 0.0, 1e-9),
    check("Monthly returns compound to the cumulative index (max abs diff, index pts)",
          float(max(abs(g.sort_values("period").eval("1+usd_adjusted_return_pct/100").prod() * 100 - g.cum_usd_index.iloc[-1])
                    for _, g in monthly.groupby("instrument"))), 0.0, 1e-6),
    check("Full-month interest = r*days/365 (Sep 2026, 3m max), pct", float(monthly.query("instrument=='ZWG_3m_deposit_max' and period=='2026-09'").nominal_return_pct.iloc[0]),
          float(mi.loc["2026-09", "three_month_max_pct"]) * 30 / 365, 1e-9),
]
metrics = pd.DataFrame(chk)

# key metrics vs the USD baseline (T-bill) for Agent 5
key = sub[sub.subperiod.isin(["P0 full window", "P4 2026 to Sep", "P5 since 2025 (Jan 2025 to Sep 2026)"])]
for _, r in key.iterrows():
    if r.instrument.startswith("ZWG"):
        metrics.loc[len(metrics)] = {"question_id": "BQ2", "model": r.instrument, "metric": f"annualised USD-adjusted return, {r.subperiod} (%)",
                                     "value": r.annualised_pct, "baseline_value": r.tbill_annualised_pct,
                                     "beats_baseline": bool(r.annualised_pct > r.tbill_annualised_pct)}

# ------------------------------------------------------------------ write
OUT.mkdir(exist_ok=True)
outputs = {"result_returns_monthly.csv": monthly, "result_bridge.csv": bridge, "result_subperiods.csv": sub,
           "result_scenarios.csv": scenarios, "result_rolling.csv": rolling, "result_metrics.csv": metrics,
           "result_sensitivity.csv": sensitivity}
for fn, df in outputs.items():
    df.to_csv(OUT / fn, index=False, float_format="%.6f")
    print(f"{fn}: {len(df)} rows")
params = {"e_2026_ann_pct": 100 * e_2026, "c_latest_pct": 100 * c_latest, "c_2026_avg_pct": 100 * c_2026, "r_usd_bey_oct2026_pct": 100 * r_usd,
          "mc_mu_m": mu_m, "mc_sd_m": sd_m, "mc_months": len(calm), "dtdf_rate": DTDF_RATE, "dtdf_start": str(DTDF_START.date())}
pd.Series(params).to_csv(OUT / "run_parameters.csv", header=["value"])
print(pd.Series(params).to_string())
print("VALIDATION:", "ALL PASS" if metrics[metrics.question_id == "VAL"].beats_baseline.all() else "FAIL")
print(metrics[metrics.question_id == "VAL"][["metric", "value", "baseline_value", "beats_baseline"]].to_string(index=False))
