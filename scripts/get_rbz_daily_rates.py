"""Download RBZ daily interbank rate PDFs (D1).

Run: python get_rbz_daily_rates.py 2024-04-08 2026-11-13 D1_rbz_daily_rates
RBZ file names vary (zero-padded or not), and some business days have no file.
Every attempted date is logged to D1_download_log.csv so Agent 2 can fill gaps.
"""
import csv, sys, time, datetime as dt, pathlib, urllib.request

BASE = "https://www.rbz.co.zw/documents/Exchange_Rates"
PATTERNS = ["RATES_{dd}_{MON}_{Y}.pdf", "RATES_{d}_{MON}_{Y}.pdf"]


def candidates(d):
    folder = f"{BASE}/{d.year}/{d.strftime('%B')}/"
    for p in PATTERNS:
        yield folder + p.format(dd=d.strftime("%d"), d=d.day, MON=d.strftime("%B").upper(), Y=d.year)


def main(start, end, out_dir):
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    d, end = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    with open(out / "D1_download_log.csv", "w", newline="") as log:
        w = csv.writer(log)
        w.writerow(["rate_date", "status", "url", "bytes"])
        while d <= end:
            if d.weekday() < 5:  # Mon-Fri only
                target = out / f"RBZ_RATES_{d.isoformat()}.pdf"
                status, used, size = "missing", "", 0
                for u in candidates(d):
                    try:
                        data = urllib.request.urlopen(u, timeout=30).read()
                        if data[:4] == b"%PDF":
                            target.write_bytes(data)
                            status, used, size = "ok", u, len(data)
                            break
                    except Exception:
                        continue
                w.writerow([d.isoformat(), status, used, size])
                time.sleep(0.5)  # be polite to the RBZ server
            d += dt.timedelta(days=1)


if __name__ == "__main__":
    main(*sys.argv[1:4])
