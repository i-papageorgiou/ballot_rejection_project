# Variable Memo — One Page Before Touching Analysis Code

Per the project plan, this memo gates Week 2. It lists every variable
needed per wave, where definitions diverge, and every trap confirmed
against the real files in `data/raw/`.

## Outcome variable

`rejection_rate = rejected_total / returned_by_voters`

| Wave | Numerator | Denominator | Verified national total (rejected) |
|---|---|---|---|
| 2016 | `C4b` | `C1b` | 318,728 |
| 2018 | `C4a` | `C1b` | 430,196 |
| 2020 | `C4a` | `C1b` | 560,826 |
| 2022 | `C9a` | `C1b` | 549,824 |
| 2024 | `C9a` | `C1b` | 584,463 |

Full derivation and the 2016 `C4a`/`C4b` inversion: `eavs_variable_crosswalk.md` §3.
Denominator wording caveat ("returned for counting" vs. "returned by
voters"): same file, §2.

## Rejection-reason breakdown (for descriptives / robustness, not the main spec)

- 2016: `C5a`–`C5r` (22 reason columns, `_Other` text pairs excluded from sums)
- 2018/2020: `C4b`–`C4r` / `C4b`–`C4r` respectively (deadline, signature,
  witness signature, non-matching signature, no EO signature, unofficial
  envelope, ballot missing, envelope not sealed, no address, multiple
  ballots, deceased, already voted, no voter ID, no ballot application, +3 other)
- 2022/2024: `C9b`–`C9t` (adds: no secrecy envelope, no postmark,
  missing documentation, voter not eligible — items that did not exist as
  separate categories before 2022)

Drop-box return volume (`C6a` in 2024, matching item in 2022) exists in
**only 2 of 5 waves** — insufficient for a panel treatment or control; note
in the writeup as a scope limitation, do not attempt to backfill.

## Identifiers

| Wave | FIPS column | State | Jurisdiction name |
|---|---|---|---|
| 2016 | `FIPSCode` | `State` | `JurisdictionName` |
| 2018–2024 | `FIPSCode` | `State_Full` / `State_Abbr` | `Jurisdiction_Name` |

- Normalize FIPS with `.astype(str).str.strip().str.replace(r'\.0$','',regex=True).str.zfill(10)`.
- Cross-wave linkage verified: **6,445 / ~6,460 jurisdictions (99.7–99.8%)
  present in all five waves.**
- 3 duplicate FIPS rows total: 2020 (`82575`, `84275`), 2022 (`31550`).
  Resolve explicitly in `03_clean_eavs.py`; do not silently sum or drop.

## File mechanics (the part that breaks silently)

- **Encoding**: all five files parse cleanly as `latin-1`. 2016 raises
  `UnicodeDecodeError` at byte `0x93` under UTF-8 — this is a hard failure
  the pipeline will hit immediately if the wrong encoding is used, not a
  subtle one.
- **Sentinels**: 2016 embeds them as descriptive text in the value itself
  (`'-888888: Not Applicable'`, `'-999999: Data Not Available'`); 2018–2024
  use numeric `-88`/`-99`. Read every numeric column as a string first,
  coerce with `pandas.to_numeric(errors="coerce")` (turns 2016's text into
  `NaN`), then `.mask(v < 0)` (catches the numeric sentinels). This is the
  only sequencing that handles both schemes with one code path.
- **Usable-row share** after applying the above (row has both numerator and
  denominator, denominator > 0, rate ≤ 1): 90.7% (2016) / 96.2% (2018) /
  97.5% (2020) / 95.2% (2022) / 94.2% (2024). ~30,600 of ~32,225
  jurisdiction-year rows usable across all five waves combined.

## Controls needed from ACS (Week 2, `04_merge_controls.py`)

Median household income, educational attainment (% bachelor's+), median
age, race/ethnicity composition, rural/urban classification — all at
county level via the Census API, joined on the first 5 digits of FIPS.
Wisconsin, Michigan (municipality-level reporting) and New England
(township-level) jurisdictions will not match 1:1 to a county FIPS;
aggregate the county ACS value onto every constituent jurisdiction and flag
the row rather than dropping it. Needs a Census API key
(https://api.census.gov/data/key_signup.html) — not yet obtained.

## Non-random missingness (document, don't just delete)

Missingness in the numerator/denominator correlates with jurisdiction
capacity — small/under-resourced jurisdictions are more likely to report a
sentinel than a number. Listwise deletion would selectively drop exactly
the jurisdictions the rejection-rate analysis is about. `05_build_panel.py`
must produce a missingness-by-jurisdiction-size report; the writeup treats
this as a documented limitation, not a silent exclusion.

## Open item before Week 3

Census API key not yet obtained — blocks `03_merge_controls.py`. Everything
else in Week 1–2 is unblocked.
