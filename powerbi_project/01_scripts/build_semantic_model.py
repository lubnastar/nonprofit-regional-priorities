"""
Step 2 of the Power BI build: writes the semantic model (TMDL) of RegionalPriorities.pbip
and the DAX / Power Query reference documents from one definition.

    .venv\\Scripts\\python powerbi_project\\01_scripts\\build_semantic_model.py
"""
import base64
import json
import zlib
import shutil
import textwrap
import uuid
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
DATA = PROJECT / "02_data"
PBI = PROJECT / "03_powerbi"
SM = PBI / "RegionalPriorities.SemanticModel"
DOCS = PROJECT / "04_docs"
NS = uuid.UUID("6f1c2d9e-0b7a-4c55-9e1f-2a6b3c4d5e6f")


def tag(*parts):
    return str(uuid.uuid5(NS, "/".join(parts)))


def q(name):
    """TMDL / DAX quoted object name."""
    return name if name.replace("_", "").isalnum() and not name[0].isdigit() else "'" + name.replace("'", "''") + "'"


# ============================================================ tables
# (column, M type, TMDL dataType, formatString, hidden, sortBy, description)
I, T, D, B, DT = "Int64.Type", "type text", "type number", "type logical", "type date"
TABLES = {
    "dim_region": dict(desc="One row per administrative region (13). Conformed dimension for every fact.", cols=[
        ("region_id", I, "int64", "0", True, None, "Region key (1-13, equals SAMA Province ID)"),
        ("region_en", T, "string", None, False, "baseline_gap_rank", "Region name (English)"),
        ("region_ar", T, "string", None, False, "baseline_gap_rank", "Region name (Arabic)"),
        ("tile_col", I, "int64", "0", True, None, "Column of the region on the schematic tile map"),
        ("tile_row", I, "int64", "0", True, None, "Row of the region on the schematic tile map"),
        ("priority_group", T, "string", None, False, "priority_group_order",
         "Final notebook classification: stable priority (top 5 in >= 5 of 6 tests) split by gap source"),
        ("priority_group_order", I, "int64", "0", True, None, "Sort order of priority_group"),
        ("baseline_gap_rank", I, "int64", "0", False, None, "Gap rank in scenario A with equal weights (notebook result)"),
    ]),
    "dim_year": dict(desc="Year dimension 2005-2022 (all time series in the data are annual).", cols=[
        ("year", I, "int64", "0", False, None, "Calendar year"),
        ("year_start", DT, "dateTime", "yyyy", True, None, "1 January of the year"),
        ("period", T, "string", None, False, None, "2005-2019 or the 2020-2022 averaging window"),
        ("is_transition_year", B, "boolean", None, False, None, "TRUE for 2022, the transition to the new social security system"),
    ]),
    "dim_org_type": dict(desc="Organization type: association or foundation.", cols=[
        ("org_type_id", I, "int64", "0", True, None, "Organization type key"),
        ("org_type", T, "string", None, False, "org_type_id", "Association or Foundation"),
        ("org_type_ar", T, "string", None, False, "org_type_id", "Arabic label"),
    ]),
    "dim_sensitivity_test": dict(desc="The six sensitivity tests of notebook section 8.1.", cols=[
        ("test_id", I, "int64", "0", True, None, "Test key"),
        ("test_key", T, "string", None, True, None, "Column name used in the notebook"),
        ("test_name", T, "string", None, False, "test_id", "Test name"),
        ("test_short", T, "string", None, False, "test_id", "Short test name for matrix headers"),
        ("what_changes", T, "string", None, False, None, "What the test changes versus the base"),
    ]),
    "dim_scenario": dict(desc="Disconnected selector for the four gap scenarios of notebook section 7.", cols=[
        ("scenario", T, "string", None, False, "scenario_order", "Scenario letter A-D"),
        ("scenario_label", T, "string", None, False, "scenario_order", "Scenario label for slicers"),
        ("social_security_basis", T, "string", None, False, None, "2022 or average 2020-2022"),
        ("organizations_counted", T, "string", None, False, None, "All organizations or associations only"),
        ("scenario_order", I, "int64", "0", True, None, "Sort order"),
    ]),
    "fact_region_snapshot": dict(desc="Region-level snapshot: population 2022, social security 2022 and 2020-22 average, HIES 2023 income and spending.", cols=[
        ("region_id", I, "int64", "0", True, None, "Region key"),
        ("population_2022", I, "int64", "#,0", True, None, "Total population 2022 (SAMA)"),
        ("saudi_population_2022", I, "int64", "#,0", True, None, "Saudi population 2022 (GASTAT census)"),
        ("saudi_population_avg_2020_2022", D, "double", "#,0", True, None, "Average Saudi population 2020-2022"),
        ("beneficiaries_2022", I, "int64", "#,0", True, None, "Social security beneficiaries 2022"),
        ("beneficiaries_avg_2020_2022", D, "double", "#,0", True, None, "Average beneficiaries 2020-2022"),
        ("income_median_saudi", I, "int64", "#,0", True, None, "Median monthly disposable income per Saudi, SAR (HIES 2023)"),
        ("income_mean_saudi", I, "int64", "#,0", True, None, "Mean monthly income per Saudi, SAR"),
        ("spend_mean_saudi", I, "int64", "#,0", True, None, "Mean monthly spending per Saudi, SAR"),
        ("food_share", D, "double", "0.0%", True, None, "Food & beverages share of household spending, all households (0-1)"),
    ]),
    "fact_population": dict(desc="Population by region and year, 2010-2022.", cols=[
        ("region_id", I, "int64", "0", True, None, "Region key"),
        ("year", I, "int64", "0", True, None, "Year key"),
        ("population", I, "int64", "#,0", True, None, "Total population (SAMA)"),
        ("saudi_population", I, "int64", "#,0", True, None, "Saudi population (GASTAT; 2010-2021 back-cast from the 2022 census)"),
    ]),
    "fact_social_security": dict(desc="Social security beneficiaries by region and year, 2005-2022 (Grand Total row removed after reconciliation).", cols=[
        ("region_id", I, "int64", "0", True, None, "Region key"),
        ("year", I, "int64", "0", True, None, "Year key"),
        ("beneficiaries", I, "int64", "#,0", True, None, "Beneficiaries (individuals: head of household and dependants)"),
    ]),
    "fact_organizations": dict(desc="One row per registered non-profit organization (2,723), by region of head office.", cols=[
        ("org_id", I, "int64", "0", True, None, "Surrogate key (reg_no is not unique in the source)"),
        ("region_id", I, "int64", "0", True, None, "Region key"),
        ("org_type_id", I, "int64", "0", True, None, "Organization type key"),
        ("reg_no", I, "int64", "0", False, None, "Registration number from NCNP"),
        ("name", T, "string", None, False, None, "Organization name (Arabic, as published)"),
        ("name_truncated", B, "boolean", None, False, None, "TRUE when the published name ends with an ellipsis"),
    ]),
    "fact_sensitivity_rank": dict(desc="Gap rank of each region in each of the six sensitivity tests (notebook 8.1).", cols=[
        ("region_id", I, "int64", "0", True, None, "Region key"),
        ("test_id", I, "int64", "0", True, None, "Test key"),
        ("gap_rank", I, "int64", "0", True, None, "Gap rank, 1 = largest gap (ties share the lowest rank)"),
    ]),
    "fact_robustness": dict(desc="Random-weights (1,000 Dirichlet draws, seed 42) and leave-one-out results (notebook 8.2-8.3).", cols=[
        ("region_id", I, "int64", "0", True, None, "Region key"),
        ("weights_top5_pct", D, "double", "0.0", True, None, "% of 1,000 random weightings with the region in the top 5"),
        ("weights_median_rank", D, "double", "0", True, None, "Median rank across the 1,000 weightings"),
        ("weights_best", I, "int64", "0", True, None, "Best rank across the weightings"),
        ("weights_worst", I, "int64", "0", True, None, "Worst rank across the weightings"),
        ("loo_top5", I, "int64", "0", True, None, "Times in the top 5 out of 12 leave-one-region-out runs"),
        ("loo_best", I, "int64", "0", True, None, "Best rank in leave-one-out"),
        ("loo_worst", I, "int64", "0", True, None, "Worst rank in leave-one-out"),
    ]),
}

RELATIONSHIPS = [
    ("fact_region_snapshot", "region_id", "dim_region", "region_id"),
    ("fact_population", "region_id", "dim_region", "region_id"),
    ("fact_population", "year", "dim_year", "year"),
    ("fact_social_security", "region_id", "dim_region", "region_id"),
    ("fact_social_security", "year", "dim_year", "year"),
    ("fact_organizations", "region_id", "dim_region", "region_id"),
    ("fact_organizations", "org_type_id", "dim_org_type", "org_type_id"),
    ("fact_sensitivity_rank", "region_id", "dim_region", "region_id"),
    ("fact_sensitivity_rank", "test_id", "dim_sensitivity_test", "test_id"),
    ("fact_robustness", "region_id", "dim_region", "region_id"),
]

WEIGHT_TABLES = {  # what-if parameters for the fragility weights
    "Weight SS": "Weight of the social security rate in the fragility index (0-5, default 1)",
    "Weight Income": "Weight of low Saudi median income in the fragility index (0-5, default 1)",
    "Weight Food": "Weight of the food share of spending in the fragility index (0-5, default 1)",
}

# ============================================================ measures
ORANGE, BLUE, GRAY = "#EB6834", "#2A78D6", "#B4B2A9"
ONE = "HASONEVALUE ( dim_region[region_id] )"


def z(measure, sign=""):
    return f"""
VAR _all = ALL ( dim_region )
VAR _mu = AVERAGEX ( _all, {measure} )
VAR _sd = STDEVX.P ( _all, {measure} )
RETURN
    IF ( {ONE}, {sign}DIVIDE ( {measure} - _mu, _sd ) )"""


def spearman(x, y):
    """Spearman rank correlation across the 13 regions; ties get the average rank (as pandas)."""
    return f"""
VAR _t =
    ADDCOLUMNS ( ALL ( dim_region ), "@x", {x}, "@y", {y} )
VAR _r =
    ADDCOLUMNS (
        _t,
        "@rx", VAR _cx = [@x] RETURN COUNTROWS ( FILTER ( _t, [@x] < _cx ) ) + ( COUNTROWS ( FILTER ( _t, [@x] = _cx ) ) + 1 ) / 2,
        "@ry", VAR _cy = [@y] RETURN COUNTROWS ( FILTER ( _t, [@y] < _cy ) ) + ( COUNTROWS ( FILTER ( _t, [@y] = _cy ) ) + 1 ) / 2
    )
VAR _mx = AVERAGEX ( _r, [@rx] )
VAR _my = AVERAGEX ( _r, [@ry] )
VAR _cov = SUMX ( _r, ( [@rx] - _mx ) * ( [@ry] - _my ) )
VAR _sx = SQRT ( SUMX ( _r, ( [@rx] - _mx ) ^ 2 ) )
VAR _sy = SQRT ( SUMX ( _r, ( [@ry] - _my ) ^ 2 ) )
RETURN
    DIVIDE ( _cov, _sx * _sy )"""


# (folder, name, expression, format, description)
M = [
    # ---------------------------------------------------------------- 1 Base
    ("1. Base", "Regions", "DISTINCTCOUNT ( fact_region_snapshot[region_id] )", "0", "Number of regions in the current filter context."),
    ("1. Base", "Population 2022", "SUM ( fact_region_snapshot[population_2022] )", "#,0", "Total population 2022 (SAMA)."),
    ("1. Base", "Saudi Population 2022", "SUM ( fact_region_snapshot[saudi_population_2022] )", "#,0", "Saudi population 2022 (GASTAT census)."),
    ("1. Base", "Saudi Population Avg 2020-22", "SUM ( fact_region_snapshot[saudi_population_avg_2020_2022] )", "#,0", "Average Saudi population 2020-2022; denominator of the averaged social security rate."),
    ("1. Base", "Saudi Share %", "DIVIDE ( [Saudi Population 2022], [Population 2022] )", "0.0%", "Saudis as a share of the population, 2022."),
    ("1. Base", "Population Share %", "DIVIDE ( [Population 2022], CALCULATE ( [Population 2022], ALL ( dim_region ) ) )", "0.0%", "Region's share of the national population, 2022."),
    ("1. Base", "Organizations", "COUNTROWS ( fact_organizations )", "#,0", "Registered non-profit organizations (respects an organization-type filter)."),
    ("1. Base", "Organizations (All Types)", "CALCULATE ( COUNTROWS ( fact_organizations ), REMOVEFILTERS ( dim_org_type ) ) + 0", "#,0", "Associations + foundations, ignoring any organization-type filter."),
    ("1. Base", "Associations", 'CALCULATE ( COUNTROWS ( fact_organizations ), dim_org_type[org_type] = "Association" ) + 0', "#,0", "Registered civil associations."),
    ("1. Base", "Foundations", 'CALCULATE ( COUNTROWS ( fact_organizations ), dim_org_type[org_type] = "Foundation" ) + 0', "#,0", "Registered civil foundations."),
    ("1. Base", "Foundation Share %", "DIVIDE ( [Foundations], [Organizations (All Types)] )", "0.0%", "Foundations as a share of all organizations in the region."),
    ("1. Base", "Share of National Organizations %", "DIVIDE ( [Organizations (All Types)], CALCULATE ( [Organizations (All Types)], ALL ( dim_region ) ) )", "0.0%", "Region's share of all 2,723 organizations."),
    ("1. Base", "Share of National Foundations %", "DIVIDE ( [Foundations], CALCULATE ( [Foundations], ALL ( dim_region ) ) )", "0.0%", "Region's share of all foundations."),
    ("1. Base", "Regions Without Foundations", "COUNTROWS ( FILTER ( VALUES ( dim_region[region_id] ), [Foundations] = 0 ) )", "0", "Regions with no registered foundation."),
    ("1. Base", "Beneficiaries 2022", "SUM ( fact_region_snapshot[beneficiaries_2022] )", "#,0", "Social security beneficiaries in 2022."),
    ("1. Base", "Beneficiaries Avg 2020-22", "SUM ( fact_region_snapshot[beneficiaries_avg_2020_2022] )", "#,0", "Average beneficiaries over 2020-2022."),
    ("1. Base", "Median Income (Saudi)", f"IF ( {ONE}, SUM ( fact_region_snapshot[income_median_saudi] ) )", "#,0", "Median monthly disposable income per Saudi, SAR (HIES 2023). Region level only: medians cannot be added up."),
    ("1. Base", "Mean Income (Saudi)", f"IF ( {ONE}, SUM ( fact_region_snapshot[income_mean_saudi] ) )", "#,0", "Mean monthly income per Saudi, SAR."),
    ("1. Base", "Mean Spending (Saudi)", f"IF ( {ONE}, SUM ( fact_region_snapshot[spend_mean_saudi] ) )", "#,0", "Mean monthly spending per Saudi, SAR."),
    ("1. Base", "Income Margin (Saudi)", "[Mean Income (Saudi)] - [Mean Spending (Saudi)]", "#,0", "Mean income minus mean spending; only used in the 'plus margin' sensitivity test (negative in Jazan)."),
    ("1. Base", "Food Share %", f"IF ( {ONE}, SUM ( fact_region_snapshot[food_share] ) )", "0.0%", "Food & beverages share of household spending (all households), HIES 2023."),

    # ---------------------------------------------------------------- 2 Indicators
    ("2. Indicators", "SS Rate 2022 %", "DIVIDE ( [Beneficiaries 2022], [Saudi Population 2022] )", "0.00%", "Social security beneficiaries 2022 / Saudi population 2022. Higher = more fragile."),
    ("2. Indicators", "SS Rate Avg 2020-22 %", "DIVIDE ( [Beneficiaries Avg 2020-22], [Saudi Population Avg 2020-22] )", "0.00%", "Average beneficiaries 2020-22 / average Saudi population 2020-22."),
    ("2. Indicators", "Org Density per 100k", "DIVIDE ( [Organizations (All Types)], [Population 2022] ) * 100000", "0.00", "Associations + foundations per 100,000 residents (2022)."),
    ("2. Indicators", "Association Density per 100k", "DIVIDE ( [Associations], [Population 2022] ) * 100000", "0.00", "Associations per 100,000 residents (2022)."),
    ("2. Indicators", "Selected Scenario", 'SELECTEDVALUE ( dim_scenario[scenario], "A" )', None, "Scenario chosen in the slicer; A when nothing or several are selected."),
    ("2. Indicators", "Scenario Label", 'SELECTEDVALUE ( dim_scenario[scenario_label], "A · SS 2022 · All organizations" )', None, "Label of the active scenario."),
    ("2. Indicators", "SS Rate (Scenario) %", 'IF ( [Selected Scenario] IN { "A", "B" }, [SS Rate 2022 %], [SS Rate Avg 2020-22 %] )', "0.00%", "Social security rate used by the active scenario (2022 for A/B, 2020-22 average for C/D)."),
    ("2. Indicators", "Density (Scenario)", 'IF ( [Selected Scenario] IN { "A", "C" }, [Org Density per 100k], [Association Density per 100k] )', "0.00", "Density used by the active scenario (all organizations for A/C, associations only for B/D)."),
    ("2. Indicators", "Weight SS Value", "SELECTEDVALUE ( 'Weight SS'[Weight SS], 1 )", "0", "Selected weight of the social security rate (default 1)."),
    ("2. Indicators", "Weight Income Value", "SELECTEDVALUE ( 'Weight Income'[Weight Income], 1 )", "0", "Selected weight of low income (default 1)."),
    ("2. Indicators", "Weight Food Value", "SELECTEDVALUE ( 'Weight Food'[Weight Food], 1 )", "0", "Selected weight of the food share (default 1)."),
    ("2. Indicators", "Weights Label", '"Weights  SS : Income : Food  =  " & [Weight SS Value] & " : " & [Weight Income Value] & " : " & [Weight Food Value] & IF ( [Weight SS Value] = [Weight Income Value] && [Weight Income Value] = [Weight Food Value], "  (equal, as in the notebook)", "  (custom)" ) & IF ( [Weight SS Value] + [Weight Income Value] + [Weight Food Value] = 0, "  · all weights are 0: index undefined", "" )', None, "Text of the active fragility weights."),

    # ---------------------------------------------------------------- 3 Fragility
    ("3. Fragility", "Z SS Rate", z("[SS Rate (Scenario) %]"), "0.00", "z-score of the social security rate across the 13 regions (population SD). Higher = more fragile."),
    ("3. Fragility", "Z Low Income", z("[Median Income (Saudi)]", "-"), "0.00", "Negative z-score of Saudi median income, so higher = more fragile."),
    ("3. Fragility", "Z Food Share", z("[Food Share %]"), "0.00", "z-score of the food share of spending. Higher = more fragile."),
    ("3. Fragility", "Fragility Index", f"""
VAR _w1 = [Weight SS Value]
VAR _w2 = [Weight Income Value]
VAR _w3 = [Weight Food Value]
RETURN
    IF ( {ONE}, DIVIDE ( _w1 * [Z SS Rate] + _w2 * [Z Low Income] + _w3 * [Z Food Share], _w1 + _w2 + _w3 ) )""", "+0.00;-0.00;0.00",
     "Composite economic fragility: weighted mean of the three z-scores (equal weights = notebook). 0 = average of the 13 regions."),
    ("3. Fragility", "Fragility Rank", f"IF ( {ONE}, RANKX ( ALL ( dim_region ), [Fragility Index], , DESC, SKIP ) )", "0", "1 = most fragile region."),
    ("3. Fragility", "SS Rate Rank", f"IF ( {ONE}, RANKX ( ALL ( dim_region ), [SS Rate 2022 %], , DESC, SKIP ) )", "0", "1 = highest social security rate 2022."),
    ("3. Fragility", "Income Rank", f"IF ( {ONE}, RANKX ( ALL ( dim_region ), [Median Income (Saudi)], , ASC, SKIP ) )", "0", "1 = lowest Saudi median income."),
    ("3. Fragility", "Food Share Rank", f"IF ( {ONE}, RANKX ( ALL ( dim_region ), [Food Share %], , DESC, SKIP ) )", "0", "1 = highest food share of spending."),
    ("3. Fragility", "Fragility Color", f'IF ( {ONE}, IF ( [Fragility Index] > 0, "{ORANGE}", "{GRAY}" ) )', None, "Orange when more fragile than the 13-region average."),
    ("3. Fragility", "Fragility Cell Color", 'VAR _f = [Fragility Index] RETURN SWITCH ( TRUE (), ISBLANK ( _f ), BLANK (), _f >= 1, "#F08A5D", _f > 0, "#FBD3C2", "#FFFFFF" )', None, "Table background: dark orange >= 1, light orange > 0."),
    ("3. Fragility", "Most Fragile Region", "MAXX ( FILTER ( ALL ( dim_region ), [Fragility Rank] = 1 ), dim_region[region_en] )", None, "Region with the highest fragility index."),
    ("3. Fragility", "Lowest Income Region", 'VAR _r = TOPN ( 1, ALL ( dim_region ), [Median Income (Saudi)], ASC ) RETURN MAXX ( _r, dim_region[region_en] ) & " · SAR " & FORMAT ( MAXX ( _r, [Median Income (Saudi)] ), "#,0" )', None, "Region with the lowest Saudi median income and its value."),
    ("3. Fragility", "Highest Food Share Region", 'VAR _r = TOPN ( 1, ALL ( dim_region ), [Food Share %], DESC ) RETURN MAXX ( _r, dim_region[region_en] ) & " · " & FORMAT ( MAXX ( _r, [Food Share %] ), "0.0%" )', None, "Region with the highest food share and its value."),

    # ---------------------------------------------------------------- 4 Gap & priority
    ("4. Gap & Priority", "Z Fragility", z("[Fragility Index]"), "0.00", "z-score of the fragility index across the 13 regions (the 'fragility part' of the gap)."),
    ("4. Gap & Priority", "Z Density", z("[Density (Scenario)]"), "0.00", "z-score of non-profit density across the 13 regions."),
    ("4. Gap & Priority", "Fragility Part", "[Z Fragility]", "+0.00;-0.00;0.00", "Contribution of fragility to the gap score."),
    ("4. Gap & Priority", "Few Non-profits Part", "- [Z Density]", "+0.00;-0.00;0.00", "Contribution of low non-profit density to the gap score."),
    ("4. Gap & Priority", "Gap Score", "[Z Fragility] - [Z Density]", "+0.00;-0.00;0.00", "Priority gap = standardized fragility - standardized density. Higher = more fragile relative to its non-profit base."),
    ("4. Gap & Priority", "Gap Rank", f"IF ( {ONE}, RANKX ( ALL ( dim_region ), [Gap Score], , DESC, SKIP ) )", "0", "1 = largest gap (ties share the lowest rank, as pandas method='min')."),
    ("4. Gap & Priority", "Gap Source", f'IF ( {ONE}, IF ( [Fragility Part] > [Few Non-profits Part], "Fragility", "Few non-profits" ) )', None, "Which part of the gap is larger."),
    ("4. Gap & Priority", "Is Top 5", "IF ( NOT ISBLANK ( [Gap Rank] ), IF ( [Gap Rank] <= 5, 1, 0 ) )", "0", "1 when the region is in the top 5 by gap."),
    ("4. Gap & Priority", "Density Rank", f"IF ( {ONE}, RANKX ( ALL ( dim_region ), [Density (Scenario)], , ASC, SKIP ) )", "0", "1 = lowest non-profit density."),
    ("4. Gap & Priority", "Median Fragility", "MEDIANX ( ALL ( dim_region ), [Fragility Index] )", "+0.00;-0.00;0.00", "Median fragility index of the 13 regions (quadrant line)."),
    ("4. Gap & Priority", "Median Density", "MEDIANX ( ALL ( dim_region ), [Density (Scenario)] )", "0.00", "Median density of the 13 regions (quadrant line)."),
    ("4. Gap & Priority", "Quadrant", f"""
IF (
    {ONE},
    VAR _hf = [Fragility Index] > [Median Fragility]
    VAR _ld = [Density (Scenario)] < [Median Density]
    RETURN
        SWITCH (
            TRUE (),
            _hf && _ld, "High fragility, few organizations",
            _hf, "High fragility, many organizations",
            _ld, "Low fragility, few organizations",
            "Low fragility, many organizations"
        )
)""", None, "Descriptive quadrant against the two medians (not used for the decision)."),
    ("4. Gap & Priority", "Top Priority Region", "MAXX ( FILTER ( ALL ( dim_region ), [Gap Rank] = 1 ), dim_region[region_en] )", None, "Region ranked #1 by gap in the active scenario."),
    ("4. Gap & Priority", "Top Priority Gap", "MAXX ( FILTER ( ALL ( dim_region ), [Gap Rank] = 1 ), [Gap Score] )", "+0.00;-0.00;0.00", "Gap score of the #1 region."),
    ("4. Gap & Priority", "Lead Over Second", "[Top Priority Gap] - MAXX ( FILTER ( ALL ( dim_region ), [Gap Rank] = 2 ), [Gap Score] )", "0.00", "How far the #1 region is ahead of #2."),
    ("4. Gap & Priority", "Top 5 Regions", "CONCATENATEX ( FILTER ( ALL ( dim_region ), [Gap Rank] <= 5 ), dim_region[region_en], \", \", [Gap Rank], ASC )", None, "Top 5 regions by gap, in rank order."),
    ("4. Gap & Priority", "Scenarios in Top 5", f"IF ( {ONE}, COUNTROWS ( FILTER ( ALL ( dim_scenario ), CALCULATE ( [Gap Rank] ) <= 5 ) ) + 0 )", "0", "Number of scenarios A-D in which the region is in the top 5."),
    ("4. Gap & Priority", "Priority Color", f'IF ( {ONE}, IF ( [Gap Rank] <= 5, IF ( [Gap Source] = "Fragility", "{ORANGE}", "{BLUE}" ), "{GRAY}" ) )', None, "Orange = top 5 driven by fragility; blue = top 5 driven by few non-profits; grey = others."),
    ("4. Gap & Priority", "Stable Group Color", f'SWITCH ( SELECTEDVALUE ( dim_region[priority_group] ), "Fragility + few non-profits", "{ORANGE}", "Mainly few non-profits", "{BLUE}", "{GRAY}" )', None, "Colour of the final (stable) priority group from the notebook."),
    ("4. Gap & Priority", "Tile X", "MIN ( dim_region[tile_col] )", "0", "Tile-map column."),
    ("4. Gap & Priority", "Tile Y", "- MIN ( dim_region[tile_row] )", "0", "Tile-map row (negated so north is up)."),
    ("4. Gap & Priority", "Tile Size", "1", "0", "Constant bubble size for the tile map."),

    # ---------------------------------------------------------------- 5 Robustness
    ("5. Robustness", "Test Rank", "MIN ( fact_sensitivity_rank[gap_rank] )", "0", "Gap rank in the selected sensitivity test."),
    ("5. Robustness", "Tests Run", "CALCULATE ( DISTINCTCOUNT ( fact_sensitivity_rank[test_id] ), REMOVEFILTERS ( dim_region ) )", "0", "Number of sensitivity tests (6)."),
    ("5. Robustness", "Tests in Top 5", "CALCULATE ( COUNTROWS ( fact_sensitivity_rank ), fact_sensitivity_rank[gap_rank] <= 5 ) + 0", "0", "Number of tests with the region in the top 5."),
    ("5. Robustness", "Best Rank Across Tests", "MIN ( fact_sensitivity_rank[gap_rank] )", "0", "Best rank over the six tests."),
    ("5. Robustness", "Worst Rank Across Tests", "MAX ( fact_sensitivity_rank[gap_rank] )", "0", "Worst rank over the six tests."),
    ("5. Robustness", "Stable Priority Regions", "COUNTROWS ( FILTER ( VALUES ( dim_region[region_id] ), [Tests in Top 5] >= [Tests Run] - 1 ) )", "0", "Regions in the top 5 in all tests but at most one (notebook rule)."),
    ("5. Robustness", "Stable Priority List", "CONCATENATEX ( FILTER ( ALL ( dim_region ), [Tests in Top 5] >= [Tests Run] - 1 ), dim_region[region_en], \", \", dim_region[baseline_gap_rank], ASC )", None, "Stable priority regions in baseline rank order."),
    ("5. Robustness", "Rank Cell Color", '''
VAR _r = [Test Rank]
RETURN
    SWITCH ( TRUE (), ISBLANK ( _r ), BLANK (), _r = 1, "#F08A5D", _r <= 5, "#FBD3C2", "#FFFFFF" )''', None, "Matrix background: rank 1 dark orange, ranks 2-5 light orange."),
    ("5. Robustness", "Gap Rank Cell Color", '''
VAR _r = [Gap Rank]
RETURN
    SWITCH ( TRUE (), ISBLANK ( _r ), BLANK (), _r = 1, "#F08A5D", _r <= 5, "#FBD3C2", "#FFFFFF" )''', None, "Matrix background for scenario ranks."),
    ("5. Robustness", "Random Weights Top 5 %", "DIVIDE ( SUM ( fact_robustness[weights_top5_pct] ), 100 * [Regions] )", "0.0%", "Share of 1,000 random weightings (seed 42) with the region in the top 5."),
    ("5. Robustness", "Random Weights Median Rank", "AVERAGE ( fact_robustness[weights_median_rank] )", "0", "Median rank across the 1,000 weightings."),
    ("5. Robustness", "Random Weights Best Rank", "MIN ( fact_robustness[weights_best] )", "0", "Best rank across the weightings."),
    ("5. Robustness", "Random Weights Worst Rank", "MAX ( fact_robustness[weights_worst] )", "0", "Worst rank across the weightings."),
    ("5. Robustness", "Leave-One-Out Top 5", "SUM ( fact_robustness[loo_top5] )", "0", "Times in the top 5 out of 12 leave-one-region-out runs."),
    ("5. Robustness", "Leave-One-Out Top 5 %", "DIVIDE ( SUM ( fact_robustness[loo_top5] ), 12 * [Regions] )", "0.0%", "Share of the 12 leave-one-region-out runs with the region in the top 5."),
    ("5. Robustness", "Leave-One-Out Worst Rank", "MAX ( fact_robustness[loo_worst] )", "0", "Worst rank in leave-one-out."),
    ("5. Robustness", "Least Stable Priority", '''
VAR _stable = FILTER ( ALL ( dim_region ), [Tests in Top 5] >= [Tests Run] - 1 )
VAR _r = TOPN ( 1, _stable, [Random Weights Top 5 %], ASC )
RETURN
    MAXX ( _r, dim_region[region_en] ) & " · " & FORMAT ( MAXX ( _r, [Random Weights Top 5 %] ), "0.0%" )''', None, "Stable priority region that is least often in the top 5 under random weights."),
    ("5. Robustness", "Random Weight Draws", "1000", "#,0", "Number of Dirichlet weight draws in the notebook (seed 42)."),
    ("5. Robustness", "Tile Stable Color", "[Stable Group Color]", None, "Alias used by the tile map."),

    # ---------------------------------------------------------------- 6 Trends
    ("6. Trends", "Beneficiaries", "SUM ( fact_social_security[beneficiaries] )", "#,0", "Social security beneficiaries in the years in context."),
    ("6. Trends", "Beneficiaries PY", "VAR _y = MAX ( dim_year[year] ) RETURN CALCULATE ( [Beneficiaries], dim_year[year] = _y - 1 )", "#,0", "Beneficiaries in the previous year."),
    ("6. Trends", "Beneficiaries YoY %", "DIVIDE ( [Beneficiaries] - [Beneficiaries PY], [Beneficiaries PY] )", "+0.0%;-0.0%;0.0%", "Year-over-year change in beneficiaries."),
    ("6. Trends", "Beneficiaries Index 2020=100", "VAR _y = MAX ( dim_year[year] ) RETURN IF ( _y >= 2020, DIVIDE ( [Beneficiaries], CALCULATE ( [Beneficiaries], dim_year[year] = 2020 ) ) * 100 )", "0.0", "Beneficiaries indexed to 2020 = 100 (2020-2022 only)."),
    ("6. Trends", "Change 2021 to 2022 %", "DIVIDE ( CALCULATE ( [Beneficiaries], dim_year[year] = 2022 ), CALCULATE ( [Beneficiaries], dim_year[year] = 2021 ) ) - 1", "+0.0%;-0.0%;0.0%", "Change in beneficiaries from 2021 to 2022 (transition year)."),
    ("6. Trends", "Peak Beneficiaries", "MAXX ( ALL ( dim_year[year] ), [Beneficiaries] )", "#,0", "Highest annual number of beneficiaries, 2005-2022."),
    ("6. Trends", "Peak Year", "MAXX ( TOPN ( 1, ALL ( dim_year[year] ), [Beneficiaries], DESC ), dim_year[year] )", "0", "Year of the peak."),
    ("6. Trends", "Change Peak to 2022 %", "DIVIDE ( CALCULATE ( [Beneficiaries], dim_year[year] = 2022 ), [Peak Beneficiaries] ) - 1", "+0.0%;-0.0%;0.0%", "Change from the peak year to 2022."),
    ("6. Trends", "Saudi Population (Year)", "SUM ( fact_population[saudi_population] )", "#,0", "Saudi population in the years in context (2010-2022)."),
    ("6. Trends", "Population (Year)", "SUM ( fact_population[population] )", "#,0", "Total population in the years in context (2010-2022)."),
    ("6. Trends", "SS Rate (Year) %", "DIVIDE ( [Beneficiaries], [Saudi Population (Year)] )", "0.00%", "Beneficiaries / Saudi population for each year 2010-2022."),

    # ---------------------------------------------------------------- 7 Statistics (Python correlations translated to DAX)
    ("7. Statistics", "Spearman Orgs vs Population", spearman("[Organizations (All Types)]", "[Population 2022]"), "0.00", "Rank correlation between organization counts and population (notebook 4.2: 0.87)."),
    ("7. Statistics", "Spearman Income vs Food Share", spearman("[Median Income (Saudi)]", "[Food Share %]"), "0.00", "Rank correlation between Saudi median income and food share (notebook 4.4: -0.64)."),
    ("7. Statistics", "Spearman SS Rate 2020 vs 2022", spearman("CALCULATE ( [SS Rate (Year) %], dim_year[year] = 2020 )", "CALCULATE ( [SS Rate (Year) %], dim_year[year] = 2022 )"), "0.00", "Stability of regional social security rates (notebook 4.3: 0.99)."),
    ("7. Statistics", "Spearman SS Rate 2021 vs 2022", spearman("CALCULATE ( [SS Rate (Year) %], dim_year[year] = 2021 )", "CALCULATE ( [SS Rate (Year) %], dim_year[year] = 2022 )"), "0.00", "Stability of regional social security rates (notebook 4.3: 0.94)."),
    ("7. Statistics", "Spearman Fragility 2022 vs Avg", spearman('CALCULATE ( [Fragility Index], REMOVEFILTERS ( dim_scenario ), dim_scenario[scenario] = "A" )', 'CALCULATE ( [Fragility Index], REMOVEFILTERS ( dim_scenario ), dim_scenario[scenario] = "C" )'), "0.00", "Fragility with 2022 vs 2020-22 social security rate (notebook 6: 0.99)."),
    ("7. Statistics", "Largest to Smallest Population", "DIVIDE ( MAXX ( ALL ( dim_region ), [Population 2022] ), MINX ( ALL ( dim_region ), [Population 2022] ) )", '0', "Population of the largest region / smallest region (notebook 4.2: 25x)."),

    # ---------------------------------------------------------------- 8 Titles
    ("8. Titles", "Title Gap Chart", '"Gap score by region · scenario " & [Selected Scenario]', None, "Dynamic visual title."),
    ("8. Titles", "Title Profile", 'IF ( HASONEVALUE ( dim_region[region_en] ), "Region profile · " & VALUES ( dim_region[region_en] ) & "  (" & VALUES ( dim_region[region_ar] ) & ")", "Region profile · select one region" )', None, "Dynamic page title on the profile page."),
    ("8. Titles", "Population 2022 Label", 'FORMAT ( [Population 2022] / 1000000, "0.0" ) & "M"', None, "Population 2022 in millions as text (locale-independent card label)."),
    ("8. Titles", "Title Tooltip", 'IF ( HASONEVALUE ( dim_region[region_en] ), VALUES ( dim_region[region_en] ) & "  ·  " & VALUES ( dim_region[region_ar] ) )', None, "Region name on the tooltip page."),
    ("8. Titles", "Tooltip Rank Line", 'IF ( HASONEVALUE ( dim_region[region_en] ), "Gap rank " & [Gap Rank] & " of 13  ·  " & [Gap Source] & "  ·  scenario " & [Selected Scenario] )', None, "Rank summary line on the tooltip page."),
    ("8. Titles", "Title Drillthrough", 'IF ( HASONEVALUE ( dim_region[region_en] ), "Region detail · " & VALUES ( dim_region[region_en] ) & "  (" & VALUES ( dim_region[region_ar] ) & ")", "Region detail · right-click a region on the dashboard > Drill through" )', None, "Dynamic title of the drill-through page."),
    ("8. Titles", "Profile Group", 'IF ( HASONEVALUE ( dim_region[region_en] ), VALUES ( dim_region[priority_group] ) )', None, "Final priority group of the selected region."),
]

# ============================================================ writers
def tmdl_expr(expr, indent):
    expr = textwrap.dedent(expr).strip("\n")
    if "\n" not in expr:
        return " " + expr
    pad = "\t" * indent
    return "\n" + "\n".join(pad + line if line.strip() else "" for line in expr.split("\n"))


def embedded_csv(table):
    """Raw-deflate + base64 snapshot of a model CSV, used when DataFolder is not reachable."""
    raw = (DATA / f"{table}.csv").read_bytes()
    co = zlib.compressobj(9, zlib.DEFLATED, -15)
    return base64.b64encode(co.compress(raw) + co.flush()).decode("ascii")


def m_query(table, cols, for_docs=False):
    types = ", ".join(f'{{"{c}", {t}}}' for c, t, *_ in cols)
    snap = f"<base64 snapshot of {table}.csv>" if for_docs else embedded_csv(table)
    return [
        "let",
        "    // 1) read the clean CSV from 02_data; 2) if the folder is not reachable (project moved), use the embedded snapshot",
        f'    Embedded = "{snap}",',
        f'    FileBinary = try Binary.Buffer(File.Contents(DataFolder & "\\{table}.csv")) otherwise Binary.Decompress(Binary.FromText(Embedded, BinaryEncoding.Base64), Compression.Deflate),',
        '    Source = Csv.Document(FileBinary, [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),',
        "    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),",
        f'    ChangedTypes = Table.TransformColumnTypes(PromotedHeaders, {{{types}}}, "en-US")',
        "in",
        "    ChangedTypes",
    ]


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_tmdl():
    if SM.exists():
        shutil.rmtree(SM)
    d = SM / "definition"
    write(SM / "definition.pbism", json.dumps({"version": "4.2", "settings": {}}, indent=2))
    write(SM / ".platform", json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "SemanticModel", "displayName": "RegionalPriorities"},
        "config": {"version": "2.0", "logicalId": tag("sm")}}, indent=2))
    write(d / "database.tmdl", "database\n\tcompatibilityLevel: 1600\n")
    order = list(TABLES) + list(WEIGHT_TABLES) + ["_Measures"]
    write(d / "model.tmdl", "\n".join([
        "model Model", "\tculture: en-US", "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tdiscourageImplicitMeasures", "\tsourceQueryCulture: en-US", "\tdataAccessOptions",
        "\t\tlegacyRedirects", "\t\treturnErrorValuesAsNull", "",
        f"annotation PBI_QueryOrder = {json.dumps(['DataFolder', *TABLES, '_Measures'])}", "",
        "annotation __PBI_TimeIntelligenceEnabled = 0", "",
        'annotation PBI_ProTooling = ["DevMode"]', "",
        *[f"ref table {q(t)}" for t in order], ""]))
    data_path = str(DATA).replace('"', '""')
    write(d / "expressions.tmdl", "\n".join([
        f'/// Folder holding the model CSV files. Change it if the project is moved (Transform data > Edit parameters).',
        f'expression DataFolder = "{data_path}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]',
        f"\tlineageTag: {tag('expr', 'DataFolder')}", "", "\tannotation PBI_ResultType = Text", ""]))
    rel = []
    for ft, fc, tt, tc in RELATIONSHIPS:
        rel += [f"relationship {tag('rel', ft, fc)}", f"\tfromColumn: {ft}.{fc}", f"\ttoColumn: {tt}.{tc}", ""]
    write(d / "relationships.tmdl", "\n".join(rel))

    for t, spec in TABLES.items():
        L = [f"/// {spec['desc']}", f"table {t}", f"\tlineageTag: {tag('t', t)}", ""]
        for c, _mt, dt, fmt, hidden, sort_by, desc in spec["cols"]:
            L += [f"\t/// {desc}", f"\tcolumn {q(c)}", f"\t\tdataType: {dt}"]
            if fmt:
                L.append(f"\t\tformatString: {fmt}")
            if hidden:
                L.append("\t\tisHidden")
            L += [f"\t\tlineageTag: {tag('c', t, c)}", "\t\tsummarizeBy: none", f"\t\tsourceColumn: {c}"]
            if sort_by:
                L.append(f"\t\tsortByColumn: {sort_by}")
            L += ["", "\t\tannotation SummarizationSetBy = Automatic", ""]
        L += [f"\tpartition {t} = m", "\t\tmode: import", "\t\tsource ="]
        L += ["\t\t\t\t" + line for line in m_query(t, spec["cols"])]
        L += ["", "\tannotation PBI_ResultType = Table", ""]
        write(d / "tables" / f"{t}.tmdl", "\n".join(L))

    for t, desc in WEIGHT_TABLES.items():
        write(d / "tables" / f"{t}.tmdl", "\n".join([
            f"/// {desc}", f"table {q(t)}", f"\tlineageTag: {tag('t', t)}", "",
            f"\tcolumn {q(t)}", "\t\tdataType: int64", "\t\tformatString: 0", f"\t\tlineageTag: {tag('c', t)}",
            "\t\tsummarizeBy: none", "\t\tsourceColumn: [Value]", "", "\t\tannotation SummarizationSetBy = User", "",
            f"\tpartition {q(t)} = calculated", "\t\tmode: import", "\t\tsource = GENERATESERIES ( 0, 5, 1 )", "",
            "\tannotation PBI_Id = " + tag("pbiid", t).replace("-", ""), ""]))

    L = ["/// Home table of all DAX measures (display folders 1-8).", "table _Measures", f"\tlineageTag: {tag('t', '_Measures')}", ""]
    for folder, name, expr, fmt, desc in M:
        L += [f"\t/// {desc}", f"\tmeasure {q(name)} ={tmdl_expr(expr, 3)}"]
        if fmt:
            L.append(f"\t\tformatString: {fmt}")
        L += [f"\t\tdisplayFolder: {folder}", f"\t\tlineageTag: {tag('m', name)}", ""]
    L += ["\tcolumn Dummy", "\t\tdataType: int64", "\t\tisHidden", "\t\tformatString: 0", f"\t\tlineageTag: {tag('c', '_Measures', 'Dummy')}",
          "\t\tsummarizeBy: none", "\t\tsourceColumn: Dummy", "", "\t\tannotation SummarizationSetBy = Automatic", "",
          "\tpartition _Measures = m", "\t\tmode: import", "\t\tsource =",
          "\t\t\t\tlet", "\t\t\t\t    Source = #table(type table [Dummy = Int64.Type], {})", "\t\t\t\tin", "\t\t\t\t    Source",
          "", "\tannotation PBI_ResultType = Table", ""]
    write(d / "tables" / "_Measures.tmdl", "\n".join(L))


def build_docs():
    # ---------------- DAX reference
    out = ["# DAX Measures", "",
           f"All {len(M)} measures live in the `_Measures` table of `RegionalPriorities.SemanticModel`, grouped in display folders. "
           "This file is generated from the same definition as the model (`01_scripts/build_semantic_model.py`), so it always matches the TMDL.", "",
           "Conventions: z-scores use the population standard deviation (`STDEVX.P`, same as pandas `std(ddof=0)`); "
           "ranks use `RANKX(..., SKIP)` (same as pandas `rank(method='min')`); every z-score and rank is computed against "
           "`ALL(dim_region)`, i.e. always relative to all 13 regions, whatever is filtered on the page.", ""]
    folder = None
    for f, name, expr, fmt, desc in M:
        if f != folder:
            out += [f"## {f}", ""]
            folder = f
        out += [f"### {name}", "", desc, ""]
        if fmt:
            out += [f"Format: `{fmt}`", ""]
        out += ["```dax", f"{name} =" + ("\n" + textwrap.indent(textwrap.dedent(expr).strip("\n"), "    ") if "\n" in expr else " " + expr), "```", ""]
    out += ["## What-if parameter tables", "",
            "Three calculated tables feed optional custom fragility weights (default 1 = the notebook; not placed on the dashboard, available for ad-hoc what-if analysis):", "",
            "```dax"] + [f"{q(t)} = GENERATESERIES ( 0, 5, 1 )   -- {d}" for t, d in WEIGHT_TABLES.items()] + ["```", ""]
    write(DOCS / "03_DAX_Measures.md", "\n".join(out))

    # ---------------- Power Query
    out = ["# Power Query (M)", "",
           "Every table is loaded from the clean CSV files in `02_data/` through one text parameter, `DataFolder`, with an embedded fallback (below). "
           "Types are set with an explicit `en-US` culture so decimals parse the same on any Windows locale (the machine "
           "this was built on uses Arabic regional settings).", "",
           "## Parameter", "", "```powerquery", f'DataFolder = "{DATA}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]', "```", "",
           "**Portable by design:** every query first tries `DataFolder`; if that folder is not reachable (the project was copied to another "
           "computer), it falls back to a compressed copy of the same CSV embedded in the query (`Embedded`, raw deflate + base64, "
           "generated by `build_semantic_model.py`). So the report refreshes anywhere without editing anything. To load edited CSVs from a "
           "new location: *Transform data > Edit parameters > DataFolder*, then *Refresh*.", ""]
    for t, spec in TABLES.items():
        out += [f"## {t}", "", spec["desc"], "", "```powerquery", *m_query(t, spec["cols"], for_docs=True), "```", ""]
    out += ["## _Measures", "", "Empty table that only hosts measures.", "", "```powerquery",
            "let", "    Source = #table(type table [Dummy = Int64.Type], {})", "in", "    Source", "```", "",
            "## Why the cleaning itself is in Python, not M", "",
            "The raw HIES file is a publication workbook (four separately laid-out sheets, one of them transposed, region "
            "names with embedded line breaks), and the notebook's cleaning carries assertions (Grand Total equals the sum of "
            "regions, every region name maps, no missing values). `01_scripts/build_model_data.py` re-runs that exact code "
            "and fails loudly if anything changes, then hands Power Query clean, typed, tidy CSVs. Power Query only types and "
            "loads, which keeps refreshes fast and the logic in one place.", ""]
    write(DOCS / "04_Power_Query_M.md", "\n".join(out))


if __name__ == "__main__":
    build_tmdl()
    build_docs()
    print(f"Semantic model written: {len(TABLES) + len(WEIGHT_TABLES) + 1} tables, {len(RELATIONSHIPS)} relationships, {len(M)} measures")
