# DAX Measures

All 111 measures live in the `_Measures` table of `RegionalPriorities.SemanticModel`, grouped in display folders. This file is generated from the same definition as the model (`01_scripts/build_semantic_model.py`), so it always matches the TMDL.

Conventions: z-scores use the population standard deviation (`STDEVX.P`, same as pandas `std(ddof=0)`); ranks use `RANKX(..., SKIP)` (same as pandas `rank(method='min')`); every z-score and rank is computed against `ALL(dim_region)`, i.e. always relative to all 13 regions, whatever is filtered on the page.

## 1. Base

### Regions

Number of regions in the current filter context.

Format: `0`

```dax
Regions = DISTINCTCOUNT ( fact_region_snapshot[region_id] )
```

### Population 2022

Total population 2022 (SAMA).

Format: `#,0`

```dax
Population 2022 = SUM ( fact_region_snapshot[population_2022] )
```

### Saudi Population 2022

Saudi population 2022 (GASTAT census).

Format: `#,0`

```dax
Saudi Population 2022 = SUM ( fact_region_snapshot[saudi_population_2022] )
```

### Saudi Population Avg 2020-22

Average Saudi population 2020-2022; denominator of the averaged social security rate.

Format: `#,0`

```dax
Saudi Population Avg 2020-22 = SUM ( fact_region_snapshot[saudi_population_avg_2020_2022] )
```

### Saudi Share %

Saudis as a share of the population, 2022.

Format: `0.0%`

```dax
Saudi Share % = DIVIDE ( [Saudi Population 2022], [Population 2022] )
```

### Population Share %

Region's share of the national population, 2022.

Format: `0.0%`

```dax
Population Share % = DIVIDE ( [Population 2022], CALCULATE ( [Population 2022], ALL ( dim_region ) ) )
```

### Organizations

Registered non-profit organizations (respects an organization-type filter).

Format: `#,0`

```dax
Organizations = COUNTROWS ( fact_organizations )
```

### Organizations (All Types)

Associations + foundations, ignoring any organization-type filter.

Format: `#,0`

```dax
Organizations (All Types) = CALCULATE ( COUNTROWS ( fact_organizations ), REMOVEFILTERS ( dim_org_type ) ) + 0
```

### Associations

Registered civil associations.

Format: `#,0`

```dax
Associations = CALCULATE ( COUNTROWS ( fact_organizations ), dim_org_type[org_type] = "Association" ) + 0
```

### Foundations

Registered civil foundations.

Format: `#,0`

```dax
Foundations = CALCULATE ( COUNTROWS ( fact_organizations ), dim_org_type[org_type] = "Foundation" ) + 0
```

### Foundation Share %

Foundations as a share of all organizations in the region.

Format: `0.0%`

```dax
Foundation Share % = DIVIDE ( [Foundations], [Organizations (All Types)] )
```

### Share of National Organizations %

Region's share of all 2,723 organizations.

Format: `0.0%`

```dax
Share of National Organizations % = DIVIDE ( [Organizations (All Types)], CALCULATE ( [Organizations (All Types)], ALL ( dim_region ) ) )
```

### Share of National Foundations %

Region's share of all foundations.

Format: `0.0%`

```dax
Share of National Foundations % = DIVIDE ( [Foundations], CALCULATE ( [Foundations], ALL ( dim_region ) ) )
```

### Regions Without Foundations

Regions with no registered foundation.

Format: `0`

```dax
Regions Without Foundations = COUNTROWS ( FILTER ( VALUES ( dim_region[region_id] ), [Foundations] = 0 ) )
```

### Beneficiaries 2022

Social security beneficiaries in 2022.

Format: `#,0`

```dax
Beneficiaries 2022 = SUM ( fact_region_snapshot[beneficiaries_2022] )
```

### Beneficiaries Avg 2020-22

Average beneficiaries over 2020-2022.

Format: `#,0`

```dax
Beneficiaries Avg 2020-22 = SUM ( fact_region_snapshot[beneficiaries_avg_2020_2022] )
```

### Median Income (Saudi)

Median monthly disposable income per Saudi, SAR (HIES 2023). Region level only: medians cannot be added up.

Format: `#,0`

```dax
Median Income (Saudi) = IF ( HASONEVALUE ( dim_region[region_id] ), SUM ( fact_region_snapshot[income_median_saudi] ) )
```

### Mean Income (Saudi)

Mean monthly income per Saudi, SAR.

Format: `#,0`

```dax
Mean Income (Saudi) = IF ( HASONEVALUE ( dim_region[region_id] ), SUM ( fact_region_snapshot[income_mean_saudi] ) )
```

### Mean Spending (Saudi)

Mean monthly spending per Saudi, SAR.

Format: `#,0`

```dax
Mean Spending (Saudi) = IF ( HASONEVALUE ( dim_region[region_id] ), SUM ( fact_region_snapshot[spend_mean_saudi] ) )
```

### Income Margin (Saudi)

Mean income minus mean spending; only used in the 'plus margin' sensitivity test (negative in Jazan).

Format: `#,0`

```dax
Income Margin (Saudi) = [Mean Income (Saudi)] - [Mean Spending (Saudi)]
```

### Food Share %

Food & beverages share of household spending (all households), HIES 2023.

Format: `0.0%`

```dax
Food Share % = IF ( HASONEVALUE ( dim_region[region_id] ), SUM ( fact_region_snapshot[food_share] ) )
```

## 2. Indicators

### SS Rate 2022 %

Social security beneficiaries 2022 / Saudi population 2022. Higher = more fragile.

Format: `0.00%`

```dax
SS Rate 2022 % = DIVIDE ( [Beneficiaries 2022], [Saudi Population 2022] )
```

### SS Rate Avg 2020-22 %

Average beneficiaries 2020-22 / average Saudi population 2020-22.

Format: `0.00%`

```dax
SS Rate Avg 2020-22 % = DIVIDE ( [Beneficiaries Avg 2020-22], [Saudi Population Avg 2020-22] )
```

### Org Density per 100k

Associations + foundations per 100,000 residents (2022).

Format: `0.00`

```dax
Org Density per 100k = DIVIDE ( [Organizations (All Types)], [Population 2022] ) * 100000
```

### Association Density per 100k

Associations per 100,000 residents (2022).

Format: `0.00`

```dax
Association Density per 100k = DIVIDE ( [Associations], [Population 2022] ) * 100000
```

### Selected Scenario

Scenario chosen in the slicer; A when nothing or several are selected.

```dax
Selected Scenario = SELECTEDVALUE ( dim_scenario[scenario], "A" )
```

### Scenario Label

Label of the active scenario.

```dax
Scenario Label = SELECTEDVALUE ( dim_scenario[scenario_label], "A · SS 2022 · All organizations" )
```

### SS Rate (Scenario) %

Social security rate used by the active scenario (2022 for A/B, 2020-22 average for C/D).

Format: `0.00%`

```dax
SS Rate (Scenario) % = IF ( [Selected Scenario] IN { "A", "B" }, [SS Rate 2022 %], [SS Rate Avg 2020-22 %] )
```

### Density (Scenario)

Density used by the active scenario (all organizations for A/C, associations only for B/D).

Format: `0.00`

```dax
Density (Scenario) = IF ( [Selected Scenario] IN { "A", "C" }, [Org Density per 100k], [Association Density per 100k] )
```

### Weight SS Value

Selected weight of the social security rate (default 1).

Format: `0`

```dax
Weight SS Value = SELECTEDVALUE ( 'Weight SS'[Weight SS], 1 )
```

### Weight Income Value

Selected weight of low income (default 1).

Format: `0`

```dax
Weight Income Value = SELECTEDVALUE ( 'Weight Income'[Weight Income], 1 )
```

### Weight Food Value

Selected weight of the food share (default 1).

Format: `0`

```dax
Weight Food Value = SELECTEDVALUE ( 'Weight Food'[Weight Food], 1 )
```

### Weights Label

Text of the active fragility weights.

```dax
Weights Label = "Weights  SS : Income : Food  =  " & [Weight SS Value] & " : " & [Weight Income Value] & " : " & [Weight Food Value] & IF ( [Weight SS Value] = [Weight Income Value] && [Weight Income Value] = [Weight Food Value], "  (equal, as in the notebook)", "  (custom)" ) & IF ( [Weight SS Value] + [Weight Income Value] + [Weight Food Value] = 0, "  · all weights are 0: index undefined", "" )
```

## 3. Fragility

### Z SS Rate

z-score of the social security rate across the 13 regions (population SD). Higher = more fragile.

Format: `0.00`

```dax
Z SS Rate =
    VAR _all = ALL ( dim_region )
    VAR _mu = AVERAGEX ( _all, [SS Rate (Scenario) %] )
    VAR _sd = STDEVX.P ( _all, [SS Rate (Scenario) %] )
    RETURN
        IF ( HASONEVALUE ( dim_region[region_id] ), DIVIDE ( [SS Rate (Scenario) %] - _mu, _sd ) )
```

### Z Low Income

Negative z-score of Saudi median income, so higher = more fragile.

Format: `0.00`

```dax
Z Low Income =
    VAR _all = ALL ( dim_region )
    VAR _mu = AVERAGEX ( _all, [Median Income (Saudi)] )
    VAR _sd = STDEVX.P ( _all, [Median Income (Saudi)] )
    RETURN
        IF ( HASONEVALUE ( dim_region[region_id] ), -DIVIDE ( [Median Income (Saudi)] - _mu, _sd ) )
```

### Z Food Share

z-score of the food share of spending. Higher = more fragile.

Format: `0.00`

```dax
Z Food Share =
    VAR _all = ALL ( dim_region )
    VAR _mu = AVERAGEX ( _all, [Food Share %] )
    VAR _sd = STDEVX.P ( _all, [Food Share %] )
    RETURN
        IF ( HASONEVALUE ( dim_region[region_id] ), DIVIDE ( [Food Share %] - _mu, _sd ) )
```

### Fragility Index

Composite economic fragility: weighted mean of the three z-scores (equal weights = notebook). 0 = average of the 13 regions.

Format: `+0.00;-0.00;0.00`

```dax
Fragility Index =
    VAR _w1 = [Weight SS Value]
    VAR _w2 = [Weight Income Value]
    VAR _w3 = [Weight Food Value]
    RETURN
        IF ( HASONEVALUE ( dim_region[region_id] ), DIVIDE ( _w1 * [Z SS Rate] + _w2 * [Z Low Income] + _w3 * [Z Food Share], _w1 + _w2 + _w3 ) )
```

### Fragility Rank

1 = most fragile region.

Format: `0`

```dax
Fragility Rank = IF ( HASONEVALUE ( dim_region[region_id] ), RANKX ( ALL ( dim_region ), [Fragility Index], , DESC, SKIP ) )
```

### SS Rate Rank

1 = highest social security rate 2022.

Format: `0`

```dax
SS Rate Rank = IF ( HASONEVALUE ( dim_region[region_id] ), RANKX ( ALL ( dim_region ), [SS Rate 2022 %], , DESC, SKIP ) )
```

### Income Rank

1 = lowest Saudi median income.

Format: `0`

```dax
Income Rank = IF ( HASONEVALUE ( dim_region[region_id] ), RANKX ( ALL ( dim_region ), [Median Income (Saudi)], , ASC, SKIP ) )
```

### Food Share Rank

1 = highest food share of spending.

Format: `0`

```dax
Food Share Rank = IF ( HASONEVALUE ( dim_region[region_id] ), RANKX ( ALL ( dim_region ), [Food Share %], , DESC, SKIP ) )
```

### Fragility Color

Orange when more fragile than the 13-region average.

```dax
Fragility Color = IF ( HASONEVALUE ( dim_region[region_id] ), IF ( [Fragility Index] > 0, "#EB6834", "#B4B2A9" ) )
```

### Fragility Cell Color

Table background: dark orange >= 1, light orange > 0.

```dax
Fragility Cell Color = VAR _f = [Fragility Index] RETURN SWITCH ( TRUE (), ISBLANK ( _f ), BLANK (), _f >= 1, "#F08A5D", _f > 0, "#FBD3C2", "#FFFFFF" )
```

### Most Fragile Region

Region with the highest fragility index.

```dax
Most Fragile Region = MAXX ( FILTER ( ALL ( dim_region ), [Fragility Rank] = 1 ), dim_region[region_en] )
```

### Lowest Income Region

Region with the lowest Saudi median income and its value.

```dax
Lowest Income Region = VAR _r = TOPN ( 1, ALL ( dim_region ), [Median Income (Saudi)], ASC ) RETURN MAXX ( _r, dim_region[region_en] ) & " · SAR " & FORMAT ( MAXX ( _r, [Median Income (Saudi)] ), "#,0" )
```

### Highest Food Share Region

Region with the highest food share and its value.

```dax
Highest Food Share Region = VAR _r = TOPN ( 1, ALL ( dim_region ), [Food Share %], DESC ) RETURN MAXX ( _r, dim_region[region_en] ) & " · " & FORMAT ( MAXX ( _r, [Food Share %] ), "0.0%" )
```

## 4. Gap & Priority

### Z Fragility

z-score of the fragility index across the 13 regions (the 'fragility part' of the gap).

Format: `0.00`

```dax
Z Fragility =
    VAR _all = ALL ( dim_region )
    VAR _mu = AVERAGEX ( _all, [Fragility Index] )
    VAR _sd = STDEVX.P ( _all, [Fragility Index] )
    RETURN
        IF ( HASONEVALUE ( dim_region[region_id] ), DIVIDE ( [Fragility Index] - _mu, _sd ) )
```

### Z Density

z-score of non-profit density across the 13 regions.

Format: `0.00`

```dax
Z Density =
    VAR _all = ALL ( dim_region )
    VAR _mu = AVERAGEX ( _all, [Density (Scenario)] )
    VAR _sd = STDEVX.P ( _all, [Density (Scenario)] )
    RETURN
        IF ( HASONEVALUE ( dim_region[region_id] ), DIVIDE ( [Density (Scenario)] - _mu, _sd ) )
```

### Fragility Part

Contribution of fragility to the gap score.

Format: `+0.00;-0.00;0.00`

```dax
Fragility Part = [Z Fragility]
```

### Few Non-profits Part

Contribution of low non-profit density to the gap score.

Format: `+0.00;-0.00;0.00`

```dax
Few Non-profits Part = - [Z Density]
```

### Gap Score

Priority gap = standardized fragility - standardized density. Higher = more fragile relative to its non-profit base.

Format: `+0.00;-0.00;0.00`

```dax
Gap Score = [Z Fragility] - [Z Density]
```

### Gap Rank

1 = largest gap (ties share the lowest rank, as pandas method='min').

Format: `0`

```dax
Gap Rank = IF ( HASONEVALUE ( dim_region[region_id] ), RANKX ( ALL ( dim_region ), [Gap Score], , DESC, SKIP ) )
```

### Gap Source

Which part of the gap is larger.

```dax
Gap Source = IF ( HASONEVALUE ( dim_region[region_id] ), IF ( [Fragility Part] > [Few Non-profits Part], "Fragility", "Few non-profits" ) )
```

### Is Top 5

1 when the region is in the top 5 by gap.

Format: `0`

```dax
Is Top 5 = IF ( NOT ISBLANK ( [Gap Rank] ), IF ( [Gap Rank] <= 5, 1, 0 ) )
```

### Density Rank

1 = lowest non-profit density.

Format: `0`

```dax
Density Rank = IF ( HASONEVALUE ( dim_region[region_id] ), RANKX ( ALL ( dim_region ), [Density (Scenario)], , ASC, SKIP ) )
```

### Median Fragility

Median fragility index of the 13 regions (quadrant line).

Format: `+0.00;-0.00;0.00`

```dax
Median Fragility = MEDIANX ( ALL ( dim_region ), [Fragility Index] )
```

### Median Density

Median density of the 13 regions (quadrant line).

Format: `0.00`

```dax
Median Density = MEDIANX ( ALL ( dim_region ), [Density (Scenario)] )
```

### Quadrant

Descriptive quadrant against the two medians (not used for the decision).

```dax
Quadrant =
    IF (
        HASONEVALUE ( dim_region[region_id] ),
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
    )
```

### Top Priority Region

Region ranked #1 by gap in the active scenario.

```dax
Top Priority Region = MAXX ( FILTER ( ALL ( dim_region ), [Gap Rank] = 1 ), dim_region[region_en] )
```

### Top Priority Gap

Gap score of the #1 region.

Format: `+0.00;-0.00;0.00`

```dax
Top Priority Gap = MAXX ( FILTER ( ALL ( dim_region ), [Gap Rank] = 1 ), [Gap Score] )
```

### Lead Over Second

How far the #1 region is ahead of #2.

Format: `0.00`

```dax
Lead Over Second = [Top Priority Gap] - MAXX ( FILTER ( ALL ( dim_region ), [Gap Rank] = 2 ), [Gap Score] )
```

### Top 5 Regions

Top 5 regions by gap, in rank order.

```dax
Top 5 Regions = CONCATENATEX ( FILTER ( ALL ( dim_region ), [Gap Rank] <= 5 ), dim_region[region_en], ", ", [Gap Rank], ASC )
```

### Scenarios in Top 5

Number of scenarios A-D in which the region is in the top 5.

Format: `0`

```dax
Scenarios in Top 5 = IF ( HASONEVALUE ( dim_region[region_id] ), COUNTROWS ( FILTER ( ALL ( dim_scenario ), CALCULATE ( [Gap Rank] ) <= 5 ) ) + 0 )
```

### Priority Color

Orange = top 5 driven by fragility; blue = top 5 driven by few non-profits; grey = others.

```dax
Priority Color = IF ( HASONEVALUE ( dim_region[region_id] ), IF ( [Gap Rank] <= 5, IF ( [Gap Source] = "Fragility", "#EB6834", "#2A78D6" ), "#B4B2A9" ) )
```

### Stable Group Color

Colour of the final (stable) priority group from the notebook.

```dax
Stable Group Color = SWITCH ( SELECTEDVALUE ( dim_region[priority_group] ), "Fragility + few non-profits", "#EB6834", "Mainly few non-profits", "#2A78D6", "#B4B2A9" )
```

### Tile X

Tile-map column.

Format: `0`

```dax
Tile X = MIN ( dim_region[tile_col] )
```

### Tile Y

Tile-map row (negated so north is up).

Format: `0`

```dax
Tile Y = - MIN ( dim_region[tile_row] )
```

### Tile Size

Constant bubble size for the tile map.

Format: `0`

```dax
Tile Size = 1
```

## 5. Robustness

### Test Rank

Gap rank in the selected sensitivity test.

Format: `0`

```dax
Test Rank = MIN ( fact_sensitivity_rank[gap_rank] )
```

### Tests Run

Number of sensitivity tests (6).

Format: `0`

```dax
Tests Run = CALCULATE ( DISTINCTCOUNT ( fact_sensitivity_rank[test_id] ), REMOVEFILTERS ( dim_region ) )
```

### Tests in Top 5

Number of tests with the region in the top 5.

Format: `0`

```dax
Tests in Top 5 = CALCULATE ( COUNTROWS ( fact_sensitivity_rank ), fact_sensitivity_rank[gap_rank] <= 5 ) + 0
```

### Best Rank Across Tests

Best rank over the six tests.

Format: `0`

```dax
Best Rank Across Tests = MIN ( fact_sensitivity_rank[gap_rank] )
```

### Worst Rank Across Tests

Worst rank over the six tests.

Format: `0`

```dax
Worst Rank Across Tests = MAX ( fact_sensitivity_rank[gap_rank] )
```

### Stable Priority Regions

Regions in the top 5 in all tests but at most one (notebook rule).

Format: `0`

```dax
Stable Priority Regions = COUNTROWS ( FILTER ( VALUES ( dim_region[region_id] ), [Tests in Top 5] >= [Tests Run] - 1 ) )
```

### Stable Priority List

Stable priority regions in baseline rank order.

```dax
Stable Priority List = CONCATENATEX ( FILTER ( ALL ( dim_region ), [Tests in Top 5] >= [Tests Run] - 1 ), dim_region[region_en], ", ", dim_region[baseline_gap_rank], ASC )
```

### Rank Cell Color

Matrix background: rank 1 dark orange, ranks 2-5 light orange.

```dax
Rank Cell Color =
    VAR _r = [Test Rank]
    RETURN
        SWITCH ( TRUE (), ISBLANK ( _r ), BLANK (), _r = 1, "#F08A5D", _r <= 5, "#FBD3C2", "#FFFFFF" )
```

### Gap Rank Cell Color

Matrix background for scenario ranks.

```dax
Gap Rank Cell Color =
    VAR _r = [Gap Rank]
    RETURN
        SWITCH ( TRUE (), ISBLANK ( _r ), BLANK (), _r = 1, "#F08A5D", _r <= 5, "#FBD3C2", "#FFFFFF" )
```

### Random Weights Top 5 %

Share of 1,000 random weightings (seed 42) with the region in the top 5.

Format: `0.0%`

```dax
Random Weights Top 5 % = DIVIDE ( SUM ( fact_robustness[weights_top5_pct] ), 100 * [Regions] )
```

### Random Weights Median Rank

Median rank across the 1,000 weightings.

Format: `0`

```dax
Random Weights Median Rank = AVERAGE ( fact_robustness[weights_median_rank] )
```

### Random Weights Best Rank

Best rank across the weightings.

Format: `0`

```dax
Random Weights Best Rank = MIN ( fact_robustness[weights_best] )
```

### Random Weights Worst Rank

Worst rank across the weightings.

Format: `0`

```dax
Random Weights Worst Rank = MAX ( fact_robustness[weights_worst] )
```

### Leave-One-Out Top 5

Times in the top 5 out of 12 leave-one-region-out runs.

Format: `0`

```dax
Leave-One-Out Top 5 = SUM ( fact_robustness[loo_top5] )
```

### Leave-One-Out Top 5 %

Share of the 12 leave-one-region-out runs with the region in the top 5.

Format: `0.0%`

```dax
Leave-One-Out Top 5 % = DIVIDE ( SUM ( fact_robustness[loo_top5] ), 12 * [Regions] )
```

### Leave-One-Out Worst Rank

Worst rank in leave-one-out.

Format: `0`

```dax
Leave-One-Out Worst Rank = MAX ( fact_robustness[loo_worst] )
```

### Least Stable Priority

Stable priority region that is least often in the top 5 under random weights.

```dax
Least Stable Priority =
    VAR _stable = FILTER ( ALL ( dim_region ), [Tests in Top 5] >= [Tests Run] - 1 )
    VAR _r = TOPN ( 1, _stable, [Random Weights Top 5 %], ASC )
    RETURN
        MAXX ( _r, dim_region[region_en] ) & " · " & FORMAT ( MAXX ( _r, [Random Weights Top 5 %] ), "0.0%" )
```

### Random Weight Draws

Number of Dirichlet weight draws in the notebook (seed 42).

Format: `#,0`

```dax
Random Weight Draws = 1000
```

### Tile Stable Color

Alias used by the tile map.

```dax
Tile Stable Color = [Stable Group Color]
```

## 6. Trends

### Beneficiaries

Social security beneficiaries in the years in context.

Format: `#,0`

```dax
Beneficiaries = SUM ( fact_social_security[beneficiaries] )
```

### Beneficiaries PY

Beneficiaries in the previous year.

Format: `#,0`

```dax
Beneficiaries PY = VAR _y = MAX ( dim_year[year] ) RETURN CALCULATE ( [Beneficiaries], dim_year[year] = _y - 1 )
```

### Beneficiaries YoY %

Year-over-year change in beneficiaries.

Format: `+0.0%;-0.0%;0.0%`

```dax
Beneficiaries YoY % = DIVIDE ( [Beneficiaries] - [Beneficiaries PY], [Beneficiaries PY] )
```

### Beneficiaries Index 2020=100

Beneficiaries indexed to 2020 = 100 (2020-2022 only).

Format: `0.0`

```dax
Beneficiaries Index 2020=100 = VAR _y = MAX ( dim_year[year] ) RETURN IF ( _y >= 2020, DIVIDE ( [Beneficiaries], CALCULATE ( [Beneficiaries], dim_year[year] = 2020 ) ) * 100 )
```

### Change 2021 to 2022 %

Change in beneficiaries from 2021 to 2022 (transition year).

Format: `+0.0%;-0.0%;0.0%`

```dax
Change 2021 to 2022 % = DIVIDE ( CALCULATE ( [Beneficiaries], dim_year[year] = 2022 ), CALCULATE ( [Beneficiaries], dim_year[year] = 2021 ) ) - 1
```

### Peak Beneficiaries

Highest annual number of beneficiaries, 2005-2022.

Format: `#,0`

```dax
Peak Beneficiaries = MAXX ( ALL ( dim_year[year] ), [Beneficiaries] )
```

### Peak Year

Year of the peak.

Format: `0`

```dax
Peak Year = MAXX ( TOPN ( 1, ALL ( dim_year[year] ), [Beneficiaries], DESC ), dim_year[year] )
```

### Change Peak to 2022 %

Change from the peak year to 2022.

Format: `+0.0%;-0.0%;0.0%`

```dax
Change Peak to 2022 % = DIVIDE ( CALCULATE ( [Beneficiaries], dim_year[year] = 2022 ), [Peak Beneficiaries] ) - 1
```

### Saudi Population (Year)

Saudi population in the years in context (2010-2022).

Format: `#,0`

```dax
Saudi Population (Year) = SUM ( fact_population[saudi_population] )
```

### Population (Year)

Total population in the years in context (2010-2022).

Format: `#,0`

```dax
Population (Year) = SUM ( fact_population[population] )
```

### SS Rate (Year) %

Beneficiaries / Saudi population for each year 2010-2022.

Format: `0.00%`

```dax
SS Rate (Year) % = DIVIDE ( [Beneficiaries], [Saudi Population (Year)] )
```

## 7. Statistics

### Spearman Orgs vs Population

Rank correlation between organization counts and population (notebook 4.2: 0.87).

Format: `0.00`

```dax
Spearman Orgs vs Population =
    VAR _t =
        ADDCOLUMNS ( ALL ( dim_region ), "@x", [Organizations (All Types)], "@y", [Population 2022] )
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
        DIVIDE ( _cov, _sx * _sy )
```

### Spearman Income vs Food Share

Rank correlation between Saudi median income and food share (notebook 4.4: -0.64).

Format: `0.00`

```dax
Spearman Income vs Food Share =
    VAR _t =
        ADDCOLUMNS ( ALL ( dim_region ), "@x", [Median Income (Saudi)], "@y", [Food Share %] )
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
        DIVIDE ( _cov, _sx * _sy )
```

### Spearman SS Rate 2020 vs 2022

Stability of regional social security rates (notebook 4.3: 0.99).

Format: `0.00`

```dax
Spearman SS Rate 2020 vs 2022 =
    VAR _t =
        ADDCOLUMNS ( ALL ( dim_region ), "@x", CALCULATE ( [SS Rate (Year) %], dim_year[year] = 2020 ), "@y", CALCULATE ( [SS Rate (Year) %], dim_year[year] = 2022 ) )
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
        DIVIDE ( _cov, _sx * _sy )
```

### Spearman SS Rate 2021 vs 2022

Stability of regional social security rates (notebook 4.3: 0.94).

Format: `0.00`

```dax
Spearman SS Rate 2021 vs 2022 =
    VAR _t =
        ADDCOLUMNS ( ALL ( dim_region ), "@x", CALCULATE ( [SS Rate (Year) %], dim_year[year] = 2021 ), "@y", CALCULATE ( [SS Rate (Year) %], dim_year[year] = 2022 ) )
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
        DIVIDE ( _cov, _sx * _sy )
```

### Spearman Fragility 2022 vs Avg

Fragility with 2022 vs 2020-22 social security rate (notebook 6: 0.99).

Format: `0.00`

```dax
Spearman Fragility 2022 vs Avg =
    VAR _t =
        ADDCOLUMNS ( ALL ( dim_region ), "@x", CALCULATE ( [Fragility Index], REMOVEFILTERS ( dim_scenario ), dim_scenario[scenario] = "A" ), "@y", CALCULATE ( [Fragility Index], REMOVEFILTERS ( dim_scenario ), dim_scenario[scenario] = "C" ) )
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
        DIVIDE ( _cov, _sx * _sy )
```

### Largest to Smallest Population

Population of the largest region / smallest region (notebook 4.2: 25x).

Format: `0`

```dax
Largest to Smallest Population = DIVIDE ( MAXX ( ALL ( dim_region ), [Population 2022] ), MINX ( ALL ( dim_region ), [Population 2022] ) )
```

## 8. Titles

### Title Gap Chart

Dynamic visual title.

```dax
Title Gap Chart = "Gap score by region · scenario " & [Selected Scenario]
```

### Title Profile

Dynamic page title on the profile page.

```dax
Title Profile = IF ( HASONEVALUE ( dim_region[region_en] ), "Region profile · " & VALUES ( dim_region[region_en] ) & "  (" & VALUES ( dim_region[region_ar] ) & ")", "Region profile · select one region" )
```

### Population 2022 Label

Population 2022 in millions as text (locale-independent card label).

```dax
Population 2022 Label = FORMAT ( [Population 2022] / 1000000, "0.0" ) & "M"
```

### Title Tooltip

Region name on the tooltip page.

```dax
Title Tooltip = IF ( HASONEVALUE ( dim_region[region_en] ), VALUES ( dim_region[region_en] ) & "  ·  " & VALUES ( dim_region[region_ar] ) )
```

### Tooltip Rank Line

Rank summary line on the tooltip page.

```dax
Tooltip Rank Line = IF ( HASONEVALUE ( dim_region[region_en] ), "Gap rank " & [Gap Rank] & " of 13  ·  " & [Gap Source] & "  ·  scenario " & [Selected Scenario] )
```

### Title Drillthrough

Dynamic title of the drill-through page.

```dax
Title Drillthrough = IF ( HASONEVALUE ( dim_region[region_en] ), "Region detail · " & VALUES ( dim_region[region_en] ) & "  (" & VALUES ( dim_region[region_ar] ) & ")", "Region detail · right-click a region on the dashboard > Drill through" )
```

### Profile Group

Final priority group of the selected region.

```dax
Profile Group = IF ( HASONEVALUE ( dim_region[region_en] ), VALUES ( dim_region[priority_group] ) )
```

## What-if parameter tables

Three calculated tables feed optional custom fragility weights (default 1 = the notebook; not placed on the dashboard, available for ad-hoc what-if analysis):

```dax
'Weight SS' = GENERATESERIES ( 0, 5, 1 )   -- Weight of the social security rate in the fragility index (0-5, default 1)
'Weight Income' = GENERATESERIES ( 0, 5, 1 )   -- Weight of low Saudi median income in the fragility index (0-5, default 1)
'Weight Food' = GENERATESERIES ( 0, 5, 1 )   -- Weight of the food share of spending in the fragility index (0-5, default 1)
```
