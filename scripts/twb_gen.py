"""Generate the UMFDOP ZiG-returns Tableau workbook (.twb) over the BI data CSVs.

Run: python3 twb_gen.py <out.twb> <data_dir_with_forward_slashes>
One text-file datasource per CSV; worksheets S1-S6 plus three tie-out sheets (T1-T3).
Tested: opens in Tableau 2026.3 (workbook schema 18.1). The `dash` block below is not written: a generated
dashboard failed to load ("sheet has no visual representation"), so the dashboard and story are added in Tableau.
Schema notes learned in testing: no <simple-id> elements at 18.1; in <view>, <sort> must come before <slices>.
"""
import sys
from xml.sax.saxutils import quoteattr, escape

OUT, DIR = sys.argv[1], sys.argv[2]

TYPES = {"s": ("string", "dimension", "nominal"), "d": ("real", "measure", "quantitative"),
         "i": ("integer", "measure", "quantitative"), "t": ("date", "dimension", "ordinal"), "b": ("boolean", "dimension", "nominal")}
DS = {
    "findings": [("row_id", "i"), ("question_id", "s"), ("finding", "s"), ("number", "d"), ("unit", "s"), ("confidence", "s"), ("limits", "s")],
    "fx_daily": [("date_key", "t"), ("zwg_per_usd", "d"), ("is_carried_forward", "b"), ("rate_source", "s")],
    "returns_monthly": [("question_id", "s"), ("period", "s"), ("period_date", "t"), ("instrument", "s"), ("currency_held", "s"), ("days", "i"),
                        ("partial_month", "b"), ("rate_pct_pa", "d"), ("nominal_return_pct", "d"), ("fx_effect_pct", "d"),
                        ("usd_adjusted_return_pct", "d"), ("real_zwg_return_pct", "d"), ("usd_adjusted_real_return_pct", "d"),
                        ("cum_usd_index", "d"), ("zwg_cpi_imputed", "b")],
    "subperiods": [("question_id", "s"), ("subperiod", "s"), ("subperiod_label", "s"), ("subperiod_order", "i"), ("instrument", "s"),
                   ("from", "t"), ("to", "t"), ("days", "i"), ("usd_adjusted_return_pct", "d"), ("annualised_pct", "d"),
                   ("tbill_return_pct", "d"), ("tbill_annualised_pct", "d"), ("spread_vs_tbill_ann_pp", "d"),
                   ("spread_vs_usd_cash_ann_pp", "d"), ("instrument_start_later", "b")],
    "scenarios": [("question_id", "s"), ("scenario", "s"), ("kind", "s"), ("conversion_case", "s"), ("depreciation_case", "s"),
                  ("hold_label", "s"), ("hold_months", "i"), ("instrument", "s"), ("assumptions", "s"), ("p5", "d"), ("p50", "d"),
                  ("p95", "d"), ("unit", "s")],
    "rolling": [("question_id", "s"), ("instrument", "s"), ("window_days", "i"), ("regime", "s"), ("windows", "i"), ("share_loss_pct", "d"),
                ("share_below_tbill_pct", "d"), ("worst_return_pct", "d"), ("worst_window_start", "t"), ("median_return_pct", "d"),
                ("best_return_pct", "d")],
}
LABEL_CALC = ('CASE [instrument] WHEN "ZWG_cash" THEN "ZiG cash" WHEN "ZWG_savings_min" THEN "ZiG savings (min)" '
              'WHEN "ZWG_savings_max" THEN "ZiG savings (max)" WHEN "ZWG_3m_deposit_min" THEN "ZiG 3-month deposit (min)" '
              'WHEN "ZWG_3m_deposit_max" THEN "ZiG 3-month deposit (max)" WHEN "ZWG_ZiGDTDF_90d" THEN "RBZ ZiGDTDF 90-day bill" '
              'WHEN "USD_cash" THEN "USD cash" WHEN "USD_tbill_3m" THEN "US 3-month T-bill" END')
CALCS = {  # datasource -> [(internal name, caption, datatype, role, type, formula)]
    "fx_daily": [("Calculation_rate_20261113", "Rate on 2026-11-13", "real", "measure", "quantitative",
                  "IF [date_key] = #2026-11-13# THEN [zwg_per_usd] END")],
    "returns_monthly": [("Calculation_instrument_label", "Instrument Label", "string", "dimension", "nominal", LABEL_CALC),
                        ("Calculation_cash_index_sep26", "ZiG cash index Sep 2026", "real", "measure", "quantitative",
                         'IF [instrument] = "ZWG_cash" AND [period] = "2026-09" THEN [cum_usd_index] END')],
    "subperiods": [("Calculation_instrument_label", "Instrument Label", "string", "dimension", "nominal", LABEL_CALC)],
    "rolling": [("Calculation_instrument_label", "Instrument Label", "string", "dimension", "nominal", LABEL_CALC)],
}


def fed(ds):
    return f"federated.{ds}"


def datasource_xml(ds, cols):
    tcon = f"textscan.{ds}"
    x = [f"<datasource caption='{ds}' inline='true' name='{fed(ds)}' version='18.1'>",
         "<connection class='federated'>", "<named-connections>",
         f"<named-connection caption='{ds}' name='{tcon}'>",
         f"<connection class='textscan' directory={quoteattr(DIR)} filename='{ds}.csv' password='' server='' />",
         "</named-connection>", "</named-connections>",
         f"<relation connection='{tcon}' name='{ds}.csv' table='[{ds}#csv]' type='table'>",
         "<columns character-set='UTF-8' header='yes' locale='en_US' separator=','>"]
    for i, (c, t) in enumerate(cols):
        x.append(f"<column datatype='{TYPES[t][0]}' name={quoteattr(c)} ordinal='{i}' />")
    x += ["</columns>", "</relation>", "</connection>", "<aliases enabled='yes' />"]
    for c, t in cols:
        dt, role, typ = TYPES[t]
        x.append(f"<column datatype='{dt}' name={quoteattr('[' + c + ']')} role='{role}' type='{typ}' />")
    for name, cap, dt, role, typ, f in CALCS.get(ds, []):
        fmt = " default-format='n#,##0.0000;-#,##0.0000'" if name == "Calculation_rate_20261113" else ""
        x.append(f"<column caption={quoteattr(cap)} datatype='{dt}'{fmt} name='[{name}]' role='{role}' type='{typ}'>"
                 f"<calculation class='tableau' formula={quoteattr(f)} /></column>")
    x.append("</datasource>")
    return "\n".join(x)


def coldef(ds, c):
    for n, t in DS[ds]:
        if n == c:
            dt, role, typ = TYPES[t]
            return f"<column datatype='{dt}' name={quoteattr('[' + c + ']')} role='{role}' type='{typ}' />"
    for name, cap, dt, role, typ, f in CALCS.get(ds, []):
        if name == c:
            fmt = " default-format='n#,##0.0000;-#,##0.0000'" if name == "Calculation_rate_20261113" else ""
            return (f"<column caption={quoteattr(cap)} datatype='{dt}'{fmt} name='[{name}]' role='{role}' type='{typ}'>"
                    f"<calculation class='tableau' formula={quoteattr(f)} /></column>")
    raise KeyError(c)


DERIV = {"none": "None", "sum": "Sum", "avg": "Avg", "tdy": "Day-Trunc", "min": "Min"}


def inst(c, d, k):
    """column-instance tuple: (column, derivation prefix, key nk/ok/qk)"""
    return (c, d, k)


def iname(ci):
    c, d, k = ci
    return f"[{d}:{c}:{k}]"


def ref(ds, ci):
    return f"[{fed(ds)}].{iname(ci)}"


def ci_xml(ci):
    c, d, k = ci
    typ = {"nk": "nominal", "ok": "ordinal", "qk": "quantitative"}[k]
    return f"<column-instance column='[{c}]' derivation='{DERIV[d]}' name='{iname(ci)}' pivot='key' type='{typ}' />"


def member(v):
    if isinstance(v, str):
        return quoteattr('"' + v + '"')
    return quoteattr(str(v))


def worksheet(name, ds, rows, cols, mark, instances, filters=(), color=None, text=None, label=None, title=None, sort=None):
    deps = sorted({c for c, d, k in instances})
    x = [f"<worksheet name={quoteattr(name)}>"]
    if title:
        x += ["<layout-options>", "<title>", "<formatted-text>", f"<run bold='true' fontsize='13'>{escape(title)}</run>",
              "</formatted-text>", "</title>", "</layout-options>"]
    x += ["<table>", "<view>", "<datasources>", f"<datasource caption='{ds}' name='{fed(ds)}' />", "</datasources>",
          f"<datasource-dependencies datasource='{fed(ds)}'>"]
    x += [coldef(ds, c) for c in deps]
    x += [ci_xml(ci) for ci in sorted(set(instances), key=iname)]
    x.append("</datasource-dependencies>")
    for ci, vals in filters:
        x.append(f"<filter class='categorical' column='{ref(ds, ci)}'>")
        x.append("<groupfilter function='union' user:ui-domain='database' user:ui-enumeration='inclusive' user:ui-marker='enumerate'>")
        for v in vals:
            x.append(f"<groupfilter function='member' level='{iname(ci)}' member={member(v)} />")
        x += ["</groupfilter>", "</filter>"]
    if sort:
        x.append(f"<sort class='computed' column='{ref(ds, sort[0])}' direction='{sort[2]}' using='{ref(ds, sort[1])}' />")
    if filters:
        x.append("<slices>")
        x += [f"<column>{ref(ds, ci)}</column>" for ci, _ in filters]
        x.append("</slices>")
    x += ["<aggregation value='true' />", "</view>", "<style />", "<panes>",
          "<pane selection-relaxation-option='selection-relaxation-allow'>", "<view>", "<breakdown value='auto' />", "</view>",
          f"<mark class='{mark}' />"]
    enc = []
    if color:
        enc.append(f"<color column='{ref(ds, color)}' />")
    if text:
        enc.append(f"<text column='{ref(ds, text)}' />")
    if label:
        enc.append(f"<text column='{ref(ds, label)}' />")
    if enc:
        x += ["<encodings>"] + enc + ["</encodings>"]
    if label:
        x += ["<style>", "<style-rule element='mark'>", "<format attr='mark-labels-show' value='true' />",
              "<format attr='mark-labels-cull' value='true' />", "</style-rule>", "</style>"]
    x += ["</pane>", "</panes>", f"<rows>{' / '.join(ref(ds, r) for r in rows) if rows else ''}</rows>",
          f"<cols>{' / '.join(ref(ds, c) for c in cols) if cols else ''}</cols>", "</table>",
          "</worksheet>"]
    return "\n".join(x)


def hex_uuid(seed):
    import hashlib, uuid
    return str(uuid.UUID(hashlib.md5(seed.encode()).hexdigest())).upper()


LBL = "Calculation_instrument_label"
sheets = []
# S1 FX
d1, v1 = inst("date_key", "tdy", "qk"), inst("zwg_per_usd", "avg", "qk")
sheets.append(("S1 FX", worksheet("S1 FX", "fx_daily", [v1], [d1], "Line", [d1, v1],
                                  title="One day in September 2024 decides the whole period: RBZ mid rate, ZiG per US$")))
# S2 Value
d2, v2, l2, i2 = inst("period_date", "tdy", "qk"), inst("cum_usd_index", "sum", "qk"), inst(LBL, "none", "nk"), inst("instrument", "none", "nk")
sheets.append(("S2 Value", worksheet("S2 Value", "returns_monthly", [v2], [d2], "Line", [d2, v2, l2, i2],
                                     filters=[(i2, ["ZWG_cash", "ZWG_savings_max", "ZWG_3m_deposit_max", "USD_tbill_3m", "USD_cash"])],
                                     color=l2, title="US$ value of 100 placed on 2024-04-08, month-end")))
# S3 Spreads
p3, l3, i3, v3 = inst("subperiod", "none", "nk"), inst(LBL, "none", "nk"), inst("instrument", "none", "nk"), inst("spread_vs_tbill_ann_pp", "sum", "qk")
sheets.append(("S3 Spreads", worksheet("S3 Spreads", "subperiods", [v3], [p3, l3], "Bar", [p3, l3, i3, v3],
                                       filters=[(p3, ["P1 pre-devaluation", "P3 2025", "P4 2026 to Sep"]),
                                                (i3, ["ZWG_cash", "ZWG_savings_max", "ZWG_3m_deposit_max", "ZWG_ZiGDTDF_90d"])],
                                       color=l3, label=v3, title="Since 2025, the top-rate 3-month index beat the US T-bill; savings did not (pp a year)")))
# S4 Break-even
h4, c4, k4, e4, v4 = inst("hold_months", "none", "ok"), inst("conversion_case", "none", "nk"), inst("kind", "none", "nk"), inst("depreciation_case", "none", "nk"), inst("p50", "sum", "qk")
sheets.append(("S4 Break-even", worksheet("S4 Break-even", "scenarios", [v4], [h4, c4], "Bar", [h4, c4, k4, e4, v4],
                                          filters=[(k4, ["required ZiG yield"]), (e4, ["2026 realised depreciation"]), (h4, [3, 6, 12])],
                                          color=c4, label=v4, title="ZiG yield needed to match the US T-bill (% a year) by months held")))
# S5 Loss windows
l5, i5, w5, r5, v5 = inst(LBL, "none", "nk"), inst("instrument", "none", "nk"), inst("window_days", "none", "ok"), inst("regime", "none", "nk"), inst("share_loss_pct", "sum", "qk")
sheets.append(("S5 Loss windows", worksheet("S5 Loss windows", "rolling", [l5], [v5], "Bar", [l5, i5, w5, r5, v5],
                                            filters=[(w5, [90]), (r5, ["windows starting 2025-01-01 or later"])],
                                            label=v5, sort=(l5, v5, "DESC"), title="Share of 90-day windows since 2025 that lost US$ value (%)")))
# S6 Findings
r6, q6, f6, n6 = inst("row_id", "none", "ok"), inst("question_id", "none", "nk"), inst("finding", "none", "nk"), inst("number", "sum", "qk")
sheets.append(("S6 Findings", worksheet("S6 Findings", "findings", [r6, q6, f6], [], "Text", [r6, q6, f6, n6], text=n6,
                                        title="Every number, with its source row (result_findings.csv)")))
# Tie-out sheets
sheets.append(("T1 KPI tie-out", worksheet("T1 KPI tie-out", "findings", [r6, f6], [], "Text", [r6, f6, n6], text=n6,
                                           filters=[(r6, [0, 4, 6, 8, 12, 13, 17, 18])], title="Tie-out: headline KPIs (result_findings rows)")))
v7 = inst("Calculation_rate_20261113", "sum", "qk")
sheets.append(("T2 FX 2026-11-13", worksheet("T2 FX 2026-11-13", "fx_daily", [], [], "Text", [v7], text=v7, title="Tie-out: ZiG per US$ on 2026-11-13")))
v8 = inst("Calculation_cash_index_sep26", "sum", "qk")
sheets.append(("T3 Index Sep 2026", worksheet("T3 Index Sep 2026", "returns_monthly", [], [], "Text", [v8], text=v8,
                                              title="Tie-out: ZiG cash, US$100 placed 2024-04-08, value at Sep 2026")))


def zone(zid, name, x, y, w, h):
    return f"<zone h='{h}' id='{zid}' name={quoteattr(name)} w='{w}' x='{x}' y='{y}' />"


dash = ["<dashboards>", "<dashboard name='ZiG returns'>", "<style />",
        "<size maxheight='800' maxwidth='1200' minheight='800' minwidth='1200' />", "<zones>",
        "<zone h='100000' id='1' type='layout-basic' w='100000' x='0' y='0'>",
        zone(2, "S1 FX", 0, 0, 50000, 33333), zone(3, "S2 Value", 50000, 0, 50000, 33333),
        zone(4, "S3 Spreads", 0, 33333, 50000, 33333), zone(5, "S4 Break-even", 50000, 33333, 50000, 33333),
        zone(6, "S5 Loss windows", 0, 66666, 50000, 33334), zone(7, "T1 KPI tie-out", 50000, 66666, 50000, 33334),
        "</zone>", "</zones>", "</dashboard>", "</dashboards>"]

windows = ["<windows source-height='30'>"]
for n, _ in sheets:
    windows.append(f"<window class='worksheet' name={quoteattr(n)}><cards><edge name='left'><strip size='160'><card type='pages' /><card type='filters' /><card type='marks' /></strip></edge><edge name='top'><strip size='2147483647'><card type='columns' /></strip><strip size='2147483647'><card type='rows' /></strip><strip size='31'><card type='title' /></strip></edge></cards></window>")
windows.append("</windows>")

xml = ["<?xml version='1.0' encoding='utf-8' ?>", "",
       "<workbook original-version='18.1' source-build='2026.3.0' source-platform='win' version='18.1' xmlns:user='http://www.tableausoftware.com/xml/user'>",
       "<preferences>", "<preference name='ui.encoding.shelf.height' value='24' />", "<preference name='ui.shelf.height' value='26' />", "</preferences>",
       "<datasources>"] + [datasource_xml(d, c) for d, c in DS.items()] + ["</datasources>", "<worksheets>"] + [s for _, s in sheets] + \
      ["</worksheets>"] + windows + ["</workbook>", ""]
open(OUT, "w", encoding="utf-8").write("\n".join(xml))
print("ok", OUT)
