"""Second pass: retry RBZ gap days, add ZIMSTAT files with irregular names, and fetch FCB overlap days for reconciliation."""
import csv, sys, hashlib, datetime as dt, pathlib, urllib.request, time
RAW = pathlib.Path(sys.argv[1]) / "raw"
UA = {"User-Agent": "Mozilla/5.0 (UMFDOP research fetch)"}
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90) as r:
        return r.read()
man = list(csv.reader(open(RAW / "fetch_manifest.csv")))
def save(ds, url, path, data):
    path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
    man.append([ds, str(path.relative_to(RAW)), url, len(data), hashlib.sha256(data).hexdigest()[:16]])

# 1. Retry RBZ for days still missing after FCB
log7 = list(csv.reader(open(RAW / "D7_download_log.csv")))
still = [r[0] for r in log7[1:] if r[1] == "missing"]
log1 = list(csv.reader(open(RAW / "D1_download_log.csv")))
idx = {r[0]: i for i, r in enumerate(log1)}
recovered = 0
for ds in still:
    d = dt.date.fromisoformat(ds)
    for name in (f"RATES_{d:%d}_{d:%B}_{d.year}", f"RATES_{d.day}_{d:%B}_{d.year}"):
        url = f"https://www.rbz.co.zw/documents/Exchange_Rates/{d.year}/{d:%B}/{name.upper()}.pdf"
        try:
            data = get(url)
            if data[:4] == b"%PDF":
                save("D1", url, RAW / "D1_rbz_daily_rates" / f"RBZ_RATES_{ds}.pdf", data)
                log1[idx[ds]] = [ds, "ok_retry", url]; recovered += 1; break
        except Exception:
            time.sleep(1)
with open(RAW / "D1_download_log.csv", "w", newline="") as f:
    csv.writer(f).writerows(log1)
print("D1 retry recovered", recovered, "of", len(still))

# 2. ZIMSTAT files with irregular names
base = "https://www.zimstat.co.zw/wp-content/uploads/Macro/Prices/CPI/"
alt = {("USD","2024-10"):"2024/CPI_USD_Front_10_2024.pdf", ("USD","2024-12"):"2024/CPI_USD_Front_12_2024.pdf",
       ("USD","2026-08"):"2026/National/08/CPI_USD_Front_page_08_2026.pdf", ("Weighted","2024-09"):"2024/CPI_Weighted_Front_09_2024.pdf",
       ("Weighted","2024-10"):"2024/CPI_Weighted_10_2024%20.pdf", ("Weighted","2024-12"):"2024/CPI_Weighted_Front_12_2024.pdf",
       ("Weighted","2026-08"):"2026/National/08/CPI_Weighted_Front_page_08_2026.pdf", ("ZWG","2024-04"):"2024/CPI_ZIG_04_2024.pdf",
       ("ZWG","2024-05"):"2024/CPI_ZiG_05_2024.pdf", ("ZWG","2024-07"):"2024/CPI_ZiG_07_2024.pdf",
       ("ZWG","2024-09"):"2024/CPI_ZWG_Front_09_2024.pdf", ("ZWG","2024-12"):"2024/CPI_ZWG_Front12_2024.pdf",
       ("ZWG","2026-08"):"2026/National/08/CPI_ZWG_Front_page_08_2026.pdf"}
log4 = list(csv.reader(open(RAW / "D4_download_log.csv")))
for i, r in enumerate(log4[1:], 1):
    key = (r[0], r[1])
    if key in alt:
        url = base + alt[key]; data = get(url)
        save("D4", url, RAW / "D4_zimstat_cpi" / f"CPI_{r[0]}_{r[1]}.pdf", data)
        log4[i] = [r[0], r[1], "ok_alt_name", url]
with open(RAW / "D4_download_log.csv", "w", newline="") as f:
    csv.writer(f).writerows(log4)
print("D4 now", sum(r[2].startswith("ok") for r in log4[1:]), "of", len(log4) - 1)

# 3. FCB files on days that also have an RBZ file (for reconciliation)
over = ["2025-12-29", "2026-01-05", "2026-05-15", "2026-08-12", "2026-08-14", "2026-08-28", "2026-09-07", "2026-11-12"]
ok = 0
for ds in over:
    d = dt.date.fromisoformat(ds)
    for y, m in {(d.year, d.month), ((d.replace(day=28) + dt.timedelta(days=4)).year, (d.replace(day=28) + dt.timedelta(days=4)).month)}:
        for nm in (f"Exchange-Rates-{d:%d}-{d:%B}-{d.year}.pdf", f"Exchange-Rates-{d.day}-{d:%B}-{d.year}.pdf"):
            url = f"https://www.firstcapitalbank.co.zw/wp-content/uploads/{y}/{m:02d}/{nm}"
            try:
                data = get(url)
                if data[:4] == b"%PDF":
                    save("D7_overlap", url, RAW / "D7_fcb_overlap" / f"FCB_RATES_{ds}.pdf", data); ok += 1; raise StopIteration
            except StopIteration:
                break
            except Exception:
                pass
        else:
            continue
        break
print("FCB overlap files", ok, "of", len(over))
with open(RAW / "fetch_manifest.csv", "w", newline="") as f:
    csv.writer(f).writerows(man)
