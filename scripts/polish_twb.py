"""Polish the ZiG Returns Tableau workbook XML (run after the dashboard and story exist).

- Series labels follow the 2026-11-14 revision: "3-month index (top/lowest rate)", "savings (top/lowest rate)".
- Plain captions for axis and header fields; "Product" for the instrument label.
- One colour per product, ZiG cash as the orange accent (palette checked for colour-blind separation).
- Direct line-end labels on S2 Value; colour legends on S3 Spreads and S4 Break-even.

Run: python3 polish_twb.py <in.twb> <out.twb>    (works on a .twb or on the .twb inside a .twbx)
Tested: the output opens in Tableau Public 2026.3 and was published from there.
"""
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
s = open(src, "rb").read().decode("utf-8")
crlf = "\r\n" in s
s = s.replace("\r\n", "\n")

LABELS = {
    "ZiG savings (min)": "ZiG savings (lowest rate)",
    "ZiG savings (max)": "ZiG savings (top rate)",
    "ZiG 3-month deposit (min)": "ZiG 3-month index (lowest rate)",
    "ZiG 3-month deposit (max)": "ZiG 3-month index (top rate)",
}
for a, b in LABELS.items():
    s = s.replace(f"&quot;{a}&quot;", f"&quot;{b}&quot;")
s = s.replace("caption='Instrument Label'", "caption='Product'")

CAPTIONS = [  # (datasource, column, datatype, role, type, caption)
    ("fx_daily", "zwg_per_usd", "real", "measure", "quantitative", "ZiG per US$ (RBZ official mid rate)"),
    ("returns_monthly", "cum_usd_index", "real", "measure", "quantitative", "US$ value of 100 placed on 8 Apr 2024"),
    ("subperiods", "spread_vs_tbill_ann_pp", "real", "measure", "quantitative", "Gap to the US T-bill (percentage points a year)"),
    ("subperiods", "subperiod", "string", "dimension", "nominal", "Period"),
    ("scenarios", "p50", "real", "measure", "quantitative", "ZiG yield needed to match the T-bill (% a year)"),
    ("scenarios", "conversion_case", "string", "dimension", "nominal", "Conversion"),
    ("scenarios", "hold_months", "integer", "measure", "quantitative", "Months held"),
    ("rolling", "share_loss_pct", "real", "measure", "quantitative", "Share of 90-day windows with a US$ loss (%)"),
]
COLOURS = [
    ("ZiG cash", "#d9480f"), ("ZiG 3-month index (top rate)", "#1e8a55"), ("ZiG 3-month index (lowest rate)", "#8cc4a3"),
    ("ZiG savings (top rate)", "#6c7a73"), ("ZiG savings (lowest rate)", "#a3ada8"), ("RBZ ZiGDTDF 90-day bill", "#7b5ea7"),
    ("US 3-month T-bill", "#2563b0"), ("USD cash", "#a3ada8"),
]
LABEL_CI = "<column-instance column='[Calculation_instrument_label]' derivation='None' name='[none:Calculation_instrument_label:nk]' pivot='key' type='nominal' />"
PALETTE = ("<style>\n<style-rule element='mark'>\n<encoding attr='color' field='[none:Calculation_instrument_label:nk]' type='palette'>\n"
           + "".join(f"<map to='{c}'>\n<bucket>&quot;{l}&quot;</bucket>\n</map>\n" for l, c in COLOURS)
           + "</encoding>\n</style-rule>\n</style>\n")


def edit_ds(name, fn):
    global s
    m = re.search(rf"<datasource caption='{name}' inline='true'.*?</datasource>", s, re.S)
    assert m, name
    s = s[:m.start()] + fn(m.group(0)) + s[m.end():]


for ds, col, dt, role, typ, cap in CAPTIONS:
    plain = f"<column datatype='{dt}' name='[{col}]' role='{role}' type='{typ}' />"
    named = f"<column caption='{cap}' datatype='{dt}' name='[{col}]' role='{role}' type='{typ}' />"
    edit_ds(ds, lambda b: b.replace("<aliases enabled='yes' />", "<aliases enabled='yes' />\n" + named, 1))
    s = s.replace(plain, named)

for ds in ("returns_monthly", "subperiods", "rolling"):
    def add_palette(b):
        cut = min(i for i in (b.find(t) for t in ("<group ", "<drill-paths", "<extract ", "<layout ")) if i >= 0)
        b = b[:cut] + LABEL_CI + "\n" + b[cut:]
        return b.replace("<semantic-values>", PALETTE + "<semantic-values>", 1)
    edit_ds(ds, add_palette)

# S2 Value: label the lines at their ends
m = re.search(r"<worksheet name='S2 Value'>.*?</worksheet>", s, re.S)
w = m.group(0)
colour = "<color column='[federated.returns_monthly].[none:Calculation_instrument_label:nk]' />"
w = w.replace(colour, colour + "\n<text column='[federated.returns_monthly].[none:Calculation_instrument_label:nk]' />", 1)
w = w.replace("</encodings>", "</encodings>\n<style>\n<style-rule element='mark'>\n<format attr='mark-labels-show' value='true' />\n"
              "<format attr='mark-labels-cull' value='true' />\n</style-rule>\n</style>", 1)
s = s[:m.start()] + w + s[m.end():]


def legend(win, param):
    global s
    m = re.search(rf"<window class='worksheet' name='{win}'>.*?</window>", s, re.S)
    w = m.group(0)
    i = w.index("</cards>")
    w = w[:i] + (f"<edge name='right'>\n<strip size='160'>\n<card pane-specification-id='0' param='{param}' type='color' />\n"
                 "</strip>\n</edge>\n") + w[i:]
    s = s[:m.start()] + w + s[m.end():]


legend("S3 Spreads", "[federated.subperiods].[none:Calculation_instrument_label:nk]")
legend("S4 Break-even", "[federated.scenarios].[none:conversion_case:nk]")

for a in LABELS:
    assert a not in s, a
open(dst, "wb").write((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))
print("ok", dst)
