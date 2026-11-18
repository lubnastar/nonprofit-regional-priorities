# 1. Project Analysis: what `analysis.ipynb` does

## Business question

| | |
|---|---|
| **Decision question** | Where should donors and charities prioritize resources across Saudi Arabia's 13 administrative regions? |
| **Analytical question** | Which regions combine high **economic fragility** with low **non-profit density**? |
| **Unit of analysis** | The 13 administrative regions |
| **Answer (notebook)** | Najran first, then Jazan (fragility-driven). Madinah, Tabuk and Makkah form a second, service-gap group (few non-profits, average or below-average fragility). |

## Data sources (`data_raw/`)

| File | Content | Source | Period |
|---|---|---|---|
| `nonprofit_organizations.csv` | Associations and foundations by region of head office | NCNP open data | Not dated explicitly; the publishing path suggests mid-2022 |
| `sama_population_by_region_2010_2022.csv` | Total population by region | SAMA | 2010-2022 |
| `gastat_saudi_population_by_region_2010_2022.csv` | Saudi population by region | GASTAT census 2022; pre-2022 figures back-cast by GASTAT | 2010-2022 |
| `sama_social_security_by_region_2005_2022.csv` | Social security beneficiaries and payments | SAMA via DataSaudi | 2005-2022 |
| `hies_2023_publication_tables.xlsx` | Household income and expenditure survey; the notebook extracts four tables (11-2, 10-2, 9-3, 16-4) | GASTAT via DataSaudi | 2023 |

## Cleaning steps (notebook section 3)

1. **Region names unified** to one English key per region (13), with an assertion that every source maps completely.
2. **Organizations:** type normalised (association / foundation), region mapped. `reg_no` is not unique in the source, so the Power BI model adds a surrogate `org_id`. 2,723 organizations.
3. **Population:** SAMA total population and GASTAT Saudi population, by region and year.
4. **Social security:** the *Grand Total* row is reconciled against the sum of the regions and then removed.
5. **HIES 2023:** four differently laid-out publication sheets (one transposed, region names with embedded line breaks) are parsed into median and mean income, mean spending and the food share.
6. **Unified table** `regions_merged.csv`, one row per region, with assertions on completeness.

## Indicators (sections 5-6)

| Indicator | Definition | Direction |
|---|---|---|
| Social security rate | Beneficiaries / Saudi population (2022, or average 2020-22) | Higher = more fragile |
| Median income | Median monthly disposable income per Saudi (HIES 2023) | Lower = more fragile |
| Food share | Food and beverages share of household spending, all households | Higher = more fragile |
| **Fragility index** | Mean of the three z-scores (population SD across the 13 regions; income reversed) | Higher = more fragile |
| **Non-profit density** | (Associations + foundations) per 100,000 residents, 2022 | Lower = fewer non-profits |
| **Gap score** | z(fragility index) − z(density) | Higher = higher priority |

The gap splits into a **fragility part** (= z(fragility)) and a **few non-profits part** (= −z(density)). The larger part is the **gap source**.

## Analyses in the notebook

| § | Analysis | Key output |
|---|---|---|
| 4.1 | Distribution of non-profits | Riyadh has 29.3% of all non-profits and 60.1% of foundations. Spearman orgs vs population = 0.87. |
| 4.2 | Population | Size differences between regions; density must be per capita. |
| 4.3 | Social security 2005-2022 | Peak of 1.55M beneficiaries in 2021, −28.7% in 2022 (transition year). Rank stability: Spearman 0.99 (2020 vs 2022) and 0.94 (2021 vs 2022). |
| 4.4 | Income and spending | Najran has the lowest median income (SAR 1,650) and the highest food share (43.5%). |
| 4.5 | Correlation between fragility indicators | Spearman income vs food share = −0.64. |
| 5-6 | Indicator construction, fragility index | z-scores and equal-weight index; fragility 2022 vs average 2020-22: Spearman 0.99. |
| 7 | Priority gap, 4 scenarios (A-D), quadrants, gap source | The same 5 regions are in the top 5 in all 4 scenarios. |
| 8.1 | Six sensitivity tests | Stable priority = top 5 in at least 5 of 6 tests. |
| 8.2 | 1,000 Dirichlet random weightings (seed 42) | Share of draws in the top 5, best, worst and median rank. |
| 8.3 | Leave one region out (12 runs per region) | Top-5 count, best and worst rank. |
| 9 | Results: tile map, priority table, recommendations | Two stable priority groups. |
| 10 | Limitations | Data periods, back-cast population, food share for all households, survey error, transition year, density limits, equal weights. |

## Findings carried into Power BI

- Najran: gap +1.94 (next region +0.77). It is #1 in all four scenarios and all six tests, and in the top 5 in 100% of random weightings and in all 12 leave-one-out runs.
- Jazan: 2nd. Second-highest social security rate (9.84%) and no foundations. It is the least stable of the five (72.9% of weightings).
- Madinah (8.56 per 100k), Tabuk (8.24) and Makkah (5.54): low density with fragility at or below average. Makkah has the most beneficiaries of the five (245,796).
- Al-Jouf is borderline: in the top 5 in 2 of the 6 tests, 27.5% of weightings and 6 of 12 leave-one-out runs.
