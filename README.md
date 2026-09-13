# Administrative Burden at the Ballot Box

**Status: Weeks 1–3 done; Week 4 part 1 (treatment-panel join + first-cut
TWFE/Sun-Abraham estimates) done; Week 4 part 2 (bootstrap SEs,
heterogeneity, robustness checklist) and Week 5 (dashboard) not started.**
A first, preliminary estimate exists (`output/tables/estimates_v1.md`) but
is not yet robustness-checked — see `PROJECT_PLAN.md`'s Week 4 section
before citing it. The project's primary deliverable is still an
interactive web dashboard (not a static writeup — see `PROJECT_PLAN.md`'s
Week 5). **Picking this project up? Start with `HANDOFF.md`** — it has the
reading order, verified facts, and next steps. See `PROJECT_PLAN.md` for
the full week-by-week plan and `Project_Handoff_Ballot_Rejection_Analysis.md`
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
```

R (estimation — Week 4): `fixest`, `did`, `didimputation`, `fwildclusterboot`,
`data.table`, `ggplot2`, `modelsummary`, `broom` are already installed and
verified to load on this machine. If setting up fresh elsewhere:

```bash
Rscript -e 'install.packages(c("fixest","did","didimputation"))'
Rscript -e 'install.packages("fwildclusterboot", repos=c("https://s3alfisc.r-universe.dev","https://cloud.r-project.org"))'
```

## Reproduce the panel so far

```bash
python src/01_download.py       # fetch all 5 waves + codebooks -> data/raw/
python src/02_build_crosswalk.py  # derive + verify the variable crosswalk -> codebooks/crosswalk.yaml
python src/03_clean_eavs.py       # clean + validate each wave -> data/interim/, output/tables/validation_report.md
pytest tests/                     # independent validation suite over crosswalk.yaml + data/interim/
python src/04_build_treatment.py  # code the 51-state treatment variable -> data/processed/treatment.csv
python src/05_build_panel.py      # stack into the panel + join treatment -> data/processed/panel.{parquet,csv}, output/tables/missingness_report.md
Rscript src/06_estimate.R          # first-cut TWFE vs. Sun-Abraham estimates -> output/tables/estimates_v1.md
```

Python steps above need `pandas`/`pyarrow`; this repo was built and
verified against the anaconda distribution's `python3`, not the system
one — if `import pyarrow` fails, check which `python3` is on `PATH`.

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
│   ├── 04_build_treatment.py   # 51-state treatment coding -> treatment.csv
│   ├── 05_build_panel.py       # stack panel + join treatment
│   ├── 06_estimate.R           # TWFE vs. Sun-Abraham, first cut
│   └── 07_figures.py           # not yet written (Week 5)
├── output/{figures,tables}/
├── tests/            # pytest suite validating crosswalk.yaml + data/interim/, independent of 03_clean_eavs.py's own gate
└── writeup/
```
