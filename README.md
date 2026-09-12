# Administrative Burden at the Ballot Box

**Status: Week 1 in progress.** No estimate exists yet — this README will be
rewritten with the question, finding, and method once Week 4 is done. See
`PROJECT_PLAN.md` for the full plan and `Project_Handoff_Ballot_Rejection_Analysis.md`
for the original project brief.

## Research question

Do state-level mail voting policies — signature cure procedures, witness or
notarization requirements, drop box availability, no-excuse absentee
eligibility — predict jurisdiction-level mail ballot rejection rates, and
does any effect differ between large urban jurisdictions and small rural
ones?

## Data

Election Administration and Voting Survey (EAVS), U.S. Election Assistance
Commission, 2016–2024 (5 waves). Public, no authentication required. See
`codebooks/eavs_variable_crosswalk.md` for the full variable mapping and
`codebooks/variable_memo.md` for the one-page summary.

## Setup

```bash
# Python (data acquisition, cleaning, panel construction, choropleth)
python3 -m pip install -r requirements.txt

# R (estimation — Week 4)
Rscript -e 'install.packages(c("fixest","did","didimputation"))'
Rscript -e 'install.packages("fwildclusterboot", repos=c("https://s3alfisc.r-universe.dev","https://cloud.r-project.org"))'
```

## Reproduce the panel so far

```bash
python src/01_download.py       # fetch all 5 waves + codebooks -> data/raw/
python src/02_build_crosswalk.py  # derive + verify the variable crosswalk -> codebooks/crosswalk.yaml
```

## Repository structure

```
├── data/
│   ├── raw/          # untouched downloads (gitignored)
│   ├── interim/       # per-wave cleaned files (gitignored)
│   └── processed/     # final panel.parquet + panel.csv (committed)
├── codebooks/
│   ├── eavs_variable_crosswalk.md   # wave-by-wave variable mapping, verified
│   ├── crosswalk.yaml               # machine-readable version of the above
│   ├── variable_memo.md             # one-page pre-analysis memo
│   └── policy_coding_sheet.md       # treatment coding (Week 3)
├── src/
│   ├── 01_download.py
│   ├── 02_build_crosswalk.py
│   ├── 03_clean_eavs.py
│   ├── 04_merge_controls.py
│   ├── 05_build_panel.py
│   ├── 06_estimate.R
│   └── 07_figures.py
├── output/{figures,tables}/
└── writeup/
```
