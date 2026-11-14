"""Generate the UMFDOP ZiG-returns Power BI project (PBIP: TMDL semantic model + PBIR report).

Run: python3 pbip_gen.py <out_dir> <windows_data_folder>
Output mirrors what Power BI Desktop (Nov 2026) writes: definition.pbir v4.0, report schema 3.3.0,
page schema 2.1.0, TMDL compatibilityLevel 1606. CRLF line endings, tabs in TMDL.
"""
import json, os, sys, uuid, hashlib

OUT = sys.argv[1]
DATA = sys.argv[2]  # e.g. C:\path\to\zig-returns\data\
SM = os.path.join(OUT, "ZiG Returns.SemanticModel", "definition")
RP = os.path.join(OUT, "ZiG Returns.Report", "definition")


def lt(seed):
    return str(uuid.UUID(hashlib.md5(seed.encode()).hexdigest()))


def vid(seed):
    return hashlib.md5(seed.encode()).hexdigest()[:20]


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def wjson(path, obj):
    write(path, json.dumps(obj, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------- semantic model
S, D, I, B, T = "string", "double", "int64", "boolean", "dateTime"
MTYPE = {S: "type text", D: "type number", I: "Int64.Type", B: "type logical", T: "type date"}
TABLES = {
    "findings": [("row_id", I), ("question_id", S), ("finding", S), ("number", D), ("unit", S), ("confidence", S), ("limits", S)],
    "returns_monthly": [("question_id", S), ("period", S), ("period_date", T), ("instrument", S), ("currency_held", S), ("days", I),
                        ("partial_month", B), ("rate_pct_pa", D), ("nominal_return_pct", D), ("fx_effect_pct", D),
                        ("usd_adjusted_return_pct", D), ("real_zwg_return_pct", D), ("usd_adjusted_real_return_pct", D),
                        ("cum_usd_index", D), ("zwg_cpi_imputed", B)],
    "subperiods": [("question_id", S), ("subperiod", S), ("subperiod_label", S), ("subperiod_order", I), ("instrument", S), ("from", T),
                   ("to", T), ("days", I), ("usd_adjusted_return_pct", D), ("annualised_pct", D), ("tbill_return_pct", D),
                   ("tbill_annualised_pct", D), ("spread_vs_tbill_ann_pp", D), ("spread_vs_usd_cash_ann_pp", D), ("instrument_start_later", B)],
    "rolling": [("question_id", S), ("instrument", S), ("window_days", I), ("regime", S), ("windows", I), ("share_loss_pct", D),
                ("share_below_tbill_pct", D), ("worst_return_pct", D), ("worst_window_start", T), ("median_return_pct", D), ("best_return_pct", D)],
    "scenarios": [("question_id", S), ("scenario", S), ("kind", S), ("conversion_case", S), ("depreciation_case", S), ("hold_label", S),
                  ("hold_months", I), ("instrument", S), ("assumptions", S), ("p5", D), ("p50", D), ("p95", D), ("unit", S)],
    "fx_daily": [("date_key", T), ("zwg_per_usd", D), ("is_carried_forward", B), ("rate_source", S)],
    "dim_instrument": [("instrument", S), ("label", S), ("currency_held", S), ("sort", I)],
    "dim_date": [("Date", T), ("Year", I), ("MonthNumber", I), ("YearMonth", S), ("MonthLabel", S)],
    "return_basis": [("basis", S), ("order", I)],
}
SORT_BY = {("dim_instrument", "label"): "sort", ("subperiods", "subperiod_label"): "subperiod_order",
           ("scenarios", "hold_label"): "hold_months", ("return_basis", "basis"): "order", ("dim_date", "MonthLabel"): "YearMonth"}
FORMATS = {T: "yyyy-mm-dd", D: "0.00", I: "0"}


def q(name):
    return name if name.replace("_", "").isalnum() else "'" + name.replace("'", "''") + "'"


def table_tmdl(name, cols):
    out = [f"table {q(name)}", f"\tlineageTag: {lt('t' + name)}", ""]
    if name == "dim_date":
        out.insert(1, "\tdataCategory: Time")
    for c, t in cols:
        out.append(f"\tcolumn {q(c)}")
        out.append(f"\t\tdataType: {t}")
        if name == "dim_date" and c == "Date":
            out.append("\t\tisKey")
        if t in FORMATS:
            out.append(f"\t\tformatString: {FORMATS[t]}")
        out.append(f"\t\tlineageTag: {lt('c' + name + c)}")
        out.append("\t\tsummarizeBy: none")
        out.append(f"\t\tsourceColumn: {c}")
        if (name, c) in SORT_BY:
            out.append(f"\t\tsortByColumn: {SORT_BY[(name, c)]}")
        out.append("")
        out.append("\t\tannotation SummarizationSetBy = User")
        out.append("")
    types = ", ".join('{"%s", %s}' % (c, MTYPE[t]) for c, t in cols)
    out += [f"\tpartition {q(name)} = m", "\t\tmode: import", "\t\tsource =",
            "\t\t\t\tlet",
            f'\t\t\t\t    Source = Csv.Document(File.Contents(DataFolder & "{name}.csv"),[Delimiter=",", Columns={len(cols)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
            '\t\t\t\t    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
            f'\t\t\t\t    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{{{types}}}, "en-US")',
            "\t\t\t\tin",
            '\t\t\t\t    #"Changed Type"', "",
            "\tannotation PBI_ResultType = Table", ""]
    return "\n".join(out)


IN5 = '{"ZWG_cash", "ZWG_savings_max", "ZWG_3m_deposit_max", "USD_tbill_3m", "USD_cash"}'
IN4 = '{"ZWG_cash", "ZWG_savings_max", "ZWG_3m_deposit_max", "ZWG_ZiGDTDF_90d"}'
MEASURES = [  # (name, folder, format, DAX)
    ("ZiG Cash USD Return Since Launch %", "Headline", "0.00", "CALCULATE ( SUM ( findings[number] ), findings[row_id] = 0 )"),
    ("3M Deposit Max USD Return Since 2025 %", "Headline", "+0.00;-0.00;0.00", "CALCULATE ( SUM ( findings[number] ), findings[row_id] = 4 )"),
    ("3M Deposit Max Spread 2026 pp", "Headline", "+0.00;-0.00;0.00", "CALCULATE ( SUM ( findings[number] ), findings[row_id] = 6 )"),
    ("Savings Max Spread 2026 pp", "Headline", "+0.00;-0.00;0.00", "CALCULATE ( SUM ( findings[number] ), findings[row_id] = 8 )"),
    ("Required Yield Already ZiG %", "Headline", "0.00", "CALCULATE ( SUM ( findings[number] ), findings[row_id] = 12 )"),
    ("Required Yield Converter 12m %", "Headline", "0.00", "CALCULATE ( SUM ( findings[number] ), findings[row_id] = 13 )"),
    ("ZiG Cash 90d Loss Share Since 2025 %", "Headline", "0.00", "CALCULATE ( SUM ( findings[number] ), findings[row_id] = 17 )"),
    ("3M Max 90d Loss Share Since 2025 %", "Headline", "0.00", "CALCULATE ( SUM ( findings[number] ), findings[row_id] = 18 )"),
    ("Selected Basis", "Returns", None, "SELECTEDVALUE ( return_basis[basis], \"USD-adjusted\" )"),
    ("Monthly Return %", "Returns", "0.00", "SWITCH ( [Selected Basis], \"USD-adjusted\", SUM ( returns_monthly[usd_adjusted_return_pct] ), \"USD-adjusted real\", SUM ( returns_monthly[usd_adjusted_real_return_pct] ), \"ZiG nominal\", SUM ( returns_monthly[nominal_return_pct] ), \"ZiG real\", SUM ( returns_monthly[real_zwg_return_pct] ) )"),
    ("Monthly Return % (one instrument)", "Returns", "0.00", "VAR inst = SELECTEDVALUE ( dim_instrument[instrument], \"ZWG_cash\" ) RETURN CALCULATE ( [Monthly Return %], dim_instrument[instrument] = inst )"),
    ("Cumulative USD Index", "Returns", "0.0", "VAR lastP = MAX ( returns_monthly[period_date] ) RETURN CALCULATE ( SUM ( returns_monthly[cum_usd_index] ), returns_monthly[period_date] = lastP )"),
    ("Cumulative USD Index (chart)", "Returns", "0.0", f"CALCULATE ( [Cumulative USD Index], KEEPFILTERS ( dim_instrument[instrument] IN {IN5} ) )"),
    ("Quoted Rate % p.a.", "Returns", "0.00", "AVERAGE ( returns_monthly[rate_pct_pa] )"),
    ("Rate Sep 2026 3M Deposit Max %", "Returns", "0.00", "CALCULATE ( SUM ( returns_monthly[rate_pct_pa] ), returns_monthly[period] = \"2026-09\", returns_monthly[instrument] = \"ZWG_3m_deposit_max\" )"),
    ("Rate Sep 2026 ZiGDTDF %", "Returns", "0.00", "CALCULATE ( SUM ( returns_monthly[rate_pct_pa] ), returns_monthly[period] = \"2026-09\", returns_monthly[instrument] = \"ZWG_ZiGDTDF_90d\" )"),
    ("Rate Sep 2026 Savings Max %", "Returns", "0.00", "CALCULATE ( SUM ( returns_monthly[rate_pct_pa] ), returns_monthly[period] = \"2026-09\", returns_monthly[instrument] = \"ZWG_savings_max\" )"),
    ("ZiG Cash Index Sep 2026", "Tie-out", "0.00", "CALCULATE ( SUM ( returns_monthly[cum_usd_index] ), returns_monthly[instrument] = \"ZWG_cash\", returns_monthly[period] = \"2026-09\" )"),
    ("Annualised USD Return %", "Comparisons", "0.00", "SUM ( subperiods[annualised_pct] )"),
    ("Spread vs T-bill pp", "Comparisons", "+0.00;-0.00;0.00", "SUM ( subperiods[spread_vs_tbill_ann_pp] )"),
    ("Spread vs T-bill (chart) pp", "Comparisons", "+0.0;-0.0;0.0", f"CALCULATE ( [Spread vs T-bill pp], KEEPFILTERS ( subperiods[subperiod] IN {{\"P1 pre-devaluation\", \"P3 2025\", \"P4 2026 to Sep\"}} ), KEEPFILTERS ( dim_instrument[instrument] IN {IN4} ) )"),
    ("Required Yield %", "Comparisons", "0.00", "SUM ( scenarios[p50] )"),
    ("Required Yield (chart) %", "Comparisons", "0.0", "CALCULATE ( [Required Yield %], scenarios[kind] = \"required ZiG yield\", scenarios[depreciation_case] = \"2026 realised depreciation\", KEEPFILTERS ( scenarios[hold_months] IN {3, 6, 12} ) )"),
    ("Scenario P5", "Comparisons", "0.00", "CALCULATE ( SUM ( scenarios[p5] ), KEEPFILTERS ( scenarios[kind] IN {\"MC relative wealth vs T-bill\", \"stress: 27-Sep-2024 devaluation repeats within a 12m hold\"} ) )"),
    ("Scenario P50", "Comparisons", "0.00", "CALCULATE ( SUM ( scenarios[p50] ), KEEPFILTERS ( scenarios[kind] IN {\"MC relative wealth vs T-bill\", \"stress: 27-Sep-2024 devaluation repeats within a 12m hold\"} ) )"),
    ("Scenario P95", "Comparisons", "0.00", "CALCULATE ( SUM ( scenarios[p95] ), KEEPFILTERS ( scenarios[kind] IN {\"MC relative wealth vs T-bill\", \"stress: 27-Sep-2024 devaluation repeats within a 12m hold\"} ) )"),
    ("Effective Rate 3M Deposit Max %", "Comparisons", "0.00", "CALCULATE ( SUM ( scenarios[p50] ), scenarios[kind] = \"effective annual rate on offer\", scenarios[instrument] = \"ZWG_3m_deposit_max\" )"),
    ("Effective Rate ZiGDTDF %", "Comparisons", "0.00", "CALCULATE ( SUM ( scenarios[p50] ), scenarios[kind] = \"effective annual rate on offer\", scenarios[instrument] = \"ZWG_ZiGDTDF_90d\" )"),
    ("Effective Rate Savings Max %", "Comparisons", "0.00", "CALCULATE ( SUM ( scenarios[p50] ), scenarios[kind] = \"effective annual rate on offer\", scenarios[instrument] = \"ZWG_savings_max\" )"),
    ("Loss Window Share %", "Comparisons", "0.00", "SUM ( rolling[share_loss_pct] )"),
    ("Loss Share 90d Since 2025 %", "Comparisons", "0.0", "CALCULATE ( [Loss Window Share %], rolling[window_days] = 90, rolling[regime] = \"windows starting 2025-01-01 or later\" )"),
    ("Worst Window Return %", "Comparisons", "0.00", "MIN ( rolling[worst_return_pct] )"),
    ("ZiG per USD", "FX", "0.0000", "AVERAGE ( fx_daily[zwg_per_usd] )"),
    ("ZiG per USD Month End", "FX", "0.0000", "CALCULATE ( [ZiG per USD], LASTDATE ( dim_date[Date] ) )"),
    ("ZiG per USD on 2026-11-13", "Tie-out", "0.0000", "CALCULATE ( SUM ( fx_daily[zwg_per_usd] ), fx_daily[date_key] = DATE ( 2026, 11, 13 ) )"),
]


def measures_tmdl():
    out = ["table _Measures", f"\tlineageTag: {lt('t_Measures')}", ""]
    for n, folder, fmt, dax in MEASURES:
        out.append(f"\tmeasure {q(n)} = {dax}")
        if fmt:
            out.append(f"\t\tformatString: {fmt}")
        out.append(f"\t\tdisplayFolder: {folder}")
        out.append(f"\t\tlineageTag: {lt('m' + n)}")
        out.append("")
    out += ["\tcolumn Value", "\t\tdataType: int64", "\t\tisHidden", "\t\tformatString: 0", f"\t\tlineageTag: {lt('c_MeasuresValue')}",
            "\t\tsummarizeBy: none", "\t\tisNameInferred", "\t\tsourceColumn: [Value]", "",
            "\t\tannotation SummarizationSetBy = User", "",
            "\tpartition _Measures = calculated", "\t\tmode: import", "\t\tsource = ROW ( \"Value\", 0 )", "",
            "\tannotation PBI_Id = " + vid("measures"), ""]
    return "\n".join(out)


RELS = [("returns_monthly", "instrument", "dim_instrument", "instrument"),
        ("subperiods", "instrument", "dim_instrument", "instrument"),
        ("rolling", "instrument", "dim_instrument", "instrument"),
        ("returns_monthly", "period_date", "dim_date", "Date"),
        ("fx_daily", "date_key", "dim_date", "Date")]

write(os.path.join(SM, "database.tmdl"), "database\n\tcompatibilityLevel: 1606\n\n")
order = list(TABLES) + ["_Measures"]
write(os.path.join(SM, "model.tmdl"), "\n".join([
    "model Model", "\tculture: en-US", "\tdefaultPowerBIDataSourceVersion: powerBI_V3", "\tsourceQueryCulture: en-US",
    "\tvalueFilterBehavior: independent", "\tdataAccessOptions", "\t\tlegacyRedirects", "\t\treturnErrorValuesAsNull", "",
    "annotation __PBI_TimeIntelligenceEnabled = 0", "",
    "annotation PBI_ProTooling = [\"DevMode\"]", "",
    "annotation PBI_QueryOrder = " + json.dumps(["DataFolder"] + list(TABLES)), "",
    *[f"ref table {q(t)}" for t in order], "",
    "ref cultureInfo en-US", "", ""]))
write(os.path.join(SM, "cultures", "en-US.tmdl"), "cultureInfo en-US\n\n")
write(os.path.join(SM, "expressions.tmdl"), "\n".join([
    f'expression DataFolder = "{DATA}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]',
    f"\tlineageTag: {lt('eDataFolder')}", "", "\tannotation PBI_ResultType = Text", "", ""]))
for t, cols in TABLES.items():
    write(os.path.join(SM, "tables", f"{t}.tmdl"), table_tmdl(t, cols))
write(os.path.join(SM, "tables", "_Measures.tmdl"), measures_tmdl())
write(os.path.join(SM, "relationships.tmdl"), "\n".join(
    sum([[f"relationship {lt('r' + a + b + c + d)}", f"\tfromColumn: {a}.{b}", f"\ttoColumn: {c}.{d}", ""] for a, b, c, d in RELS], [])) + "\n")

# ---------------------------------------------------------------- report
VC = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json"


def col(t, c, active=False):
    p = {"field": {"Column": {"Expression": {"SourceRef": {"Entity": t}}, "Property": c}}, "queryRef": f"{t}.{c}", "nativeQueryRef": c}
    if active:
        p["active"] = True
    return p


def mea(m, t="_Measures"):
    return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": t}}, "Property": m}}, "queryRef": f"{t}.{m}", "nativeQueryRef": m}


def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def title(text, show=True):
    return {"title": [{"properties": {"show": lit("true" if show else "false"), "text": lit("'" + text.replace("'", "''") + "'")}}],
            "subTitle": [{"properties": {"show": lit("false")}}]}


CARD_OBJ = {"categoryLabels": [{"properties": {"show": lit("false")}}]}
LABELS = {"labels": [{"properties": {"show": lit("true")}}]}
NO_TOTALS = {"total": [{"properties": {"totals": lit("false")}}]}
NO_SUBTOTALS = {"subTotals": [{"properties": {"rowSubtotals": lit("false"), "columnSubtotals": lit("false")}}]}
SINGLE = {"selection": [{"properties": {"singleSelect": lit("true")}}]}


def visual(page, key, vtype, x, y, w, h, roles=None, ttl=None, sort=None, objects=None, z=0):
    v = {"visualType": vtype, "drillFilterOtherVisuals": True}
    if roles:
        v["query"] = {"queryState": {r: {"projections": p} for r, p in roles.items()}}
        if sort:
            v["query"]["sortDefinition"] = {"sort": [{"field": sort[0]["field"], "direction": sort[1]}], "isDefaultSort": True}
    if objects:
        v["objects"] = objects
    if ttl is not None:
        v["visualContainerObjects"] = title(ttl)
    name = vid(page + key)
    obj = {"$schema": VC, "name": name, "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z}, "visual": v}
    wjson(os.path.join(RP, "pages", page, "visuals", name, "visual.json"), obj)


def textbox(page, key, text, x, y, w, h, size="16pt", bold=True, z=0):
    style = {"fontSize": size}
    if bold:
        style["fontWeight"] = "bold"
    visual(page, key, "textbox", x, y, w, h, objects={"general": [{"properties": {"paragraphs": [{"textRuns": [{"value": text, "textStyle": style}]}]}}]}, z=z)


PAGES = [("5240477fb052566b9e73", "Summary"), (vid("p2"), "FX and value"), (vid("p3"), "Versus USD"), (vid("p4"), "Break-even"), (vid("p5"), "Risk")]
for pid, pname in PAGES:
    wjson(os.path.join(RP, "pages", pid, "page.json"), {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
        "name": pid, "displayName": pname, "displayOption": "FitToPage", "height": 720, "width": 1280})
wjson(os.path.join(RP, "pages", "pages.json"), {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
    "pageOrder": [p for p, _ in PAGES], "activePageName": PAGES[0][0]})

FOOT = "Data as of 2026-11-13. UMFDOP pipeline: RBZ, ZIMSTAT, IMF and FRED data; results from Agent 4 (2026-11-13, revised 2026-11-14 after review)."
# Page 1 Summary
p = PAGES[0][0]
textbox(p, "t", "Holding ZiG lost about half its USD value since launch; since 2025 the top-rate 3-month index has beaten the T-bill", 20, 10, 1240, 50)
cards = [("ZiG Cash USD Return Since Launch %", "ZiG cash, USD-adjusted, launch to Sep 2026 (%)"),
         ("3M Deposit Max USD Return Since 2025 %", "3-month index (top rate), Jan 2025 to Sep 2026 (%)"),
         ("3M Deposit Max Spread 2026 pp", "2026: 3-month index (top rate) vs T-bill (pp)"),
         ("Savings Max Spread 2026 pp", "2026: savings (max) vs T-bill (pp)"),
         ("Required Yield Converter 12m %", "Yield needed, converting US$, 12 months (%)"),
         ("Required Yield Already ZiG %", "Yield needed, already holds ZiG (%)"),
         ("ZiG Cash 90d Loss Share Since 2025 %", "ZiG cash: 90-day windows with a loss since 2025 (%)"),
         ("3M Max 90d Loss Share Since 2025 %", "3-month index (top rate): same measure (%)")]
for i, (m, t) in enumerate(cards):
    visual(p, "c" + str(i), "card", 20 + (i % 4) * 312, 64 + (i // 4) * 138, 300, 130, {"Values": [mea(m)]}, ttl=t, objects=CARD_OBJ, z=i + 1)
visual(p, "tbl", "tableEx", 20, 346, 1240, 334, {"Values": [col("findings", "question_id"), col("findings", "finding"), col("findings", "number"),
       col("findings", "unit"), col("findings", "confidence")]}, ttl="All findings (result_findings.csv)", objects=NO_TOTALS, z=20)
textbox(p, "f", FOOT, 20, 686, 1240, 28, size="9pt", bold=False, z=30)

# Page 2 FX and value
p = PAGES[1][0]
textbox(p, "t", "One day in September 2024 decides the whole period", 20, 10, 1240, 44)
visual(p, "fx", "lineChart", 20, 60, 840, 300, {"Category": [col("fx_daily", "date_key", True)], "Y": [mea("ZiG per USD")]},
       ttl="RBZ official mid rate, ZiG per US$ (devaluation on 2024-09-27)", z=1)
visual(p, "k1", "card", 880, 60, 380, 140, {"Values": [mea("ZiG per USD on 2026-11-13")]}, ttl="ZiG per US$ on 2026-11-13", objects=CARD_OBJ, z=2)
visual(p, "k2", "card", 880, 220, 380, 140, {"Values": [mea("ZiG Cash Index Sep 2026")]}, ttl="ZiG cash: US$100 placed 2024-04-08, value at Sep 2026", objects=CARD_OBJ, z=3)
visual(p, "cum", "lineChart", 20, 370, 840, 310, {"Category": [col("returns_monthly", "period_date", True)], "Series": [col("dim_instrument", "label")],
       "Y": [mea("Cumulative USD Index (chart)")]}, ttl="US$ value of 100 placed on 2024-04-08, month-end", z=4)
visual(p, "sb", "slicer", 880, 370, 185, 150, {"Values": [col("return_basis", "basis")]}, ttl="Return basis", z=5)
visual(p, "si", "slicer", 1075, 370, 185, 150, {"Values": [col("dim_instrument", "label")]}, ttl="Instrument (one)", objects=SINGLE, z=6)
visual(p, "mr", "clusteredColumnChart", 880, 530, 380, 150, {"Category": [col("returns_monthly", "period_date", True)], "Y": [mea("Monthly Return % (one instrument)")]},
       ttl="Monthly return (%), selected basis; ZiG cash unless one instrument is picked", sort=(col("returns_monthly", "period_date"), "Ascending"), z=7)
textbox(p, "f", "Source: mart.v_fx_daily; result_returns_monthly.csv. " + FOOT, 20, 686, 1240, 28, size="9pt", bold=False, z=30)

# Page 3 Versus USD
p = PAGES[2][0]
textbox(p, "t", "Against the US T-bill, ZiG term products have led since 2025 while ZiG savings and cash have lagged", 20, 10, 1240, 50)
visual(p, "sp", "clusteredColumnChart", 20, 70, 1240, 330, {"Category": [col("subperiods", "subperiod_label", True)], "Series": [col("dim_instrument", "label")],
       "Y": [mea("Spread vs T-bill (chart) pp")]}, ttl="Annualised gap to the US 3-month T-bill (pp); devaluation quarter excluded",
       sort=(col("subperiods", "subperiod_label"), "Ascending"), objects=LABELS, z=1)
visual(p, "mx", "pivotTable", 20, 410, 1240, 270, {"Rows": [col("dim_instrument", "label")], "Columns": [col("subperiods", "subperiod_label")],
       "Values": [mea("Annualised USD Return %"), mea("Spread vs T-bill pp")]}, ttl="Annualised USD-adjusted return (%) and spread vs T-bill (pp) by period", objects=NO_SUBTOTALS, z=2)
textbox(p, "f", "Source: result_subperiods.csv. " + FOOT, 20, 686, 1240, 28, size="9pt", bold=False, z=30)

# Page 4 Break-even
p = PAGES[3][0]
textbox(p, "t", "At today's rates, money already in ZiG clears the hurdle; a 12-month conversion clears it only at the top 3-month rate", 20, 10, 1240, 50)
visual(p, "rq", "clusteredColumnChart", 20, 70, 840, 330, {"Category": [col("scenarios", "hold_label", True)], "Series": [col("scenarios", "conversion_case")],
       "Y": [mea("Required Yield (chart) %")]}, ttl="ZiG yield needed to match the US T-bill (% a year), 2026 depreciation pace",
       sort=(col("scenarios", "hold_label"), "Ascending"), objects=LABELS, z=1)
for i, (m, t) in enumerate([("Effective Rate 3M Deposit Max %", "3-month deposit (max), effective %"),
                            ("Effective Rate ZiGDTDF %", "ZiGDTDF 90-day, effective %"),
                            ("Effective Rate Savings Max %", "Savings (max), effective %")]):
    visual(p, "r" + str(i), "card", 880, 70 + i * 112, 380, 104, {"Values": [mea(m)]}, ttl=t, objects=CARD_OBJ, z=2 + i)
visual(p, "mc", "tableEx", 20, 410, 1240, 270, {"Values": [col("scenarios", "scenario"), mea("Scenario P5"), mea("Scenario P50"), mea("Scenario P95")]},
       ttl="Ending wealth vs the T-bill (%): fitted-model simulation (P5, median, P95) and devaluation stress", objects=NO_TOTALS, z=6)
textbox(p, "f", "Source: result_scenarios.csv. Rates on offer, Sep 2026, converted to effective annual rates (quoted 13.88%, 10.98%, 4.71%). Excludes IMTT, withholding tax and fees. " + FOOT, 20, 686, 1240, 28, size="9pt", bold=False, z=30)

# Page 5 Risk
p = PAGES[4][0]
textbox(p, "t", "Since 2025, ZiG cash lost US-dollar value in far more 90-day holdings than the top-rate 3-month index (windows overlap)", 20, 10, 1240, 50)
visual(p, "ls", "clusteredBarChart", 20, 70, 1240, 300, {"Category": [col("dim_instrument", "label", True)], "Y": [mea("Loss Share 90d Since 2025 %")]},
       ttl="Share of 90-day windows since 2025-01-01 that lost US$ value (%)", objects=LABELS, z=1)
visual(p, "rt", "tableEx", 20, 380, 1240, 300, {"Values": [col("rolling", "instrument"), col("rolling", "window_days"), col("rolling", "regime"), col("rolling", "windows"),
       col("rolling", "share_loss_pct"), col("rolling", "worst_return_pct"), col("rolling", "worst_window_start")]}, ttl="Rolling-window detail (result_rolling.csv)", objects=NO_TOTALS, z=2)
textbox(p, "f", "Source: result_rolling.csv. Windows overlap. " + FOOT, 20, 686, 1240, 28, size="9pt", bold=False, z=30)
print("ok")
