# Ballot Rejection Analysis — Project Initialization Plan

## Context

The working directory contains exactly one file: `Project_Handoff_Ballot_Rejection_Analysis.md`. Nothing has been built yet.

The handoff document specifies a five-week, part-time portfolio project: *Administrative Burden at the Ballot Box: State Policy and Mail Ballot Rejection Rates, 2016–2024*. Its purpose is to close a specific gap — every existing portfolio project is a data-engineering artifact that never poses a research question, chooses a method, produces an estimate, or defends an interpretation. This project must produce a defensible causal estimate and, as of the current plan, **an interactive web dashboard** presenting the data and findings — this supersedes the handoff document's original 6–10 page static writing sample as the project's primary deliverable (see Week 5).

Before planning, I verified the project's core feasibility against the live data rather than assuming it. **The project is viable, and several of the handoff document's stated fears are wrong in ways that change the plan.**

### What I verified (all against real downloads)

| Check | Result |
|---|---|
| All 5 waves + codebooks downloadable, no auth | ✅ 9/9 URLs return 200, ~30 MB total |
| Outcome variable constructs end-to-end | ✅ **~30,600 usable jurisdiction-years** |
| National totals match published EAC figures | ✅ 2020: 560,826 rejected; 2024: 584,463 |
| FIPS links across waves | ✅ **99.7–99.8%** — 6,445 jurisdictions in all 5 waves |
| Codebooks machine-readable | ✅ `Variables` sheet w/ explicit sentinel columns |

**The handoff doc is wrong about identifiers.** It warns "FIPS matching will fail for a meaningful share of rows" and budgets Week 2 as the hardest week. Actual linkage is 99.8%, yielding a near-balanced panel of 6,445 × 5. Week 2 is materially easier than budgeted; the freed time should go to Week 3 policy coding, which is the real bottleneck.

### The three traps that will actually break this

These are specific, verified, and each one silently produces wrong numbers rather than an error.

1. **2016 renumbers the outcome.** `C4b` is *rejected total*; `C4a` is *counted*. In 2018/2020 `C4a` **is** rejected total. Grabbing `C4a` uniformly yields a 2016 rejection rate near 1.0 that looks plausible enough to survive review. Confirmed empirically: 2016 `C4b` correlates 0.9927 with the sum of its `C5a`-`C5v` reason columns and matches exactly in 91.4% of rows (vs. 0.857 for `C4a`).

2. **2016 encodes sentinels as text**, not numbers: `'-888888: Not Applicable'`, `'-999999: Data Not Available'`. Waves 2018–2024 use numeric `-88`/`-99`. Type inference makes the 2016 column `object`; arithmetic then either throws or concatenates strings.

3. **2016 is cp1252-encoded**, not UTF-8. `pd.read_csv` raises `UnicodeDecodeError` at byte 0x93. The other waves are fine.

Also: 3 duplicate FIPS rows exist (2020: `82575`, `84275`; 2022: `31550`), and FIPS arrives with inconsistent width (10-char and 5-char, from lost leading zeros) requiring `.zfill(10)`.

### Verified crosswalk

| Wave | Denominator (returned by voters) | Numerator (rejected total) | Encoding | Sentinels |
|---|---|---|---|---|
| 2016 | `C1b` | **`C4b`** | cp1252 | text `-888888`/`-999999` |
| 2018 | `C1b` | `C4a` | cp1252 | numeric `-88`/`-99` |
| 2020 | `C1b` | `C4a` | cp1252 | numeric `-88`/`-99` |
| 2022 | `C1b` | `C9a` | cp1252 | numeric `-88`/`-99` |
| 2024 | `C1b` | `C9a` | cp1252 | numeric `-88`/`-99` |

One definitional caveat to carry into the writeup: 2018's `C1b` is labeled "Returned **for Counting**" while 2020+ read "Returned **By Voters** Total". Flag as a robustness check, not a silent assumption.

### Stack decision

Python for cleaning, R for estimation (per your selection). Two adjustments to reduce install risk:

- **Choropleth stays in Python.** `geopandas` 1.1.1 is already working; the R `sf` path would require GDAL/PROJ system libraries. This removes the single riskiest install.
- **Panel handed to R as CSV, not parquet.** Avoids installing the heavy R `arrow` package. Write `panel.parquet` for Python and `panel.csv` for R.

Installed and usable now: Python `pandas` 2.1.4, `numpy`, `pyarrow`, `geopandas`, `statsmodels`, `matplotlib`, `openpyxl` (anaconda 3.11.4); R 4.5.3 with `data.table`, `ggplot2`, `modelsummary`, `broom`, `fixest`, `did`, `didimputation`, `fwildclusterboot` — all verified to load as of Week 2.
Not yet installed: `renv`.

---

## Week 1 — Scaffold, acquisition, crosswalk memo (detailed)

### 1.1 Repository scaffold

`git init` in the working directory, then create the structure from handoff §6, with an R estimation script + a figures script reflecting the split above. (These ended up numbered `src/06_estimate.R` and `src/07_figures.py` once the actual pipeline was built — the `05`/`06` numbering here is this section's original Week 1 guess, left as historical record rather than silently renumbered; see the Week 4/5 sections below for the files that actually exist.)

`.gitignore` must exclude `data/raw/` (~120 MB unzipped) and `data/interim/`, but **commit `data/processed/panel.csv`** — a reviewer cloning the repo should be able to run the estimation without re-downloading.

### 1.2 `src/01_download.py`

Downloads 5 data files + 5 codebooks to `data/raw/`, idempotently (skip if present, verify size). All URLs verified live:

```
2016 data https://www.eac.gov/sites/default/files/2023-12/EAVS_2016_for_Public_Release_nolabel_V1.1_CSV.zip
2018 data https://www.eac.gov/sites/default/files/2019-10/EAVS_2018_for_Public_Release_nolabel%20v1.1.csv
2020 data https://www.eac.gov/sites/default/files/2023-12/2020_EAVS_for_Public_Release_nolabel_V1.2_CSV.zip
2022 data https://www.eac.gov/sites/default/files/2023-12/2022_EAVS_for_Public_Release_nolabel_V1.1_CSV.zip
2024 data https://www.eac.gov/sites/default/files/2026-02/2024_EAVS_for_Public_Release_nolabel_V2_csv.zip
2016 cb   https://www.eac.gov/sites/default/files/eac_assets/1/6/EAVS_Codebook_2016.pdf
2018 cb   https://www.eac.gov/sites/default/files/eac_assets/1/6/2018_EAVS_Codebook.xlsx
2020 cb   https://www.eac.gov/sites/default/files/2021-08/2020_EAVS_Codebook.xlsx
2022 cb   https://www.eac.gov/sites/default/files/2023-06/2022_EAVS_Codebook.xlsx
2024 cb   https://www.eac.gov/sites/default/files/2025-06/2024_EAVS_Codebook.xlsx
```

**Use the 2024 V2 file (Feb 2026 revision).** The handoff doc predates it and assumes the June 2025 V1. Record the version in the README — a revision changed the data after initial publication.

Only the 2016 codebook is a PDF; 2018–2024 are `.xlsx` with a `Variables` sheet (columns `VariableName`, `Label`, `ValidSkip`, `RespondedDoesNotApply`, `RespondedDataNotAvailable`, `Missing`).

### 1.3 `codebooks/eavs_variable_crosswalk.md`

The handoff doc calls `codebooks/` "the differentiator" — it is where the resume's documentation claim gets demonstrated. Write the crosswalk table above by hand, with a sourced note per wave and an explicit paragraph on the 2016 `C4a`/`C4b` inversion and the "for Counting" vs "By Voters" wording shift.

Generate the machine-readable half programmatically by parsing the four codebook `Variables` sheets into `codebooks/crosswalk.yaml`, so the numbering is derived from the EAC's own labels rather than transcribed.

### 1.4 One-page variable memo

Per handoff §10, this gates everything downstream. Cover: outcome numerator/denominator per wave; sentinel scheme per wave; encoding; the three traps; controls needed from ACS; and the definitional divergence list.

**Week 1 done when:** all 10 files in `data/raw/`, crosswalk written, memo written, repo committed.

---

## Week 2 — Cleaning and panel construction (detailed)

### 2.1 `src/03_clean_eavs.py` — done

Per-wave loader plus validation gate, folded into one script (numbered `03_`
since `02_build_crosswalk.py` already occupies `02_`; the folding also drops
the separately-numbered validation file originally sketched below — there is
no panel yet to validate independently, and the README's declared structure
never listed one). Reads `codebooks/crosswalk.yaml` — including a
`rejection_reasons` list per wave, added to that script for this step — so
no column letter is hard-coded here. Non-negotiable rules, each mapping to a
verified trap:

- Read every wave with `encoding="latin-1"` and `dtype=str`. Read as string first, coerce second — this neutralizes traps 2 and 3 together and prevents any sentinel from entering arithmetic.
- Coerce with `pd.to_numeric(..., errors="coerce")`, then `.mask(v < 0)`. Order matters: text sentinels become `NaN` at coercion, numeric `-88`/`-99` are caught by the mask.
- Normalize FIPS: `.astype(str).str.strip().str.replace(r'\.0$','',regex=True).str.zfill(10)`.
- Harmonize ID columns — 2016 uses `State` / `JurisdictionName`; 2020+ use `State_Full` / `State_Abbr` / `Jurisdiction_Name`. 2016 has no full state name column; it's filled from a lookup built off the union of the other four waves (no single wave covers every 2016 abbreviation).
- Resolve the 3 known duplicate FIPS explicitly by summing counts (never rates) and flag the surviving row.

Emits `data/interim/eavs_<year>.parquet`, one row per jurisdiction-year, unusable rows kept and flagged rather than dropped.

**Validation gate**, run after cleaning in the same script. This is the step that makes the crosswalk defensible rather than asserted. Assert, per wave:

- National rejected totals reproduce **exactly**: **2016: 318,728 · 2018: 430,196 · 2020: 560,826 · 2022: 549,824 · 2024: 584,463**. Verified — these are regression-test fixtures; if a refactor changes them, something broke.
- `rejected_total ≈ sum(reason columns)` as a band, not a point fixture: corr ≥ 0.95 and exact-match ≥ 85%. Verified per wave: corr 0.9927/0.9602/0.9745/0.9997/0.9994, exact 91.4%/94.1%/94.7%/95.5%/94.2% for 2016/2018/2020/2022/2024 (the 2016 figure corrects an earlier draft of `variable_memo.md` that cited 0.9974/94.3% from a partial `C5a`-`C5r` range rather than the full `C5a`-`C5v` block).
- `rejection_rate ∈ [0, 1]`; count and report violations (informational — expect ≤2/wave; 2022 ran to 4, still passes as informational).
- Usable-row share ≥ 90% per wave — verified: 90.7 / 96.2 / 97.5 / 95.3 / 94.2%.
- Duplicate FIPS after resolution = 0 per wave — verified.

Fails loudly (non-zero exit) on violation. Writes `output/tables/validation_report.md`.

### 2.2 `src/04_merge_controls.py` (deferred)

ACS 5-year jurisdiction covariates (median income, education, age, race, rurality) via the Census API, merged on county FIPS. Deferred: no Census API key yet, and with jurisdiction fixed effects the time-invariant county covariates drop out of the main spec anyway — this mainly buys the urban/rural heterogeneity split, which a static classification can supply if needed before Week 4. Wisconsin/Michigan/New England sub-county jurisdictions will not match a county-level ACS pull — aggregate the ACS county value onto constituent jurisdictions and **flag the row** rather than dropping it. Count and report the flagged share.

### 2.3 `src/05_build_panel.py` — done

Stacks the 5 cleaned interim files into `data/processed/panel.parquet` **and** `panel.csv` (32,305 rows), adding a `waves_present` column so the balanced-subset check is queryable directly from the panel.

Produces `output/tables/missingness_report.md` by state and jurisdiction size. Handoff §7 is right that missingness correlates with jurisdiction capacity, so listwise deletion would drop exactly the under-resourced jurisdictions the analysis is about — verified: state dominates the pattern (AL 19.7% usable, MS/PR/ID 60-73%, vs. dozens of states at 100%), with a milder gradient by jurisdiction size (93.8-94.3% in the bottom three size quartiles vs. 97.2% in the largest). Document the pattern — a paragraph on non-random missingness is a strength in the dashboard's limitations section.

**Week 2 done:** `panel.parquet` + `panel.csv` exist (32,305 rows, 30,621 usable = 94.8%, close to the ~30,600/~32,225 estimate), validation passes with national totals reproduced, missingness documented, 6,447 FIPS present in all 5 waves.

---

## Weeks 3–5 (outline — re-plan once the panel exists)

**Week 3 — Policy coding — done. All 51 units coded in one consolidated table**, `codebooks/policy_coding_sheet.md`. The pilot (8 states) validated the coding methodology (statutory + mandatory + notice, each coded separately; a wave-alignment rule; a confidence scale); six scaling passes then coded current status and progressively resolved adoption timing for every remaining state + DC, closing with a pass that resolved the last 3 units (Illinois, Massachusetts, Oklahoma) and corrected one earlier entry (Mississippi). What were four separate in-progress tiers are now one table — nothing is left in an unresolved bucket, though several rows are flagged inferences rather than dated citations, not smoothed over now that everything technically has a value.

Key finding from the pilot, reconfirmed and extended at scale: **current-status trackers (NCSL, Ballotpedia) don't give adoption timing**, which the staggered-DiD design actually needs — California reads as a settled "Yes" everywhere but its mandatory statewide requirement only became law in 2018 (SB 759/AB 216); treated as always-on, it would silently drop out of the identifying variation. The mirror-image error also turned up: **Connecticut looks like a settled "Yes" today but its law was enacted in 2026**, after the panel's 2024 endpoint. **The single most consequential finding came from Iowa**: its 2017 signature-verification law was judicially enjoined starting Sept. 30, 2019, and — per multiple 2026 sources describing ongoing litigation to *reinstate* it — that injunction has held continuously since. NCSL's current "Yes" citation is technically accurate (the statute is unrepealed) but administratively false (unenforceable since 2019). Iowa is coded as a genuine **treatment reversal** — treated for the 2018 wave only, untreated 2020-2024 — which the panel/estimation code must represent as a time-varying indicator, not a single adoption-year scalar, or Iowa gets miscoded regardless of which single value is chosen. **The final push also caught a real error, not just a gap**: chasing Oklahoma's status surfaced a source contradicting Mississippi's existing "pre-2016" coding — Mississippi's actual cure *opportunity* (not just notice) was added by the Secretary of State in **October 2020**, corrected accordingly. That correction is the strongest argument for treating any "confirmed" row as provisional until deliberately re-tested. Two states (Illinois, Massachusetts) were closed only by documented inference after 7+ research attempts each found nothing more specific — flagged as the two lowest-confidence rows in the table, not hidden among the dated ones. Methodologically: **switching between search synthesis and direct primary-source fetches, in either direction, is what broke most remaining states loose** — session-law history notes are exactly what a search engine's synopsis drops, but Justia blocked direct statute fetches with HTTP 403 for several states where only further search worked instead; neither method dominates. Two recency sweeps found **no coding revisions needed** across all 33 states checked that way, but surfaced real post-panel (2025-2026) context — Ohio, Kansas, Utah, and North Dakota all passed 2025 laws ending the "postmark counts" grace period for late-arriving mail ballots, and 400+ election-related bills were enacted in just the first seven months of 2026 — this coding sheet will likely need periodic re-checking, not a one-time build, if the project's timeline extends. See the coding sheet's "Open items" for exactly which rows are inferences vs. citations, Iowa's treatment-reversal design implication, one internally-conflicting source now resolved (Kansas), Delaware's still-imprecise date, and the Pennsylvania county-optional design decision still pending.

**Validated against independent primary sources, three passes, done — `codebooks/policy_coding_validation.md`.** Pass 1 (4 checks by state) found 2 corrections and a scope clarification. At the user's request, Pass 2 went adversarial (search for counter-evidence, not confirmation) and found more, including one problem it left unresolved: **North Dakota's "statute, 2020" rested on a citation never independently verified**, and adversarial checking found the real 2020 mechanism was a federal court injunction — structurally the same litigation basis already excluded from North Carolina. Pass 3, organized by **category of error** rather than by state (existence, mechanism-misclassification, mandatory-vs-discretionary language, wave arithmetic, and a full re-read of the project's foundational source, NCSL's Table 15, directly rather than summarized for the first time), **resolved North Dakota cleanly**: North Dakota's own 2021 legislature independently repealed the old statute and enacted a real replacement (S.L. 2021, ch. 164) — genuinely a statute, just wave-corrected from 2020 to **2022**. The same category check also caught a parallel-but-distinct case in New Jersey (real litigation *and* a real, independently-confirmed statute — coded correctly as-is) and resolved Arizona, Massachusetts, and Oregon's previously-open questions.

**Final tally**: 44 of 51 states independently re-checked by a method different from how each was originally coded; 7 concrete errors found and fixed across all three passes (Louisiana, Mississippi ×2, California, Michigan, North Dakota, plus Kansas's conflict resolved); 0 wave-arithmetic mismatches remain on a full final recheck. **Explicit residual risk carried forward, not absorbed into "validated"**: Illinois and Massachusetts have confirmed cure rights but a genuinely unknown adoption year after 8+ and 5+ research attempts — treat their timing as censored, not `pre-2016`, in the event-study window. Ohio and Montana are the two weakest-supported rows (one inconclusive re-check attempt each, original single-source coding otherwise unreinforced). Pennsylvania (design decision) and North Carolina (litigation-excluded by definition) were never meant to resolve to a single wave. See the validation report's Pass 3 "Final disposition" table for the complete per-row breakdown before Week 4 treats this sheet as settled.

(This paragraph originally posed a mid-Week-3 decision — proceed with the 9-10-state treatment variable then available, or finish the 28 remaining timing lookups first — that the subsequent scaling passes resolved by finishing all 51 rows; left here only as a historical marker of where that decision point was, not as a live open question.) Pennsylvania's county-optional cure remains a known hard case needing its own state-vs-jurisdiction-level coding convention before it enters the treatment variable either way.

Produce descriptives and the summary table once the full 51-unit coding is done. Note `C6a` (drop box returns) exists only in 2022/2024 — insufficient waves for a drop-box treatment; signature cure remains the right choice.

**Week 4 — Estimation.**

*Part 1 (done)*: `src/04_build_treatment.py` transcribes `policy_coding_sheet.md`'s 51-unit table into `data/processed/treatment.csv` (one row per state x wave), with explicit non-scalar handling for Iowa's reversal (per-wave dict, not a single `first_treated_wave`) and North Carolina's litigation-based process (a separate `sensitivity_treated` column, primary variable stays `never`). Pennsylvania is coded `treated=0` state-level with a `pa_partial=True` flag — a deliberate, documented approximation (no statewide law exists; some counties cure), not a gap, chosen so it's reversible in a robustness check without re-deriving the join. `src/05_build_panel.py` now left-joins this onto the panel by `(state_abbr, year)`, asserting a 100% match for all 50 states + DC; the 5 EAVS territories (AS, GU, MP, PR, VI) are out of scope for the treatment variable and explicitly flagged `in_scope=False` rather than silently coded 0. Panel row count, usable share, and FIPS coverage are unchanged after the join (32,305 rows, 94.8% usable, 6,447 FIPS in all 5 waves) — confirms the join added columns without altering the underlying panel. `pytest tests/` (51 cases) still passes unmodified.

*Part 1 (done)*: `src/06_estimate.R` first cut — naive TWFE via `fixest::feols` (jurisdiction + year FE, state-clustered) alongside `fixest::sunab()` (Sun-Abraham), the staggered-adoption-corrected estimator, with Iowa excluded from the `sunab` sample specifically since its reversal doesn't fit a single-cohort model (kept in the TWFE sample). Point estimates: TWFE gives essentially a null, imprecise effect (-0.0014, SE 0.0026, p=0.59); Sun-Abraham's aggregated ATT (37 states — also excludes the 13 always-treated states, which have no pre-period to identify an event-time effect from) is +0.0024, SE 0.0025, p=0.34 — also a clean null, same direction as TWFE this time. Output: `output/tables/estimates_v1.md`.

*Correction (VALIDATION_REPORT.md Pass 4, Defect 1)*: an earlier version of this script derived the Sun-Abraham cohort from the filtered (usable & in_scope) estimation sample rather than from `treatment.csv`. Vermont's 2016 wave happens to be 0% usable, so always-treated Vermont was silently miscoded as a fabricated 2018 adopter — that bug, not a real effect, produced a previously-reported "+0.0037, p=0.051" result. **That number was wrong and is retracted.** Fixed: cohort now comes from `treatment.csv` directly (no missingness to exploit), and always-treated states are excluded from the `sunab` model on the same no-pre-period logic already applied to Iowa.

*Part 2 (not started)*: `fwildclusterboot` wild-cluster bootstrap (~50 effective clusters); Callaway–Sant'Anna via the `did` package as a second corrected estimator alongside `sunab`, with the TWFE-vs-corrected gap explained; heterogeneity by log(ballots returned) and urban/rural; the robustness checklist (drop 2020; drop WI/MI; winsorize at p99; weight by ballots returned; fractional logit vs linear). These are listed as `TODO`s in `06_estimate.R`'s own comments, not silently dropped.

**Week 5 — Dashboard and packaging.** The primary deliverable is now an interactive web dashboard, not a static writing sample — replaces the handoff brief's original 6-10 page writeup as the project's main output. Content: the same four analyses as before (event study, coefficient plot, rejection-rate distribution by state, county choropleth) rebuilt as interactive views over the panel and estimation results, plus a findings summary and the same limitations/robustness material a writeup would have carried. Static assets (Python/geopandas for the choropleth, `06_estimate.R`'s output tables) feed the dashboard rather than a PDF. Decide the hosting/build path early in Week 5 (a self-contained static site is the lowest-risk choice given no `pandoc`/`quarto` install currently). README readable in 90 seconds either way.

---

## Verification

- **Week 1:** `python src/01_download.py` twice — second run is a no-op. All 10 files present with expected sizes.
- **Week 2:** `python src/03_clean_eavs.py` reproduces all five national totals exactly (verified — see `output/tables/validation_report.md`). This is the single strongest end-to-end check.
- **Panel sanity:** median rejection rate by wave lands near 0.37 / 0.67 / 0.25 / 0.47 / 0.39% for 2016–2024 — verified against the cleaned interim files. The 2020 dip survives as a visible feature. (6,445-FIPS cross-wave linkage is a panel-level check, still pending `05_build_panel.py`.)
- **Reproducibility:** `bash run_all.sh` from a clean clone rebuilds the entire pipeline from raw downloads through the first-cut estimates (written as part of Week 4 part 1's fixes — VALIDATION_REPORT.md Defect 4 caught this claim being false when the script didn't yet exist).
- **R environment:** `fixest`, `did`, `didimputation`, `fwildclusterboot` are installed and verified to load (checked Week 2, ahead of Week 4) — no outstanding install risk here.

## Non-goals

No causal claim beyond what the design supports; no methodological novelty; no partisan framing; one outcome, one treatment, one heterogeneity dimension. Scope creep is the main schedule risk.

(Supersedes handoff §8's "not a dashboard or web app" — the deliverable direction changed; see Week 5 above. The rest of §8's scope discipline still holds.)
