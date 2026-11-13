"""UMFDOP Agent 2 - cleaning script for the 2026-11-13 ZiG returns brief.
Python 3.10+, pandas 2.x or 3.x, pdfplumber 0.11, openpyxl.
Layout: <run_dir>/raw (untouched inputs) -> <run_dir>/clean, <run_dir>/rejects.
Run:    python clean_zig_returns.py <run_dir>
Idempotent: outputs are rewritten on every run; raw files are only read.
"""
import re, sys, xml.etree.ElementTree as ET
from datetime import datetime, timezone, date
from pathlib import Path
import pandas as pd
import pdfplumber

RUN = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
RAW, CLEAN, REJECTS = RUN / "raw", RUN / "clean", RUN / "rejects"
LOADED_AT = datetime.now(timezone.utc).isoformat(timespec="seconds")
MON = "January|February|March|April|May|June|July|August|September|October|November|December"
LOG = []


def log(file_id, n_in, n_out, n_rej, out):
    LOG.append((file_id, n_in, n_out, n_rej))
    print(f"{file_id}: in={n_in} out={n_out} rejected={n_rej} -> {out}")


def lineage(df, source_id):
    df = df.copy()
    df["source_id"], df["loaded_at"] = source_id, LOADED_AT
    return df


def write(good, bad, name):
    good.to_csv(CLEAN / name, index=False)
    bad.to_csv(REJECTS / name.replace(".csv", "_rejects.csv"), index=False)


# ---------------------------------------------------------------- D1 RBZ daily
def row_cells(page, label="USD"):
    """Rebuild a table row from character positions: cells split on gaps > 3pt, spaces inside a cell removed."""
    w = next(w for w in page.extract_words() if w["text"] == label)
    chars = sorted((c for c in page.chars if abs(c["top"] - w["top"]) < 2), key=lambda c: c["x0"])
    cells, cur, prev = [], "", None
    for c in chars:
        if prev is not None and c["x0"] - prev["x1"] > 3:
            cells.append(cur); cur = ""
        cur += c["text"]; prev = c
    cells.append(cur)
    return [re.sub(r"\s+", "", x) for x in cells]


def parse_rbz(path):
    rec = {"source_file": f"raw/D1_rbz_daily_rates/{path.name}", "file_date": path.stem[-10:]}
    try:
        with pdfplumber.open(path) as pdf:
            page = pdf.pages[0]
            text = page.extract_text() or ""
            m = re.search(rf"(\d{{1,2}})\s+({MON}),?\s+(\d{{4}})", text)          # 12 November 2026
            m2 = re.search(rf"({MON})\s+(\d{{1,2}}),?\s+(\d{{4}})", text)         # January 5, 2026
            if m:
                rec["header_date"] = datetime.strptime(" ".join(m.groups()), "%d %B %Y").date().isoformat()
            elif m2:
                rec["header_date"] = datetime.strptime(" ".join(m2.groups()), "%B %d %Y").date().isoformat()
            else:
                rec["header_date"] = None
            cells = row_cells(page)
        rec["bid"], rec["ask"], rec["mid"] = (float(x.replace(",", "")) for x in cells[-3:])
    except Exception as e:  # unreadable file or row not found
        rec["error"] = f"parse_error:{type(e).__name__}"
    return rec


def parse_fcb(path, folder):
    rec = {"source_file": f"raw/{folder}/{path.name}", "file_date": path.stem[-10:]}
    with pdfplumber.open(path) as pdf:
        text = pdf.pages[0].extract_text() or ""
    d = re.search(r"(\d{1,2})-([A-Za-z]{3})-(\d{4})", text)
    m = re.search(r"USD/Z(?:iG|IG|WG)\s+USD/Z\w+\s+\(RTGS\$\)[^\n]*\n\s*((?:\d[ ,]?)+\.\d+)", text)
    rec["header_date"] = datetime.strptime(d.group(0), "%d-%b-%Y").date().isoformat() if d else None
    rec["mid"] = float(re.sub(r"[ ,]", "", m.group(1))) if m else None
    if not m:
        rec["error"] = "parse_error:interbank_rate_not_found"
    return rec


def clean_fx():
    rbz = pd.DataFrame([parse_rbz(p) for p in sorted((RAW / "D1_rbz_daily_rates").glob("*.pdf"))])
    fcb = pd.DataFrame([parse_fcb(p, "D7_fcb_gap_rates") for p in sorted((RAW / "D7_fcb_gap_rates").glob("*.pdf"))])
    for df in (rbz, fcb):
        if "error" not in df:
            df["error"] = None
    rbz["rate_source"], rbz["source_id"] = "RBZ_interbank", "D1"
    fcb["rate_source"], fcb["source_id"] = "FCB_republished_RBZ_interbank", "D7"
    fcb["bid"], fcb["ask"] = None, None

    def checks(df, need_spread):
        r = pd.Series("", index=df.index)
        r[df["error"].notna()] += df["error"].fillna("") + ";"
        r[df["header_date"].isna() & df["error"].isna()] += "no_header_date;"
        r[df["header_date"].notna() & (df["header_date"] != df["file_date"])] += "header_date_mismatch;"
        if need_spread:
            ok = df["error"].isna()
            bad_order = ok & ~((df["bid"] < df["mid"]) & (df["mid"] < df["ask"]))
            bad_mid = ok & ((df["bid"] + df["ask"]) / 2 - df["mid"]).abs().gt(0.0005)
            r[bad_order] += "bid_mid_ask_order;"
            r[bad_mid] += "mid_not_average;"
        return r

    rr, fr = checks(rbz, True), checks(fcb, False)
    fr[fcb["file_date"].isin(rbz.loc[rr.eq(""), "file_date"])] += "date_already_in_rbz;"
    allrows = pd.concat([rbz.assign(reject_reason=rr), fcb.assign(reject_reason=fr)], ignore_index=True)
    good = allrows[allrows["reject_reason"].eq("")].copy()
    bad = allrows[allrows["reject_reason"].ne("")].copy()
    good = good.rename(columns={"file_date": "rate_date"}).sort_values("rate_date")
    good["base_currency"], good["quote_currency"] = "USD", "ZWG"
    good["pct_change_mid"] = (good["mid"] / good["mid"].shift(1) - 1) * 100
    good["flag_jump_gt_5pct"] = good["pct_change_mid"].abs().gt(5)
    good["loaded_at"] = LOADED_AT
    cols = ["rate_date", "base_currency", "quote_currency", "bid", "ask", "mid", "pct_change_mid", "flag_jump_gt_5pct",
            "rate_source", "source_id", "source_file", "loaded_at"]
    write(good[cols], bad, "fx_usd_zwg_daily.csv")
    log("D1+D7", len(allrows), len(good), len(bad), "clean/fx_usd_zwg_daily.csv")
    # Reconciliation: FCB vs RBZ on overlap days
    ov = pd.DataFrame([parse_fcb(p, "D7_fcb_overlap") for p in sorted((RAW / "D7_fcb_overlap").glob("*.pdf"))])
    rec = ov.merge(good.loc[good["rate_source"].eq("RBZ_interbank"), ["rate_date", "mid"]],
                   left_on="file_date", right_on="rate_date", suffixes=("_fcb", "_rbz"))
    rec["diff_abs"] = rec["mid_fcb"] - rec["mid_rbz"]
    rec["diff_pct"] = rec["diff_abs"] / rec["mid_rbz"] * 100
    rec[["rate_date", "mid_rbz", "mid_fcb", "diff_abs", "diff_pct"]].to_csv(CLEAN / "recon_fx_fcb_vs_rbz.csv", index=False)
    return good


# ---------------------------------------------------------------- D2 IMF ER
def clean_imf(fx_daily):
    rows = []
    for fn, tr in (("D2_imf_er_pa.xml", "period_average"), ("D2_imf_er_eop.xml", "end_of_period")):
        for obs in ET.parse(RAW / fn).getroot().iter():
            if obs.tag.endswith("Obs") and "TIME_PERIOD" in obs.attrib:
                rows.append({"period": obs.attrib["TIME_PERIOD"].replace("-M", "-"), "transformation": tr,
                             "usd_per_unit": float(obs.attrib["OBS_VALUE"]), "source_file": f"raw/{fn}"})
    df = pd.DataFrame(rows)
    r = pd.Series("", index=df.index)
    this_month = date.today().strftime("%Y-%m")
    r[df["period"].gt(this_month)] += "future_period;"
    r[df.duplicated(["period", "transformation"], keep="first")] += "duplicate_key;"
    df["currency"] = df["period"].lt("2024-04").map({True: "ZWL", False: "ZWG"})
    df["local_per_usd"] = 1 / df["usd_per_unit"]
    df["flag_partial_zig_month"] = df["period"].eq("2024-04")
    df["period_start"] = pd.to_datetime(df["period"] + "-01").dt.strftime("%Y-%m-%d")
    df["period_end"] = (pd.to_datetime(df["period"] + "-01") + pd.offsets.MonthEnd(0)).dt.strftime("%Y-%m-%d")
    df = lineage(df, "D2")
    good, bad = df[r.eq("")], df[r.ne("")].assign(reject_reason=r[r.ne("")])
    cols = ["period", "period_start", "period_end", "transformation", "currency", "usd_per_unit", "local_per_usd",
            "flag_partial_zig_month", "source_id", "source_file", "loaded_at"]
    write(good[cols].sort_values(["transformation", "period"]), bad, "fx_imf_monthly.csv")
    log("D2", len(df), len(good), len(bad), "clean/fx_imf_monthly.csv")
    # Reconciliation: RBZ daily mid aggregated to month vs IMF
    fx = fx_daily.assign(period=fx_daily["rate_date"].str[:7])
    agg = fx.groupby("period").agg(rbz_avg=("mid", "mean"), rbz_eop=("mid", "last"), rbz_days=("mid", "size")).reset_index()
    imf = good[good["currency"].eq("ZWG")].pivot(index="period", columns="transformation", values="local_per_usd").reset_index()
    rec = agg.merge(imf, on="period", how="inner")
    rec["avg_diff_pct"] = (rec["period_average"] / rec["rbz_avg"] - 1) * 100
    rec["eop_diff_pct"] = (rec["end_of_period"] / rec["rbz_eop"] - 1) * 100
    rec.to_csv(CLEAN / "recon_fx_rbz_vs_imf.csv", index=False)


# ---------------------------------------------------------------- D3 deposit rates
def clean_deposit_rates():
    raw = pd.read_excel(RAW / "D3_rbz_bank_deposit_rates.xlsx", sheet_name="T8.2 ", header=None, dtype=object)
    months = {m[:3]: i for i, m in enumerate(MON.split("|"), 1)}
    rows, year, structural = [], None, 0
    for i, r in raw.iterrows():
        vals = [v for v in r.tolist() if v is not None and not (isinstance(v, float) and pd.isna(v)) and str(v).strip() != ""]
        if not vals:
            continue
        first = str(vals[0]).strip()
        if re.fullmatch(r"\d{4}(\.0)?", first):
            year = int(float(first)); structural += 1; continue
        label = first.lstrip("*").strip()[:3]
        if year and label in months and len(vals) >= 5:
            rows.append({"sheet_row": i + 1, "year": year, "month": months[label], "zig_marker": first.startswith("*"),
                         "raw_values": vals[1:5]})
        else:
            structural += 1  # titles, headers, footnotes
    df = pd.DataFrame(rows)
    num = pd.DataFrame(df["raw_values"].tolist(), columns=["savings_min_pct", "savings_max_pct", "three_month_min_pct", "three_month_max_pct"])
    num = num.apply(pd.to_numeric, errors="coerce")
    df = pd.concat([df.drop(columns="raw_values"), num], axis=1)
    df["period"] = df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2)
    df["period_start"] = df["period"] + "-01"
    df["period_end"] = (pd.to_datetime(df["period_start"]) + pd.offsets.MonthEnd(0)).dt.strftime("%Y-%m-%d")
    df["currency"] = df["zig_marker"].map({True: "ZWG", False: "ZWL"})
    r = pd.Series("", index=df.index)
    r[num.isna().any(axis=1)] += "bad_number;"
    r[df.duplicated("period", keep="first")] += "duplicate_key;"
    r[(df["currency"].eq("ZWG") & df["period"].lt("2024-04")) | (df["currency"].eq("ZWL") & df["period"].ge("2024-04"))] += "currency_marker_inconsistent;"
    df["flag_savings_min_gt_max"] = df["savings_min_pct"] > df["savings_max_pct"]
    df["flag_3m_min_gt_max"] = df["three_month_min_pct"] > df["three_month_max_pct"]
    cols4 = ["savings_min_pct", "savings_max_pct", "three_month_min_pct", "three_month_max_pct"]
    df["flag_same_as_prior_month"] = df[cols4].eq(df[cols4].shift(1)).all(axis=1)
    df["source_file"] = "raw/D3_rbz_bank_deposit_rates.xlsx#T8.2"
    df = lineage(df, "D3")
    good, bad = df[r.eq("")], df[r.ne("")].assign(reject_reason=r[r.ne("")])
    cols = ["period", "period_start", "period_end", "currency"] + cols4 + ["flag_savings_min_gt_max", "flag_3m_min_gt_max",
            "flag_same_as_prior_month", "source_id", "source_file", "loaded_at"]
    write(good[cols], bad, "deposit_rates_monthly.csv")
    log("D3", len(df), len(good), len(bad), f"clean/deposit_rates_monthly.csv (structural rows skipped: {structural})")


# ---------------------------------------------------------------- D4 CPI
def cpi_left_text(page):
    ws = [w for w in page.extract_words() if w["x1"] <= page.width * 0.345]
    ws.sort(key=lambda w: (round(w["top"]), w["x0"]))
    return " ".join(w["text"] for w in ws)


def parse_cpi(path):
    kind, period = path.stem.split("_")[1], path.stem.split("_")[2]
    rec = {"cpi_type": kind, "period": period, "source_file": f"raw/D4_zimstat_cpi/{path.name}"}
    with pdfplumber.open(path) as pdf:
        left = cpi_left_text(pdf.pages[0])
        full = "\n".join((p.extract_text() or "") for p in pdf.pages[:3])
    seg = left[left.find("Consumer Price Index ("):][:400] if "Consumer Price Index (" in left else left[:400]
    pairs = [(f"{m.group(3)}-{datetime.strptime(m.group(2), '%B').month:02d}", float(m.group(1)))
             for m in re.finditer(rf"(\d+(?:\.\d+)?)\s+in\s+(?:in\s+)?({MON})\s+(\d{{4}})", seg)]
    pairs += [(f"{m.group(2)}-{datetime.strptime(m.group(1), '%B').month:02d}", float(m.group(3)))
              for m in re.finditer(rf"In\s+({MON})\s+(\d{{4}}),?\s+(?:it|the\s+index)\s+was\s+(\d+(?:\.\d+)?)", seg)]
    base = re.search(r"\((\w+)\s+(\d{4})\s*=\s*100\)", full.upper())
    rec["index_base"] = f"{base.group(2)}-{datetime.strptime(base.group(1).title(), '%B').month:02d}=100" if base else None
    rec["levels"] = pairs
    # 13-month month-on-month table (rounded to 0.1)
    mom = {}
    lines = full.splitlines()
    for i, l in enumerate(lines[:-1]):
        heads = re.findall(r"([A-Z][a-z]{2,3})-(\d{2})", l)
        nums = re.findall(r"-?\d+\.\d", lines[i + 1])
        if len(heads) >= 10 and len(nums) == len(heads):
            for (mo, yy), v in zip(heads, nums):
                mom[f"20{yy}-{datetime.strptime(mo[:3], '%b').month:02d}"] = float(v)
    rec["mom_table"] = mom
    return rec


def clean_cpi():
    parsed = [parse_cpi(p) for p in sorted((RAW / "D4_zimstat_cpi").glob("*.pdf"))]
    obs, mom_rows, rej = [], [], []
    for r in parsed:
        if not r["levels"]:
            rej.append({**{k: r[k] for k in ("cpi_type", "period", "source_file")}, "reject_reason": "no_index_level_found"})
            continue
        own = [lv for p, lv in r["levels"] if p == r["period"]]
        if not own:
            rej.append({**{k: r[k] for k in ("cpi_type", "period", "source_file")}, "reject_reason": "reference_month_level_missing"})
            continue
        for p, lv in r["levels"]:
            role = "current" if p == r["period"] else ("prior_month" if p < r["period"] and p >= (pd.Period(r["period"]) - 1).strftime("%Y-%m") else "prior_year")
            obs.append({"cpi_type": r["cpi_type"], "period": p, "index_level": lv, "role": role, "published_in": r["period"],
                        "index_base": r["index_base"], "source_file": r["source_file"]})
        for p, v in r["mom_table"].items():
            mom_rows.append({"cpi_type": r["cpi_type"], "period": p, "mom_pct_1dp": v, "published_in": r["period"]})
    obs = lineage(pd.DataFrame(obs), "D4")
    write(obs, pd.DataFrame(rej), "cpi_observations.csv")
    log("D4", len(parsed), len(parsed) - len(rej), len(rej), f"clean/cpi_observations.csv ({len(obs)} level statements)")

    # Revisions: same type and period stated with different levels
    rev = obs.groupby(["cpi_type", "period"])["index_level"].agg(["min", "max", "count"]).reset_index()
    rev = rev[rev["max"] - rev["min"] > 0.005]
    rev.to_csv(CLEAN / "recon_cpi_revisions.csv", index=False)

    # Monthly table with documented fill order
    mom = pd.DataFrame(mom_rows).sort_values("published_in").drop_duplicates(["cpi_type", "period"], keep="last")
    priority = {"current": 1, "prior_month": 2, "prior_year": 3}
    best = obs.assign(p=obs["role"].map(priority)).sort_values(["p", "published_in"]).drop_duplicates(["cpi_type", "period"])
    months = pd.period_range("2024-04", "2026-10", freq="M").strftime("%Y-%m")
    out = []
    for kind in ("ZWG", "USD", "Weighted"):
        base = "2022-06=100" if kind == "USD" else "2024-04=100"
        ser = {}
        for m in months:
            hit = best[(best["cpi_type"] == kind) & (best["period"] == m)]
            if len(hit):
                h = hit.iloc[0]
                ser[m] = (h["index_level"], {"current": "reported_own_release", "prior_month": "reported_in_next_release",
                                              "prior_year": "reported_in_release_12m_later"}[h["role"]], h["source_file"])
            elif kind == "Weighted" and m == "2024-04":
                ser[m] = (100.0, "base_period_definition", "raw/D4_zimstat_cpi (index base April 2024 = 100)")
        for _ in range(3):  # chain gaps from neighbouring months using the published m/m table
            for m in months:
                if m in ser:
                    continue
                nxt = (pd.Period(m) + 1).strftime("%Y-%m")
                prv = (pd.Period(m) - 1).strftime("%Y-%m")
                mm_n = mom[(mom["cpi_type"] == kind) & (mom["period"] == nxt)]["mom_pct_1dp"]
                mm_m = mom[(mom["cpi_type"] == kind) & (mom["period"] == m)]["mom_pct_1dp"]
                if nxt in ser and ser[nxt][1] != "chained_from_mom_1dp" and len(mm_n):
                    ser[m] = (round(ser[nxt][0] / (1 + mm_n.iloc[0] / 100), 2), "chained_from_mom_1dp", "derived")
                elif prv in ser and len(mm_m):
                    ser[m] = (round(ser[prv][0] * (1 + mm_m.iloc[0] / 100), 2), "chained_from_mom_1dp", "derived")
        for m in months:
            lv, how, src = ser.get(m, (None, "missing", None))
            out.append({"cpi_type": kind, "period": m, "period_start": f"{m}-01", "index_base": base,
                        "index_level": lv, "fill_method": how, "is_imputed": how == "chained_from_mom_1dp",
                        "source_file": src})
    cpi = lineage(pd.DataFrame(out), "D4")
    cpi["period_end"] = (pd.to_datetime(cpi["period_start"]) + pd.offsets.MonthEnd(0)).dt.strftime("%Y-%m-%d")
    cpi = cpi.sort_values(["cpi_type", "period"])
    cpi["mom_pct"] = cpi.groupby("cpi_type")["index_level"].pct_change(fill_method=None) * 100
    cpi["yoy_pct"] = cpi.groupby("cpi_type")["index_level"].pct_change(12, fill_method=None) * 100
    cols = ["cpi_type", "period", "period_start", "period_end", "index_base", "index_level", "mom_pct", "yoy_pct",
            "fill_method", "is_imputed", "source_id", "source_file", "loaded_at"]
    cpi[cols].to_csv(CLEAN / "cpi_monthly.csv", index=False)
    print(f"D4 monthly: {len(cpi)} rows -> clean/cpi_monthly.csv;", cpi["fill_method"].value_counts().to_dict())


# ---------------------------------------------------------------- D5 FRED
def clean_fred():
    parts, n_in, bad_all = [], 0, []
    meta = {"DTB3": ("daily", "percent_pa_discount_basis"), "SOFR": ("daily", "percent_pa"), "CPIAUCSL": ("monthly", "index_1982_84=100")}
    for sid, (freq, unit) in meta.items():
        df = pd.read_csv(RAW / f"D5_fred_{sid}.csv", dtype=str, keep_default_na=False)
        n_in += len(df)
        df.columns = ["obs_date", "value_raw"]
        df["value"] = pd.to_numeric(df["value_raw"].replace({".": None, "": None}), errors="coerce")
        df["series_id"], df["frequency"], df["unit"], df["source_file"] = sid, freq, unit, f"raw/D5_fred_{sid}.csv"
        df["currency"] = "USD"
        r = pd.Series("", index=df.index)
        r[pd.to_datetime(df["obs_date"], errors="coerce", format="%Y-%m-%d").isna()] += "bad_date;"
        r[df["value"].isna()] += "no_observation;"  # FRED leaves non-trading days blank
        parts.append(df[r.eq("")]); bad_all.append(df[r.ne("")].assign(reject_reason=r[r.ne("")]))
    good = lineage(pd.concat(parts, ignore_index=True), "D5")
    bad = pd.concat(bad_all, ignore_index=True)
    cols = ["series_id", "obs_date", "value", "unit", "frequency", "currency", "source_id", "source_file", "loaded_at"]
    write(good[cols], bad, "us_benchmarks.csv")
    log("D5", n_in, len(good), len(bad), "clean/us_benchmarks.csv")


# ---------------------------------------------------------------- D6 events
def clean_events():
    df = pd.read_csv(RAW / "D6_rbz_events.csv", dtype=str, keep_default_na=False)
    r = pd.Series("", index=df.index)
    r[pd.to_datetime(df["event_date"], errors="coerce", format="%Y-%m-%d").isna()] += "bad_date;"
    r[~df["currency"].isin(["USD", "ZWG", "ZWL"])] += "bad_currency;"
    r[~df["status"].isin(["verified", "single_source", "unverified"])] += "bad_status;"
    for c in ("rate_pct", "amount_zwg_m", "tenor_days"):
        df[c] = pd.to_numeric(df[c].replace("", None), errors="coerce")
    df["source_file"] = "raw/D6_rbz_events.csv"
    df = lineage(df, "D6")
    good, bad = df[r.eq("")], df[r.ne("")].assign(reject_reason=r[r.ne("")])
    write(good, bad, "rbz_events.csv")
    log("D6", len(df), len(good), len(bad), "clean/rbz_events.csv")


if __name__ == "__main__":
    CLEAN.mkdir(exist_ok=True); REJECTS.mkdir(exist_ok=True)
    fx = clean_fx()
    clean_imf(fx)
    clean_deposit_rates()
    clean_cpi()
    clean_fred()
    clean_events()
    assert all(i == o + r for _, i, o, r in LOG), "row count mismatch: in != out + rejected"
    pd.DataFrame(LOG, columns=["file_id", "rows_in", "rows_out", "rows_rejected"]).to_csv(CLEAN / "run_log.csv", index=False)
    print("RUN OK", LOADED_AT)
