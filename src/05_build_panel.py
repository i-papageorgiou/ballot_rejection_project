"""
05_build_panel.py — Stack the five cleaned EAVS waves into one
jurisdiction-year panel, join the treatment coding, and document
missingness.

Reads data/interim/eavs_<year>.parquet (written by 03_clean_eavs.py, already
validated by that script's own gate and by tests/) and concatenates them
into one long panel. This script does no additional cleaning or validation
of its own — that already happened per-wave; its job is assembly and
description.

Also reads data/processed/treatment.csv (written by 04_build_treatment.py)
and left-joins it onto the panel by (state_abbr, year). Every panel row is
asserted to match — a silent non-match would quietly zero out a state's
treatment status rather than error, which is the failure mode most worth
guarding against here.

Emits data/processed/panel.parquet and panel.csv (identical content, two
formats — per PROJECT_PLAN.md's stack decision, R reads the CSV so the heavy
arrow package doesn't need installing there).

Also writes output/tables/missingness_report.md. Missingness in
rejected_total/returned_by_voters is not random (see
codebooks/variable_memo.md): a jurisdiction's usability correlates with which
state it's in far more than with its size, so listwise deletion would
selectively drop exactly the under-resourced jurisdictions/states the
analysis is about. This report documents the pattern rather than deleting
past it.

Usage:
    python src/05_build_panel.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
TREATMENT_PATH = PROCESSED / "treatment.csv"
MISSINGNESS_REPORT = ROOT / "output" / "tables" / "missingness_report.md"

WAVES = (2014, 2016, 2018, 2020, 2022, 2024)

# EAVS covers 50 states + DC + 5 U.S. territories; the policy coding sheet
# (and the underlying legal-research question) only covers the 51 states +
# DC. Territories are out of scope for the treatment variable, not a join
# failure — flagged via in_scope=False rather than silently dropped or
# forced to a fabricated Yes/No.
TERRITORIES = ("AS", "GU", "MP", "PR", "VI")


def load_panel() -> pd.DataFrame:
    frames = [pd.read_parquet(INTERIM / f"eavs_{year}.parquet") for year in WAVES]
    panel = pd.concat(frames, ignore_index=True)
    panel = panel.sort_values(["fips", "year"]).reset_index(drop=True)

    # Cross-wave presence: how many of the 5 waves each fips appears in.
    # Makes the balanced-subset check (jurisdictions present in all 5 waves)
    # queryable directly from the panel instead of requiring a separate script.
    waves_present = panel.groupby("fips")["year"].transform("nunique")
    panel["waves_present"] = waves_present

    panel = join_treatment(panel)
    panel = flag_outliers(panel)

    return panel


def flag_outliers(panel: pd.DataFrame) -> pd.DataFrame:
    """Flag (not remove) jurisdiction-years with an implausible outcome.

    VALIDATION_REPORT.md (Pass 4, Defect 7) found 15 usable jurisdiction-
    years with rejection_rate == 1.0 exactly (100% of returned ballots
    rejected), several with non-trivial N (e.g. 383, 943 returned
    ballots) — more likely a raw EAVS data-entry artifact (returned_
    by_voters miscoded identically to rejected_total) than a real
    outcome, but not confirmed either way. Flagged rather than dropped:
    usable's own rate<=1 threshold already excludes what's structurally
    impossible, and this pass has no basis to unilaterally delete real
    rows from a validated panel. Downstream code (06_estimate.R and any
    successor) can filter on flagged_outlier explicitly as a documented
    robustness check, rather than trust the value silently.
    """
    panel["flagged_outlier"] = panel["usable"] & (panel["rejection_rate"] == 1.0)
    return panel


def join_treatment(panel: pd.DataFrame) -> pd.DataFrame:
    if not TREATMENT_PATH.exists():
        raise FileNotFoundError(
            f"{TREATMENT_PATH} not found — run `python src/04_build_treatment.py` first."
        )
    treatment = pd.read_csv(TREATMENT_PATH)

    n_before = len(panel)
    merged = panel.merge(treatment, on=["state_abbr", "year"], how="left", validate="m:1")
    assert len(merged) == n_before, "treatment join changed row count — duplicate keys in treatment.csv"

    merged["in_scope"] = ~merged["state_abbr"].isin(TERRITORIES)

    unmatched = merged.loc[merged["treated"].isna() & merged["in_scope"], "state_abbr"].unique()
    assert len(unmatched) == 0, (
        f"in-scope panel state_abbr values with no match in treatment.csv: {sorted(unmatched)} — "
        "every state/DC row must have a treatment row (territories are the only expected exception)."
    )
    territory_rows = merged.loc[~merged["in_scope"]]
    assert set(territory_rows["state_abbr"].unique()) <= set(TERRITORIES)

    # Territories: no treatment coding exists (out of scope), so treated/
    # sensitivity_treated stay NaN rather than a fabricated 0/1 — anything
    # downstream must filter on in_scope before using these columns.
    merged["treated"] = merged["treated"].astype("Int64")
    merged["sensitivity_treated"] = merged["sensitivity_treated"].astype("Int64")

    return merged


def missingness_report(panel: pd.DataFrame) -> str:
    lines = ["# Panel Missingness Report", ""]

    lines.append("## Overall")
    lines.append("")
    n_rows = len(panel)
    n_usable = int(panel["usable"].sum())
    n_fips_all_waves = panel.loc[panel["waves_present"] == len(WAVES), "fips"].nunique()
    n_fips_total = panel["fips"].nunique()
    lines.append(f"- Total jurisdiction-year rows: {n_rows:,}")
    lines.append(f"- Usable rows: {n_usable:,} ({n_usable / n_rows:.1%})")
    lines.append(f"- Distinct FIPS across all waves: {n_fips_total:,}")
    lines.append(f"- FIPS present in all {len(WAVES)} waves: {n_fips_all_waves:,}")
    n_in_scope_states = panel.loc[panel["in_scope"], "state_abbr"].nunique()
    n_territories = panel.loc[~panel["in_scope"], "state_abbr"].nunique()
    lines.append(
        f"- Treatment join (src/04_build_treatment.py): 100% match on all "
        f"{n_in_scope_states} states + DC x {len(WAVES)} waves (see "
        f"join_treatment() in this script for the assertion that enforces "
        f"this). {n_territories} U.S. territories ({', '.join(TERRITORIES)}) "
        f"are out of scope for the treatment variable (`in_scope=False`, "
        f"`treated`/`sensitivity_treated` left null) — the coding sheet "
        f"only covers the 50 states + DC."
    )
    n_outliers = int(panel["flagged_outlier"].sum())
    lines.append(
        f"- Outlier flag (VALIDATION_REPORT.md Defect 7): {n_outliers} usable "
        f"jurisdiction-years have `rejection_rate == 1.0` exactly (implausible "
        f"for any but a handful of ballots) and are marked `flagged_outlier=True`. "
        f"Not removed from `usable` — see the flag_outliers() docstring in "
        f"this script for why."
    )
    lines.append("")

    lines.append("## Usable-row share by state (ascending — worst first)")
    lines.append("")
    lines.append(
        "Missingness is dominated by state, not jurisdiction size: some states "
        "simply don't report the rejected-ballot field in a given wave. Listwise "
        "deletion would drop these states' jurisdictions disproportionately."
    )
    lines.append("")
    by_state = (
        panel.groupby("state_abbr")["usable"]
        .agg(rows="count", usable_share="mean")
        .sort_values("usable_share")
    )
    lines.append("| state | rows | usable share |")
    lines.append("|---|---|---|")
    for state, row in by_state.iterrows():
        lines.append(f"| {state} | {int(row['rows']):,} | {row['usable_share']:.1%} |")
    lines.append("")

    lines.append("## Usable-row share by jurisdiction-size quartile")
    lines.append("")
    lines.append(
        "Size = each jurisdiction's largest observed `returned_by_voters` across "
        "its available waves (a jurisdiction's scale doesn't shift enough year to "
        "year for this to matter, and using the max avoids a jurisdiction with one "
        "missing wave being miscategorized as tiny)."
    )
    lines.append("")
    size = panel.groupby("fips")["returned_by_voters"].max().rename("size_proxy")
    sized = panel.merge(size, on="fips")
    sized["size_quartile"] = pd.qcut(sized["size_proxy"], 4, duplicates="drop")
    by_size = sized.groupby("size_quartile", observed=True)["usable"].agg(rows="count", usable_share="mean")
    lines.append("| size quartile (returned_by_voters) | rows | usable share |")
    lines.append("|---|---|---|")
    for interval, row in by_size.iterrows():
        lines.append(f"| {interval} | {int(row['rows']):,} | {row['usable_share']:.1%} |")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    MISSINGNESS_REPORT.parent.mkdir(parents=True, exist_ok=True)

    panel = load_panel()

    panel.to_parquet(PROCESSED / "panel.parquet", index=False)
    panel.to_csv(PROCESSED / "panel.csv", index=False)
    print(f"wrote {PROCESSED / 'panel.parquet'} and panel.csv ({len(panel):,} rows)")
    print(f"  usable: {panel['usable'].sum():,} ({panel['usable'].mean():.1%})")
    n_fips_all_waves = panel.loc[panel["waves_present"] == len(WAVES), "fips"].nunique()
    print(f"  FIPS present in all {len(WAVES)} waves: {n_fips_all_waves:,}")

    report = missingness_report(panel)
    MISSINGNESS_REPORT.write_text(report + "\n")
    print(f"wrote {MISSINGNESS_REPORT}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
