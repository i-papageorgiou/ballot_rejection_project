"""
04_build_treatment.py — Turn codebooks/policy_coding_sheet.md's final
coding table into a machine-readable state-year treatment file.

The sheet itself (see its "Final coding table" and "Wave-alignment rule"
sections) is the source of truth; this script transcribes its 51-state
table into structured data below, once, rather than regex-parsing the
markdown. Parsing was rejected on purpose: the table's citation column
contains literal `|` and `[...]` characters that make a markdown-table
regex fragile, and the sheet is a human-curated document that changes
rarely enough that a manual transcription re-checked against the sheet
is more reliable than a parser that has to handle its prose cells.

If the coding sheet changes, this file's TREATMENT dict must be updated
by hand to match — the summary this script prints at the end (switcher
list, cohort counts) is designed to make a stale transcription obvious
by comparison against HANDOFF.md's "19 switchers across 4 cohorts" claim.

Two rows are NOT simple step functions and get explicit per-wave
handling instead of a scalar `first_treated_wave`:
- Iowa: treated for the 2018 wave only, reverting to untreated from 2020
  onward (2017 law judicially enjoined starting Sept. 2019).
- North Carolina: coded `never` on the primary (statutory-only) variable
  since its cure process came from litigation, not a statute; a separate
  `sensitivity_treated` column treats it as treated from 2020 onward, for
  a robustness check that wants to include non-statutory regimes.

Pennsylvania is a deliberate, documented approximation, not a gap: no
statewide law exists (cure is county-optional), so it is coded
`treated=0` (the correct state-level answer to what this variable
measures) with `pa_partial=True` flagging it for a robustness check that
might want to drop it or replace it with a jurisdiction-level covariate
instead. See PROJECT_PLAN.md / HANDOFF.md for the discussion.

Usage:
    python src/04_build_treatment.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
OUT_PATH = PROCESSED / "treatment.csv"

WAVES = (2014, 2016, 2018, 2020, 2022, 2024)

# ---------------------------------------------------------------------------
# Transcribed from codebooks/policy_coding_sheet.md's "Final coding table"
# (all 51 units), row by row. `first_treated_wave` is one of:
#   - an int in WAVES:  treated from that wave onward
#   - "pre-2016":       treated in every wave, INCLUDING 2014 — the label is
#                        historical (from when 2016 was the panel's first
#                        wave) and now really means "predates the panel
#                        entirely." Re-verified state-by-state when 2014 was
#                        added (see PROJECT_PLAN.md's "Extend the panel
#                        backward" section): every remaining "pre-2016" row's
#                        own cited evidence (FL 2001, GA 2010, MN's statute
#                        already being amended in 2013, MT 1979, NM 1969,
#                        OR 1998, VT 1977) predates 2014 too, and the
#                        inferred rows (AZ, IL, MA, OH — no exact date) have
#                        no evidence suggesting a 2014-2016 adoption
#                        specifically, so the inference extends cleanly.
#                        Two rows had a real resolution instead of just a
#                        recheck: CO (HB13-1303, 2013) and WA (2011 c.10,
#                        effective 8/24/2011) both have an exact date inside
#                        the newly-visible 2010-2014 window and are now
#                        coded `first_treated_wave=2014` below, not
#                        "pre-2016" — real new switcher cohorts, not just
#                        relabeled always-treated states.
#   - "never":          untreated in every wave
# `mechanism` and `confidence` are carried through unchanged from the sheet.
# ---------------------------------------------------------------------------
TREATMENT: dict[str, dict] = {
    "AK": dict(first_treated_wave="never", mechanism="none", confidence="High"),
    "AL": dict(first_treated_wave="never", mechanism="none", confidence="High"),
    "AZ": dict(first_treated_wave="pre-2016", mechanism="statute", confidence="High"),
    "AR": dict(first_treated_wave="never", mechanism="none", confidence="Medium"),
    "CA": dict(first_treated_wave=2018, mechanism="statute", confidence="High"),
    "CO": dict(first_treated_wave=2014, mechanism="statute", confidence="High",
               notes="Resolved from 'pre-2016' when the 2014 wave was added: HB13-1303 (2013 Voter Access and Modernized Elections Act) is well before the Nov. 2014 election, making CO a real 2014-cohort switcher, not always-treated."),
    "CT": dict(first_treated_wave="never", mechanism="statute", confidence="High",
               notes="Law enacted 2026 (Public Act 26-42) — postdates the panel entirely."),
    "DE": dict(first_treated_wave="never", mechanism="statute", confidence="Medium",
               notes="Adoption falls at/after the 2024 panel edge; coded conservatively as outside the panel.",
               de_edge_case=True),
    "DC": dict(first_treated_wave=2024, mechanism="statute", confidence="High"),
    "FL": dict(first_treated_wave="pre-2016", mechanism="statute", confidence="High"),
    "GA": dict(first_treated_wave="pre-2016", mechanism="statute", confidence="Medium"),
    "HI": dict(first_treated_wave=2020, mechanism="statute", confidence="High"),
    "ID": dict(first_treated_wave="never", mechanism="none", confidence="Medium"),
    "IL": dict(first_treated_wave="pre-2016", mechanism="statute", confidence="Low",
               notes="Existence confirmed; adoption year is an inference (timing unresolved after 8+ attempts)."),
    "IN": dict(first_treated_wave=2022, mechanism="statute", confidence="High"),
    # Iowa: explicit per-wave override, not a scalar — see module docstring.
    "IA": dict(
        first_treated_wave=None,
        per_wave={2014: 0, 2016: 0, 2018: 1, 2020: 0, 2022: 0, 2024: 0},
        mechanism="statute, then enjoined",
        confidence="Medium",
        notes="Treatment reversal: 2017 law in force for 2018 wave only; enjoined from Sept. 2019 onward (LULAC v. Pate).",
    ),
    "KS": dict(first_treated_wave=2020, mechanism="statute", confidence="High"),
    "KY": dict(first_treated_wave=2022, mechanism="statute", confidence="High"),
    "LA": dict(first_treated_wave=2022, mechanism="statute", confidence="High"),
    "ME": dict(first_treated_wave=2022, mechanism="statute", confidence="High"),
    "MD": dict(first_treated_wave=2024, mechanism="statute", confidence="High"),
    "MA": dict(first_treated_wave="pre-2016", mechanism="statute", confidence="Medium",
               notes="Existence confirmed via direct statutory text; adoption year is an inference."),
    "MI": dict(first_treated_wave=2024, mechanism="constitutional amendment (2022 Ballot Proposal 2), implemented via administrative rule", confidence="High"),
    "MN": dict(first_treated_wave="pre-2016", mechanism="statute", confidence="High"),
    "MS": dict(first_treated_wave=2020, mechanism="guidance (administrative rule)", confidence="High"),
    "MO": dict(first_treated_wave="never", mechanism="none", confidence="Medium"),
    "MT": dict(first_treated_wave="pre-2016", mechanism="statute", confidence="Low-Medium",
               notes="Weakest-supported row: inferred from a neighboring statutory section, not directly dated."),
    "NE": dict(first_treated_wave="never", mechanism="none", confidence="High"),
    "NV": dict(first_treated_wave=2020, mechanism="statute", confidence="High"),
    "NH": dict(first_treated_wave="never", mechanism="none", confidence="Medium"),
    "NJ": dict(first_treated_wave=2020, mechanism="statute (contemporaneous litigation also present)", confidence="Medium"),
    "NM": dict(first_treated_wave="pre-2016", mechanism="statute", confidence="Low-Medium"),
    "NY": dict(first_treated_wave=2020, mechanism="statute", confidence="High"),
    # North Carolina: primary variable is statutory-only ("never"); the
    # litigation-based cure process is exposed only via sensitivity_treated.
    "NC": dict(
        first_treated_wave="never",
        sensitivity_first_treated_wave=2020,
        mechanism="litigation (consent decree, 2020)",
        confidence="Medium",
        notes="Primary variable: No (statutory-only definition). Sensitivity variable treats as treated from 2020 (consent decree).",
    ),
    "ND": dict(first_treated_wave=2022, mechanism="statute (post-litigation codification)", confidence="High"),
    "OH": dict(first_treated_wave="pre-2016", mechanism="statute", confidence="Medium",
               notes="One of the two weakest-supported rows in the table (single source, unreinforced on re-check)."),
    "OK": dict(first_treated_wave="never", mechanism="none", confidence="Medium"),
    "OR": dict(first_treated_wave="pre-2016", mechanism="statute", confidence="Medium"),
    # Pennsylvania: deliberate approximation, see module docstring.
    "PA": dict(first_treated_wave="never", mechanism="discretionary", confidence="Medium",
               pa_partial=True,
               notes="No statewide law; county-optional cure. Coded untreated at state level pending a jurisdiction-level design decision."),
    "RI": dict(first_treated_wave=2018, mechanism="guidance (administrative regulation)", confidence="High"),
    "SC": dict(first_treated_wave="never", mechanism="none", confidence="Medium"),
    "SD": dict(first_treated_wave="never", mechanism="none", confidence="Medium"),
    "TN": dict(first_treated_wave="never", mechanism="none", confidence="Medium"),
    "TX": dict(first_treated_wave=2022, mechanism="statute", confidence="Medium"),
    "UT": dict(first_treated_wave=2020, mechanism="statute", confidence="High"),
    "VT": dict(first_treated_wave="pre-2016", mechanism="statute", confidence="High"),
    "VA": dict(first_treated_wave=2020, mechanism="statute", confidence="High"),
    "WA": dict(first_treated_wave=2014, mechanism="statute", confidence="High",
               notes="Resolved from 'pre-2016' when the 2014 wave was added: 2011 c.10 (effective 8/24/2011, confirmed) is well before the Nov. 2014 election, making WA a real 2014-cohort switcher, not always-treated."),
    "WV": dict(first_treated_wave="never", mechanism="none", confidence="Medium"),
    "WI": dict(first_treated_wave="never", mechanism="discretionary", confidence="High",
               notes='Clerks "may" return a defective ballot for correction; no uniform mandate.'),
    "WY": dict(first_treated_wave="never", mechanism="none", confidence="Medium"),
}

# All 50 states + DC. PROJECT_PLAN.md/HANDOFF.md say "51 units" (50 states + DC).
EXPECTED_UNITS = 51


def _wave_indicator(first_treated_wave, wave: int) -> int:
    if first_treated_wave == "pre-2016":
        return 1
    if first_treated_wave == "never":
        return 0
    return int(wave >= first_treated_wave)


def build_treatment_table() -> pd.DataFrame:
    assert len(TREATMENT) == EXPECTED_UNITS, (
        f"expected {EXPECTED_UNITS} units (50 states + DC), got {len(TREATMENT)} — "
        "re-check TREATMENT against policy_coding_sheet.md"
    )

    rows = []
    for state_abbr, spec in TREATMENT.items():
        per_wave = spec.get("per_wave")
        sens_first = spec.get("sensitivity_first_treated_wave")
        for wave in WAVES:
            if per_wave is not None:
                treated = per_wave[wave]
            else:
                treated = _wave_indicator(spec["first_treated_wave"], wave)

            if sens_first is not None:
                sensitivity_treated = _wave_indicator(sens_first, wave)
            else:
                sensitivity_treated = treated

            rows.append(dict(
                state_abbr=state_abbr,
                year=wave,
                treated=treated,
                sensitivity_treated=sensitivity_treated,
                mechanism=spec["mechanism"],
                confidence=spec["confidence"],
                pa_partial=bool(spec.get("pa_partial", False)),
                de_edge_case=bool(spec.get("de_edge_case", False)),
                notes=spec.get("notes", ""),
            ))

    df = pd.DataFrame(rows).sort_values(["state_abbr", "year"]).reset_index(drop=True)
    assert len(df) == EXPECTED_UNITS * len(WAVES), "row count doesn't match units x waves"
    return df


def summarize(df: pd.DataFrame) -> str:
    lines = ["Treatment table summary", "=" * 40, ""]

    by_wave = df.groupby("year")["treated"].agg(["sum", "count"])
    lines.append("Treated states by wave (primary variable):")
    for year, row in by_wave.iterrows():
        lines.append(f"  {year}: {int(row['sum'])} / {int(row['count'])}")
    lines.append("")

    # Switchers: treated=0 in 2016, treated=1 in some later wave, and not
    # a pure step-down (Iowa) - identify first wave each state goes to 1.
    pivot = df.pivot(index="state_abbr", columns="year", values="treated")
    always = pivot[(pivot.sum(axis=1) == len(WAVES))].index.tolist()
    never = pivot[(pivot.sum(axis=1) == 0)].index.tolist()
    switchers = pivot.index.difference(always).difference(never)

    lines.append(f"Always-treated (pre-2016), {len(always)}: {', '.join(sorted(always))}")
    lines.append(f"Never-treated, {len(never)}: {', '.join(sorted(never))}")
    lines.append(f"Switchers / special cases, {len(switchers)}: {', '.join(sorted(switchers))}")
    lines.append("")

    lines.append("Switcher cohorts (first wave treated=1, per primary variable):")
    cohorts: dict[int, list[str]] = {}
    for state in switchers:
        series = pivot.loc[state]
        treated_waves = [w for w in WAVES if series[w] == 1]
        if treated_waves:
            first = min(treated_waves)
            cohorts.setdefault(first, []).append(state)
        else:
            cohorts.setdefault(0, []).append(state)  # e.g. Iowa reverts to 0
    for wave in sorted(cohorts):
        label = wave if wave else "never (post-reversal or special case)"
        lines.append(f"  {label}: {', '.join(sorted(cohorts[wave]))}")

    return "\n".join(lines)


def main() -> int:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    df = build_treatment_table()
    df.to_csv(OUT_PATH, index=False)
    print(f"wrote {OUT_PATH} ({len(df):,} rows, {df['state_abbr'].nunique()} units x {len(WAVES)} waves)")
    print()
    print(summarize(df))
    return 0


if __name__ == "__main__":
    sys.exit(main())
