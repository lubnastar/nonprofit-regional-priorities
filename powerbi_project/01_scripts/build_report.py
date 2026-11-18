"""
Step 3 of the Power BI build: writes the report (PBIR) of RegionalPriorities.pbip.

    .venv\\Scripts\\python powerbi_project\\01_scripts\\build_report.py
"""
import json
import shutil
import uuid
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
PBI = PROJECT / "03_powerbi"
RPT = PBI / "RegionalPriorities.Report"
NS = uuid.UUID("0d4f6a7b-1c2e-4f3a-9b8c-7d6e5f4a3b2c")
THEME_NAME = "RegionalPriorities_Theme.json"

ORANGE, BLUE, GRAY, INK, MUTED, GRID, BG = "#EB6834", "#2A78D6", "#B4B2A9", "#0B0B0B", "#6F6D66", "#E1E0D9", "#F4F3EF"
REGIONS = ["Riyadh", "Makkah", "Madinah", "Qassim", "Eastern Province", "Asir", "Tabuk", "Hail", "Northern Borders",
           "Jazan", "Najran", "Al-Baha", "Al-Jouf"]
W, H = 1280, 720


# ============================================================ JSON helpers
def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def s(text):  # string literal
    return lit("'" + str(text).replace("'", "''") + "'")


def b(v):
    return lit("true" if v else "false")


def n(v):
    return lit(f"{v}D")


def color(hex_):
    return {"solid": {"color": s(hex_)}}


def m_ref(name):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": name}}


def c_ref(table, column):
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": column}}


def split_col(f):
    t, c = f[:-1].split("[")
    return t.strip("'"), c


def field(f):
    """'Measure Name' or 'table[column]' -> field expression."""
    if "[" in f:
        return c_ref(*split_col(f))
    return m_ref(f)


def query_ref(f):
    if "[" in f:
        t, c = split_col(f)
        return f"{t}.{c}", c
    return f"_Measures.{f}", f


def proj(f, display=None):
    qr, nq = query_ref(f)
    p = {"field": field(f), "queryRef": qr, "nativeQueryRef": nq}
    if display:
        p["displayName"] = display
    return p


def measure_color(measure, metadata=None):
    sel = {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}
    if metadata:
        sel["metadata"] = query_ref(metadata)[0]
    return {"properties": {"fill": {"solid": {"color": {"expr": m_ref(measure)}}}}, "selector": sel}


def container(title=None, subtitle=None, title_measure=None, bg=True, border=True):
    o = {}
    if title or title_measure:
        o["title"] = [{"properties": {
            "show": b(True), "text": {"expr": m_ref(title_measure)} if title_measure else s(title),
            "fontColor": color(INK), "fontSize": n(12), "bold": b(True), "fontFamily": s("Segoe UI Semibold")}}]
    else:
        o["title"] = [{"properties": {"show": b(False)}}]
    if subtitle:
        o["subTitle"] = [{"properties": {"show": b(True), "text": s(subtitle), "fontColor": color(MUTED), "fontSize": n(9)}}]
    o["background"] = [{"properties": {"show": b(bg), "color": color("#FFFFFF"), "transparency": n(0)}}]
    o["border"] = [{"properties": {"show": b(border), "color": color(GRID), "radius": n(8)}}]
    o["dropShadow"] = [{"properties": {"show": b(False)}}]
    o["padding"] = [{"properties": {"top": n(8), "bottom": n(6), "left": n(10), "right": n(10)}}]
    return o


class Page:
    def __init__(self, name, display):
        self.name, self.display, self.visuals, self.z = name, display, [], 0
        self.size, self.extra = None, {}

    def add(self, x, y, w, h, visual, name=None):
        self.z += 1
        vid = name or f"v{self.z:02d}"
        self.visuals.append({
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.0.0/schema.json",
            "name": f"{self.name}_{vid}",
            "position": {"x": x, "y": y, "z": self.z * 1000, "height": h, "width": w, "tabOrder": self.z * 1000},
            "visual": visual,
        })


# ============================================================ visual builders
def textbox(paragraphs, bg=False, border=False, bgcolor="#FFFFFF"):
    """paragraphs: list of lists of (text, size, color, bold) runs, or plain strings."""
    paras = []
    for p in paragraphs:
        runs = p if isinstance(p, list) else [(p, 10, INK, False)]
        paras.append({"textRuns": [{"value": t, "textStyle": {
            "fontFamily": "Segoe UI Semibold" if bold else "Segoe UI", "fontSize": f"{size}pt", "color": col,
            **({"fontWeight": "bold"} if bold else {})}} for t, size, col, bold in runs]})
    vco = container(bg=bg, border=border)
    vco["background"] = [{"properties": {"show": b(bg), "color": color(bgcolor), "transparency": n(0)}}]
    return {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": paras}}]},
            "visualContainerObjects": vco}


def card(measure, label, value_color=INK, size=22):
    return {"visualType": "card",
            "query": {"queryState": {"Values": {"projections": [proj(measure, label)]}}},
            "objects": {
                "labels": [{"properties": {"color": color(value_color), "fontSize": n(size), "fontFamily": s("Segoe UI Semibold"), "labelDisplayUnits": n(1)}}],
                "categoryLabels": [{"properties": {"show": b(True), "color": color(MUTED), "fontSize": n(9)}}],
                "wordWrap": [{"properties": {"show": b(True)}}]},
            "visualContainerObjects": container()}


def slicer(column, title, mode="Dropdown", single=True, default=None, sync=None):
    t, c = split_col(column)
    objects = {"data": [{"properties": {"mode": s(mode)}}],
               "selection": [{"properties": {"strictSingleSelect": b(single), "selectAllCheckboxEnabled": b(False)}}],
               "header": [{"properties": {"show": b(True), "fontColor": color(MUTED), "textSize": n(9)}}],
               "items": [{"properties": {"fontColor": color(INK), "textSize": n(10)}}]}
    if default is not None:
        objects["general"] = [{"properties": {"filter": {"filter": {
            "Version": 2, "From": [{"Name": "d", "Entity": t, "Type": 0}],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": c}}],
                "Values": [[{"Literal": {"Value": "'" + default + "'" if isinstance(default, str) else f"{default}L"}}]]}}}]}}}}]
    v = {"visualType": "slicer",
         "query": {"queryState": {"Values": {"projections": [proj(column, title)]}}},
         "objects": objects, "visualContainerObjects": container(border=True)}
    v["visualContainerObjects"]["title"] = [{"properties": {"show": b(False)}}]
    if sync:
        v["syncGroup"] = {"groupName": sync, "fieldChanges": True, "filterChanges": True}
    return v


def sort_def(f, desc=True):
    return {"sort": [{"field": field(f), "direction": "Descending" if desc else "Ascending"}], "isDefaultSort": True}


def bar(category, values, title=None, subtitle=None, color_measure=None, series_colors=None, tooltips=(),
        sort=None, sort_desc=True, kind="clusteredBarChart", labels=True, title_measure=None, legend=False,
        label_units=0, value_axis=False, label_precision=None, default_color=None):
    cats = category if isinstance(category, list) else [category]
    qs = {"Category": {"projections": [proj(c) for c in cats]},
          "Y": {"projections": [proj(v, d) for v, d in values]}}
    if tooltips:
        qs["Tooltips"] = {"projections": [proj(t) for t in tooltips]}
    q = {"queryState": qs}
    if sort:
        q["sortDefinition"] = sort_def(sort, sort_desc)
    objects = {
        "categoryAxis": [{"properties": {"showAxisTitle": b(False), "fontSize": n(9), "labelColor": color(INK)}}],
        "valueAxis": [{"properties": {"show": b(value_axis), "showAxisTitle": b(False), "gridlineShow": b(False)}}],
        "labels": [{"properties": {"show": b(labels), "fontSize": n(8), "color": color(INK), "labelDisplayUnits": n(label_units),
                                   **({"labelPrecision": lit(f"{label_precision}L")} if label_precision is not None else {})}}],
        "legend": [{"properties": {"show": b(legend), "position": s("Top"), "fontSize": n(9), "showTitle": b(False)}}],
    }
    dp = []
    if default_color:
        dp.append({"properties": {"defaultColor": color(default_color)}})
    if color_measure:
        dp.append(measure_color(color_measure))
    for meas, hexc in (series_colors or {}).items():
        dp.append({"properties": {"fill": color(hexc)}, "selector": {"metadata": query_ref(meas)[0]}})
    if dp:
        objects["dataPoint"] = dp
    return {"visualType": kind, "query": q, "objects": objects, "drillFilterOtherVisuals": True,
            "visualContainerObjects": container(title, subtitle, title_measure)}


def scatter(category, x, y, title, subtitle=None, size=None, color_measure=None, tooltips=(), axes=True,
            x_title=None, y_title=None, ref_x=None, ref_y=None, x_range=None, y_range=None):
    qs = {"Category": {"projections": [proj(category)]},
          "X": {"projections": [proj(x, x_title)]}, "Y": {"projections": [proj(y, y_title)]}}
    if size:
        qs["Size"] = {"projections": [proj(size)]}
    if tooltips:
        qs["Tooltips"] = {"projections": [proj(t) for t in tooltips]}
    objects = {
        "categoryAxis": [{"properties": {"show": b(axes), "showAxisTitle": b(axes), "gridlineShow": b(False), "fontSize": n(9)}}],
        "valueAxis": [{"properties": {"show": b(axes), "showAxisTitle": b(axes), "gridlineShow": b(axes), "gridlineColor": color(GRID), "fontSize": n(9)}}],
        "categoryLabels": [{"properties": {"show": b(True), "color": color(INK), "fontSize": n(9 if axes else 10)}}],
        "legend": [{"properties": {"show": b(False)}}],
    }
    if color_measure:
        objects["dataPoint"] = [measure_color(color_measure)]
    if x_range:
        objects["categoryAxis"][0]["properties"].update({"start": n(x_range[0]), "end": n(x_range[1])})
    if y_range:
        objects["valueAxis"][0]["properties"].update({"start": n(y_range[0]), "end": n(y_range[1])})
    if ref_x:
        objects["xAxisReferenceLine"] = [{"properties": {
            "show": b(True), "value": {"expr": m_ref(ref_x)}, "lineColor": color(MUTED), "style": s("dashed"),
            "transparency": n(30), "displayName": s("Median"), "dataLabelShow": b(True), "dataLabelColor": color(MUTED)},
            "selector": {"id": "1"}}]
    if ref_y:
        objects["y1AxisReferenceLine"] = [{"properties": {
            "show": b(True), "value": {"expr": m_ref(ref_y)}, "lineColor": color(MUTED), "style": s("dashed"),
            "transparency": n(30), "displayName": s("Median"), "dataLabelShow": b(True), "dataLabelColor": color(MUTED)},
            "selector": {"id": "1"}}]
    return {"visualType": "scatterChart", "query": {"queryState": qs}, "objects": objects, "drillFilterOtherVisuals": True,
            "visualContainerObjects": container(title, subtitle)}


def line(category, values, title, subtitle=None, series=None, labels=False, legend=False, series_colors=None, label_units=0,
         value_colors=None):
    qs = {"Category": {"projections": [proj(category)]}, "Y": {"projections": [proj(v, d) for v, d in values]}}
    if series:
        qs["Series"] = {"projections": [proj(series)]}
    objects = {
        "categoryAxis": [{"properties": {"showAxisTitle": b(False), "fontSize": n(9), "axisType": s("Categorical")}}],
        "valueAxis": [{"properties": {"showAxisTitle": b(False), "gridlineColor": color(GRID), "fontSize": n(9), "labelDisplayUnits": n(label_units)}}],
        "labels": [{"properties": {"show": b(labels), "fontSize": n(8), "labelDisplayUnits": n(label_units)}}],
        "lineStyles": [{"properties": {"showMarker": b(True), "strokeWidth": n(2)}}],
        "legend": [{"properties": {"show": b(legend), "position": s("Top"), "fontSize": n(9), "showTitle": b(False)}}],
    }
    if series_colors:
        objects["dataPoint"] = [{"properties": {"fill": color(c)}, "selector": {"metadata": query_ref(m)[0]}} for m, c in series_colors.items()]
    if value_colors:  # colour each series (legend value) explicitly
        objects["dataPoint"] = [{"properties": {"fill": color(c)}, "selector": {"data": [{"scopeId": {"Comparison": {
            "ComparisonKind": 0, "Left": field(series), "Right": {"Literal": {"Value": "'" + v + "'"}}}}}]}}
            for v, c in value_colors.items()]
    return {"visualType": "lineChart", "query": {"queryState": qs}, "objects": objects, "drillFilterOtherVisuals": True,
            "visualContainerObjects": container(title, subtitle)}


def grid_objects(font=9, cell_colors=None):
    o = {"columnHeaders": [{"properties": {"fontColor": color(INK), "backColor": color("#F4F3EF"), "fontSize": n(font), "wordWrap": b(True), "bold": b(True)}}],
         "values": [{"properties": {"fontSize": n(font), "fontColor": color(INK), "backColorSecondary": color("#FFFFFF")}}],
         "grid": [{"properties": {"gridHorizontal": b(True), "gridHorizontalColor": color(GRID), "rowPadding": n(2)}}],
         "rowHeaders": [{"properties": {"fontSize": n(font), "fontColor": color(INK)}}]}
    for meas, cmeas in (cell_colors or {}).items():
        o["values"].append({"properties": {"backColor": {"solid": {"color": {"expr": m_ref(cmeas)}}}},
                            "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": query_ref(meas)[0]}})
    return o


def table(columns, title, subtitle=None, sort=None, sort_desc=False, font=9, cell_colors=None):
    o = grid_objects(font, cell_colors)
    o["total"] = [{"properties": {"totals": b(False)}}]
    q = {"queryState": {"Values": {"projections": [proj(c, d) for c, d in columns]}}}
    if sort:
        q["sortDefinition"] = sort_def(sort, sort_desc)
    return {"visualType": "tableEx", "query": q, "objects": o, "drillFilterOtherVisuals": True,
            "visualContainerObjects": container(title, subtitle)}


def matrix(rows, cols, values, title, subtitle=None, font=9, cell_colors=None):
    o = grid_objects(font, cell_colors)
    o["subTotals"] = [{"properties": {"rowSubtotals": b(False), "columnSubtotals": b(False)}}]
    qs = {"Rows": {"projections": [proj(r, "Region") for r in rows]}, "Values": {"projections": [proj(v, d) for v, d in values]}}
    if cols:
        qs["Columns"] = {"projections": [proj(c) for c in cols]}
    return {"visualType": "pivotTable", "query": {"queryState": qs}, "objects": o, "drillFilterOtherVisuals": True,
            "visualContainerObjects": container(title, subtitle)}


# ============================================================ page furniture
def header(p, title, subtitle):
    p.add(20, 16, 6, 44, textbox([""], bg=True, bgcolor=ORANGE))
    p.add(32, 4, 960, 46, textbox([[(title, 19, INK, True)]]))
    p.add(32, 44, 960, 28, textbox([[(subtitle, 10, MUTED, False)]]))


def footer(p, text="Sources: NCNP non-profit register · SAMA population & social security · GASTAT census 2022 · HIES 2023.  "
                     "Ranking is relative across the 13 regions, not an absolute measure of need."):
    p.add(20, 694, 1240, 26, textbox([[(text, 8, MUTED, False)]]))


def scenario_slicer(p, x=1010, y=12, w=250):
    p.add(x, y, w, 56, slicer("dim_scenario[scenario_label]", "Gap scenario", default="A · SS 2022 · All organizations", sync="scenario"))


def kpi_row(p, items, y=80, h=78, x0=20, total_w=1240, gap=10):
    """items: (measure, label[, colour[, font size[, width weight]]])"""
    weights = [it[4] if len(it) > 4 else 1 for it in items]
    unit = (total_w - gap * (len(items) - 1)) / sum(weights)
    x = x0
    for it, wt in zip(items, weights):
        meas, label = it[0], it[1]
        col_ = it[2] if len(it) > 2 else INK
        size = it[3] if len(it) > 3 else 22
        p.add(round(x), y, round(unit * wt), h, card(meas, label, col_, size))
        x += unit * wt + gap


GAP_TIPS = ("Gap Rank", "Gap Score", "Gap Source", "Fragility Index", "Org Density per 100k")

# ============================================================ pages
pages = []

# ------------------------------------------------ 1 Executive overview
p = Page("p1_overview", "1 · Executive Overview")
header(p, "Where should charitable resources go first?",
       "13 Saudi regions ranked by the gap between economic fragility and non-profit density")
scenario_slicer(p)
kpi_row(p, [
    ("Organizations (All Types)", "Registered non-profits"),
    ("Population 2022", "Population 2022"),
    ("Org Density per 100k", "Non-profits per 100k (national)"),
    ("Beneficiaries 2022", "Social security beneficiaries 2022"),
    ("Top Priority Region", "#1 priority (active scenario)", ORANGE),
    ("Stable Priority Regions", "Stable priorities (≥5 of 6 tests)", BLUE),
])
p.add(20, 170, 370, 522, scatter("dim_region[region_en]", "Tile X", "Tile Y", "Where the priority regions are",
                                 "Schematic tile map (not to scale) · orange = fragility + few non-profits · blue = mainly few non-profits",
                                 size="Tile Size", color_measure="Stable Group Color", axes=False,
                                 x_range=(-0.7, 3.7), y_range=(-4.7, 0.7),
                                 tooltips=("Gap Rank", "Gap Score", "Gap Source", "Profile Group")))
p.add(400, 170, 450, 522, bar("dim_region[region_en]", [("Gap Score", "Gap score")], title_measure="Title Gap Chart",
                              subtitle="Standardized fragility − standardized density · top 5 coloured by gap source",
                              color_measure="Priority Color", tooltips=GAP_TIPS, sort="Gap Score"))
p.add(860, 170, 400, 522, textbox([
    [("Key insights", 14, INK, True)],
    [("1  Najran is the clear first priority. ", 10, ORANGE, True),
     ("Gap score 1.94 vs 0.77 for #2; lowest Saudi median income (SAR 1,650/month), highest food share (43.5%), no foundations. #1 in all 6 sensitivity tests and all 12 leave-one-out runs.", 10, INK, False)],
    [("2  Jazan is second, also driven by fragility. ", 10, ORANGE, True),
     ("2nd-highest social security rate (9.84%) and no foundations. Least stable priority: top 5 in 72.9% of 1,000 random weightings.", 10, INK, False)],
    [("3  Madinah, Tabuk and Makkah: service gaps. ", 10, BLUE, True),
     ("Fragility at or below average, but among the lowest non-profit densities (8.56, 8.24 and 5.54 per 100k). Makkah has the most beneficiaries of the five (245,796).", 10, INK, False)],
    [("4  Non-profits are concentrated. ", 10, INK, True),
     ("Riyadh hosts 29% of all non-profits and 60% of foundations; Jazan, Hail, Al-Baha, Tabuk and Najran have none.", 10, INK, False)],
    [("5  Al-Jouf is borderline. ", 10, INK, True),
     ("Top 5 in 2 of 6 tests, 27.5% of weightings and 6 of 12 leave-one-out runs: worth monitoring.", 10, INK, False)],
    [("Read as a relative ranking of 13 regions, not an absolute measure of need.", 9, MUTED, False)],
], bg=True, border=True))
footer(p)
pages.append(p)

# ------------------------------------------------ 2 Priority gap analysis
p = Page("p2_gap", "2 · Priority Gap")
header(p, "Which regions combine high fragility with few non-profits?",
       "Gap score = z(fragility) − z(non-profit density) · the larger part tells why a region is a priority")
scenario_slicer(p)
kpi_row(p, [
    ("Top 5 Regions", "Top 5 by gap (rank order)", INK, 13, 2.2),
    ("Top Priority Gap", "Gap score of #1", ORANGE),
    ("Lead Over Second", "Lead of #1 over #2"),
    ("Median Fragility", "Median fragility (13 regions)"),
    ("Median Density", "Median non-profits per 100k"),
], x0=20, total_w=1240)
p.add(20, 168, 610, 330, scatter("dim_region[region_en]", "Density (Scenario)", "Fragility Index",
                                 "Fragility vs. non-profit density",
                                 "Each dot is a region · dashed lines = 13-region medians · top-left = more fragile, fewer organizations",
                                 color_measure="Priority Color", tooltips=("Gap Rank", "Gap Score", "Gap Source", "Quadrant"),
                                 x_title="Non-profits per 100k", y_title="Fragility index", ref_x="Median Density", ref_y="Median Fragility"))
p.add(640, 168, 620, 330, bar("dim_region[region_en]", [("Fragility Part", "Fragility part of the gap"), ("Few Non-profits Part", "Few non-profits part")],
                              "Where each gap comes from", "Gap = fragility part + few non-profits part · sorted by gap score",
                              series_colors={"Fragility Part": ORANGE, "Few Non-profits Part": BLUE},
                              tooltips=("Gap Score", "Gap Rank", "Gap Source"), sort="Gap Score", legend=True, labels=False))
p.add(20, 506, 1240, 188, table([
    ("Gap Rank", "Rank"), ("dim_region[region_en]", "Region"), ("Gap Score", "Gap"), ("Fragility Part", "Fragility part"),
    ("Few Non-profits Part", "Few non-profits part"), ("Gap Source", "Gap source"), ("Fragility Index", "Fragility index"),
    ("Density (Scenario)", "Non-profits /100k"), ("Quadrant", "Quadrant (descriptive)"), ("Scenarios in Top 5", "Scenarios A-D in top 5"),
], "Priority table", sort="Gap Rank", cell_colors={"Gap Rank": "Gap Rank Cell Color"}))
footer(p)
pages.append(p)

# ------------------------------------------------ 3 Fragility drivers
p = Page("p3_fragility", "3 · Fragility Drivers")
header(p, "What drives economic fragility?",
       "Fragility index = weighted mean of three z-scores · change the weights to test your own priorities")
scenario_slicer(p)
p.add(20, 76, 170, 56, slicer("'Weight SS'[Weight SS]", "Weight: social security", default=1))
p.add(198, 76, 170, 56, slicer("'Weight Income'[Weight Income]", "Weight: low income", default=1))
p.add(376, 76, 170, 56, slicer("'Weight Food'[Weight Food]", "Weight: food share", default=1))
p.add(556, 76, 704, 56, card("Weights Label", "Active fragility weights (notebook default = equal)", INK, 12))
p.add(20, 142, 390, 550, bar("dim_region[region_en]", [("Fragility Index", "Fragility index")], "Fragility index by region",
                             "0 = average of the 13 regions · orange = more fragile than average",
                             color_measure="Fragility Color", sort="Fragility Index",
                             tooltips=("Fragility Rank", "Z SS Rate", "Z Low Income", "Z Food Share")))
p.add(420, 142, 840, 300, table([
    ("Fragility Rank", "#"), ("dim_region[region_en]", "Region"), ("SS Rate (Scenario) %", "SS rate"),
    ("Z SS Rate", "z SS"), ("Median Income (Saudi)", "Income (SAR)"), ("Z Low Income", "z income"),
    ("Food Share %", "Food share"), ("Z Food Share", "z food"), ("Fragility Index", "Fragility"),
], "The three indicators and their z-scores", "Positive z = more fragile than the 13-region average · income is reversed (low income = positive z)",
    sort="Fragility Rank", cell_colors={"Fragility Index": "Fragility Cell Color"}))
p.add(420, 450, 520, 242, scatter("dim_region[region_en]", "Median Income (Saudi)", "Food Share %",
                                  "Lower-income regions spend a larger share on food",
                                  "Saudi median monthly income (SAR) vs food share of spending, HIES 2023",
                                  color_measure="Fragility Color", x_title="Median income (SAR)", y_title="Food share"))
p.add(950, 450, 310, 76, card("Spearman Income vs Food Share", "Rank correlation, income vs food share"))
p.add(950, 533, 310, 76, card("Lowest Income Region", "Lowest Saudi median income", ORANGE, 15))
p.add(950, 616, 310, 76, card("Highest Food Share Region", "Highest food share of spending", ORANGE, 15))
footer(p)
pages.append(p)

# ------------------------------------------------ 4 Robustness
p = Page("p4_robustness", "4 · Robustness")
header(p, "How stable is the ranking?",
       "Six method changes, four scenarios, 1,000 random weightings and leave-one-region-out runs")
kpi_row(p, [
    ("Stable Priority List", "Stable priorities (top 5 in ≥5 of 6 tests)", INK, 13, 2.2),
    ("Tests Run", "Sensitivity tests"),
    ("Random Weight Draws", "Random weightings (seed 42)"),
    ("Least Stable Priority", "Least stable priority (random weights)", ORANGE, 14, 1.4),
    ("Spearman Fragility 2022 vs Avg", "Fragility 2022 vs 2020-22 (rank corr.)", INK, 22, 1.2),
])
p.add(20, 168, 560, 524, matrix(["dim_region[region_en]"], ["dim_sensitivity_test[test_short]"], [("Test Rank", "Rank")],
                                "Gap rank in each sensitivity test (scenario A)",
                                "1 = largest gap · shaded = top 5 · No SS / income / food = indicator dropped · + Margin = income margin added · Ranks = percentile ranks",
                                cell_colors={"Test Rank": "Rank Cell Color"}))
p.add(590, 168, 236, 524, matrix(["dim_region[region_en]"], ["dim_scenario[scenario]"], [("Gap Rank", "Rank")],
                                 "Scenarios A-D (live DAX)", "A/B: SS 2022 · C/D: SS 2020-22 avg · B/D: associations only",
                                 cell_colors={"Gap Rank": "Gap Rank Cell Color"}))
p.add(836, 168, 424, 524, bar("dim_region[region_en]", [("Random Weights Top 5 %", "1,000 random weightings"),
                                                         ("Leave-One-Out Top 5 %", "12 leave-one-out runs")],
                              "Share of runs with the region in the top 5", "Dirichlet weights (seed 42) and dropping one region at a time",
                              series_colors={"Random Weights Top 5 %": "#5B5A56", "Leave-One-Out Top 5 %": GRAY},
                              sort="Random Weights Top 5 %", legend=True, label_precision=0,
                              tooltips=("Random Weights Median Rank", "Random Weights Worst Rank", "Leave-One-Out Top 5", "Leave-One-Out Worst Rank")))
footer(p)
pages.append(p)

# ------------------------------------------------ 5 Social security trends
p = Page("p5_trends", "5 · Social Security Trends")
header(p, "Social security beneficiaries, 2005-2022",
       "2022 is the transition year to the new social security system: numbers fell everywhere, regional ranks barely moved")
p.add(1010, 12, 250, 56, slicer("dim_region[region_en]", "Region", single=False))
kpi_row(p, [
    ("Peak Beneficiaries", "Peak beneficiaries"),
    ("Peak Year", "Peak year"),
    ("Change Peak to 2022 %", "Change, peak → 2022", ORANGE),
    ("Change 2021 to 2022 %", "Change, 2021 → 2022", ORANGE),
    ("Spearman SS Rate 2020 vs 2022", "Rank corr. of SS rate, 2020 vs 2022"),
    ("Spearman SS Rate 2021 vs 2022", "Rank corr. of SS rate, 2021 vs 2022"),
])
p.add(20, 168, 760, 262, line("dim_year[year]", [("Beneficiaries", "Beneficiaries")], "Beneficiaries per year",
                              "All selected regions · SAMA · values in thousands", labels=True, series_colors={"Beneficiaries": BLUE}, label_units=1000))
p.add(20, 438, 760, 256, line("dim_year[year]", [("SS Rate (Year) %", "Social security rate")],
                              "Social security rate by priority group, 2010-2022",
                              "Beneficiaries / Saudi population · pooled within each group", series="dim_region[priority_group]", legend=True))
p.add(790, 168, 470, 262, line("dim_year[year]", [("Beneficiaries Index 2020=100", "Index")], "Each region indexed, 2020 = 100",
                               "Riyadh (orange) is the only region that fell in 2021 · hover for the others", series="dim_region[region_en]",
                               value_colors={r: (ORANGE if r == "Riyadh" else "#9BC2EA") for r in REGIONS}))
p.add(790, 438, 470, 256, bar("dim_region[region_en]", [("Change 2021 to 2022 %", "Change 2021 → 2022")],
                              "Change in beneficiaries, 2021 → 2022", "Every region fell in the transition year",
                              default_color=BLUE, sort="Change 2021 to 2022 %", sort_desc=False))
footer(p)
pages.append(p)

# ------------------------------------------------ 6 Organizations & population
p = Page("p6_orgs", "6 · Organizations & Population")
header(p, "Where are the non-profits, and how many people do they serve?",
       "Counts follow population (rank corr. 0.87), so regions are compared per 100,000 residents · click a bar to list its organizations")
p.add(1010, 12, 250, 56, slicer("dim_org_type[org_type]", "Organization type (register table)", single=False))
kpi_row(p, [
    ("Associations", "Associations"),
    ("Foundations", "Foundations"),
    ("Regions Without Foundations", "Regions without a foundation", ORANGE),
    ("Spearman Orgs vs Population", "Rank corr., organizations vs population"),
    ("Largest to Smallest Population", "Largest / smallest region (population ×)"),
])
p.add(20, 168, 500, 526, bar(["dim_region[priority_group]", "dim_region[region_en]"],
                             [("Foundations", "Foundations"), ("Associations", "Associations")],
                             "Organizations by region (drill down from priority group)",
                             "Use the drill arrows: priority group → region",
                             series_colors={"Associations": BLUE, "Foundations": ORANGE}, kind="barChart",
                             sort="Organizations (All Types)", legend=True,
                             tooltips=("Share of National Organizations %", "Share of National Foundations %", "Org Density per 100k")))
p.add(530, 168, 330, 262, bar("dim_region[region_en]", [("Population 2022", "Population 2022")], "Population 2022",
                              "Millions · Riyadh, Makkah and Eastern Province are the largest", default_color=GRAY,
                              sort="Population 2022", label_units=1000000, label_precision=1, tooltips=("Population Share %", "Saudi Share %")))
p.add(530, 438, 330, 256, bar("dim_region[region_en]", [("Org Density per 100k", "Non-profits per 100k")],
                              "Non-profits per 100,000 residents", "Coloured = stable priority region",
                              color_measure="Stable Group Color", sort="Org Density per 100k", sort_desc=False,
                              tooltips=("Density Rank", "Organizations (All Types)")))
p.add(870, 168, 390, 526, table([("dim_region[region_en]", "Region"), ("dim_org_type[org_type]", "Type"),
                                 ("fact_organizations[name]", "Name"), ("fact_organizations[reg_no]", "Reg. no.")],
                                "Organization register (detail)", "Filtered by the bars and slicer · 2,723 organizations", font=8))
footer(p)
pages.append(p)

# ------------------------------------------------ 7 Region profile
p = Page("p7_profile", "7 · Region Profile")
p.add(20, 16, 6, 44, textbox([""], bg=True, bgcolor=ORANGE))
p.add(32, 10, 960, 40, card("Title Profile", "", INK, 20) | {"objects": {
    "labels": [{"properties": {"color": color(INK), "fontSize": n(20), "fontFamily": s("Segoe UI Semibold")}}],
    "categoryLabels": [{"properties": {"show": b(False)}}]}, "visualContainerObjects": container(bg=False, border=False)})
p.add(32, 44, 960, 24, textbox([[("Every indicator for one region, with its rank among the 13 · pick a region on the right", 10, MUTED, False)]]))
p.add(1010, 12, 250, 56, slicer("dim_region[region_en]", "Region", default="Najran"))
kpi_row(p, [("Gap Rank", "Gap rank (of 13)", ORANGE), ("Gap Score", "Gap score"), ("Gap Source", "Gap source", INK, 15),
            ("Profile Group", "Final priority group", INK, 11), ("Fragility Index", "Fragility index"), ("Fragility Rank", "Fragility rank")], y=78)
kpi_row(p, [("SS Rate 2022 %", "Social security rate 2022"), ("SS Rate Rank", "Rank (1 = highest)"),
            ("Median Income (Saudi)", "Median income per Saudi (SAR)"), ("Income Rank", "Rank (1 = lowest)"),
            ("Food Share %", "Food share of spending"), ("Food Share Rank", "Rank (1 = highest)")], y=164)
kpi_row(p, [("Org Density per 100k", "Non-profits per 100k"), ("Density Rank", "Rank (1 = lowest)"),
            ("Organizations (All Types)", "Organizations"), ("Foundations", "Foundations"),
            ("Tests in Top 5", "Sensitivity tests in top 5 (of 6)"), ("Random Weights Top 5 %", "Random weightings in top 5")], y=250)
p.add(20, 338, 610, 356, line("dim_year[year]", [("Beneficiaries", "Beneficiaries")], "Social security beneficiaries",
                              "2005-2022 · 2022 is the transition year", labels=True, series_colors={"Beneficiaries": BLUE}, label_units=1000))
p.add(640, 338, 620, 356, table([("dim_org_type[org_type]", "Type"), ("fact_organizations[name]", "Name"),
                                 ("fact_organizations[reg_no]", "Reg. no.")], "Registered organizations", font=8))
footer(p)
pages.append(p)

# ------------------------------------------------ 8 Methodology
p = Page("p8_method", "8 · Methodology & Notes")
header(p, "Methodology, definitions and limitations", "How every number on this report is built")
H2 = lambda t: [(t, 12, INK, True)]
T = lambda t: [(t, 9.5, INK, False)]
p.add(20, 76, 405, 616, textbox([
    H2("Decision question"), T("Where should donors and charities prioritize resources across the 13 regions?"),
    H2("Economic fragility (3 indicators)"),
    T("• Social security rate = beneficiaries / Saudi population (2022, or 2020-22 average)."),
    T("• Median monthly disposable income per Saudi, HIES 2023 (lower = more fragile)."),
    T("• Food & beverages share of household spending, all households (higher = more fragile)."),
    T("Each is converted to a z-score across the 13 regions (population SD); income is reversed. Fragility index = mean of the three (equal weights)."),
    H2("Non-profit density"), T("Associations + foundations per 100,000 residents, 2022 population."),
    H2("Gap score"), T("z(fragility index) − z(density). Fragility part = z(fragility); few non-profits part = −z(density). The larger part is the gap source."),
], bg=True, border=True))
p.add(437, 76, 405, 616, textbox([
    H2("Scenarios (section 7)"),
    T("A: SS 2022 · all organizations (baseline)"), T("B: SS 2022 · associations only"),
    T("C: SS average 2020-22 · all organizations"), T("D: SS average 2020-22 · associations only"),
    H2("Robustness (section 8)"),
    T("• Six tests on scenario A: base, without each indicator, plus income margin, ranks instead of z-scores."),
    T("• 1,000 Dirichlet random weightings (seed 42)."), T("• Leave one region out (12 runs per region)."),
    T("Stable priority = top 5 in at least 5 of 6 tests: Najran, Jazan, Madinah, Tabuk, Makkah."),
    H2("What is live DAX vs. pre-computed"),
    T("Live in DAX: all indicators, z-scores, fragility, gap, ranks, scenarios A-D, custom weights, quadrants, Spearman correlations, trends."),
    T("Pre-computed in Python (stored as facts): the six-test ranks (incl. the percentile-rank variant), 1,000 random weightings and leave-one-out, because they need repeated re-standardization that DAX cannot do efficiently."),
], bg=True, border=True))
p.add(854, 76, 406, 616, textbox([
    H2("Limitations"),
    T("• Indicators are not from one year: population and social security 2022, organizations ~mid-2022, HIES 2023."),
    T("• 2022 is the transition to the new social security system; the rate partly reflects system coverage, not poverty alone."),
    T("• Saudi population 2020-21 is back-cast from the 2022 census (affects scenarios C/D)."),
    T("• Food share covers all households; the source has no nationality split by region."),
    T("• No margin of error is published for the HIES survey."),
    T("• Organization counts ignore size and service area; each is counted in its head-office region."),
    H2("Data sources"),
    T("NCNP open data (2,723 organizations) · SAMA population 2010-22 and social security 2005-22 · GASTAT Saudi population (census 2022) · GASTAT HIES 2023 publication tables."),
    H2("Validation"),
    T("Every region-level value and rank in this model was checked against the notebook outputs (see 04_docs/10_Validation_Report.md)."),
], bg=True, border=True))
pages.append(p)

# ============================================================ single-page dashboard (the delivered report)
# The multi-page layout above is kept as a reference library. The delivered report is ONE dashboard page plus two
# hidden helper pages: a report-page tooltip (hover a region) and a drill-through page (right-click a region).
W, H = 1600, 900
TT = "tt_region"          # tooltip page name
DT = "region_detail"      # drill-through page name


def with_tooltip(v):
    """Use the region tooltip page when hovering this visual."""
    v["visualContainerObjects"]["visualTooltip"] = [{"properties": {"show": b(True), "type": s("Canvas"), "section": s(TT)}}]
    return v


def tune_bars(v, padding=12, font=8):
    v["objects"]["categoryAxis"][0]["properties"].update({"innerPadding": n(padding), "fontSize": n(font)})
    return v


d = Page("dashboard", "Regional Priorities Dashboard")
d.add(20, 14, 6, 46, textbox([""], bg=True, bgcolor=ORANGE))
d.add(32, 0, 1100, 50, textbox([[("Where should charitable resources go first?", 20, INK, True)]]))
d.add(32, 46, 1100, 32, textbox([[("13 regions ranked by the gap between economic fragility and non-profit density · orange = fragility-driven · "
                                   "blue = few non-profits · hover a region for its profile, right-click > Drill through for details", 9, MUTED, False)]]))
d.add(1150, 12, 210, 58, slicer("dim_scenario[scenario_label]", "Gap scenario", default="A · SS 2022 · All organizations", sync="scenario"))
d.add(1370, 12, 210, 58, slicer("dim_region[region_en]", "Region filter", single=False))
kpi_row(d, [
    ("Organizations (All Types)", "Registered non-profits"),
    ("Population 2022 Label", "Population 2022"),
    ("Org Density per 100k", "Non-profits per 100k"),
    ("Beneficiaries 2022", "SS beneficiaries 2022"),
    ("Top Priority Region", "#1 priority (scenario)", ORANGE),
    ("Top Priority Gap", "Gap score of #1", ORANGE),
    ("Stable Priority List", "Stable priorities (top 5 in ≥5 of 6 tests)", BLUE, 13, 2.2),
], y=80, h=72, total_w=1560)
# row 2
tile = scatter("dim_region[region_en]", "Tile X", "Tile Y", "Where the priority regions are",
               "Schematic tile map, not to scale · stable priority groups", size="Tile Size", color_measure="Stable Group Color",
               axes=False, x_range=(-0.75, 3.75), y_range=(-4.7, 0.7))
tile["objects"]["categoryLabels"][0]["properties"]["fontSize"] = n(8)
d.add(20, 162, 360, 336, with_tooltip(tile))
d.add(390, 162, 380, 336, with_tooltip(tune_bars(bar("dim_region[region_en]", [("Gap Score", "Gap score")], title_measure="Title Gap Chart",
                                           color_measure="Priority Color", sort="Gap Score"), padding=5)))
d.add(780, 162, 440, 336, with_tooltip(scatter(
    "dim_region[region_en]", "Density (Scenario)", "Fragility Index", "Fragility vs. non-profit density",
    "Dashed lines = 13-region medians · top-left = more fragile, fewer organizations", color_measure="Priority Color",
    x_title="Non-profits per 100k", y_title="Fragility index", ref_x="Median Density", ref_y="Median Fragility")))
# row 3
d.add(20, 506, 420, 366, with_tooltip(tune_bars(bar(
    "dim_region[region_en]", [("Fragility Part", "Fragility part of the gap"), ("Few Non-profits Part", "Few non-profits part")],
    "Why each region is a priority", None,
    series_colors={"Fragility Part": ORANGE, "Few Non-profits Part": BLUE}, sort="Gap Score", legend=True, labels=False,
    kind="barChart"), padding=5)))
d.add(450, 506, 370, 366, with_tooltip(tune_bars(bar(
    "dim_region[region_en]", [("Random Weights Top 5 %", "% of 1,000 weightings in top 5"), ("Leave-One-Out Top 5 %", "% of 12 leave-one-out")],
    "How stable is the ranking?", None,
    series_colors={"Random Weights Top 5 %": "#5B5A56", "Leave-One-Out Top 5 %": GRAY},
    sort="Random Weights Top 5 %", legend=True, labels=False), padding=5)))
trend = line("dim_year[year]", [("Beneficiaries", "Beneficiaries")], "Social security beneficiaries, 2005-2022",
             "Peak 1.55M in 2021, −28.7% in 2022 (transition to the new system)", series_colors={"Beneficiaries": BLUE}, label_units=1000)
trend["objects"]["categoryAxis"][0]["properties"]["axisType"] = s("Scalar")
d.add(830, 506, 390, 366, trend)
# insights column
d.add(1230, 162, 350, 710, textbox([
    [("Key insights", 14, INK, True)],
    [("1  Najran is the clear first priority. ", 10, ORANGE, True),
     ("Gap 1.94 vs 0.77 for #2; lowest Saudi median income (SAR 1,650/month), highest food share (43.5%), no foundations. #1 in all 6 sensitivity tests.", 10, INK, False)],
    [("2  Jazan is second, also driven by fragility. ", 10, ORANGE, True),
     ("2nd-highest social security rate (9.84%), no foundations. Least stable priority: top 5 in 72.9% of 1,000 random weightings.", 10, INK, False)],
    [("3  Madinah, Tabuk and Makkah: service gaps. ", 10, BLUE, True),
     ("Fragility at or below average but among the lowest non-profit densities (8.56, 8.24, 5.54 per 100k). Makkah has the most beneficiaries of the five (245,796).", 10, INK, False)],
    [("4  Non-profits are concentrated. ", 10, INK, True),
     ("Riyadh hosts 29% of all non-profits and 60% of foundations; Jazan, Hail, Al-Baha, Tabuk and Najran have none.", 10, INK, False)],
    [("5  Al-Jouf is borderline. ", 10, INK, True),
     ("Top 5 in 2 of 6 tests and 27.5% of weightings: worth monitoring.", 10, INK, False)],
    [("Recommendation", 12, INK, True)],
    [("Donors targeting economic need: Najran, then Jazan (more beneficiaries reached). Donors targeting service gaps: Madinah, Tabuk, Makkah.", 10, INK, False)],
    [("How to use", 12, INK, True)],
    [("The scenario slicer switches the gap definition (A-D). Click any bar or bubble to cross-filter; hover a region for its profile; "
      "right-click a region > Drill through > Region detail for every indicator and its organizations.", 9, MUTED, False)],
    [("How to read", 12, INK, True)],
    [("Gap = z(fragility) − z(non-profit density). Fragility = mean z-score of the social security rate, Saudi median income (reversed) and food share of spending. "
      "Density = non-profits per 100k residents. Ranking is relative across 13 regions, not an absolute measure of need. "
      "Indicators mix 2022 and 2023 (HIES) data; 2022 is a transition year for social security.", 9, MUTED, False)],
], bg=True, border=True))
d.add(20, 876, 1560, 22, textbox([[("Sources: NCNP non-profit register · SAMA population & social security · GASTAT census 2022 · HIES 2023 · "
                                    "every value validated against analysis.ipynb (534 checks)", 8, MUTED, False)]]))


# ------------------------------------------------ hidden tooltip page (hover a region)
def region_binding(page_type):
    f = c_ref("dim_region", "region_en")
    key = page_type.lower()
    return ({"filters": [{"name": f"{key}_region_filter", "field": f, "type": "Categorical", "howCreated": "Drillthrough"}]},
            {"name": f"{key}_region_binding", "type": page_type,
             "parameters": [{"name": f"{key}_region_param", "boundFilter": f"{key}_region_filter", "fieldExpr": f}]})


def plain_card(measure, size, col=INK, bold=True):
    v = card(measure, "", col, size)
    v["objects"]["categoryLabels"] = [{"properties": {"show": b(False)}}]
    v["objects"]["labels"][0]["properties"]["fontFamily"] = s("Segoe UI Semibold" if bold else "Segoe UI")
    v["visualContainerObjects"] = container(bg=False, border=False)
    return v


tt = Page(TT, "Region tooltip")
tt.size, tt.extra = (340, 250), {"type": "Tooltip", "visibility": "HiddenInViewMode"}
tt.extra["filterConfig"], tt.extra["pageBinding"] = region_binding("Tooltip")
tt.add(8, 2, 324, 34, plain_card("Title Tooltip", 13))
tt.add(8, 34, 324, 24, plain_card("Tooltip Rank Line", 9, MUTED, False))
for i, (meas, label) in enumerate([("Gap Score", "Gap score"), ("Fragility Index", "Fragility index"), ("Org Density per 100k", "Per 100k"),
                                   ("SS Rate 2022 %", "SS rate 2022"), ("Median Income (Saudi)", "Income (SAR)"), ("Food Share %", "Food share"),
                                   ("Organizations (All Types)", "Organizations"), ("Tests in Top 5", "Tests top 5"),
                                   ("Random Weights Top 5 %", "Weights top 5")]):
    v = card(meas, label, ORANGE if i == 0 else INK, 13)
    v["visualContainerObjects"] = container(bg=False, border=False)
    tt.add(8 + (i % 3) * 110, 62 + (i // 3) * 62, 104, 58, v)

# ------------------------------------------------ hidden drill-through page (right-click a region > Drill through)
dt = Page(DT, "Region detail")
dt.extra = {"type": "Drillthrough", "visibility": "HiddenInViewMode"}
dt.extra["filterConfig"], dt.extra["pageBinding"] = region_binding("Drillthrough")
dt.add(20, 14, 6, 46, textbox([""], bg=True, bgcolor=ORANGE))
dt.add(32, 6, 1100, 42, plain_card("Title Drillthrough", 20))
dt.add(32, 44, 1100, 30, textbox([[("Every indicator for this region with its rank among the 13 · use the Back button (Ctrl+click in Desktop) to return to the dashboard",
                                    9, MUTED, False)]]))
dt.add(1150, 12, 210, 58, slicer("dim_scenario[scenario_label]", "Gap scenario", default="A · SS 2022 · All organizations", sync="scenario"))
DEF = {"id": "default"}
dt.add(1370, 12, 210, 58, {"visualType": "actionButton",
                           "objects": {"icon": [{"properties": {"show": b(True), "shapeType": s("back"), "lineColor": color(INK), "lineWeight": n(2)}, "selector": DEF}],
                                       "text": [{"properties": {"show": b(True), "text": s("Back to dashboard"), "fontColor": color(INK), "fontSize": n(11)}, "selector": DEF}],
                                       "fill": [{"properties": {"show": b(True), "fillColor": color("#FFFFFF"), "transparency": n(0)}, "selector": DEF}],
                                       "outline": [{"properties": {"show": b(True), "lineColor": color(GRID)}, "selector": DEF}]},
                           "visualContainerObjects": {"visualLink": [{"properties": {"show": b(True), "type": s("Back")}}]}})
kpi_row(dt, [("Gap Rank", "Gap rank (of 13)", ORANGE), ("Gap Score", "Gap score"), ("Gap Source", "Gap source", INK, 15),
             ("Profile Group", "Final priority group", INK, 11), ("Fragility Index", "Fragility index"), ("Fragility Rank", "Fragility rank")], y=80, total_w=1560)
kpi_row(dt, [("SS Rate 2022 %", "Social security rate 2022"), ("SS Rate Rank", "Rank (1 = highest)"),
             ("Median Income (Saudi)", "Median income per Saudi (SAR)"), ("Income Rank", "Rank (1 = lowest)"),
             ("Food Share %", "Food share of spending"), ("Food Share Rank", "Rank (1 = highest)")], y=166, total_w=1560)
kpi_row(dt, [("Org Density per 100k", "Non-profits per 100k"), ("Density Rank", "Rank (1 = lowest)"),
             ("Organizations (All Types)", "Organizations"), ("Foundations", "Foundations"),
             ("Tests in Top 5", "Sensitivity tests in top 5 (of 6)"), ("Random Weights Top 5 %", "Random weightings in top 5")], y=252, total_w=1560)
dt_trend = line("dim_year[year]", [("Beneficiaries", "Beneficiaries")], "Social security beneficiaries", "2005-2022 · 2022 is the transition year",
                labels=True, series_colors={"Beneficiaries": BLUE}, label_units=1000)
dt_trend["objects"]["categoryAxis"][0]["properties"]["axisType"] = s("Scalar")
dt.add(20, 340, 560, 530, dt_trend)
dt.add(590, 340, 380, 530, bar("dim_sensitivity_test[test_short]", [("Test Rank", "Gap rank")], "Rank in each sensitivity test",
                               "1 = highest priority · 6 robustness tests on scenario A", default_color=GRAY))
dt.add(980, 340, 600, 530, table([("dim_org_type[org_type]", "Type"), ("fact_organizations[name]", "Name"),
                                  ("fact_organizations[reg_no]", "Reg. no.")], "Registered organizations", font=8))
dt.add(20, 876, 1560, 22, textbox([[("Ranks and z-scores are always computed against all 13 regions · Sources: NCNP, SAMA, GASTAT census 2022, HIES 2023",
                                     8, MUTED, False)]]))
pages = [d, tt, dt]


# ============================================================ write PBIR
def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def theme():
    return {
        "name": "RegionalPriorities",
        "dataColors": [ORANGE, BLUE, GRAY, "#1BAF7A", "#7E57C2", "#F2C14E", "#5B5A56", "#9BC2EA", "#F6A988", "#3D6E9E",
                       "#8C8A82", "#C7E3D6", "#D9C2F0"],
        "background": "#FFFFFF", "foreground": INK, "tableAccent": ORANGE,
        "good": "#1BAF7A", "neutral": GRAY, "bad": ORANGE, "maximum": ORANGE, "center": "#FBD3C2", "minimum": "#FFFFFF",
        "textClasses": {
            "callout": {"fontSize": 22, "fontFace": "Segoe UI Semibold", "color": INK},
            "title": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": INK},
            "header": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": INK},
            "label": {"fontSize": 9, "fontFace": "Segoe UI", "color": INK},
        },
        "visualStyles": {
            "*": {"*": {
                "background": [{"show": True, "color": {"solid": {"color": "#FFFFFF"}}, "transparency": 0}],
                "border": [{"show": True, "color": {"solid": {"color": GRID}}, "radius": 8}],
                "dropShadow": [{"show": False}],
                "visualHeader": [{"show": True}],
            }},
            "page": {"*": {
                "background": [{"color": {"solid": {"color": BG}}, "transparency": 0}],
                "outspace": [{"color": {"solid": {"color": BG}}, "transparency": 0}],
            }},
        },
    }


if RPT.exists():
    shutil.rmtree(RPT)
dump(PBI / "RegionalPriorities.pbip", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
    "version": "1.0", "artifacts": [{"report": {"path": "RegionalPriorities.Report"}}],
    "settings": {"enableAutoRecovery": True}})
dump(RPT / ".platform", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
    "metadata": {"type": "Report", "displayName": "RegionalPriorities"},
    "config": {"version": "2.0", "logicalId": str(uuid.uuid5(NS, "report"))}})
dump(RPT / "definition.pbir", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
    "version": "4.0", "datasetReference": {"byPath": {"path": "../RegionalPriorities.SemanticModel"}}})
D = RPT / "definition"
dump(D / "version.json", {"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
dump(D / "report.json", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.0.0/schema.json",
    "themeCollection": {
        "baseTheme": {"name": "CY24SU10", "reportVersionAtImport": {"visual": "1.8.97", "report": "2.0.97", "page": "1.3.97"}, "type": "SharedResources"},
        "customTheme": {"name": THEME_NAME, "reportVersionAtImport": {"visual": "1.8.97", "report": "2.0.97", "page": "1.3.97"}, "type": "RegisteredResources"}},
    "objects": {"outspacePane": [{"properties": {"expanded": b(False)}}]},
    "resourcePackages": [
        {"name": "SharedResources", "type": "SharedResources", "items": [{"name": "CY24SU10", "path": "BaseThemes/CY24SU10.json", "type": "BaseTheme"}]},
        {"name": "RegisteredResources", "type": "RegisteredResources", "items": [{"name": THEME_NAME, "path": THEME_NAME, "type": "CustomTheme"}]}],
    "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized", "defaultDrillFilterOtherVisuals": True,
                 "allowChangeFilterTypes": True, "useEnhancedTooltips": True}})
dump(RPT / "StaticResources" / "RegisteredResources" / THEME_NAME, theme())
dump(PBI / "theme" / THEME_NAME, theme())
dump(D / "pages" / "pages.json", {
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
    "pageOrder": [pg.name for pg in pages], "activePageName": pages[0].name})
for pg in pages:
    dump(D / "pages" / pg.name / "page.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
        "name": pg.name, "displayName": pg.display, "displayOption": "FitToPage",
        "height": (pg.size or (W, H))[1], "width": (pg.size or (W, H))[0], **pg.extra})
    for v in pg.visuals:
        dump(D / "pages" / pg.name / "visuals" / v["name"] / "visual.json", v)
print(f"Report written: {len(pages)} pages, {sum(len(pg.visuals) for pg in pages)} visuals")
