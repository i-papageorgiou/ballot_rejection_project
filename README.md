# Administrative Burden at the Ballot Box

## What this project is about

When you vote by mail, your ballot can get rejected — not counted — for
reasons that have nothing to do with who you voted for. A signature on the
envelope that doesn't quite match the one on file. A missing witness
signature. A ballot that arrived a day late. States differ a lot in how
they handle this: some let voters fix ("cure") a signature problem before
their ballot is thrown out, some require a witness or notary to sign the
envelope, some make it easy to request an absentee ballot and some don't.

This project asks a simple question: **do these state-level rules actually
change how many mail ballots get rejected** — and does the answer depend
on whether you're in a big city or a small rural county, where election
offices have very different staff and resources?

To find out, we used a U.S. government survey that every state and county
election office fills out (the EAVS survey, 2016–2024) and compared places
that changed their mail-voting rules over that period to places that
didn't, looking at what happened to rejection rates before and after each
change.

**What we've found so far:** across several different statistical methods,
there's no clear, reliable effect of these policies on rejection rates —
a "null result." That's a genuinely useful finding — it suggests some
popular policy levers, on both sides of the debate, may not move the
needle the way people assume — but there are a couple of open data
questions that could still change the picture (see the status note just
below before citing any number from this project).

**Explore the results yourself, no coding required:**
[live interactive dashboard](https://i-papageorgiou.github.io/ballot_rejection_project/)
— browse rejection rates by state and county and see how they've moved
over time. (Everything from here down in this README is for people
running or extending the underlying analysis code.)

**Status: Phases 1–5 done.** TWFE, Sun-Abraham, and Callaway-Sant'Anna all
agree on a clean null effect (see `PROJECT_PLAN.md`'s Phase 4 section for
the two diagnosed-but-unresolved caveats worth reading before citing any
number).

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

R (estimation — Phase 4): `fixest`, `did`, `didimputation`, `fwildclusterboot`,
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
Rscript src/06_estimate.R          # TWFE, Sun-Abraham, Callaway-Sant'Anna, bootstrap, heterogeneity, robustness (~25-30 min) -> output/tables/{estimates_v1,heterogeneity,robustness_checklist}.md, docs/data/*.json
python src/07_figures.py          # panel-derived dashboard data -> docs/data/{state_distribution,county_choropleth}.json
```

Python steps above need `pandas`/`pyarrow`; this repo was built and
verified against the anaconda distribution's `python3`, not the system
one — if `import pyarrow` fails, check which `python3` is on `PATH`.

All of the above, chained: `bash run_all.sh` (set `PYTHON=/path/to/python3`
first if the anaconda interpreter isn't the first `python3` on `PATH`).

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
│   └── policy_coding_sheet.md       # treatment coding (Phase 3)
├── src/
│   ├── 01_download.py
│   ├── 02_build_crosswalk.py
│   ├── 03_clean_eavs.py
│   ├── 04_build_treatment.py   # 51-state treatment coding -> treatment.csv
│   ├── 05_build_panel.py       # stack panel + join treatment
│   ├── 06_estimate.R           # TWFE, Sun-Abraham, Callaway-Sant'Anna + bootstrap/heterogeneity/robustness
│   └── 07_figures.py           # panel-derived dashboard data (docs/data/)
├── output/{figures,tables}/
├── docs/
│   └── data/           # JSON written by 06_estimate.R + 07_figures.py — the pipeline's
│                       # own record of these results; index.html doesn't fetch it at
│                       # runtime (see note below)
├── tests/            # pytest suite validating crosswalk.yaml + data/interim/, independent of 03_clean_eavs.py's own gate
├── writeup/
├── index.html          # Phase 5 dashboard — GitHub Pages serves the repo root; self-contained
│                       # (inline CSS, data baked into a DATA/TILES/CHOROPLETH_PATHS blob)
└── chart.js            # all render logic for index.html; no charting library, no CDN dep
```

**Note on `index.html`'s data:** it doesn't fetch `docs/data/*.json` at runtime — the same
numbers (plus per-state series, county choropleth paths, and a few other figures not yet
in `docs/data/`) are baked directly into the page as a `DATA` constant. There's currently no
committed script that regenerates that blob from the pipeline's output automatically, so if
`06_estimate.R` or `07_figures.py` are rerun with materially different numbers, `index.html`
needs to be regenerated by hand to match.
