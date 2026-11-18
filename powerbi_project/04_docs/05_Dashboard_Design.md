# 5. Dashboard Design

The report is **one dashboard page**, *Regional Priorities Dashboard*, at 1600 × 900. It has two hidden helper pages that never appear as tabs in view mode:

- **Region tooltip:** opens when you hover a region on any region chart.
- **Region detail:** a drill-through page. Right-click a region, then choose *Drill through > Region detail*.

## Layout

```
┌──────────────────────────────────────────────────────────────────────────────┬──────────┬──────────┐
│ ▌Where should charitable resources go first?                                  │ Scenario │ Region   │
│  subtitle: method + colour legend + how to interact                           │ slicer   │ slicer   │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬────────────┴──────────┴──────────┤
│ Non-     │ Popula-  │ Non-     │ SS bene- │ #1       │ Gap of   │ Stable priorities                 │
│ profits  │ tion     │ profits  │ ficiaries│ priority │ #1       │ (top 5 in ≥5 of 6 tests)          │
│          │ 2022     │ /100k    │ 2022     │          │          │                                   │
├──────────┴───┬──────┴──────────┴──┬───────┴──────────┴──────┬───┴──────────────┐                   │
│ Tile map     │ Gap score by region│ Fragility vs density    │ Key insights     │                   │
│ (priority    │ (sorted, coloured  │ (scatter, median lines, │ Recommendation   │                   │
│  groups)     │  by gap source)    │  quadrants)             │ How to use       │                   │
├──────────────┼────────────────────┼─────────────────────────┤ How to read      │                   │
│ Why each     │ How stable is the  │ Social security         │                  │                   │
│ region is a  │ ranking? (random   │ beneficiaries 2005-2022 │                  │                   │
│ priority     │ weights, leave-    │ (trend)                 │                  │                   │
│ (stacked)    │ one-out)           │                         │                  │                   │
├──────────────┴────────────────────┴─────────────────────────┴──────────────────┘                   │
│ Sources · validation note                                                                          │
└────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

Reading order: **question → headline numbers → where → how big → why → how sure → context → so what.**

## Colour system (same as the notebook)

| Colour | Meaning |
|---|---|
| Orange `#EB6834` | Gap driven by **fragility** (Najran, Jazan) |
| Blue `#2A78D6` | Gap driven by **few non-profits** (Madinah, Tabuk, Makkah) |
| Grey `#B4B2A9` | Not a priority in the active scenario |

Colours are applied by measures (`Priority Color`, `Stable Group Color`), so they follow the active scenario.

## Visual by visual

| # | Visual | Fields / measures | Question it answers |
|---|---|---|---|
| 1 | Scenario slicer (single select, default A) | `dim_scenario[scenario_label]` | Which definition of the gap am I looking at? |
| 2 | Region slicer (multi select) | `dim_region[region_en]` | Focus on some regions (ranks stay relative to all 13) |
| 3 | KPI: Registered non-profits | `Organizations (All Types)` | How big is the sector? (2,723) |
| 4 | KPI: Population 2022 | `Population 2022 Label` | Scale (32.2M) |
| 5 | KPI: Non-profits per 100k | `Org Density per 100k` | National density (8.46) |
| 6 | KPI: SS beneficiaries 2022 | `Beneficiaries 2022` | Size of the need (1,107,071) |
| 7 | KPI: #1 priority | `Top Priority Region` | The answer (Najran) |
| 8 | KPI: Gap of #1 | `Top Priority Gap` | How strong is it (+1.94)? |
| 9 | KPI: Stable priorities | `Stable Priority List` | Which regions hold up under every test? |
| 10 | Tile map (scatter) | `Tile X`, `Tile Y`, `Tile Size`, colour `Stable Group Color` | Where are the priority regions? |
| 11 | Gap score bar | `Gap Score`, colour `Priority Color`, dynamic title `Title Gap Chart` | How do all 13 regions rank? |
| 12 | Fragility vs density scatter | `Density (Scenario)`, `Fragility Index`, reference lines `Median Density` and `Median Fragility` | Which quadrant is each region in? |
| 13 | Gap decomposition (stacked bar) | `Fragility Part`, `Few Non-profits Part` | Why is each region a priority? |
| 14 | Robustness (clustered bar) | `Random Weights Top 5 %`, `Leave-One-Out Top 5 %` | How sure are we? |
| 15 | Beneficiaries trend (line) | `Beneficiaries` by `dim_year[year]` | Context: what happened to social security over time? |
| 16 | Insights text | Static text taken from the validated notebook results | So what? Recommendation, how to use, how to read |

## Interactivity

- **Scenario switch (A-D):** every gap, rank, colour and title recalculates.
- **Cross-filtering:** clicking a region on any chart filters or highlights the others. The trend chart then shows that region's beneficiaries.
- **Report-page tooltip:** shows the region name (English and Arabic), its gap rank, gap source and scenario, and 9 indicators: gap, fragility, density, social security rate, income, food share, organizations, tests in the top 5, and random weights.
- **Drill-through:** *Region detail* has 18 KPI cards with each region's rank among the 13, the beneficiaries trend, its rank in each of the 6 sensitivity tests, and the list of its registered organizations. It has a Back button and its own scenario slicer, synced with the dashboard.
- **Dynamic titles:** the gap chart title shows the active scenario.

## Hidden pages

| Page | Type | Size | Bound field |
|---|---|---|---|
| Region tooltip | Tooltip | 340 × 250 | `dim_region[region_en]` |
| Region detail | Drill-through | 1600 × 900 | `dim_region[region_en]` |
