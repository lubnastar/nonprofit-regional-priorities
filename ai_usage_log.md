# AI Usage Log

**Tool:** Claude Code (Anthropic), used inside VS Code.

**Division of work:** I defined the questions, raised the methodological problems, supplied missing data, made every decision, and reviewed and rewrote the text. The AI wrote most of the code and first drafts, explained methods, proposed options for my problems, and ran checks.

**My rule for the AI:** no number in any text unless it comes from a cell output.

**What the AI could see:** Claude Code ran on my computer and read the whole project folder: the raw data files, the notebook, and the reports. All data are public official sources (see the README). The project contains no personal or confidential data.

**How the code was checked:**
- The notebook stops on errors instead of continuing silently: region IDs and names are checked across all five files, the social-security `Grand Total` row is checked against the sum of the regions, and every merged table is checked for missing values and row counts.
- The survey tables extracted from the Excel file were checked value by value against the source, and the notebook now extracts them itself, so the extraction is reproducible.
- I read the code line by line.
- I did not accept a step before the AI explained it. I questioned the methods behind the code, and that is how the wrong social-security denominator and the hard median threshold were caught (see "Errors caught").
- The notebook is run from the first cell to the last with no errors, and a re-run reproduces the same result tables (random weights use a fixed seed).

| Phase | My role | AI role |
|------|---------|---------|
| Data inventory and preparation | Rejected the first survey extraction (stacked tables) and asked for one row per region | Inspected the raw files read-only; extracted the tables and verified all 286 values against the Excel |
| Analysis plan | Set the decision and analytical questions and the open decisions: Saudi columns only, both social-security years and both organization types as scenarios | Proposed the notebook structure and cleaning plan |
| Method | Asked for step-by-step explanations before accepting each step | Built the indicators, the composite fragility index and the gap score |
| Methodological review | Raised the problems: uncertainty, two conflicting priority definitions, Saudi vs. total population, equal weights, double weighting, median thresholds, mixed years. Brought external review notes. Chose the solutions | Assessed each problem and proposed options; implemented the chosen ones (Saudi denominator, random-weights and leave-one-region-out tests, gap split into two sources) |
| External data | Found and supplied the Saudi population file; confirmed that social-security beneficiaries are counted as individuals; asked for 2023 regional data | Matched the file to the GASTAT 2022 census; searched for 2023 data (none found, stated as a limitation) |
| Notebook text | Rewrote the text for clarity; removed filler and questions that did not fit; spotted statements that answered problems never raised; shortened section titles; chose what to collapse | Checked every number and claim in my rewrites against the outputs before applying them |
| Reports | Set the audience (hackathon judges) and length; rejected a title that stated the result; restructured and edited the Arabic report | Drafted the reports from the outputs; reviewed the exported pages and fixed right-to-left layout issues |

## Errors caught

- **Social-security denominator:** beneficiaries were divided by the total population. I raised that they should be divided by Saudis only, and supplied the data. Fixing it changed the result: Makkah entered the priority list.
- **Hard threshold:** splitting regions at a median or average line separated near-identical regions (Madinah and Tabuk). I raised it; it was replaced by comparing the two parts of the gap.
- **Overstated text:** Najran was described as first in all tests (it is first or second under random weights), and year stability was computed on counts instead of rates. Both came from the review notes I brought.
- **Errors in the AI's own output:** a wrong Excel sheet count (42 instead of 41), and a sentence claiming one correlation was "not stronger than any other pair" when it was stronger than one pair.
