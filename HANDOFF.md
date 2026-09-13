# Project Handoff

**This is the outbound handoff** — written for whoever picks this project
up next, human or AI. Don't confuse it with
`Project_Handoff_Ballot_Rejection_Analysis.md`, which is the *inbound*
brief that started the project five weeks ago. That file is now historical
context; this one is current state and next steps.

## Orient in 60 seconds

**Question**: Do state-level mail-ballot signature-cure laws reduce
jurisdiction-level mail ballot rejection rates, and does the effect differ
by jurisdiction size? Staggered difference-in-differences, EAVS
administrative data, 2016–2024.

**Status**: Weeks 1–3 done (data pipeline, panel, treatment coding, three
rounds of independent validation). Week 4 part 1 is now also done: the
treatment coding is joined to the panel (`src/04_build_treatment.py` +
an update to `src/05_build_panel.py`), and a first-cut estimation script
(`src/06_estimate.R`) produces a preliminary TWFE-vs-Sun-Abraham
comparison (`output/tables/estimates_v1.md`). **This is a first cut, not
a robustness-checked result** — no wild-cluster bootstrap, no
heterogeneity, none of the robustness checklist yet (see "Next steps"
below, which is now shorter than it was). Week 5 (an interactive
dashboard — the deliverable changed from a static writeup partway
through; see `PROJECT_PLAN.md`) is further out.

**Read in this order**:
1. `PROJECT_PLAN.md` — the living plan; every week's section was updated
   as work happened, so it's the most current narrative account of what
   was done and found, including things that turned out to be wrong and
   got corrected.
2. `codebooks/policy_coding_sheet.md` — the treatment variable, all 51
   states, one row each.
3. `codebooks/policy_coding_validation.md` — **read this before trusting
   anything in the coding sheet**. Three validation passes, 7 confirmed
   errors found and fixed, and an explicit list of what's still weak.
   Skip to "Final disposition" (near the end) for the one table that
   matters most.

## What exists and is trustworthy

Pipeline, in order:

```bash
python src/01_download.py         # fetch 5 EAVS waves + codebooks -> data/raw/
python src/02_build_crosswalk.py  # derive variable crosswalk -> codebooks/crosswalk.yaml
python src/03_clean_eavs.py       # clean + validate each wave -> data/interim/, output/tables/validation_report.md
pytest tests/                     # independent check on the above, from outside the pipeline's own gate
python src/04_build_treatment.py  # code the 51-state treatment variable -> data/processed/treatment.csv
python src/05_build_panel.py      # stack into panel + join treatment -> data/processed/panel.{parquet,csv}, output/tables/missingness_report.md
Rscript src/06_estimate.R          # first-cut TWFE vs. Sun-Abraham estimates -> output/tables/estimates_v1.md
```

Note: the Python steps need `pyarrow`; this project was built and
verified against the anaconda distribution's `python3`, not whatever
`python3` is first on `PATH` — check that if `import pyarrow` fails.

(ACS controls were deliberately deferred, no `04_merge_controls.py` was
ever built — `04` went to the treatment coding instead; see Caveats
below. `07_figures.py` is still unwritten — Week 5.)

**First-cut estimates already exist** (`output/tables/estimates_v1.md`):
naive TWFE gives an imprecise near-null (-0.0014, SE 0.0026, p=0.59);
Sun-Abraham's aggregated ATT is positive and marginally significant
(+0.0037, SE 0.0018, p=0.051) — the corrected estimator flips the sign
relative to naive TWFE, which is exactly the divergence this design
exists to surface. **Do not treat this as a finding yet** — no
wild-cluster bootstrap, no robustness checks, no heterogeneity. See
`06_estimate.R`'s own `TODO` block and "Next steps" below for exactly
what's still missing before this is citable.

Verified facts, so nobody has to re-derive them:
- All five national rejected-ballot totals reproduce **exactly**:
  2016: 318,728 · 2018: 430,196 · 2020: 560,826 · 2022: 549,824 ·
  2024: 584,463.
- `data/processed/panel.parquet`: **32,305 jurisdiction-years**, 94.8%
  usable (30,621 rows), **6,447 FIPS present in all 5 waves**.
- Median rejection rate by wave (usable rows): 0.37 / 0.67 / 0.25 / 0.47 /
  0.39% for 2016–2024 — the 2020 dip is a real, visible feature, not
  noise.
- `pytest tests/` (51 cases) is the fast regression check — run it after
  touching anything in `src/`.

## The three EAVS traps (the reason Weeks 1–2 took real care)

Full detail in `codebooks/variable_memo.md`; the short version, because
these silently produce plausible-but-wrong numbers rather than errors:

1. **2016 renumbers the outcome.** `C4b` is *rejected total* in 2016;
   `C4a` is *counted*. Every other wave has it the other way. Grabbing
   `C4a` uniformly gives a ~100% rejection rate for 2016 that looks
   plausible enough to survive a casual review.
2. **2016 encodes sentinels as text** (`'-888888: Not Applicable'`), not
   the numeric `-88`/`-99` every later wave uses. Read every wave as
   `dtype=str` first, coerce with `pd.to_numeric(errors="coerce")`, *then*
   `.mask(v < 0)` — that order handles both schemes in one pass.
3. **2016 is cp1252-encoded**, not UTF-8; all waves parse cleanly as
   `latin-1`.

Also: the rejection-reason column range is wave-specific and not a simple
offset from the total column (2016: `C5a`–`C5v`; 2018/2020: `C4b`–`C4r`;
2022/2024: `C9b`–`C9t`) — derived from the codebooks' own labels in
`src/02_build_crosswalk.py`, not hand-typed.

## The treatment variable — what it actually looks like

All 51 states + DC coded in `codebooks/policy_coding_sheet.md`, one row
each, with a `first_treated_wave`, `mechanism`, `confidence`, and sourced
`adoption_event` per row. The shape that matters for identification:

- **19 in-panel switchers** (the source of identifying variation):
  - **2018**: CA, RI
  - **2020**: HI, KS, MS, NV, NJ, NY, UT, VA
  - **2022**: IN, KY, LA, ME, ND, TX
  - **2024**: DC, MD, MI
- **13 always-treated** (cure law predates 2016 — Callaway–Sant'Anna will
  drop these as "already treated," but they're not useless: still usable
  in the naive TWFE comparison, and as a sanity check): AZ, CO, FL, GA,
  IL, MA, MN, MT, NM, OH, OR, VT, WA
- **17 never-treated controls**: AK, AL, AR, CT, ID, IA, MO, NE, NH, NC,
  OK, SC, SD, TN, WV, WI, WY
- **2 special cases, not simple values**: DE (adoption falls right at or
  past the 2024 panel edge — treat as outside panel), PA (no statewide
  law; county-optional, needs a state-vs-jurisdiction-level design
  decision before it enters anything)

**This is a usable staggered-adoption design** — four real cohorts, a
meaningful control group, adoption timing that clusters around 2020 (the
pandemic) but isn't all-at-once. That was the open viability question
going into Week 3; it's answered.

**The treatment coding is now joined to the panel.** `src/04_build_treatment.py`
transcribes the coding sheet into `data/processed/treatment.csv`
(51 units x 5 waves), and `src/05_build_panel.py` left-joins it onto
`panel.parquet`/`panel.csv` by `(state_abbr, year)`, asserting a 100%
match for every state + DC. Two non-step-function rows got explicit
handling rather than a single scalar:
- **Iowa** — a per-wave dict (`{2016:0, 2018:1, 2020:0, 2022:0, 2024:0}`),
  not a `first_treated_wave` value, exactly the treatment-reversal
  handling this doc flagged as easy to get wrong.
- **North Carolina** — primary `treated` stays `0` in every wave
  (statutory-only definition); a separate `sensitivity_treated` column
  is `1` from 2020 (the litigation/consent-decree mechanism), for a
  robustness check that wants to include non-statutory regimes.

**Pennsylvania** is coded `treated=0` (no statewide law) with a
`pa_partial=True` flag column — a documented approximation, not a
resolved fact; a future jurisdiction-level covariate could override it
without re-deriving the join.

**5 EAVS territories** (AS, GU, MP, PR, VI) are in the panel but out of
scope for this treatment variable — `in_scope=False`,
`treated`/`sensitivity_treated` left null rather than fabricated. Filter
on `in_scope == True` before running anything treatment-related (already
done in `06_estimate.R`).

## Caveats that must survive the handoff — read before using any of these rows

Carried forward from `policy_coding_validation.md` so they aren't
silently lost by whoever reads the coding sheet without the validation
report:

- **Iowa is a treatment *reversal*, not a simple switch.** Its 2017
  signature-verification law was judicially enjoined starting Sept. 2019
  and, per multiple 2026 sources, the injunction still holds. Coded:
  treated for the **2018 wave only**, untreated 2020/2022/2024. This
  needs a **time-varying indicator per wave** in whatever code builds the
  treatment panel — a single `first_treated_wave` scalar will miscode Iowa
  no matter what value is chosen. This is easy to get wrong by copying
  the pattern used for every other state.
- **Illinois and Massachusetts**: the cure right itself is confirmed real
  (direct statutory "shall notify" language for both), but the adoption
  *year* is genuinely unknown after 8+ and 5+ independent research
  attempts respectively, across three validation passes, using every
  method this project had available (search, direct fetch, adversarial
  re-search). The sheet marks these `pre-2016 (inferred)` as a best
  guess — **treat their timing as censored/unknown in the event-study
  window, not as a confirmed pre-2016 date**, unless someone finds the
  actual enactment year through a channel this project didn't have access
  to (e.g., a state legislative archive database).
- **Ohio and Montana** are the two weakest-supported rows in the entire
  table — original coding rests on a single source each, and a dedicated
  re-check attempt in the validation passes found nothing more. Not known
  to be wrong, just less scrutinized than everything else.
- **North Carolina** is deliberately coded `No` on the primary
  (statutory-only) treatment variable — its cure process came from
  litigation (a consent decree), not a statute. A `mechanism=litigation`
  sensitivity variable is available in the same row if a robustness check
  wants to include non-statutory regimes.
- **Pennsylvania** was deliberately left without a single
  `first_treated_wave` — no statewide law exists; cure is optional
  county-by-county. Decide state-level `Partial` vs. a jurisdiction-level
  covariate before Week 4 uses this row; don't default it.
- **ACS controls were deferred, on purpose** — no Census API key
  obtained, and jurisdiction fixed effects absorb time-invariant
  covariates anyway. This mainly costs the urban/rural heterogeneity
  split from the original design; a static rural/urban classification
  (not requiring live ACS data) could substitute if that interaction is
  still wanted.
- **The coding sheet will go stale.** 400+ election-related bills were
  enacted in just the first seven months of 2026 (a finding from the
  validation passes, not a hypothetical). If picking this up more than a
  few months after Sept. 2026, re-run at least the adversarial "never
  treated" check from `policy_coding_validation.md`'s Pass 2 before
  trusting the control group.

## Next steps, in order

1. ~~Build the treatment-panel join.~~ **Done** — `src/04_build_treatment.py`
   + the updated `src/05_build_panel.py`. Iowa is handled as a
   time-varying per-wave column, not a scalar.
2. ~~First-cut `src/06_estimate.R`~~ **Done, but incomplete** — naive TWFE
   and `fixest::sunab()` run side by side (Iowa excluded from the `sunab`
   sample only, since a single reversal doesn't fit its single-cohort
   assumption). Not yet done, and the actual next task:
   - **`fwildclusterboot`** wild-cluster bootstrap — only ~50 effective
     (state) clusters, and the current SEs are the default
     cluster-robust ones, not bootstrapped.
   - **Callaway–Sant'Anna via the `did` package**, as a second corrected
     estimator alongside `sunab()`, with the TWFE-vs-corrected gap
     explained — this comparison is the actual point of the design.
3. **Heterogeneity**: interact treatment with log(ballots returned) and
   an urban/rural classification (see ACS caveat above for how to get the
   latter without live Census data).
4. **Robustness checklist** (already specified in `PROJECT_PLAN.md`'s
   Week 4 section): drop 2020; drop WI/MI (municipality/township-level
   reporting, thousands of small jurisdictions); winsorize at p99; weight
   by ballots returned; fractional logit vs. linear.
5. **Week 5 — dashboard**, once the estimate is robustness-checked: event
   study, coefficient plot, rejection-rate distribution by state, county
   choropleth (`geopandas`, already working in this environment). The
   deliverable is an interactive dashboard, not a static writeup — see
   `PROJECT_PLAN.md`'s Week 5 section for why that changed and what it
   implies for the build.

## Practical notes

- R packages (`fixest`, `did`, `didimputation`, `fwildclusterboot`,
  `data.table`, `ggplot2`, `modelsummary`, `broom`) are already installed
  and verified to load on this machine — see `README.md`.
- No `pandoc`/`quarto`/LaTeX installed. Irrelevant now that the
  deliverable is a dashboard rather than a PDF, but worth knowing if that
  changes back.
- `data/raw/` and `data/interim/` are large and currently committed
  despite `PROJECT_PLAN.md`'s original intent to gitignore them — a
  pre-existing repo-hygiene gap, not something introduced during Weeks
  1–3, and not fixed as part of this work (out of scope each time it came
  up).
- Nothing in this repo has ever been auto-committed by an AI session
  working on it — every commit was made by the project owner after
  reviewing the diff. If continuing with AI assistance, that's a
  standing preference worth re-establishing explicitly with whatever tool
  picks this up next.
