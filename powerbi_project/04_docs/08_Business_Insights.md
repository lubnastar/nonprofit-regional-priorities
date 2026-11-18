# 8. Business Insights and Recommendations

Every figure comes from the notebook and is reproduced live in the Power BI model (validated, 534 checks).

## Answer

**Najran first, then Jazan.** These two regions combine above-average economic fragility with low non-profit density, and fragility is the larger part of their gap.

**Second group: Madinah, Tabuk and Makkah.** Their fragility is average or below average, but non-profit density is among the lowest. They are service-gap priorities, not economic-need priorities.

## Insights

1. **Najran is the clear first priority.** Its gap score is +1.94, against +0.77 for #2. It has the lowest Saudi median income (SAR 1,650 a month), the highest food share of spending (43.5%) and no foundations. It is #1 in all four scenarios and all six sensitivity tests, in the top 5 in 100% of the 1,000 random weightings and in all 12 leave-one-out runs.
2. **Jazan is second and also fragility-driven.** It has the second-highest social security rate (9.84%), density right at the median (10.53 per 100k) and no foundations. Its ranking depends most on the weight of the social security indicator: top 5 in 72.9% of random weightings, with a worst rank of 8.
3. **Madinah, Tabuk and Makkah are service gaps.** Their densities are 8.56, 8.24 and 5.54 per 100k, among the lowest. Makkah has the second-lowest density and the most social security beneficiaries of the five (245,796). Madinah is in the top 5 in 100% of weightings and Makkah in 96.2%.
4. **Non-profits are concentrated.** Riyadh hosts 29.3% of all non-profits and 60.1% of foundations. Jazan, Hail, Al-Baha, Tabuk and Najran have no foundations. Organization counts follow population (Spearman 0.87), so per-capita density is the fair comparison.
5. **Al-Jouf is borderline.** It is in the top 5 in 2 of the 6 tests, 27.5% of weightings and 6 of 12 leave-one-out runs. It is worth monitoring, not funding first.
6. **High fragility does not always mean a high gap.** Al-Baha, Hail and Northern Borders are more fragile than the median, but their non-profit density is relatively high, which lowers their gap.
7. **The ranking holds up.** The same five regions are in the top 5 in all four scenarios (A-D) and in at least 5 of the 6 tests.
8. **2022 is a transition year.** Beneficiaries peaked at 1.55M in 2021 and fell 28.7% in 2022 with the move to the new social security system. Regional ranks barely moved (Spearman 0.94 between 2021 and 2022, 0.99 between 2020 and 2022), so the relative ranking is still usable.

## Recommendations

| Donor goal | Where | Why |
|---|---|---|
| Meet economic need | **Najran**, then **Jazan** | Highest fragility with few non-profits. Jazan reaches more beneficiaries (98,716 against 33,760). |
| Close service gaps | **Madinah, Tabuk, Makkah** (no fixed order) | Few non-profits for their population. Makkah has the largest number of beneficiaries. |
| Monitor | **Al-Jouf** | Borderline in the robustness tests |

## Caveats (notebook section 10)

- The ranking is **relative** across the 13 regions. It is not an absolute measure of need.
- Indicators mix periods: population and social security from 2022, organizations from about mid-2022, and HIES from 2023.
- Saudi population for 2020-21 is back-cast from the 2022 census, which affects scenarios C and D.
- The food share covers all households, and the survey's margin of error is not published.
- Density counts organizations by head office. It does not reflect their size or service area.
- Fragility and density have equal weight in the gap, so always read the **gap source** together with the rank.
- Before final funding decisions, validate with direct data on services delivered, organization resources and beneficiary needs.
