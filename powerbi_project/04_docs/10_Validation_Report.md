# Validation Report

**Status: ALL PASS** · 36 pipeline checks + 61 model checks covering 534 individual values.

Two independent layers were checked:

1. **Pipeline (Python):** `build_model_data.py` re-runs the notebook's cleaning, indicator, scenario, sensitivity, random-weights (seed 42) and leave-one-out code from `data_raw/` and asserts that every result equals the notebook's own files in `data_clean/` and `outputs/`.
2. **Model (DAX):** the report was opened in Power BI Desktop, refreshed, and `pbi_dax.ps1` ran `validation_queries.dax` against the live model. `compare_results.py` compares each DAX value with the notebook value. Floating-point tolerance: 1e-09 (relative).

## 1. Pipeline checks (Python vs. notebook files)

| Check | Result |
|---|---|
| HIES: 13 regions, no missing values | PASS |
| Raw shapes match notebook (2723, 169, 13, 252) | PASS |
| SAMA population: Province ID equals region_id | PASS |
| SAMA social security: Province ID equals region_id | PASS |
| Region names in nonprofit_organizations all map to region_map | PASS |
| Region names in sama_population all map to region_map | PASS |
| Region names in gastat_saudi_population all map to region_map | PASS |
| Region names in sama_social_security all map to region_map | PASS |
| Region names in hies_2023 all map to region_map | PASS |
| Organizations: 0 exact duplicate rows removed | PASS |
| Organizations: every row has region and type | PASS |
| Organizations equal notebook data_clean/charities.csv | PASS |
| Saudi population < total population in every region | PASS |
| Social security: Grand Total equals the sum of regions every year | PASS |
| Social security: 234 rows = 13 regions x 18 years | PASS |
| Social security equals notebook data_clean/social_security.csv | PASS |
| Merged table: 13 rows, no missing values | PASS |
| Merged table equals notebook data_clean/regions_merged.csv | PASS |
| Indicators equal notebook outputs/indicators.csv (all 20 numeric columns) | PASS |
| A_gap equals notebook priority_results.csv (2 dp) | PASS |
| B_gap equals notebook priority_results.csv (2 dp) | PASS |
| C_gap equals notebook priority_results.csv (2 dp) | PASS |
| D_gap equals notebook priority_results.csv (2 dp) | PASS |
| A_frag_part equals notebook priority_results.csv (2 dp) | PASS |
| A_dens_part equals notebook priority_results.csv (2 dp) | PASS |
| A_gap_rank equals notebook priority_results.csv | PASS |
| B_gap_rank equals notebook priority_results.csv | PASS |
| C_gap_rank equals notebook priority_results.csv | PASS |
| D_gap_rank equals notebook priority_results.csv | PASS |
| top5_scenarios equals notebook priority_results.csv | PASS |
| A_source equals notebook (Arabic labels translated) | PASS |
| Sensitivity ranks (6 tests) equal notebook sensitivity_ranks.csv | PASS |
| Random-weights and leave-one-out results equal notebook robustness_checks.csv | PASS |
| Stable priority regions = Najran, Jazan, Madinah, Tabuk, Makkah | PASS |
| Population fact: 169 rows = 13 regions x 13 years, no gaps | PASS |
| Organization counts by region equal notebook crosstab (2,723 total) | PASS |

## 2. Model checks (DAX in Power BI vs. notebook)

| Area | Check | Values | Max abs. diff / result | Result |
|---|---|---:|---|---|
| Base & indicators | population (13 regions) | 13 | 0.00e+00 | PASS |
| Base & indicators | saudi_population (13 regions) | 13 | 0.00e+00 | PASS |
| Base & indicators | association (13 regions) | 13 | 0.00e+00 | PASS |
| Base & indicators | foundation (13 regions) | 13 | 0.00e+00 | PASS |
| Base & indicators | total (13 regions) | 13 | 0.00e+00 | PASS |
| Base & indicators | beneficiaries_2022 (13 regions) | 13 | 0.00e+00 | PASS |
| Base & indicators | income_median_saudi (13 regions) | 13 | 0.00e+00 | PASS |
| Base & indicators | food_share (13 regions) | 13 | 0.00e+00 | PASS |
| Base & indicators | ss_rate_2022 (13 regions) | 13 | 9.77e-15 | PASS |
| Base & indicators | ss_rate_avg (13 regions) | 13 | 8.88e-15 | PASS |
| Base & indicators | density_all (13 regions) | 13 | 0.00e+00 | PASS |
| Base & indicators | density_assoc (13 regions) | 13 | 8.88e-16 | PASS |
| Fragility | Fragility index, SS 2022 (fragility_2022) | 13 | 2.66e-15 | PASS |
| Fragility | Fragility index, SS avg 2020-22 (fragility_avg) | 13 | 4.44e-16 | PASS |
| Gap & priority | Scenario A: gap score | 13 | 1.22e-15 | PASS |
| Gap & priority | Scenario A: gap rank | 13 | 0.00e+00 | PASS |
| Gap & priority | Scenario B: gap score | 13 | 1.11e-15 | PASS |
| Gap & priority | Scenario B: gap rank | 13 | 0.00e+00 | PASS |
| Gap & priority | Scenario C: gap score | 13 | 4.44e-16 | PASS |
| Gap & priority | Scenario C: gap rank | 13 | 0.00e+00 | PASS |
| Gap & priority | Scenario D: gap score | 13 | 6.11e-16 | PASS |
| Gap & priority | Scenario D: gap rank | 13 | 0.00e+00 | PASS |
| Gap & priority | Scenario A: fragility part | 13 | 1.11e-15 | PASS |
| Gap & priority | Scenario A: few non-profits part | 13 | 2.22e-16 | PASS |
| Gap & priority | Scenario A: gap source | 13 | exact match | PASS |
| Gap & priority | Scenario A: quadrant | 13 | exact match | PASS |
| Gap & priority | Scenarios A-D in top 5 | 13 | 0.00e+00 | PASS |
| What-if weights | Weight = 0 reproduces notebook test 'no_ss' ranks | 13 | 0.00e+00 | PASS |
| What-if weights | Weight = 0 reproduces notebook test 'no_income' ranks | 13 | 0.00e+00 | PASS |
| What-if weights | Weight = 0 reproduces notebook test 'no_food' ranks | 13 | 0.00e+00 | PASS |
| Robustness | Tests in top 5 (of 6) | 13 | 0.00e+00 | PASS |
| Robustness | Best rank across tests | 13 | 0.00e+00 | PASS |
| Robustness | Worst rank across tests | 13 | 0.00e+00 | PASS |
| Robustness | Random weights: % in top 5 | 13 | 1.42e-14 | PASS |
| Robustness | Leave-one-out: times in top 5 | 13 | 0.00e+00 | PASS |
| Robustness | Leave-one-out: worst rank | 13 | 0.00e+00 | PASS |
| Statistics | spearman_orgs_vs_population | 1 | 1.11e-16 | PASS |
| Statistics | spearman_income_vs_food_share | 1 | 1.11e-16 | PASS |
| Statistics | spearman_ss_rate_2020_vs_2022 | 1 | 0.00e+00 | PASS |
| Statistics | spearman_ss_rate_2021_vs_2022 | 1 | 0.00e+00 | PASS |
| Statistics | spearman_fragility_2022_vs_avg | 1 | 0.00e+00 | PASS |
| Statistics | national_beneficiaries_2021 | 1 | 0.00e+00 | PASS |
| Statistics | national_beneficiaries_2022 | 1 | 0.00e+00 | PASS |
| Statistics | total_organizations | 1 | 0.00e+00 | PASS |
| Statistics | total_population_2022 | 1 | 0.00e+00 | PASS |
| Statistics | riyadh_share_of_orgs_pct | 1 | 0.00e+00 | PASS |
| Statistics | riyadh_share_of_foundations_pct | 1 | 0.00e+00 | PASS |
| Statistics | median_fragility_2022 | 1 | 6.11e-16 | PASS |
| Statistics | median_density_all | 1 | 0.00e+00 | PASS |
| Trends | National beneficiaries per year 2005-2022 | 18 | 0.00e+00 | PASS |
| Trends | Change 2021 -> 2022 by region | 13 | 8.33e-17 | PASS |
| Trends | Index 2022 (2020 = 100) by region | 13 | 1.42e-14 | PASS |
| Headline KPIs | Top priority region | 1 | 'Najran' | PASS |
| Headline KPIs | Top 5 regions | 1 | 'Najran, Jazan, Madinah, Tabuk, Makkah' | PASS |
| Headline KPIs | Stable priority regions | 1 | 'Najran, Jazan, Madinah, Tabuk, Makkah' | PASS |
| Headline KPIs | Least stable priority (random weights) | 1 | 'Jazan · 72.9%' | PASS |
| Headline KPIs | Regions without foundations | 1 | '5' | PASS |
| Headline KPIs | Lowest income region | 1 | 'Najran · SAR 1,650' | PASS |
| Headline KPIs | Highest food share region | 1 | 'Najran · 43.5%' | PASS |
| Headline KPIs | Peak year of beneficiaries | 1 | '2021' | PASS |
| Headline KPIs | Largest / smallest population (x) | 1 | '25' | PASS |

## Notes

- Differences of ~1e-15 are floating-point rounding between NumPy and the VertiPaq engine.
- Ranks use `RANKX(..., SKIP)`, which equals pandas `rank(method='min')`; z-scores use `STDEVX.P`, which equals pandas `std(ddof=0)`.
- Spearman correlations are implemented in DAX with average ranks for ties (Al-Jouf and Tabuk both have 73 organizations), the same convention as pandas.
- Setting one what-if weight to 0 drops that indicator from the fragility index; the resulting ranks equal the notebook's 'without social security / income / food share' sensitivity tests, which validates the weighting logic.
- Raw DAX outputs are in `validation/dax_results/`; the expected values are in `validation/notebook_expected_*.csv`.

## How to re-run

```powershell
# 1. rebuild data and model files
.venv\Scripts\python powerbi_project\01_scripts\build_model_data.py
# 2. open powerbi_project\03_powerbi\RegionalPriorities.pbip in Power BI Desktop, then:
powershell -File powerbi_project\01_scripts\pbi_dax.ps1 -Refresh -QueryFile powerbi_project\01_scripts\validation_queries.dax -OutDir powerbi_project\04_docs\validation\dax_results
.venv\Scripts\python powerbi_project\01_scripts\compare_results.py
```
