"""
03_clean_eavs.py — Per-wave cleaning of the raw EAVS files into one common
schema, plus the validation gate that makes the crosswalk defensible rather
than asserted.

Reads codebooks/crosswalk.yaml (built by 02_build_crosswalk.py) so this
script never hard-codes a column letter, cleans data/raw/eavs_<year>.csv per
wave, and writes data/interim/eavs_<year>.parquet. Then validates the
cleaned output against known fixtures and writes
output/tables/validation_report.md.

Non-negotiable rules, each mapping to a verified trap (see
codebooks/variable_memo.md):

  1. Read with encoding="latin-1", dtype=str. String first, coerce second —
     this neutralizes 2016's cp1252 encoding and text sentinels in one pass
     and keeps every sentinel out of arithmetic until explicitly coerced.
  2. Coerce with pd.to_numeric(errors="coerce"), THEN .mask(v < 0). Order
     matters: 2016's '-888888: Not Applicable' text becomes NaN at
     coercion; 2018-2024's numeric -88/-99 are caught by the mask.
     Reversing the order silently breaks 2016.
  3. Normalize FIPS to a 10-character, zero-padded string.
  4. Harmonize identifiers across the two ID schemes (2016 uses
     State/JurisdictionName; 2018-2024 use
     State_Full/State_Abbr/Jurisdiction_Name). 2016 has no State_Full
     column, so it is filled from a lookup built off the other four waves.
  5. Resolve the 3 known duplicate FIPS rows by summing counts (never
     rates), and flag the surviving row. See DUPLICATE_FIPS below.

Unusable rows (missing numerator/denominator, zero denominator, or an
out-of-range rate) are kept with usable=False, not dropped — missingness
here correlates with jurisdiction capacity, and 05_build_panel.py needs the
full set to report that pattern rather than silently deleting it.

Usage:
    python src/03_clean_eavs.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
CROSSWALK_PATH = ROOT / "codebooks" / "crosswalk.yaml"
VALIDATION_REPORT = ROOT / "output" / "tables" / "validation_report.md"

WAVES = (2016, 2018, 2020, 2022, 2024)
COUNT_COLS = ["transmitted_total", "returned_by_voters", "counted_total", "rejected_total"]

# National rejected-ballot totals as published by the EAC, verified against
# the raw files (see PROJECT_PLAN.md). Regression-test fixtures: if a
# refactor changes these, something in the cleaning path broke.
EXPECTED_NATIONAL_TOTAL = {
    2016: 318_728,
    2018: 430_196,
    2020: 560_826,
    2022: 549_824,
    2024: 584_463,
}

# The 3 duplicate FIPS codes, verified by hand: each is a Wisconsin
# town/village pair sharing one EAC-assigned code, where one member of the
# pair always reports 0 ballots returned. Summing counts is equivalent to
# keeping the reporting jurisdiction while staying correct if that changes.
# Codes are post-zfill(10).
DUPLICATE_FIPS = {
    2020: ["0000082575", "0000084275"],
    2022: ["0000031550"],
}


def load_crosswalk() -> dict[int, dict]:
    waves = yaml.safe_load(CROSSWALK_PATH.read_text())["waves"]
    return {w["wave"]: w for w in waves}


def _load_raw(year: int) -> pd.DataFrame:
    return pd.read_csv(RAW / f"eavs_{year}.csv", encoding="latin-1", dtype=str, low_memory=False)


def _clean_numeric(s: pd.Series) -> pd.Series:
    """String -> numeric -> sentinel-masked. Order matters (see module
    docstring): to_numeric turns 2016's text sentinels into NaN; the mask
    then catches 2018-2024's numeric -88/-99."""
    v = pd.to_numeric(s, errors="coerce")
    return v.mask(v < 0)


def _build_state_lookup() -> dict[str, str]:
    """abbr -> full state name, derived from the union of the four waves
    that carry both columns (2016 has abbr only). No single wave covers
    every abbreviation 2016 uses (2018 lacks PR); the union of all four
    does."""
    lookup: dict[str, str] = {}
    for year in (2018, 2020, 2022, 2024):
        df = _load_raw(year)
        lookup.update(dict(zip(df["State_Abbr"], df["State_Full"])))
    return lookup


def _harmonize_ids(raw: pd.DataFrame, year: int, state_lookup: dict[str, str]) -> pd.DataFrame:
    fips = raw["FIPSCode"].str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(10)
    if year == 2016:
        state_abbr = raw["State"]
        state_full = state_abbr.map(state_lookup)
        jurisdiction_name = raw["JurisdictionName"]
    else:
        state_abbr = raw["State_Abbr"]
        state_full = raw["State_Full"]
        jurisdiction_name = raw["Jurisdiction_Name"]
    return pd.DataFrame({
        "fips": fips,
        "state_abbr": state_abbr,
        "state_full": state_full,
        "jurisdiction_name": jurisdiction_name,
    })


def _resolve_duplicates(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Collapse each known duplicate-FIPS pair into one row by summing
    counts (never rates), flagging the survivor. See DUPLICATE_FIPS."""
    df = df.reset_index(drop=True)
    df["dup_resolved"] = False
    dup_codes = DUPLICATE_FIPS.get(year, [])
    if not dup_codes:
        return df

    survivors = []
    drop_idx = []
    for code in dup_codes:
        group = df[df["fips"] == code]
        if len(group) != 2:
            raise ValueError(f"{year}: expected exactly 2 rows for duplicate FIPS {code}, found {len(group)}")
        survivor = group.iloc[0].copy()
        for col in COUNT_COLS + ["reason_sum"]:
            survivor[col] = group[col].sum(min_count=1)
        survivor["jurisdiction_name"] = " + ".join(group["jurisdiction_name"])
        survivor["dup_resolved"] = True
        survivors.append(survivor)
        drop_idx.extend(group.index)

    df = df.drop(index=drop_idx)
    df = pd.concat([df, pd.DataFrame(survivors)], ignore_index=True)
    return df


def clean_wave(year: int, crosswalk: dict[int, dict], state_lookup: dict[str, str]) -> pd.DataFrame:
    cw = crosswalk[year]
    raw = _load_raw(year)

    ids = _harmonize_ids(raw, year, state_lookup)
    counts = pd.DataFrame({col: _clean_numeric(raw[cw[col]]) for col in COUNT_COLS})

    # Reason-breakdown sum: an all-missing row contributes 0 per reason
    # column rather than propagating NaN, matching the derivation verified
    # in codebooks/variable_memo.md (this is a descriptive/robustness field,
    # not the main-spec numerator).
    reason_sum = sum(_clean_numeric(raw[c]).fillna(0) for c in cw["rejection_reasons"])

    df = pd.concat([ids, counts], axis=1)
    df["year"] = year
    df["reason_sum"] = reason_sum

    df = _resolve_duplicates(df, year)

    df["rejection_rate"] = df["rejected_total"] / df["returned_by_voters"]
    df["usable"] = (
        df["rejected_total"].notna()
        & df["returned_by_voters"].notna()
        & (df["returned_by_voters"] > 0)
        & (df["rejection_rate"] <= 1)
    )

    cols = [
        "fips", "state_abbr", "state_full", "jurisdiction_name", "year",
        "transmitted_total", "returned_by_voters", "counted_total", "rejected_total",
        "reason_sum", "rejection_rate", "usable", "dup_resolved",
    ]
    return df[cols]


def validate(cleaned: dict[int, pd.DataFrame]) -> tuple[bool, str]:
    """Run the validation gate and build the markdown report. Returns
    (all_passed, report_text)."""
    lines = ["# EAVS Cleaning Validation Report", ""]
    ok = True

    lines.append("## National rejected-ballot total (exact match required)")
    lines.append("")
    lines.append("| wave | expected | actual | match |")
    lines.append("|---|---|---|---|")
    for year in WAVES:
        df = cleaned[year]
        actual = int(df["rejected_total"].sum())
        expected = EXPECTED_NATIONAL_TOTAL[year]
        match = actual == expected
        ok &= match
        lines.append(f"| {year} | {expected:,} | {actual:,} | {'OK' if match else 'FAIL'} |")
    lines.append("")

    lines.append("## rejected_total vs. sum of reason columns (band, not a point fixture)")
    lines.append("")
    lines.append("| wave | corr | exact match | pass (corr>=0.95 and exact>=0.85) |")
    lines.append("|---|---|---|---|")
    for year in WAVES:
        df = cleaned[year]
        both = df["rejected_total"].notna() & df["reason_sum"].notna()
        corr = df.loc[both, "rejected_total"].corr(df.loc[both, "reason_sum"])
        exact = (df.loc[both, "rejected_total"] - df.loc[both, "reason_sum"]).abs().le(1e-6).mean()
        passed = corr >= 0.95 and exact >= 0.85
        ok &= passed
        lines.append(f"| {year} | {corr:.4f} | {exact:.1%} | {'OK' if passed else 'FAIL'} |")
    lines.append("")

    lines.append("## rejection_rate out-of-range violations (informational; expect <=2/wave)")
    lines.append("")
    lines.append("| wave | violations |")
    lines.append("|---|---|")
    for year in WAVES:
        df = cleaned[year]
        rate = df["rejection_rate"]
        n_violations = int((rate.notna() & ((rate < 0) | (rate > 1))).sum())
        lines.append(f"| {year} | {n_violations} |")
    lines.append("")

    lines.append("## Usable-row share (>=90% required)")
    lines.append("")
    lines.append("| wave | rows | usable share | pass |")
    lines.append("|---|---|---|---|")
    for year in WAVES:
        df = cleaned[year]
        share = df["usable"].mean()
        passed = share >= 0.90
        ok &= passed
        lines.append(f"| {year} | {len(df):,} | {share:.1%} | {'OK' if passed else 'FAIL'} |")
    lines.append("")

    lines.append("## Duplicate FIPS after resolution (0 required)")
    lines.append("")
    lines.append("| wave | duplicate fips |")
    lines.append("|---|---|")
    for year in WAVES:
        df = cleaned[year]
        n_dup = int(df["fips"].duplicated().sum())
        passed = n_dup == 0
        ok &= passed
        lines.append(f"| {year} | {n_dup} {'OK' if passed else 'FAIL'} |")
    lines.append("")

    return ok, "\n".join(lines)


def main() -> int:
    crosswalk = load_crosswalk()
    state_lookup = _build_state_lookup()

    INTERIM.mkdir(parents=True, exist_ok=True)
    VALIDATION_REPORT.parent.mkdir(parents=True, exist_ok=True)

    cleaned: dict[int, pd.DataFrame] = {}
    for year in WAVES:
        df = clean_wave(year, crosswalk, state_lookup)
        out = INTERIM / f"eavs_{year}.parquet"
        df.to_parquet(out, index=False)
        cleaned[year] = df
        print(f"{year}: wrote {out} ({len(df):,} rows, {df['usable'].mean():.1%} usable)")

    passed, report = validate(cleaned)
    VALIDATION_REPORT.write_text(report + "\n")
    print(f"\nwrote {VALIDATION_REPORT}")
    print(f"\n{'PASSED' if passed else 'FAILED'} — see {VALIDATION_REPORT} for detail")

    if not passed:
        raise SystemExit(
            "\nValidation gate failed — a cleaning rule regressed or a "
            "crosswalk entry is wrong. Inspect the report before trusting "
            "these interim files."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
