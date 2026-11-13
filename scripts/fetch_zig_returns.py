"""Fetch all raw datasets for the 2026-11-13 ZiG returns brief (D1-D8).
Run: python fetch_zig_returns.py <run_dir>
Writes untouched files to <run_dir>/raw/ and a manifest raw/fetch_manifest.csv.
"""
import csv, re, sys, time, hashlib, datetime as dt, pathlib, urllib.request
from concurrent.futures import ThreadPoolExecutor

RUN = pathlib.Path(sys.argv[1])
RAW = RUN / "raw"
UA = {"User-Agent": "Mozilla/5.0 (UMFDOP research fetch)"}
START, END = dt.date(2024, 4, 8), dt.date(2026, 11, 13)
manifest = []


def get(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def save(dataset, url, path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    manifest.append([dataset, str(path.relative_to(RAW)), url, len(data), hashlib.sha256(data).hexdigest()[:16]])


def bdays(a, b):
    d = a
    while d <= b:
        if d.weekday() < 5:
            yield d
        d += dt.timedelta(days=1)


# ---- D1 RBZ daily rates -------------------------------------------------
def rbz_day(d):
    folder = f"https://www.rbz.co.zw/documents/Exchange_Rates/{d.year}/{d.strftime('%B')}/"
    for name in (f"RATES_{d:%d}_{d:%B}_{d.year}.pdf".upper().replace(".PDF", ".pdf"),
                 f"RATES_{d.day}_{d:%B}_{d.year}.pdf".upper().replace(".PDF", ".pdf")):
        try:
            data = get(folder + name, 45)
            if data[:4] == b"%PDF":
                return d, folder + name, data
        except Exception:
            pass
    return d, "", None


d1_log = []
with ThreadPoolExecutor(max_workers=4) as ex:
    for d, url, data in ex.map(rbz_day, bdays(START, END)):
        if data:
            save("D1", url, RAW / "D1_rbz_daily_rates" / f"RBZ_RATES_{d}.pdf", data)
        d1_log.append([d.isoformat(), "ok" if data else "missing", url])
with open(RAW / "D1_download_log.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["rate_date", "status", "url"]); w.writerows(sorted(d1_log))
missing = [dt.date.fromisoformat(r[0]) for r in d1_log if r[1] == "missing"]
print(f"D1: {len(d1_log) - len(missing)} ok, {len(missing)} missing")

# ---- D7 FCB PDFs for RBZ gap days ----------------------------------------
def fcb_day(d):
    folders = {(d.year, d.month)}
    nxt = d.replace(day=1) + dt.timedelta(days=32)
    folders.add((nxt.year, nxt.month))
    for y, m in sorted(folders):
        for name in (f"Exchange-Rates-{d:%d}-{d:%B}-{d.year}.pdf", f"Exchange-Rates-{d.day}-{d:%B}-{d.year}.pdf"):
            url = f"https://www.firstcapitalbank.co.zw/wp-content/uploads/{y}/{m:02d}/{name}"
            try:
                data = get(url, 45)
                if data[:4] == b"%PDF":
                    return d, url, data
            except Exception:
                pass
    return d, "", None


d7_log = []
with ThreadPoolExecutor(max_workers=4) as ex:
    for d, url, data in ex.map(fcb_day, missing):
        if data:
            save("D7", url, RAW / "D7_fcb_gap_rates" / f"FCB_RATES_{d}.pdf", data)
        d7_log.append([d.isoformat(), "ok" if data else "missing", url])
with open(RAW / "D7_download_log.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["rate_date", "status", "url"]); w.writerows(sorted(d7_log))
print(f"D7: {sum(r[1] == 'ok' for r in d7_log)} of {len(d7_log)} gap days found at FCB")

# ---- D2 IMF ER ------------------------------------------------------------
for t, fn in (("PA_RT", "D2_imf_er_pa.xml"), ("EOP_RT", "D2_imf_er_eop.xml")):
    url = f"https://api.imf.org/external/sdmx/2.1/data/IMF.STA,ER/ZWE.USD_XDC.{t}.M?startPeriod=2024-01"
    save("D2", url, RAW / fn, get(url))
print("D2: ok")

# ---- D3 and D8 RBZ statistics workbooks (links read from the RBZ pages) ----
def rbz_links(page, pattern):
    html = get("https://www.rbz.co.zw" + page).decode("utf-8", "replace")
    return ["https://www.rbz.co.zw" + h for h in re.findall(r'href="(/documents/statistics/[^"]+\.xlsx)"', html) if re.search(pattern, h)]

for url in rbz_links("/index.php/research/markets/interest-rates", r"Bank-Deposits-rates"):
    save("D3", url, RAW / "D3_rbz_bank_deposit_rates.xlsx", get(url))
for url in rbz_links("/index.php/research/markets/monetary-financial-statistics", r"Monetary_Aggregates|Depository_Corporations_Survey"):
    save("D8", url, RAW / ("D8_" + url.rsplit("/", 1)[1]), get(url))
print("D3/D8: ok")

# ---- D4 ZIMSTAT CPI ---------------------------------------------------------
def cpi(args):
    kind, y, m = args
    url = f"https://www.zimstat.co.zw/wp-content/uploads/Macro/Prices/CPI/{y}/CPI_{kind}_{m:02d}_{y}.pdf"
    try:
        data = get(url, 60)
        return args, url, data if data[:4] == b"%PDF" else None
    except Exception:
        return args, url, None

months = [(y, m) for y in (2024, 2025, 2026) for m in range(1, 13) if dt.date(2024, 4, 1) <= dt.date(y, m, 1) <= dt.date(2026, 10, 1)]
jobs = [(k, y, m) for k in ("ZWG", "USD", "Weighted") for y, m in months]
d4_log = []
with ThreadPoolExecutor(max_workers=4) as ex:
    for (k, y, m), url, data in ex.map(cpi, jobs):
        if data:
            save("D4", url, RAW / "D4_zimstat_cpi" / f"CPI_{k}_{y}-{m:02d}.pdf", data)
        d4_log.append([k, f"{y}-{m:02d}", "ok" if data else "missing", url])
with open(RAW / "D4_download_log.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["cpi_type", "period", "status", "url"]); w.writerows(sorted(d4_log))
print(f"D4: {sum(r[2] == 'ok' for r in d4_log)} of {len(d4_log)} CPI PDFs")

# ---- D5 FRED -----------------------------------------------------------------
for sid, cosd in (("DTB3", "2024-04-01"), ("CPIAUCSL", "2024-03-01"), ("SOFR", "2024-04-01")):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd={cosd}"
    save("D5", url, RAW / f"D5_fred_{sid}.csv", get(url))
print("D5: ok")

with open(RAW / "fetch_manifest.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["dataset", "file", "url", "bytes", "sha256_16"]); w.writerows(manifest)
print("FETCH DONE", len(manifest), "files", dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"))
