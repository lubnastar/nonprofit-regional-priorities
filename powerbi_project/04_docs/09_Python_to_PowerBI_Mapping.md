# 9. Python → Power BI Mapping

| Notebook step | Python | Power BI | Where |
|---|---|---|---|
| Load raw files (§2) | `pd.read_csv` / `read_excel` | Python (`build_model_data.py`) → clean CSVs | `02_data/` |
| Region name unification (§3.1) | dict mapping + asserts | Python; `dim_region` is the conformed result | `dim_region` |
| HIES workbook parsing (§3.5) | Sheet-specific parsing, a transposed sheet, names with line breaks | **Stays in Python**: the publication layout is too irregular for maintainable M, and the asserts would be lost | `fact_region_snapshot` |
| Grand Total reconciliation (§3.4) | assert sum(regions) == total | Python assert, then the row is dropped | `fact_social_security` |
| Typing and loading | dtypes | **M**: `Csv.Document` + `Table.TransformColumnTypes(..., "en-US")`, with an embedded fallback | `04_Power_Query_M.md` |
| Organization counts by type and region (§4.1) | `groupby().size()` | **DAX**: `Organizations`, `Associations`, `Foundations` | folder 1 |
| Shares and concentration (§4.1) | `/ sum()` | **DAX**: `Share of National Organizations %`, `Share of National Foundations %` | folder 1 |
| Social security trend (§4.3) | line plot | **Visual**: line chart; **DAX**: `Beneficiaries`, YoY, peak, change 2021→22 | folder 6 |
| Spearman correlations (§4.1, 4.3, 4.5, 6) | `scipy.stats.spearmanr` | **DAX**: rank-based Pearson with average ranks for ties | folder 7 |
| Indicators (§5) | column arithmetic | **DAX** measures (`SS Rate 2022 %`, `Org Density per 100k`, …) | folder 2 |
| z-scores (§6) | `(x - mean) / std(ddof=0)` | **DAX**: `AVERAGEX` / `STDEVX.P` over `ALL(dim_region)` | folder 3 |
| Fragility index (§6) | mean of z-scores | **DAX**: `Fragility Index`, with optional what-if weights | folder 3 |
| Gap score, parts, source (§7) | `gap_z()` | **DAX**: `Gap Score`, `Fragility Part`, `Few Non-profits Part`, `Gap Source` | folder 4 |
| Ranks (§7) | `rank(method="min")` | **DAX**: `RANKX(ALL(dim_region), …, SKIP)` | folder 4 |
| Scenarios A-D (§7) | loop over 4 configs | **DAX** + disconnected `dim_scenario` slicer | folder 2, 4 |
| Quadrants (§7) | median split | **DAX**: `Quadrant`, `Median Fragility`, `Median Density`; **visual**: scatter with reference lines | folder 4 |
| Six sensitivity tests (§8.1) | re-compute per variant (includes percentile ranks) | **Python, pre-computed** → `fact_sensitivity_rank`; the DAX counts tests in the top 5 | folder 5 |
| 1,000 random weightings (§8.2) | `np.random.dirichlet`, seed 42 | **Python, pre-computed** → `fact_robustness` (random draws and 13,000 re-rankings are not a good fit for DAX) | folder 5 |
| Leave-one-out (§8.3) | 13 × re-standardisation | **Python, pre-computed** → `fact_robustness` | folder 5 |
| Stable priority groups (§9) | `top5_in_n >= 5` + source | **DAX**: `Stable Priority List`; column `dim_region[priority_group]` | folder 5 |
| Tile map (§9) | matplotlib rectangles | **Visual**: scatter on `Tile X`/`Tile Y`, coloured by `Stable Group Color` | dashboard |
| Priority table (§9) | styled DataFrame | **Visuals**: tooltip page and drill-through *Region detail* | hidden pages |
| Limitations (§10) | markdown | Dashboard *How to read* text + `08_Business_Insights.md` | |

## What could not move, and why

| Item | Reason | How it is handled |
|---|---|---|
| HIES publication parsing | Irregular multi-sheet layout; the notebook's asserts are the quality gate | Python re-runs the notebook code and fails if any result changes (36 checks) |
| Random weights and leave-one-out | Stochastic simulation (1,000 Dirichlet draws), re-standardising 13 × 12 subsets | Results stored as facts. They are fixed by seed 42 and identical to the notebook. |
| Percentile-rank sensitivity test | Needs a full re-standardisation per test | Stored in `fact_sensitivity_rank` |
| Matplotlib styling details | Different rendering engines | The same palette, titles and reading order, implemented in the Power BI theme |
