"""
Step 4: compares the values computed by the live Power BI model (DAX results exported by
pbi_dax.ps1) with the notebook outputs, and writes 04_docs/10_Validation_Report.md.

    .venv\\Scripts\\python powerbi_project\\01_scripts\\compare_results.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parent
V = PROJECT / "04_docs" / "validation"
R = V / "dax_results"
TOL = 1e-9

exp = pd.read_csv(V / "notebook_expected_region_values.csv", encoding="utf-8-sig").set_index("region_id")
sens = pd.read_csv(ROOT / "outputs" / "sensitivity_ranks.csv").set_index("region")
rob = pd.read_csv(ROOT / "outputs" / "robustness_checks.csv").set_index("region")
stats = pd.read_csv(V / "notebook_expected_statistics.csv").set_index("statistic")["notebook_value"]
social = pd.read_csv(ROOT / "data_clean" / "social_security.csv")

rows = []  # area, check, n compared, max abs diff, result


def cmp(area, name, dax, nb, numeric=True):
    dax, nb = pd.Series(dax).sort_index(), pd.Series(nb).sort_index()
    assert len(dax) == len(nb), (name, len(dax), len(nb))
    if numeric:
        d = float(np.max(np.abs(dax.astype(float).values - nb.astype(float).values)))
        ok = d <= TOL * max(1, float(np.max(np.abs(nb.astype(float).values))))
        rows.append((area, name, len(nb), f"{d:.2e}", "PASS" if ok else "FAIL"))
    else:
        ok = (dax.astype(str).values == nb.astype(str).values).all()
        rows.append((area, name, len(nb), "exact match" if ok else "mismatch", "PASS" if ok else "FAIL"))


def load(name):
    return pd.read_csv(R / f"{name}.csv", encoding="utf-8").set_index("region_id")


A = load("regions_A")
for col, scale in [("population", 1), ("saudi_population", 1), ("association", 1), ("foundation", 1), ("total", 1),
                   ("beneficiaries_2022", 1), ("income_median_saudi", 1), ("food_share", 1), ("ss_rate_2022", 100),
                   ("ss_rate_avg", 100), ("density_all", 1), ("density_assoc", 1)]:
    cmp("Base & indicators", f"{col} (13 regions)", A[col] * scale, exp[col])
cmp("Fragility", "Fragility index, SS 2022 (fragility_2022)", A["fragility"], exp["fragility_2022"])
cmp("Fragility", "Fragility index, SS avg 2020-22 (fragility_avg)", load("regions_C")["fragility"], exp["fragility_avg"])
for sc in "ABCD":
    d = load(f"regions_{sc}")
    cmp("Gap & priority", f"Scenario {sc}: gap score", d["gap"], exp[f"{sc}_gap"])
    cmp("Gap & priority", f"Scenario {sc}: gap rank", d["gap_rank"], exp[f"{sc}_gap_rank"])
cmp("Gap & priority", "Scenario A: fragility part", A["frag_part"], exp["A_frag_part"])
cmp("Gap & priority", "Scenario A: few non-profits part", A["dens_part"], exp["A_dens_part"])
cmp("Gap & priority", "Scenario A: gap source", A["source"], exp["A_source"], numeric=False)
cmp("Gap & priority", "Scenario A: quadrant", A["quadrant"], exp["A_quadrant"], numeric=False)
cmp("Gap & priority", "Scenarios A-D in top 5", A["scenarios_top5"].fillna(0), exp["top5_scenarios"])

for t in ["no_ss", "no_income", "no_food"]:
    d = pd.read_csv(R / f"weights_{t}.csv").set_index("region_en")
    cmp("What-if weights", f"Weight = 0 reproduces notebook test '{t}' ranks", d["gap_rank"], sens.loc[d.index, t])

rb = pd.read_csv(R / "robustness.csv").set_index("region_en")
cmp("Robustness", "Tests in top 5 (of 6)", rb["tests_top5"], sens.loc[rb.index, "top5_in_n"])
cmp("Robustness", "Best rank across tests", rb["best"], sens.loc[rb.index, "best"])
cmp("Robustness", "Worst rank across tests", rb["worst"], sens.loc[rb.index, "worst"])
cmp("Robustness", "Random weights: % in top 5", rb["weights_top5_pct"] * 100, rob.loc[rb.index, "weights_top5_pct"])
cmp("Robustness", "Leave-one-out: times in top 5", rb["loo_top5"], rob.loc[rb.index, "loo_top5"])
cmp("Robustness", "Leave-one-out: worst rank", rb["loo_worst"], rob.loc[rb.index, "loo_worst"])

st = pd.read_csv(R / "statistics.csv").iloc[0]
for k in stats.index:
    cmp("Statistics", k, pd.Series([st[k]]), pd.Series([stats[k]]))

tr = pd.read_csv(R / "trend.csv").set_index("year")
cmp("Trends", "National beneficiaries per year 2005-2022", tr["beneficiaries"], social.groupby("year")["beneficiaries"].sum())
wide = social.pivot(index="region_id", columns="year", values="beneficiaries")
ch = load("region_change")
cmp("Trends", "Change 2021 -> 2022 by region", ch["change_21_22"], wide[2022] / wide[2021] - 1)
cmp("Trends", "Index 2022 (2020 = 100) by region", ch["index_2022"], wide[2022] / wide[2020] * 100)

kp = pd.read_csv(R / "text_kpis.csv").iloc[0]
for name, got, want in [
    ("Top priority region", kp["Top Priority Region"], "Najran"),
    ("Top 5 regions", kp["Top 5 Regions"], "Najran, Jazan, Madinah, Tabuk, Makkah"),
    ("Stable priority regions", kp["Stable Priority List"], "Najran, Jazan, Madinah, Tabuk, Makkah"),
    ("Least stable priority (random weights)", kp["Least Stable Priority"], "Jazan · 72.9%"),
    ("Regions without foundations", str(kp["Regions Without Foundations"]), "5"),
    ("Lowest income region", kp["Lowest Income Region"], "Najran · SAR 1,650"),
    ("Highest food share region", kp["Highest Food Share Region"], "Najran · 43.5%"),
    ("Peak year of beneficiaries", str(kp["Peak Year"]), "2021"),
    ("Largest / smallest population (x)", f"{kp['Largest to Smallest Population']:.0f}", "25"),
]:
    rows.append(("Headline KPIs", name, 1, f"'{got}'", "PASS" if got == want else "FAIL"))

res = pd.DataFrame(rows, columns=["Area", "Check", "Values compared", "Max abs. difference / result", "Result"])
pipe = pd.read_csv(V / "pipeline_checks.csv")
n_vals = int(res["Values compared"].sum())
status = "ALL PASS" if (res["Result"] == "PASS").all() and (pipe["result"] == "PASS").all() else "FAILURES FOUND"

md = [
    "# Validation Report", "",
    f"**Status: {status}** · {len(pipe)} pipeline checks + {len(res)} model checks covering {n_vals:,} individual values.", "",
    "Two independent layers were checked:", "",
    "1. **Pipeline (Python):** `build_model_data.py` re-runs the notebook's cleaning, indicator, scenario, sensitivity, "
    "random-weights (seed 42) and leave-one-out code from `data_raw/` and asserts that every result equals the notebook's own "
    "files in `data_clean/` and `outputs/`.",
    "2. **Model (DAX):** the report was opened in Power BI Desktop, refreshed, and `pbi_dax.ps1` ran "
    "`validation_queries.dax` against the live model. `compare_results.py` compares each DAX value with the notebook value. "
    f"Floating-point tolerance: {TOL:g} (relative).", "",
    "## 1. Pipeline checks (Python vs. notebook files)", "",
    "| Check | Result |", "|---|---|", *[f"| {c} | {r} |" for c, r in pipe.itertuples(index=False)], "",
    "## 2. Model checks (DAX in Power BI vs. notebook)", "",
    "| Area | Check | Values | Max abs. diff / result | Result |", "|---|---|---:|---|---|",
    *[f"| {a} | {c} | {n} | {d} | {r} |" for a, c, n, d, r in res.itertuples(index=False)], "",
    "## Notes", "",
    "- Differences of ~1e-15 are floating-point rounding between NumPy and the VertiPaq engine.",
    "- Ranks use `RANKX(..., SKIP)`, which equals pandas `rank(method='min')`; z-scores use `STDEVX.P`, which equals pandas `std(ddof=0)`.",
    "- Spearman correlations are implemented in DAX with average ranks for ties (Al-Jouf and Tabuk both have 73 organizations), "
    "the same convention as pandas.",
    "- Setting one what-if weight to 0 drops that indicator from the fragility index; the resulting ranks equal the notebook's "
    "'without social security / income / food share' sensitivity tests, which validates the weighting logic.",
    "- Raw DAX outputs are in `validation/dax_results/`; the expected values are in `validation/notebook_expected_*.csv`.", "",
    "## How to re-run", "", "```powershell",
    "# 1. rebuild data and model files",
    ".venv\\Scripts\\python powerbi_project\\01_scripts\\build_model_data.py",
    "# 2. open powerbi_project\\03_powerbi\\RegionalPriorities.pbip in Power BI Desktop, then:",
    "powershell -File powerbi_project\\01_scripts\\pbi_dax.ps1 -Refresh -QueryFile powerbi_project\\01_scripts\\validation_queries.dax -OutDir powerbi_project\\04_docs\\validation\\dax_results",
    ".venv\\Scripts\\python powerbi_project\\01_scripts\\compare_results.py", "```", ""]
(PROJECT / "04_docs" / "10_Validation_Report.md").write_text("\n".join(md), encoding="utf-8")
print(res.to_string(index=False))
print(status, n_vals)
