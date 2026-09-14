> **Update — fixes applied.** Following review, the user chose (via
> explicit decisions, not silent judgment calls on my part): drop
> always-treated states from the Sun-Abraham model (SA/CS convention);
> write `run_all.sh` rather than just correct the doc claim; flag the 15
> outlier rows rather than remove or ignore them. All three, plus every
> defect not requiring a judgment call (2, 3, 6, 8), have been applied.
> Corrected Sun-Abraham estimate: **ATT +0.00237, SE 0.00247, p=0.34,
> n=37 states** (drops Iowa + 13 always-treated) — a clean null,
> reproduced by both a direct rerun and a full `run_all.sh` clean-clone
> rebuild. Defects 5, 9, 10 (a stale paragraph, `.gitignore`, test
> coverage) were left as documented backlog items, not fixed, per the
> review discussion. See each defect row below for its individual
> resolution; the tables and prose below are otherwise the **original,
> unedited Pass 4 findings** — left as the historical record of what
> this pass found, not rewritten after the fact to look like the fixes
> were always there.

# Validation Report — Pass 4 (comprehensive, post-estimation)

**Scope**: everything in the repo as of commit `5110b44` — the EAVS
pipeline, the 51-state treatment coding, the treatment-panel join, and
the first-cut estimation script — not just the policy coding that Passes
1–3 (`codebooks/policy_coding_validation.md`) covered. **Report only: no
files were changed to produce this report.** `git status` before and
after this pass shows zero modified files (one stray untracked
`src/__pycache__/` from running the pipeline, removed).

**Headline result**: the single most important finding is that **the
"marginally significant" result documented in `PROJECT_PLAN.md` and
`HANDOFF.md` is a bug, not a finding.** See Defect 1. Everything else is
secondary to that.

---

## Executive summary

| # | Severity | File(s) | What's wrong | Proposed fix | Resolved? |
|---|---|---|---|---|---|
| 1 | **High** | `src/06_estimate.R`, `PROJECT_PLAN.md`, `HANDOFF.md` | Sun-Abraham cohort is derived from the *filtered* estimation sample, not `treatment.csv`. Vermont's 2016 wave is 0% usable, so always-treated Vermont is silently reclassified as a fabricated 2018 adopter. The documented "+0.0037, p=0.051" result is this bug's artifact; correcting it gives a clean null (p=0.22–0.34). | Derive `cohort` from `treatment.csv` before any `usable`/`in_scope` filtering; decide and document whether to retain always-treated states as a "2016 cohort" or drop them per SA/CS convention (both give a null; retracts the "marginally significant" language). | ✅ Fixed — user chose "drop, SA/CS convention." New estimate: ATT +0.00237, p=0.34, n=37. |
| 2 | **High** | `HANDOFF.md` | The switcher/never-treated summary list puts Iowa among the "17 never-treated controls," contradicting the code, `treatment.csv`, and HANDOFF's own Caveats section 3 paragraphs later, which correctly describes Iowa's 2018-only reversal. | Move Iowa out of the never-treated list into its own line (a 3rd special case alongside DE/PA), and correct "17" to reflect whatever the real never-treated count becomes. | ✅ Fixed |
| 3 | Medium | `codebooks/policy_coding_sheet.md` | The Mississippi table row (`2020`, corrected twice) contradicts the "Open items" section, which still says the correction went "from pre-2016 to **2022**" — stale after the second correction. Code correctly uses 2020. | Update the "Open items" bullet to say the final correction landed on 2020, not 2022. | ✅ Fixed |
| 4 | Medium | `PROJECT_PLAN.md` (Verification section) | Instructs `bash run_all.sh` to rebuild the panel from a clean clone. **This file does not exist anywhere in the repo.** | Either write `run_all.sh` (chaining `01`→`05`, `Rscript 06`) or replace the claim with the actual command sequence already in `README.md`. | ✅ Fixed — user chose "write the script." Verified end-to-end: full clean-clone rebuild reproduces the identical corrected estimate. |
| 5 | Medium | `PROJECT_PLAN.md:157` | Stale mid-Week-3 language: "decide whether to proceed with the 9-10-state treatment variable... or block on finishing the 28 remaining timing lookups" — overtaken by the completed 51-unit coding two paragraphs below it in the same file. | Delete or rewrite as historical ("this was resolved by finishing all 51 rows"). | ✅ Fixed (bundled in, low-effort) |
| 6 | Low | `PROJECT_PLAN.md:63` | Week 1 scaffold section names `src/05_estimate.R` + `src/06_figures.py`; actual files are `src/06_estimate.R` and (planned) `src/07_figures.py`. | Correct the filenames or add a footnote that numbering shifted. | ✅ Fixed (bundled in, low-effort) |
| 7 | Low-Medium | `data/processed/panel.parquet` / outcome data | 15 jurisdiction-years have `rejection_rate == 1.0` exactly, several with non-trivial N (Desha Co. AR 2020: 383/383; Galveston Co. TX 2020: 248/248; Washington Co. UT 2022: 943/943). A literal 100% mail-ballot rejection rate for a county with hundreds of ballots is implausible and more likely a raw EAVS data-entry artifact than a real outcome. Nothing in the pipeline's own validation gate (national aggregates only) or in Passes 1–3 (policy coding only) ever examined per-jurisdiction outcome plausibility. | Flag these 15 rows explicitly (a `flagged_outlier` column, or a documented exclusion list) before they influence any regression; do not silently trust `usable`'s `rate <= 1` filter as a plausibility check — it only excludes what's structurally impossible, not what's merely absurd. | ✅ Fixed — user chose "flag, don't remove." `flagged_outlier` column added in `05_build_panel.py`; count reported in `missingness_report.md`. Underlying rows not yet investigated (see "What I could not verify"). |
| 8 | Low | `04_build_treatment.py` | Michigan's `mechanism` field drops the sheet's trailing clause "...implemented via administrative rule" — a transcription completeness gap, not a treated/wave error. | Cosmetic; append the clause if exact verbatim fidelity matters. | ✅ Fixed |
| 9 | Low | Repo hygiene | `.gitignore` has only `.DS_Store`; `data/raw/`/`data/interim/` remain committed despite stated intent (pre-existing, not new); `__pycache__` appears as untracked noise after any Python run. | Add `__pycache__/`, `.pytest_cache/`, `data/raw/`, `data/interim/` to `.gitignore` (a deliberate decision, not urgent). | ⬜ Not fixed — left as backlog per review discussion. |
| 10 | Low | `tests/` | All 51 pytest cases cover the Week 1–2 EAVS pipeline only; zero cover `treatment.csv`, the join, or `06_estimate.R`'s inputs — exactly the layer this report had to check by hand. | Add tests asserting: treatment.csv row count/shape, join match rate, Iowa's per-wave pattern, NC's primary/sensitivity split — see Layer 0 scripts below as a starting point. | ⬜ Not fixed — left as backlog per review discussion. |

---

## Layer 0 — Mechanical checks (verified, full coverage)

All run programmatically from the scratchpad, independent of the
production code they check.

- **Transcription fidelity** (parsed the sheet's markdown table
  independently, diffed against `TREATMENT` in `04_build_treatment.py`):
  membership identical (51/51 states); wave values match on every
  simply-parsed row (one apparent DE mismatch was a false positive of
  the naive parser — the sheet's own prose says "treat as outside
  panel," which is exactly what the code does); confidence values match
  verbatim on every row; only the MI mechanism omission (Defect 8) found.
- **Wave-arithmetic recheck** (extracted every dated month/year
  mentioned in each row's `adoption_event` prose, independently applied
  the sheet's own wave-alignment rule): one apparent flag (North Dakota)
  is explained by the sheet's own Pass-3 reasoning — the extracted date
  is the 2020 injunction, not the 2021 legislative session that actually
  produced the codified statute, so the "mismatch" isn't one. Zero
  genuine new arithmetic errors found across all 51 rows.
- **`treatment.csv` expansion**: exactly 255 rows; every state except
  Iowa is a monotonic step function; Iowa's pattern is exactly
  `[0,1,0,0,0]`; North Carolina's primary `treated` is all-zero with
  `sensitivity_treated = [0,0,1,1,1]` — both match spec exactly.
- **Join integrity**: zero in-scope `(state_abbr, year)` rows where
  `panel.treated` disagrees with `treatment.csv`; all 5 territories
  (AS, GU, MP, PR, VI) correctly null and `in_scope=False`.
- **Non-mutation proof**: diffed `data/processed/panel.csv` against the
  true pre-join baseline (`git show 45a77d3:data/processed/panel.csv`
  — note this required finding the right baseline commit, since the
  user had independently committed all of Week 4 part 1 since this
  pass started, moving `HEAD` past the join). All 14 pre-existing
  columns are byte-identical row-for-row after sort-aligning on
  `(fips, year)`; exactly 8 new columns were added
  (`treated, sensitivity_treated, mechanism, confidence, pa_partial,
  de_edge_case, notes, in_scope`); zero rows added or lost.
- **Panel invariants**, unchanged from Weeks 1–3: all 5 national
  rejected-ballot totals exact (318,728 / 430,196 / 560,826 / 549,824 /
  584,463); 32,305 rows; 30,621 usable (94.8%); 6,447 FIPS in all 5
  waves; median rejection rate 0.37/0.67/0.25/0.47/0.39% by wave.

## Layer 1 — Documentation accuracy audit

Checked every backticked file/command reference across `README.md`,
`PROJECT_PLAN.md`, `HANDOFF.md`, and the four `codebooks/*.md` files
against the actual repo. Results are Defects 3–6 above, plus:

- HANDOFF's always-treated (13) and switcher-cohort lists (2018: CA, RI;
  2020: HI, KS, MS, NV, NJ, NY, UT, VA; 2022: IN, KY, LA, ME, ND, TX;
  2024: DC, MD, MI) match `treatment.csv` **state-for-state**, not just
  in count — verified programmatically. Only Iowa's placement in the
  never-treated list is wrong (Defect 2).
- Quoted estimates in `PROJECT_PLAN.md`/`HANDOFF.md` do match what
  `06_estimate.R` actually prints — the numbers are internally
  consistent with the script; the problem is the script's own logic, not
  a transcription error into the docs (this is why Defect 1 is filed
  against the script, and the docs need only the retraction, not new
  data).
- No other missing-file references found beyond Defects 4/6 (a batch
  scan of ~15 apparent hits were false positives from directory-relative
  references, e.g. `codebooks/variable_memo.md` saying `03_clean_eavs.py`
  where the `src/` prefix is implied by context).

## Layer 2 — Statistical specification audit

- **Cohort derivation bug** (Defect 1) — full accounting:

  | Specification | ATT | SE | p |
  |---|---|---|---|
  | As shipped (bug) | +0.0037 | 0.0018 | **0.051** |
  | True cohorts from `treatment.csv`, always-treated retained as 2016 cohort | +0.0026 | 0.0021 | 0.22 |
  | True cohorts, always-treated dropped (SA/CS convention) | +0.0024 | 0.0025 | 0.34 |

  Only Vermont's cohort actually changes between "as shipped" and "true
  cohorts" (2016 wave 0% usable → miscoded as a 2018 adopter); the
  larger p-value shift comes from that one state's mechanical effect on
  the interaction-weighted average, not from a broad pattern of errors.
- **Never-treated encoding**: `Inf` is `fixest::sunab()`'s documented
  convention for a reference/never-treated cohort (units where
  `year < cohort` always holds, so no treatment interaction is ever
  formed) — confirmed both by the successful run producing a coherent
  event-study table and by cross-checking against `fixest` deviations.
  No coercion issue found.
- **Singleton fixed-effect drops**: 83 rows dropped by `feols` as
  singleton fixed effects. Of these, 80/83 have `treated == 0`, and
  66/83 are in **Alabama alone** — consistent with (not a new
  discovery beyond) `output/tables/missingness_report.md`'s existing
  finding that Alabama is only ~19.7% usable overall. Not a bug, but
  worth naming explicitly: the naive TWFE sample effectively down-weights
  Alabama's already-thin control-group contribution further still.
- **Outcome sanity**: see Defect 7 (15 rows at exactly 100% rejection).
- **`output/tables/estimates_v1.md` vs. script output**: table contents
  match a fresh rerun of `06_estimate.R` exactly.

## Layer 3 — 51-state legal re-audit (partial, disclosed honestly)

**True blind re-coding was not achievable in this pass** — reading the
existing sheet to scope this validation (necessary to know what to
check) already put its claims in context before any "blind" check could
start. What follows is adversarial re-verification against fresh web
sources, the same posture as Passes 2–3, not a from-scratch re-derivation.
**17 of 51 states got fresh source-checking in this pass; the remaining
34 rely on Passes 1–3's prior verification, unrepeated here.**

**Checked and confirmed accurate** (all 8 states in the 2020 cohort —
the largest, most consequential cohort):
HI (Act 136, all-mail voting, 5-day cure — confirmed), KS (SB130/Ch. 36
2019, exact statutory cure language confirmed), MS (Oct. 7 2020 SOS
rule, 1-day notice / 10-day cure — confirmed, matches recorded 2020
wave), NV (AB4, signature cure confirmed), NJ (L.2020 c.70, 24-hour
cure-letter requirement confirmed in detail), NY (S.8370B, July/Aug 2020
— confirmed), UT (HB0036 2020 — bill confirmed to exist; exact effective
date not independently re-confirmed this pass, matches sheet's own
already-cited source), VA (HB1800, 2020 special session — confirmed
reinstituted the cure process for the Nov. 3, 2020 election; note the
same bill also independently addressed a witness-signature waiver, a
different provision within the same omnibus bill — not a conflict, just
worth knowing HB1800 did more than one thing).

**Checked, confirm no new information** (the four rows already flagged
as weakest, Ohio/Montana/Illinois/Massachusetts): all four remain
undated with available tools, exactly as Passes 1–3 already disclosed.
This pass does not resolve them and does not claim to; they remain the
lowest-confidence rows in the table by design, not by oversight.

**Checked, confirmed correct, but surfaced a genuinely new data point**:
**South Carolina** — currently `never`, Medium confidence, sourced only
from a WebSearch synthesis of a Ballotpedia page. This pass found South
Carolina actually had a real bill, **H.4117 ("Absentee voting, right to
cure"), introduced March 9, 2023**, with detailed signature-mismatch
notice-and-cure language nearly identical to Kansas's enacted statute.
Direct fetch of the bill's status page confirms **it died in committee**
(referred to Judiciary, no further action) — so SC's `never` coding
remains correct through the 2024 panel. This is worth recording because
none of Passes 1–3 found this near-miss (they weren't looking for failed
bills), and it is precisely the kind of thing that could flip in a
future session — worth a specific recheck if this project's timeline
extends past 2026, alongside the general staleness warning already in
the sheet.

**Checked, confirmed no cure process (consistent with `never`)**:
Alabama, New Hampshire, Tennessee.

**Not re-checked this pass** (34 states): everything else. Their
existing confidence ratings (High/Medium/Low, several explicitly
"(inferred)") stand as Passes 1–3 left them — this pass adds no new
evidence for or against these rows.

## Layer 4 — Repo hygiene

See Defects 9–10. Additionally: `requirements.txt`'s tested-interpreter
note (anaconda `python3`) is accurate and matches what this pass had to
discover independently (system `python3` lacks `pyarrow`) — already
documented correctly in `README.md`/`HANDOFF.md` from the prior round,
no defect there.

## What I could not verify

- Illinois and Massachusetts's adoption years — unresolved after this
  pass's attempts too, consistent with 8+ and 5+ prior attempts each.
- Ohio and Montana's adoption years — same, no new leads found.
- Delaware's exact date within its 2024–2026 session — not narrowed.
- The 34 states not re-checked in Layer 3 (listed above) — this report
  does not independently confirm them; it relies on Passes 1–3.
- Whether the 15 rows at `rejection_rate == 1.0` (Defect 7) are actual
  data errors or genuine (if extraordinary) events — flagged, not
  adjudicated; would need the raw EAVS county-level source records or a
  direct inquiry to those jurisdictions to resolve definitively.

## Final disposition

| Claim / layer | Status | Method |
|---|---|---|
| 51-state sheet ↔ `TREATMENT` dict transcription | **Verified**, 1 minor gap (Defect 8) | Independent markdown parse + diff |
| Wave arithmetic, all 51 rows | **Verified**, 0 new errors | Independent date extraction + rule reapplication |
| `treatment.csv` shape/expansion | **Verified** | Direct inspection |
| Panel join integrity | **Verified** | Merge + assert vs. source file |
| Panel non-mutation | **Verified** | Diff vs. pre-join baseline commit `45a77d3` |
| Panel invariants (totals, counts, medians) | **Verified**, unchanged | Recomputed from `panel.parquet` |
| Sun-Abraham headline estimate | **Contradicted** — bug confirmed (Defect 1) | Reran with 3 specifications |
| HANDOFF's switcher/never lists | **Contradicted** on Iowa (Defect 2) | Cross-check vs. `treatment.csv` |
| Mississippi row (sheet-internal) | **Contradicted** (Defect 3) | Cross-check table vs. prose |
| `run_all.sh` claim | **Contradicted** — file absent (Defect 4) | Filesystem check |
| 2020-cohort states (8) | **Verified** | Fresh web search, this pass |
| OH/MT/IL/MA timing | **Unverifiable** (as previously disclosed) | Fresh web search, this pass — no new leads |
| South Carolina | **Verified**, with a new caveat noted | Fresh web search + direct bill-status fetch |
| AL/NH/TN | **Verified** | Fresh web search, this pass |
| Remaining 34 states | **Not re-checked this pass** | Relies on Passes 1–3 |
| Outcome-data plausibility (rejection_rate) | **New finding, unresolved** (Defect 7) | Distributional scan |
| Test coverage of Week 4 work | **Gap confirmed** (Defect 10) | Directory inspection |

**This report's own coverage tally, recomputed mechanically, not
hand-counted**: 17 states fresh-verified + 34 relying on prior passes =
51. 10 defects filed (2 High, 3 Medium, 5 Low/Low-Medium). Re-read in
full before filing; no internal contradiction found in this report
itself.
