"""
Step 1 of the Power BI build: raw data -> clean star-schema tables.

Re-runs the cleaning, indicator and robustness logic of analysis.ipynb from data_raw/
(same code, same seed), checks every result against the notebook's own output files in
outputs/ and data_clean/, then writes the tables the Power BI model loads.

Run from the project root:
    .venv\\Scripts\\python powerbi_project\\01_scripts\\build_model_data.py
"""
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data_raw"
NB_CLEAN = ROOT / "data_clean"
NB_OUT = ROOT / "outputs"
OUT = Path(__file__).resolve().parents[1] / "02_data"
REF = Path(__file__).resolve().parents[1] / "04_docs" / "validation"
OUT.mkdir(parents=True, exist_ok=True)
REF.mkdir(parents=True, exist_ok=True)

REF_YEAR = 2022
AVG_YEARS = [2020, 2021, 2022]

checks = []  # (check, result) rows for the validation report


def check(name, ok):
    checks.append((name, "PASS" if ok else "FAIL"))
    if not ok:
        raise AssertionError(name)


# ---------------------------------------------------------------- 1. load (notebook section 2)
wb = openpyxl.load_workbook(RAW / "hies_2023_publication_tables.xlsx", data_only=True, read_only=True)


def region_table(sheet, prefix):
    rows = []
    for name, *vals in wb[sheet].iter_rows(values_only=True):
        if isinstance(name, str) and isinstance(vals[0], (int, float)):
            region = name.split("\n")[0].strip()
            if region != "الإجمالي":
                rows.append((region, *vals[:3]))
    cols = [f"{prefix}_{n}" for n in ("saudi", "non_saudi", "total")]
    return pd.DataFrame(rows, columns=["region_ar", *cols]).set_index("region_ar")


SHARE_NAMES = [
    "food", "tobacco", "clothing", "housing_utilities", "furnishings", "health", "transport",
    "information_communication", "recreation", "education", "restaurants_accommodation",
    "insurance_finance", "personal_care_other",
]
rows_164 = list(wb["16-4"].iter_rows(values_only=True))
header = next(r for r in rows_164 if isinstance(r[1], str) and "Riyadh" in r[1])
share_rows = [r for r in rows_164 if isinstance(r[1], (int, float))][: len(SHARE_NAMES)]
shares = pd.DataFrame(
    [r[1:14] for r in share_rows],
    index=[f"share_{n}" for n in SHARE_NAMES],
    columns=[h.split("\n")[0].strip() for h in header[1:14]],
).T.rename_axis("region_ar")
hies_raw = (
    region_table("11-2", "income_median")
    .join(region_table("10-2", "income_mean"))
    .join(region_table("9-3", "spend_mean"))
    .join(shares)
    .reset_index()
)
check("HIES: 13 regions, no missing values", len(hies_raw) == 13 and hies_raw.notna().all().all())

charities_raw = pd.read_csv(RAW / "nonprofit_organizations.csv", skiprows=1, encoding="utf-8-sig")
population_raw = pd.read_csv(RAW / "sama_population_by_region_2010_2022.csv")
saudi_raw = pd.read_csv(RAW / "gastat_saudi_population_by_region_2010_2022.csv", encoding="utf-8-sig")
social_raw = pd.read_csv(RAW / "sama_social_security_by_region_2005_2022.csv")
check("Raw shapes match notebook (2723, 169, 13, 252)",
      (len(charities_raw), len(population_raw), len(saudi_raw), len(social_raw)) == (2723, 169, 13, 252))

# ---------------------------------------------------------------- 2. clean (notebook section 3)
region_map = pd.DataFrame(
    [
        (1, "الرياض", "Riyadh", "منطقة الرياض", "Al-Riyadh"),
        (2, "مكة المكرمة", "Makkah", "منطقة مكة المكرمة", "Makkah Al-Mokarramah"),
        (3, "المدينة المنورة", "Madinah", "منطقة المدينة المنورة", "Al-Madinah Al-Monawarah"),
        (4, "القصيم", "Qassim", "منطقة القصيم", "Al-Qaseem"),
        (5, "المنطقة الشرقية", "Eastern Province", "المنطقة الشرقية", "Eastern Region"),
        (6, "عسير", "Asir", "منطقة عسير", "Aseer"),
        (7, "تبوك", "Tabuk", "منطقة تبوك", "Tabouk"),
        (8, "حائل", "Hail", "منطقة حائل", "Hail"),
        (9, "الحدود الشمالية", "Northern Borders", "منطقة الحدود الشمالية", "Northern Borders"),
        (10, "جازان", "Jazan", "منطقة جازان", "Jazan"),
        (11, "نجران", "Najran", "منطقة نجران", "Najran"),
        (12, "الباحة", "Al-Baha", "منطقة الباحة", "Al-Baha"),
        (13, "الجوف", "Al-Jouf", "منطقة الجوف", "Al-Jouf"),
    ],
    columns=["region_id", "region_ar", "region_en", "charities_name", "sama_name"],
)

for name, df in [("population", population_raw), ("social security", social_raw)]:
    ids = df[["Province ID", "Province"]].drop_duplicates().merge(region_map, left_on="Province", right_on="sama_name")
    check(f"SAMA {name}: Province ID equals region_id", len(ids) == 13 and (ids["Province ID"] == ids["region_id"]).all())
for name, (found, col) in {
    "nonprofit_organizations": (charities_raw["المنطقة"], "charities_name"),
    "sama_population": (population_raw["Province"], "sama_name"),
    "gastat_saudi_population": (saudi_raw["المنطقة"], "region_ar"),
    "sama_social_security": (social_raw.loc[social_raw["Province"] != "Grand Total", "Province"], "sama_name"),
    "hies_2023": (hies_raw["region_ar"], "region_ar"),
}.items():
    check(f"Region names in {name} all map to region_map", set(found) == set(region_map[col]))

# organizations: exact duplicates only, keep truncated names (flagged)
charities = (
    charities_raw.drop_duplicates()
    .rename(columns={"رقم التسجيل": "reg_no", "اسم الجمعية": "name", "نوع الجهة": "org_type", "المنطقة": "charities_name"})
    .merge(region_map[["region_id", "charities_name"]], on="charities_name", how="left", validate="many_to_one")
)
check("Organizations: 0 exact duplicate rows removed", len(charities) == len(charities_raw))
charities["org_type"] = charities["org_type"].map({"جمعية أهلية": "association", "مؤسسة أهلية": "foundation"})
charities["name_truncated"] = charities["name"].str.endswith("…")
check("Organizations: every row has region and type", charities[["region_id", "org_type"]].notna().all().all())
charities = charities[["region_id", "org_type", "reg_no", "name", "name_truncated"]]
nb_charities = pd.read_csv(NB_CLEAN / "charities.csv", encoding="utf-8-sig")
check("Organizations equal notebook data_clean/charities.csv",
      charities.reset_index(drop=True).astype(str).equals(nb_charities.astype(str)))

charity_counts = pd.crosstab(charities["region_id"], charities["org_type"]).reset_index().rename_axis(columns=None)
charity_counts["total"] = charity_counts["association"] + charity_counts["foundation"]

# population
pop_wide = population_raw.pivot(index="Province ID", columns="Year", values="Population")
saudi_wide = saudi_raw.merge(region_map[["region_id", "region_ar"]], left_on="المنطقة", right_on="region_ar",
                             validate="one_to_one").set_index("region_id")
population = pd.DataFrame({
    "population": pop_wide[REF_YEAR].astype("int64"),
    "saudi_population": saudi_wide[str(REF_YEAR)].astype("int64"),
    "saudi_population_avg": saudi_wide[[str(y) for y in AVG_YEARS]].mean(axis=1),
}).rename_axis("region_id").reset_index()
check("Saudi population < total population in every region", (population["saudi_population"] < population["population"]).all())

# social security: Grand Total must equal the sum of regions before it is dropped
social = social_raw.rename(columns={"Province ID": "region_id", "Year": "year", "Beneficiaries": "beneficiaries"})
is_total = social["Province"] == "Grand Total"
check("Social security: Grand Total equals the sum of regions every year",
      (social[~is_total].groupby("year")["beneficiaries"].sum() == social[is_total].set_index("year")["beneficiaries"]).all())
social = (social.loc[~is_total, ["region_id", "year", "beneficiaries"]]
          .astype({"beneficiaries": "int64"}).sort_values(["region_id", "year"], ignore_index=True))
check("Social security: 234 rows = 13 regions x 18 years", len(social) == 234)
check("Social security equals notebook data_clean/social_security.csv",
      social.equals(pd.read_csv(NB_CLEAN / "social_security.csv")))

hies = (
    hies_raw.rename(columns={"share_food": "food_share"})
    .merge(region_map[["region_id", "region_ar"]], on="region_ar", validate="one_to_one")
    [["region_id", "income_median_saudi", "income_mean_saudi", "spend_mean_saudi", "food_share"]]
    .sort_values("region_id", ignore_index=True)
)

ss_wide = social.pivot(index="region_id", columns="year", values="beneficiaries")
regions = (
    region_map[["region_id", "region_ar", "region_en"]]
    .merge(population, on="region_id").merge(charity_counts, on="region_id")
    .assign(beneficiaries_2022=lambda d: d["region_id"].map(ss_wide[REF_YEAR]),
            beneficiaries_avg=lambda d: d["region_id"].map(ss_wide[AVG_YEARS].mean(axis=1)))
    .merge(hies, on="region_id")
)
check("Merged table: 13 rows, no missing values", len(regions) == 13 and regions.notna().all().all())
nb_regions = pd.read_csv(NB_CLEAN / "regions_merged.csv", encoding="utf-8-sig")
check("Merged table equals notebook data_clean/regions_merged.csv",
      np.allclose(regions.select_dtypes("number"), nb_regions[regions.select_dtypes("number").columns]))

# ---------------------------------------------------------------- 3. indicators (notebook sections 5-6)
ind = regions.drop(columns="region_ar").copy()
ind["ss_rate_2022"] = ind["beneficiaries_2022"] / ind["saudi_population"] * 100
ind["ss_rate_avg"] = ind["beneficiaries_avg"] / ind["saudi_population_avg"] * 100
ind["density_all"] = ind["total"] / ind["population"] * 1e5
ind["density_assoc"] = ind["association"] / ind["population"] * 1e5
ind["margin_saudi"] = ind["income_mean_saudi"] - ind["spend_mean_saudi"]


def zscore(s):
    return (s - s.mean()) / s.std(ddof=0)


def fragility_parts(df, ss_col):
    return pd.DataFrame({"ss_rate": zscore(df[ss_col]), "low_income": -zscore(df["income_median_saudi"]),
                         "food_share": zscore(df["food_share"])})


parts_2022 = fragility_parts(ind, "ss_rate_2022")
ind["fragility_2022"] = parts_2022.mean(axis=1)
ind["fragility_avg"] = fragility_parts(ind, "ss_rate_avg").mean(axis=1)
nb_ind = pd.read_csv(NB_OUT / "indicators.csv")
num = [c for c in nb_ind.columns if c != "region_en"]
check("Indicators equal notebook outputs/indicators.csv (all 20 numeric columns)", np.allclose(ind[num], nb_ind[num]))

# ---------------------------------------------------------------- 4. gap scores (notebook section 7)
SCENARIOS = {"A": ("fragility_2022", "density_all"), "B": ("fragility_2022", "density_assoc"),
             "C": ("fragility_avg", "density_all"), "D": ("fragility_avg", "density_assoc")}
results = ind[["region_id", "region_en"]].copy()
for name, (f, d) in SCENARIOS.items():
    gap = zscore(ind[f]) - zscore(ind[d])
    results[f"{name}_gap"] = gap
    results[f"{name}_gap_rank"] = gap.rank(ascending=False, method="min").astype(int)
results["A_frag_part"] = zscore(ind["fragility_2022"])
results["A_dens_part"] = -zscore(ind["density_all"])
results["A_source"] = np.where(results["A_frag_part"] > results["A_dens_part"], "Fragility", "Few non-profits")
results["top5_scenarios"] = (results[[f"{s}_gap_rank" for s in SCENARIOS]] <= 5).sum(axis=1)
fm, dm = ind["fragility_2022"].median(), ind["density_all"].median()
hf, ld = ind["fragility_2022"] > fm, ind["density_all"] < dm
results["A_quadrant"] = np.select(
    [hf & ld, hf & ~ld, ~hf & ld],
    ["High fragility, few organizations", "High fragility, many organizations", "Low fragility, few organizations"],
    "Low fragility, many organizations")

nb_prio = pd.read_csv(NB_OUT / "priority_results.csv", encoding="utf-8-sig").set_index("region_id")
r = results.set_index("region_id").loc[nb_prio.index]
for c in ["A_gap", "B_gap", "C_gap", "D_gap", "A_frag_part", "A_dens_part"]:
    check(f"{c} equals notebook priority_results.csv (2 dp)", np.allclose(r[c].round(2), nb_prio[c]))
for c in ["A_gap_rank", "B_gap_rank", "C_gap_rank", "D_gap_rank", "top5_scenarios"]:
    check(f"{c} equals notebook priority_results.csv", (r[c] == nb_prio[c]).all())
check("A_source equals notebook (Arabic labels translated)",
      (r["A_source"] == nb_prio["A_source"].map({"الهشاشة": "Fragility", "نقص المنظمات": "Few non-profits"})).all())

# ---------------------------------------------------------------- 5. sensitivity (notebook section 8)
BASE = {"ss_rate_2022": 1, "income_median_saudi": -1, "food_share": 1}
VARIANTS = {"base": BASE, "no_ss": {"income_median_saudi": -1, "food_share": 1},
            "no_income": {"ss_rate_2022": 1, "food_share": 1}, "no_food": {"ss_rate_2022": 1, "income_median_saudi": -1},
            "plus_margin": {**BASE, "margin_saudi": -1}}


def gap_z(df, comps, dens_col="density_all"):
    frag = pd.concat([s * zscore(df[c]) for c, s in comps.items()], axis=1).mean(axis=1)
    return zscore(frag) - zscore(df[dens_col])


def gap_ranks(df, comps, dens_col="density_all"):
    frag = pd.concat([(s * df[c]).rank(pct=True) for c, s in comps.items()], axis=1).mean(axis=1)
    return frag.rank(pct=True) - df[dens_col].rank(pct=True)


sens = pd.DataFrame({"region_id": ind["region_id"], "region": ind["region_en"]})
for name, comps in VARIANTS.items():
    sens[name] = gap_z(ind, comps).rank(ascending=False, method="min").astype(int)
sens["ranks_not_z"] = gap_ranks(ind, BASE).rank(ascending=False, method="min").astype(int)
test_cols = list(VARIANTS) + ["ranks_not_z"]
nb_sens = pd.read_csv(NB_OUT / "sensitivity_ranks.csv").set_index("region")
check("Sensitivity ranks (6 tests) equal notebook sensitivity_ranks.csv",
      (sens.set_index("region").loc[nb_sens.index, test_cols] == nb_sens[test_cols]).all().all())

# random weights (seed 42) and leave-one-out
rng = np.random.default_rng(42)
weights = rng.dirichlet(np.ones(len(BASE)), size=1000)
parts = pd.concat([s * zscore(ind[c]) for c, s in BASE.items()], axis=1)
draw_ranks = pd.concat([(zscore(parts @ w) - zscore(ind["density_all"])).rank(ascending=False, method="min")
                        for w in weights], axis=1)
loo = pd.DataFrame(index=ind.index, columns=ind.index, dtype=float)
for dropped in ind.index:
    rest = ind.drop(index=dropped)
    loo.loc[rest.index, dropped] = gap_z(rest, BASE).rank(ascending=False, method="min")
robust = pd.DataFrame({
    "region_id": ind["region_id"], "region": ind["region_en"],
    "weights_top5_pct": (draw_ranks <= 5).mean(axis=1) * 100,
    "weights_median_rank": draw_ranks.median(axis=1),
    "weights_best": draw_ranks.min(axis=1).astype(int), "weights_worst": draw_ranks.max(axis=1).astype(int),
    "loo_top5": (loo <= 5).sum(axis=1), "loo_best": loo.min(axis=1).astype(int), "loo_worst": loo.max(axis=1).astype(int),
})
nb_rob = pd.read_csv(NB_OUT / "robustness_checks.csv").set_index("region")
rc = [c for c in nb_rob.columns]
check("Random-weights and leave-one-out results equal notebook robustness_checks.csv",
      np.allclose(robust.set_index("region").loc[nb_rob.index, rc], nb_rob[rc]))

# ---------------------------------------------------------------- 6. final priority groups (notebook section 9)
sens["top5_in_n"] = (sens[test_cols] <= 5).sum(axis=1)
stable = sens["top5_in_n"] >= len(test_cols) - 1
src = results.set_index("region_id")["A_source"]
group = np.where(~stable, "Not a stable priority",
                 np.where(sens["region_id"].map(src) == "Fragility", "Fragility + few non-profits", "Mainly few non-profits"))
check("Stable priority regions = Najran, Jazan, Madinah, Tabuk, Makkah",
      set(sens.loc[stable, "region"]) == {"Najran", "Jazan", "Madinah", "Tabuk", "Makkah"})

# ---------------------------------------------------------------- 7. write star schema
TILES = {"Al-Jouf": (1, 0), "Northern Borders": (2, 0), "Tabuk": (0, 1), "Hail": (1, 1), "Qassim": (2, 1),
         "Madinah": (1, 2), "Riyadh": (2, 2), "Eastern Province": (3, 2), "Makkah": (1, 3), "Al-Baha": (2, 3),
         "Jazan": (1, 4), "Asir": (2, 4), "Najran": (3, 4)}
GROUP_ORDER = {"Fragility + few non-profits": 1, "Mainly few non-profits": 2, "Not a stable priority": 3}

dim_region = region_map[["region_id", "region_en", "region_ar"]].copy()
dim_region["tile_col"] = dim_region["region_en"].map(lambda x: TILES[x][0])
dim_region["tile_row"] = dim_region["region_en"].map(lambda x: TILES[x][1])
g = pd.Series(group, index=sens["region_id"])
dim_region["priority_group"] = dim_region["region_id"].map(g)
dim_region["priority_group_order"] = dim_region["priority_group"].map(GROUP_ORDER)
dim_region["baseline_gap_rank"] = dim_region["region_id"].map(results.set_index("region_id")["A_gap_rank"])

fact_region = regions[["region_id", "population", "saudi_population", "saudi_population_avg", "beneficiaries_2022",
                       "beneficiaries_avg", "income_median_saudi", "income_mean_saudi", "spend_mean_saudi",
                       "food_share"]].rename(columns={
    "population": "population_2022", "saudi_population": "saudi_population_2022",
    "saudi_population_avg": "saudi_population_avg_2020_2022", "beneficiaries_avg": "beneficiaries_avg_2020_2022"})

fact_population = (
    population_raw.rename(columns={"Province ID": "region_id", "Year": "year", "Population": "population"})
    [["region_id", "year", "population"]]
    .merge(saudi_wide[[str(y) for y in range(2010, 2023)]].rename(columns=int).rename_axis(columns="year")
           .stack().rename("saudi_population").reset_index(), on=["region_id", "year"], validate="one_to_one")
    .astype({"population": "int64", "saudi_population": "int64"})
    .sort_values(["region_id", "year"], ignore_index=True)
)
check("Population fact: 169 rows = 13 regions x 13 years, no gaps", len(fact_population) == 169 and fact_population.notna().all().all())

dim_org_type = pd.DataFrame({"org_type_id": [1, 2], "org_type": ["Association", "Foundation"],
                             "org_type_ar": ["جمعية أهلية", "مؤسسة أهلية"]})
fact_org = charities.copy()
fact_org.insert(0, "org_id", range(1, len(fact_org) + 1))  # reg_no is not unique, so a surrogate key
fact_org["org_type_id"] = fact_org["org_type"].map({"association": 1, "foundation": 2})
fact_org = fact_org[["org_id", "region_id", "org_type_id", "reg_no", "name", "name_truncated"]]
check("Organization counts by region equal notebook crosstab (2,723 total)",
      fact_org.groupby("region_id").size().sum() == 2723 and
      (fact_org.groupby("region_id").size().values == charity_counts["total"].values).all())

dim_year = pd.DataFrame({"year": range(2005, 2023)})
dim_year["year_start"] = pd.to_datetime(dim_year["year"].astype(str) + "-01-01").dt.date
dim_year["period"] = np.where(dim_year["year"] >= 2020, "2020-2022 averaging window", "2005-2019")
dim_year["is_transition_year"] = dim_year["year"] == 2022

dim_test = pd.DataFrame([
    (1, "base", "Base (scenario A)", "Base", "Equal-weight z-scores of the three fragility indicators"),
    (2, "no_ss", "Without social security", "No SS", "Drop the social security rate"),
    (3, "no_income", "Without income", "No income", "Drop Saudi median income"),
    (4, "no_food", "Without food share", "No food", "Drop the food share of spending"),
    (5, "plus_margin", "Plus income margin", "+ Margin", "Add income minus spending as a fourth indicator"),
    (6, "ranks_not_z", "Ranks instead of z-scores", "Ranks", "Percentile ranks replace z-scores"),
], columns=["test_id", "test_key", "test_name", "test_short", "what_changes"])
fact_sens = sens.melt(id_vars="region_id", value_vars=test_cols, var_name="test_key", value_name="gap_rank") \
    .merge(dim_test[["test_id", "test_key"]], on="test_key")[["region_id", "test_id", "gap_rank"]] \
    .sort_values(["test_id", "gap_rank"], ignore_index=True)

fact_robust = robust.drop(columns="region")

dim_scenario = pd.DataFrame([
    ("A", "A · SS 2022 · All organizations", "2022", "Associations + foundations", 1),
    ("B", "B · SS 2022 · Associations only", "2022", "Associations only", 2),
    ("C", "C · SS avg 2020-22 · All organizations", "Average 2020-2022", "Associations + foundations", 3),
    ("D", "D · SS avg 2020-22 · Associations only", "Average 2020-2022", "Associations only", 4),
], columns=["scenario", "scenario_label", "social_security_basis", "organizations_counted", "scenario_order"])

tables = {
    "dim_region": dim_region, "dim_year": dim_year, "dim_org_type": dim_org_type,
    "dim_sensitivity_test": dim_test, "dim_scenario": dim_scenario,
    "fact_region_snapshot": fact_region, "fact_population": fact_population,
    "fact_social_security": social, "fact_organizations": fact_org,
    "fact_sensitivity_rank": fact_sens, "fact_robustness": fact_robust,
}
for name, df in tables.items():
    df.to_csv(OUT / f"{name}.csv", index=False, encoding="utf-8-sig")

with pd.ExcelWriter(OUT / "RegionalPriorities_ModelData.xlsx", engine="openpyxl") as xw:
    for name, df in tables.items():
        df.to_excel(xw, sheet_name=name[:31], index=False)

# expected values for the DAX validation (written at full precision)
expected = ind[["region_id", "region_en", "population", "saudi_population", "association", "foundation", "total",
                "beneficiaries_2022", "income_median_saudi", "food_share", "ss_rate_2022", "ss_rate_avg",
                "density_all", "density_assoc", "fragility_2022", "fragility_avg"]].merge(
    results.drop(columns="region_en"), on="region_id")
expected.to_csv(REF / "notebook_expected_region_values.csv", index=False, encoding="utf-8-sig")

rates = ss_wide[AVG_YEARS] / saudi_wide[[str(y) for y in AVG_YEARS]].set_axis(AVG_YEARS, axis=1) * 100
stats = pd.DataFrame([
    ("spearman_orgs_vs_population", regions["total"].corr(regions["population"], method="spearman")),
    ("spearman_income_vs_food_share", hies["income_median_saudi"].corr(hies["food_share"], method="spearman")),
    ("spearman_ss_rate_2020_vs_2022", rates[2020].corr(rates[2022], method="spearman")),
    ("spearman_ss_rate_2021_vs_2022", rates[2021].corr(rates[2022], method="spearman")),
    ("spearman_fragility_2022_vs_avg", ind["fragility_2022"].corr(ind["fragility_avg"], method="spearman")),
    ("national_beneficiaries_2021", social.query("year == 2021")["beneficiaries"].sum()),
    ("national_beneficiaries_2022", social.query("year == 2022")["beneficiaries"].sum()),
    ("total_organizations", len(fact_org)),
    ("total_population_2022", regions["population"].sum()),
    ("riyadh_share_of_orgs_pct", 798 / 2723 * 100),
    ("riyadh_share_of_foundations_pct", 164 / charity_counts["foundation"].sum() * 100),
    ("median_fragility_2022", fm), ("median_density_all", dm),
], columns=["statistic", "notebook_value"])
stats.to_csv(REF / "notebook_expected_statistics.csv", index=False)
pd.DataFrame(checks, columns=["check", "result"]).to_csv(REF / "pipeline_checks.csv", index=False)

for name, df in tables.items():
    print(f"{name:24s} {len(df):5d} rows  {df.shape[1]:2d} cols")
print(f"\n{len(checks)} pipeline checks passed. Statistics:\n{stats.to_string(index=False)}")
