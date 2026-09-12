# EAVS Variable Crosswalk — Mail Ballot Transmission, Return, and Rejection

This is the differentiator claim made in the project handoff: documentation
of schema, variable definitions, and how they were confirmed, not just
asserted. Every mapping below is backed by one of two checks:

1. **Codebook label matching** (2018, 2020, 2022, 2024) — `src/02_build_crosswalk.py`
   parses each wave's `Variables` sheet and matches variables to roles by
   their EAC-authored label text, machine-verified against the table below
   on every run.
2. **Empirical verification** (2016 only) — the 2016 codebook is a PDF with
   no machine-readable variable table, and its own label text does not
   disambiguate *counted* from *rejected*. See §3.

## 1. The crosswalk

| Wave | Transmitted total | Returned by voters (denominator) | Counted total | **Rejected total (numerator)** | Source |
|---|---|---|---|---|---|
| 2016 | `C1a` | `C1b` | `C4a` | **`C4b`** | empirical (§3) |
| 2018 | `C1a` | `C1b` | `C3a` | `C4a` | codebook label match |
| 2020 | `C1a` | `C1b` | `C3a` | `C4a` | codebook label match |
| 2022 | `C1a` | `C1b` | `C8a` | `C9a` | codebook label match |
| 2024 | `C1a` | `C1b` | `C8a` | `C9a` | codebook label match |

`rejection_rate = rejected_total / returned_by_voters`, per the handoff
document's definition. Section numbering shifts (Section C question count
grows from ~35 to ~40 items across waves as drop-box and additional
rejection-reason items are added), but the *transmitted* and *returned by
voters* variables are consistently `C1a`/`C1b` in all five waves.

## 2. Definitional caveat: what "returned by voters" means

The label text for the denominator (`C1b`) is not word-for-word identical
across waves:

- **2016, 2018:** "By-mail Transmitted: Returned for Counting"
- **2020, 2022, 2024:** "Mail Returned By Voters Total"

"Returned for counting" and "returned by voters" are not guaranteed to be
the same population — a ballot returned by a voter but rejected before
tabulation could plausibly be excluded from a strict "for counting" reading
in 2016–2018. We did not find affirmative evidence in the 2018 codebook
that the two are computed differently (the item description text is
otherwise identical to 2020's), so we treat them as the same denominator
by default. **This is flagged as a robustness check in Week 4, not resolved
here.** If the pooled model's residuals show a 2016–2018 vs. 2020+ level
break, this is the first place to look.

## 3. Why 2016 is verified empirically, not from a codebook

The 2016 codebook (`EAVS_Codebook_2016.pdf`) is scanned/typeset text, not a
structured spreadsheet, and unlike later waves its own item descriptions do
not distinguish *ballots counted* from *ballots rejected* clearly enough to
automate. Critically, **the natural guess is wrong**: `C4a` looks like the
rejected-ballots field by analogy to 2018's `C4a`, but in 2016 `C4a` is
*counted* and `C4b` is *rejected* — the reverse of 2018/2020.

This was confirmed by testing which of `C4a`/`C4b` reconstructs from the
sum of the wave's full rejection-reason breakdown columns (`C5a`...`C5v`,
"Rejected: Deadline," "Rejected: Voter Signature," etc.):

| Candidate | Correlation with Σ(reason cols) | Exact match rate |
|---|---|---|
| `C4a` | 0.857 | 0.1% |
| **`C4b`** | **0.9927** | **91.4%** |

`C4b` is the only candidate that reconstructs from its own breakdown, so it
is the rejected total. `src/03_clean_eavs.py`'s validation gate re-runs this
exact check on every build — if a future data revision changes 2016's
numbering again, the pipeline fails loudly instead of silently reporting a
~100% rejection rate for 2016.

## 4. Sentinel codes and encoding, per wave

| Wave | File encoding | Sentinel scheme |
|---|---|---|
| 2016 | **cp1252/latin-1** (not UTF-8 — raises `UnicodeDecodeError` at byte `0x93` if read as UTF-8) | **Text**, embedded in the value itself: `'-888888: Not Applicable'`, `'-999999: Data Not Available'` |
| 2018 | cp1252/latin-1 | Numeric: `-88` (not applicable), `-99` (data not available) |
| 2020 | cp1252/latin-1 | Numeric: `-88`, `-99` |
| 2022 | cp1252/latin-1 | Numeric: `-88`, `-99` |
| 2024 | cp1252/latin-1 | Numeric: `-88`, `-99` |

All five files are read as `latin-1` (a strict superset of ASCII that never
raises on the byte range EAVS files use) so a single encoding argument
works everywhere rather than branching per wave. All numeric columns are
read as **strings first, then coerced** with `pandas.to_numeric(errors="coerce")`
— this turns 2016's text sentinels into `NaN` at the coercion step and lets
`.mask(v < 0)` catch the numeric sentinels in one common code path, instead
of needing wave-specific sentinel-stripping logic.

## 5. Known identifier issues

- **FIPS width**: some rows carry a 10-character FIPS code, others 5
  (leading zeros lost by an intermediate Excel step at some point in the
  file's history, judging by the pattern). Normalize with `.zfill(10)`.
- **Duplicate FIPS within a wave**: 2020 (`82575`, `84275`), 2022 (`31550`).
  Three rows total across five waves. `03_clean_eavs.py` logs and resolves
  these explicitly rather than silently summing or dropping.
- **ID column names differ**: 2016 uses `State` / `JurisdictionName`; 2020+
  use `State_Full` / `State_Abbr` / `Jurisdiction_Name`. Harmonized in
  `03_clean_eavs.py`.
- **Cross-wave FIPS linkage**: verified at 99.7–99.8% — 6,445 of ~6,460
  jurisdictions per wave are present in all five waves. This is
  substantially better than the handoff document's stated concern; see the
  project plan for detail.

## 6. Regenerating this crosswalk

```
python src/02_build_crosswalk.py
```

Re-parses the four machine-readable codebooks, writes
`codebooks/crosswalk.yaml`, and asserts the result matches the table in §1.
Fails loudly (non-zero exit) if a codebook's label wording changes such
that the pattern match no longer finds the expected variable — the correct
response is to inspect the new label text by hand, not to loosen the match
predicate until it passes.
