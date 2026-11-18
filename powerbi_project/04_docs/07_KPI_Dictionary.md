# 7. KPI Dictionary

All values below are for scenario A, and every one was checked against the notebook (`10_Validation_Report.md`). The full DAX for each measure is in `03_DAX_Measures.md`.

## Headline KPIs (dashboard cards)

| KPI | Measure | Definition | Formula | Value |
|---|---|---|---|---|
| Registered non-profits | `Organizations (All Types)` | Associations + foundations in the NCNP register, by head-office region | `COUNTROWS(fact_organizations)` ignoring the type filter | 2,723 |
| Population 2022 | `Population 2022` / `Population 2022 Label` | Total residents (SAMA) | `SUM(population_2022)` | 32,175,224 (32.2M) |
| Non-profits per 100k | `Org Density per 100k` | Organizations per 100,000 residents | Organizations / Population × 100,000 | 8.46 nationally |
| SS beneficiaries 2022 | `Beneficiaries 2022` | Social security beneficiaries (heads of household and dependants) | `SUM(beneficiaries_2022)` | 1,107,071 |
| #1 priority | `Top Priority Region` | Region with gap rank 1 in the active scenario | Region where `Gap Rank = 1` | Najran |
| Gap of #1 | `Top Priority Gap` | Gap score of that region | Gap Score where `Gap Rank = 1` | +1.94 |
| Stable priorities | `Stable Priority List` | Regions in the top 5 in at least 5 of the 6 sensitivity tests | `CONCATENATEX` over regions with `Tests in Top 5 ≥ Tests Run − 1` | Najran, Jazan, Madinah, Tabuk, Makkah |

## Fragility indicators

| KPI | Measure | Definition | Direction |
|---|---|---|---|
| Social security rate | `SS Rate 2022 %`, `SS Rate (Scenario) %` | Beneficiaries / Saudi population (2022 in scenarios A and B, average 2020-22 in C and D) | Higher = more fragile |
| Median income | `Median Income (Saudi)` | Median monthly disposable income per Saudi, SAR (HIES 2023) | Lower = more fragile |
| Food share | `Food Share %` | Food and beverages share of household spending | Higher = more fragile |
| z-scores | `Z SS Rate`, `Z Low Income`, `Z Food Share` | (x − mean of 13) / population SD of 13; income sign reversed | Higher = more fragile |
| **Fragility index** | `Fragility Index` | Weighted mean of the three z-scores (weights default to 1 = the notebook) | Higher = more fragile |
| Fragility rank | `Fragility Rank` | 1 = most fragile (RANKX, ties skip) | |

## Gap and priority

| KPI | Measure | Definition |
|---|---|---|
| Density (scenario) | `Density (Scenario)` | All organizations (A and C) or associations only (B and D) per 100k |
| Gap score | `Gap Score` | z(Fragility Index) − z(Density) |
| Fragility part | `Fragility Part` | z(Fragility Index) |
| Few non-profits part | `Few Non-profits Part` | −z(Density) |
| Gap source | `Gap Source` | "Fragility" if the fragility part > the few non-profits part, otherwise "Few non-profits" |
| Gap rank | `Gap Rank` | 1 = largest gap |
| Quadrant | `Quadrant` | High or low fragility × few or many organizations, split at the 13-region medians |
| Scenarios in top 5 | `Scenarios in Top 5` | Number of scenarios (of 4) with the region in the top 5 |

## Robustness

| KPI | Measure | Definition |
|---|---|---|
| Tests in top 5 | `Tests in Top 5` | Sensitivity tests (of 6) with the region in the top 5 |
| Random weights top 5 % | `Random Weights Top 5 %` | Share of the 1,000 Dirichlet weightings (seed 42) with the region in the top 5 |
| Leave-one-out top 5 % | `Leave-One-Out Top 5 %` | Share of the 12 leave-one-region-out runs with the region in the top 5 |
| Worst rank | `Random Weights Worst Rank`, `Leave-One-Out Worst Rank` | Worst rank observed |

## Trends and statistics

| KPI | Measure | Value |
|---|---|---|
| Peak beneficiaries | `Peak Beneficiaries` / `Peak Year` | 1,552,415 in 2021 |
| Change 2021 → 2022 | `Change 2021 to 2022 %` | −28.7% |
| Spearman: organizations vs population | `Spearman Orgs vs Population` | 0.87 |
| Spearman: income vs food share | `Spearman Income vs Food Share` | −0.64 |
| Spearman: SS rate 2020 vs 2022 | `Spearman SS Rate 2020 vs 2022` | 0.99 |
| Spearman: SS rate 2021 vs 2022 | `Spearman SS Rate 2021 vs 2022` | 0.94 |
| Spearman: fragility 2022 vs average | `Spearman Fragility 2022 vs Avg` | 0.99 |
