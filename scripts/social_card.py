"""GitHub social preview card, 1280x640 PNG. Run: python3 social_card.py <repo_dir> <out.png>"""
import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

repo, out = sys.argv[1], sys.argv[2]
serif = "Caladea"   # metric-compatible with Cambria
sans = "Carlito"    # metric-compatible with Calibri
DARK, INK, MUTED, GRID = "#123B27", "#1F2A24", "#5B6B63", "#E3E8E5"
SERIES = [("USD_tbill_3m", "US 3-month T-bill", "#2563B0"),
          ("ZWG_3m_deposit_max", "ZiG 3-month index, top rate", "#1E8A55"),
          ("ZWG_cash", "ZiG cash", "#D9480F")]

m = pd.read_csv(f"{repo}/results/result_returns_monthly.csv")
fig = plt.figure(figsize=(12.8, 6.4), dpi=100)
fig.patch.set_facecolor("white")

# left panel
left = fig.add_axes([0, 0, 0.44, 1])
left.set_axis_off()
left.add_patch(plt.Rectangle((0, 0), 1, 1, color=DARK, transform=left.transAxes))
t = lambda x, y, s, **k: left.text(x, y, s, transform=left.transAxes, va="top", ha="left", **k)
t(0.11, 0.86, "Does holding\nZimbabwe's ZiG pay?", color="white", fontsize=34, fontfamily=serif, fontweight="bold", linespacing=1.12)
t(0.11, 0.56, "Returns in US-dollar terms,\nApril 2024 to September 2026", color="#A9C9B5", fontsize=19, fontfamily=sans, linespacing=1.25)
t(0.11, 0.37, r"US\$100 → US\$51", color="#E0B73E", fontsize=34, fontfamily=serif, fontweight="bold")
t(0.11, 0.26, "ZiG cash, launch to Sep 2026", color="white", fontsize=16, fontfamily=sans)
t(0.11, 0.12, "Python · PostgreSQL · Power BI · Tableau", color="#A9C9B5", fontsize=15, fontfamily=sans)

# right chart
ax = fig.add_axes([0.505, 0.15, 0.30, 0.68])
for inst, label, col in SERIES:
    g = m[m.instrument == inst].sort_values("period")
    x = [pd.Timestamp("2024-04-08")] + list(pd.to_datetime(g.period + "-01") + pd.offsets.MonthEnd(0))
    y = [100.0] + list(g.cum_usd_index)
    ax.plot(x, y, color=col, linewidth=2.6, solid_capstyle="round", zorder=3)
    ax.scatter([x[-1]], [y[-1]], s=46, color=col, edgecolor="white", linewidth=2, zorder=4)
    ax.annotate(f"{label}\nUS${y[-1]:.0f}", xy=(x[-1], y[-1]), xytext=(10, 0), textcoords="offset points",
                va="center", ha="left", fontsize=13.5, fontfamily=sans, color=INK, linespacing=1.15, annotation_clip=False)
ax.axhline(100, color=MUTED, linewidth=1, linestyle=(0, (3, 3)), zorder=1)
ax.set_ylim(40, 120)
ax.set_yticks([50, 75, 100])
ax.set_yticklabels(["US$50", "US$75", "US$100"], fontsize=12.5, fontfamily=sans, color=MUTED)
ax.set_xticks(pd.to_datetime(["2024-07-01", "2025-07-01", "2026-07-01"]))
ax.set_xticklabels(["2024", "2025", "2026"], fontsize=12.5, fontfamily=sans, color=MUTED)
ax.grid(axis="y", color=GRID, linewidth=1)
for sp in ax.spines.values():
    sp.set_visible(False)
ax.tick_params(length=0)
fig.text(0.505, 0.9, "US$ value of 100 placed in each on 8 Apr 2024", fontsize=17, fontfamily=sans, fontweight="bold", color=INK)
fig.text(0.505, 0.055, "Month-end values. Source: RBZ, ZIMSTAT, FRED.  github.com/nelsontapfumaneyi", fontsize=12, fontfamily=sans, color=MUTED)
fig.savefig(out, dpi=100, facecolor="white")
print("wrote", out)
