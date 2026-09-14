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
rounds of independent validation). Week 4 is now fully done: the
treatment coding is joined to the panel, and `src/06_estimate.R` produces
TWFE, Sun-Abraham, and Callaway-Sant'Anna estimates plus a wild-cluster
bootstrap, heterogeneity by jurisdiction size, and a 5-item robustness
checklist re-run through all three estimators. **All three estimators
agree the headline effect is a clean null — and two caveats that
surfaced along the way have since been investigated and diagnosed (not
fixed, and not fixable — see below): a pre-trend narrowed down to one
specific cohort, and a heterogeneity result now understood to be
unidentifiable with the current cohort coverage, not just uncertain.**
See "First-cut estimates" below and `PROJECT_PLAN.md`'s Week 4 section
for the full diagnosis — read them before using either result, but
there's nothing further to chase on either one without new data. Week 5
(an interactive dashboard — the deliverable changed from a static
writeup partway through; see `PROJECT_PLAN.md`) is next.

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
Rscript src/06_estimate.R          # TWFE, Sun-Abraham, Callaway-Sant'Anna, bootstrap, heterogeneity, robustness -> output/tables/{estimates_v1,heterogeneity,robustness_checklist}.md
```

`06_estimate.R` takes **~25-30 minutes** (the wild-cluster bootstrap alone
is ~20 min on the machine this was built on — not hung, see the script's
own header comment) — don't assume it's stuck if it runs a while.

Note: the Python steps need `pyarrow`; this project was built and
verified against the anaconda distribution's `python3`, not whatever
`python3` is first on `PATH` — check that if `import pyarrow` fails.

(ACS controls were deliberately deferred, no `04_merge_controls.py` was
ever built — `04` went to the treatment coding instead; see Caveats
below. `07_figures.py` is still unwritten — Week 5.)

**Estimates exist and are now bootstrap/robustness-checked**
(`output/tables/estimates_v1.md`): naive TWFE gives an imprecise
near-null (-0.0014, SE 0.0026, p=0.59, wild-cluster bootstrap p=0.6166 —
confirms the analytic SE); Sun-Abraham's aggregated ATT (37 states —
excludes Iowa and the 13 always-treated states) is +0.0024, SE 0.0025,
p=0.34; Callaway-Sant'Anna's overall ATT (same 37-state exclusion) is
-0.0045, SE 0.0036, p=0.22. **All three estimators independently give a
clean null** — this is the strongest form of "no effect detected" this
project can currently support, not a weakness of any one method.

**Two things surfaced by this round — investigated via `did::att_gt`'s
raw group-time ATT table (`out$group/t/att/se`, available before
`aggte()` aggregates it) and diagnosed, not resolved (neither has a
mechanical fix; both are genuine limitations of the current data)**:
1. **The pre-trend traces to one specific cohort, not a broad design
   flaw.** The event-time -6 signal is exactly one of 16 group-time
   cells: group=2024 (DC, MD, MI) vs. controls at t=2018, att=-0.0089,
   SE=0.0023. Confirmed not a DC artifact (excluding DC alone moves the
   estimate only to -0.0092) — Maryland and Michigan carry this.
   Confirmed not resolved by allowing anticipation (`anticipation=2`
   still leaves it significant). **This is a genuine, unexplained
   pre-existing difference specific to MD/MI predating their 2024
   treatment by 6 years.** Any conclusion leaning on the 2024 cohort
   should carry this caveat explicitly; it is not evidence the whole
   panel violates parallel trends.
2. **Heterogeneity by jurisdiction size is unidentifiable with the
   current cohort coverage, not just uncertain.** Two confirmed reasons:
   (a) the small-jurisdiction subsample has **no 2018 or 2024 cohort at
   all** (only 2020/2022 survive the size filter, 9 treated states
   total), and one of its cells is an outlier by an order of magnitude
   (att=-0.045, SE=0.0215, vs. everything else under 0.012); (b) the
   large-jurisdiction subsample's own cohort-level effects **flip sign
   across periods within the same cohort** (2024 cohort: +0.0162 then
   -0.0038 at the next period) — Sun-Abraham's interaction-weighted and
   Callaway-Sant'Anna's group-size-weighted averaging aren't guaranteed
   to agree when the underlying effects are this heterogeneous, so their
   disagreement here is expected, not a bug in either estimator. See
   `output/tables/heterogeneity.md`. **Read as "not establishable with
   this design," not as evidence for either estimator's pattern.**

One lower-stakes numerical wrinkle: the Sun-Abraham weighted-by-ballots
robustness cell has SE=265 (broken, not a real null) — `returned_by_voters`'
extreme range (median ~210, max ~3.4M) breaks the interacted model's
weighted variance; TWFE and CS tolerate the same weights fine. Flagged
in `output/tables/robustness_checklist.md`, not silently reported.

*(An earlier version of this section reported "+0.0037, p=0.051" as
"marginally significant" and framed it as the corrected estimator
flipping TWFE's sign. That was wrong — `06_estimate.R` had a bug
[VALIDATION_REPORT.md Defect 1] that derived the Sun-Abraham cohort from
the filtered estimation sample rather than `treatment.csv`, silently
fabricating a 2018 treatment event for always-treated Vermont. Fixed;
the number above is the corrected one.)*

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
- **17 never-treated controls**: AK, AL, AR, CT, ID, MO, NE, NH, NC,
  OK, SC, SD, TN, WV, WI, WY
- **3 special cases, not simple values** — **do not treat any of these
  as a clean control or a clean switcher without reading the caveat
  below first** (VALIDATION_REPORT.md Defect 2: an earlier draft of
  this list put Iowa in the never-treated bucket above, contradicting
  the Caveats section below and the code — fixed):
  - **Iowa** — treated for the 2018 wave only, then reverts (see Caveats
    below); not never-treated, not a normal switcher either.
  - **DE** (adoption falls right at or past the 2024 panel edge — treat
    as outside panel).
  - **PA** (no statewide law; county-optional, needs a state-vs-
    jurisdiction-level design decision before it enters anything).

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
2. ~~Estimation: TWFE, Sun-Abraham, Callaway-Sant'Anna, wild-cluster
   bootstrap, heterogeneity, robustness checklist.~~ **Done** — all in
   `src/06_estimate.R`. All three estimators agree on a clean null.
3. ~~Investigate the pre-trend flag and the heterogeneity disagreement.~~
   **Done — both diagnosed, neither has a mechanical fix.** The pre-trend
   traces to one cohort (MD/MI, event-time -6) and doesn't resolve under
   anticipation periods; the heterogeneity disagreement traces to the
   small-jurisdiction subsample missing two whole cohorts plus real
   cross-cohort sign-flipping in the large subsample. See the caveat
   block above and `PROJECT_PLAN.md`'s Week 4 section for the full
   diagnosis with exact cells/states. **There is nothing further to chase
   on either one without new data** — the correct next step is to carry
   both forward as documented limitations, not to keep investigating.
4. **Week 5 — dashboard**: event study, coefficient
   plot, rejection-rate distribution by state, county choropleth
   (`geopandas`, already working in this environment). The deliverable
   is an interactive dashboard, not a static writeup — see
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
