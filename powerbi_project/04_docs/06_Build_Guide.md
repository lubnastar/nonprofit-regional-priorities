# 6. Build Guide

There are two ways to build the report:

- **Path A** regenerates the whole project from scripts in about 5 minutes.
- **Path B** builds it by hand in Power BI Desktop, which is useful for learning or for checking each step.

## Path A: automated (what produced this project)

```powershell
# from the repository root
.venv\Scripts\python powerbi_project\01_scripts\build_model_data.py      # 1. raw data → clean star schema (36 checks vs notebook)
.venv\Scripts\python powerbi_project\01_scripts\build_semantic_model.py  # 2. TMDL model: tables, relationships, 111 measures + DAX/M docs
.venv\Scripts\python powerbi_project\01_scripts\build_report.py          # 3. PBIR report: dashboard + tooltip + drill-through, theme
```

1. Open `03_powerbi/RegionalPriorities.pbip` in Power BI Desktop (June 2026 or later).
2. Click **Refresh now** in the yellow bar. The data comes from `02_data/`, or from the embedded copy if that folder is not found.
3. Optionally, validate against the notebook:

```powershell
powershell -File powerbi_project\01_scripts\pbi_dax.ps1 -QueryFile powerbi_project\01_scripts\validation_queries.dax -OutDir powerbi_project\04_docs\validation\dax_results
.venv\Scripts\python powerbi_project\01_scripts\compare_results.py      # → 04_docs/10_Validation_Report.md
```

## Path B: manual

### 1. Load the data

1. In Power BI Desktop, go to **Home > Get data > Text/CSV** and load the 11 CSVs from `02_data/`. Alternatively, load all the sheets of `RegionalPriorities_ModelData.xlsx`.
2. In **Transform data**, set the column types with **Using locale > English (United States)**, so decimals parse correctly on any Windows locale.
3. Optional: create a text parameter `DataFolder` and point each source at `DataFolder & "\<table>.csv"`. The final M is in `04_Power_Query_M.md`.

### 2. Model

1. In **Model view**, create the 10 relationships in `02_Data_Model.md`: all many-to-one, single direction.
2. Leave `dim_scenario` **unrelated**.
3. Sort `dim_region[region_en]` by `baseline_gap_rank`, and `dim_scenario[scenario_label]` by `scenario_order`.
4. Hide the key and raw numeric columns.
5. **Modeling > New parameter > Numeric range** three times: `Weight SS`, `Weight Income` and `Weight Food`, each 0-5 in steps of 1 with default 1.

### 3. Measures

1. **Home > Enter data** creates an empty table `_Measures`.
2. Add the measures from `03_DAX_Measures.md` in folder order 1 → 8. Later folders reference earlier ones.
3. Set each measure's format string as listed.

### 4. Theme

**View > Themes > Browse for themes** → `03_powerbi/theme/RegionalPriorities_Theme.json`.

### 5. Dashboard page (1600 × 900, Fit to page)

Build the layout in `05_Dashboard_Design.md`:

1. **Header:** a text box for the title and subtitle, plus a thin orange rectangle.
2. **Slicers:** `dim_scenario[scenario_label]` as a single-select dropdown with A selected; `dim_region[region_en]` as a multi-select dropdown.
3. **KPI row:** 7 cards with the measures listed in the design doc.
4. **Tile map:** a scatter chart with Values `region_en`, X `Tile X`, Y `Tile Y`, Size `Tile Size`. Set the colours with **fx > Field value > Stable Group Color**, and turn off the axes.
5. **Gap bar:** a clustered bar chart with `region_en` × `Gap Score`, sorted descending. Set the colours with **fx > Field value > Priority Color**, and the title with **fx > Title Gap Chart**.
6. **Fragility vs density:** a scatter with X `Density (Scenario)` and Y `Fragility Index`. In **Analytics**, add X and Y constant lines set with fx to `Median Density` and `Median Fragility`.
7. **Decomposition:** a stacked bar chart with `Fragility Part` (orange) and `Few Non-profits Part` (blue), sorted by `Gap Score`.
8. **Robustness:** a clustered bar chart with `Random Weights Top 5 %` and `Leave-One-Out Top 5 %`.
9. **Trend:** a line chart with `dim_year[year]` (continuous axis) × `Beneficiaries`.
10. **Insights:** a text box with the insights from `08_Business_Insights.md`.

### 6. Tooltip page

1. Add a new page, *Region tooltip*. In **Page information**, set **Allow use as tooltip = On** and canvas size **Custom 340 × 250**.
2. Add `dim_region[region_en]` to the **Tooltip** field well.
3. Add the cards `Title Tooltip` and `Tooltip Rank Line`, then a 3 × 3 grid of indicator cards.
4. On each region visual of the dashboard: **Format > General > Tooltips > Type = Report page, Page = Region tooltip**.
5. Hide the page.

### 7. Drill-through page

1. Add a new page, *Region detail*. Set **Page type = Drill through** and add `dim_region[region_en]` to **Drill through from**.
2. Add the `Title Drillthrough` card, 18 KPI cards (each indicator and its rank), a beneficiaries line chart, a `Test Rank` bar by `dim_sensitivity_test[test_short]`, and a table of organizations.
3. Add a Back button, plus a scenario slicer synced with the dashboard (**View > Sync slicers**).
4. Hide the page.

### 8. Check

- Scenario A must show **Najran +1.94** and the stable list **Najran, Jazan, Madinah, Tabuk, Makkah**.
- Compare any other value with `04_docs/validation/notebook_expected_region_values.csv`.

## Moving or sharing the project

- **Copy the whole `powerbi_project` folder.** If `02_data` is not at the original path, every query falls back automatically to the data embedded in the model.
- **To load edited CSVs from a new location:** **Transform data > Edit parameters > DataFolder**, then **Refresh**.
- **Saving:** Desktop stores the loaded data in `RegionalPriorities.SemanticModel/.pbi/cache.abf`, so the report opens with data and needs no refresh.
- **For a single file:** **File > Save as > .pbix**.
