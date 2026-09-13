"""
Validation suite for the EAVS cleaning pipeline's current state.

Checks codebooks/crosswalk.yaml (from 02_build_crosswalk.py) and
data/interim/eavs_<year>.parquet (from 03_clean_eavs.py) against the same
regression fixtures and cleaning rules documented in
codebooks/variable_memo.md and PROJECT_PLAN.md — independently of
03_clean_eavs.py's own inline validate() gate, so a bug or a weakened
assertion inside that module doesn't go unnoticed just because the module's
own report says PASSED.

Run: pytest tests/ -v
"""

from __future__ import annotations

import pandas as pd
import pytest

from conftest import RAW, WAVES

# Verified national rejected-ballot totals (see PROJECT_PLAN.md / this
# repo's own validation_report.md). Exact-match regression fixtures.
EXPECTED_NATIONAL_TOTAL = {
    2016: 318_728,
    2018: 430_196,
    2020: 560_826,
    2022: 549_824,
    2024: 584_463,
}

# Verified numerator/denominator column letters per wave (variable_memo.md).
EXPECTED_MAPPING = {
    2016: dict(returned_by_voters="C1b", rejected_total="C4b"),
    2018: dict(returned_by_voters="C1b", rejected_total="C4a"),
    2020: dict(returned_by_voters="C1b", rejected_total="C4a"),
    2022: dict(returned_by_voters="C1b", rejected_total="C9a"),
    2024: dict(returned_by_voters="C1b", rejected_total="C9a"),
}

# Verified rejection-reason column counts per wave.
EXPECTED_N_REASONS = {2016: 22, 2018: 17, 2020: 17, 2022: 19, 2024: 19}

# Verified usable-row share per wave, with slack either side.
EXPECTED_USABLE_RANGE = {
    2016: (0.85, 0.95),
    2018: (0.92, 0.99),
    2020: (0.93, 0.99),
    2022: (0.91, 0.98),
    2024: (0.90, 0.98),
}

# Verified median rejection rate (%) among usable rows per wave — the 2020
# dip is a real, documented feature, not noise, so this is checked tightly.
EXPECTED_MEDIAN_RATE_PCT = {2016: 0.37, 2018: 0.67, 2020: 0.25, 2022: 0.47, 2024: 0.39}
MEDIAN_RATE_TOLERANCE_PCT = 0.05

# The 3 known duplicate-FIPS jurisdictions (post-zfill(10)) and the raw
# FIPSCode value each was assigned before cleaning.
KNOWN_DUPLICATES = {
    2020: [("0000082575", "82575"), ("0000084275", "84275")],
    2022: [("0000031550", "31550")],
}

EXPECTED_INTERIM_COLUMNS = [
    "fips", "state_abbr", "state_full", "jurisdiction_name", "year",
    "transmitted_total", "returned_by_voters", "counted_total", "rejected_total",
    "reason_sum", "rejection_rate", "usable", "dup_resolved",
]


# ---- crosswalk.yaml ----

def test_crosswalk_schema(crosswalk, wave):
    cw = crosswalk[wave]
    for role in ("transmitted_total", "returned_by_voters", "counted_total", "rejected_total"):
        assert cw.get(role), f"{wave}: missing or empty '{role}'"
    reasons = cw.get("rejection_reasons")
    assert reasons, f"{wave}: rejection_reasons is missing or empty"
    assert len(reasons) == EXPECTED_N_REASONS[wave], (
        f"{wave}: expected {EXPECTED_N_REASONS[wave]} rejection-reason columns, "
        f"got {len(reasons)} ({reasons})"
    )


def test_crosswalk_matches_known_mapping(crosswalk, wave):
    """The check that would catch the 2016 C4a/C4b inversion if the
    crosswalk regressed: the numerator/denominator letters must match the
    empirically verified mapping, not just be present."""
    cw = crosswalk[wave]
    expected = EXPECTED_MAPPING[wave]
    assert cw["returned_by_voters"] == expected["returned_by_voters"]
    assert cw["rejected_total"] == expected["rejected_total"]


# ---- interim parquet files ----

def test_interim_schema(interim: pd.DataFrame):
    assert list(interim.columns) == EXPECTED_INTERIM_COLUMNS
    assert interim["usable"].dtype == bool
    assert interim["dup_resolved"].dtype == bool
    assert (interim["fips"].str.len() == 10).all(), "fips must be zero-padded to 10 characters"


def test_national_totals_exact(interim: pd.DataFrame, wave: int):
    actual = int(interim["rejected_total"].sum())
    expected = EXPECTED_NATIONAL_TOTAL[wave]
    assert actual == expected, (
        f"{wave}: national rejected total drifted ({actual:,} vs. expected {expected:,}) "
        "— a cleaning or crosswalk regression, not noise."
    )


def test_reason_sum_correlation(interim: pd.DataFrame, wave: int):
    both = interim["rejected_total"].notna() & interim["reason_sum"].notna()
    corr = interim.loc[both, "rejected_total"].corr(interim.loc[both, "reason_sum"])
    exact = (interim.loc[both, "rejected_total"] - interim.loc[both, "reason_sum"]).abs().le(1e-6).mean()
    assert corr >= 0.95, f"{wave}: rejected_total/reason_sum correlation {corr:.4f} < 0.95"
    assert exact >= 0.85, f"{wave}: rejected_total/reason_sum exact-match {exact:.1%} < 85%"


def test_no_duplicate_fips(interim: pd.DataFrame, wave: int):
    n_dup = int(interim["fips"].duplicated().sum())
    assert n_dup == 0, f"{wave}: {n_dup} duplicate FIPS remain after cleaning"


def test_known_duplicates_were_resolved(interim_by_wave):
    """Re-derives, from the raw CSVs (the one place this suite reads raw
    data), that each known duplicate pair was summed rather than dropped —
    a regression that silently kept only one member wouldn't necessarily
    violate the national-total fixture if it happened to be the zero-count
    member of the pair, so this is checked directly."""
    for year, pairs in KNOWN_DUPLICATES.items():
        df = interim_by_wave[year]
        raw = pd.read_csv(RAW / f"eavs_{year}.csv", encoding="latin-1", dtype=str, low_memory=False)
        for clean_fips, raw_fips in pairs:
            row = df[df["fips"] == clean_fips]
            assert len(row) == 1, f"{year}: expected exactly 1 resolved row for {clean_fips}, found {len(row)}"
            assert bool(row.iloc[0]["dup_resolved"]) is True, (
                f"{year}: {clean_fips} exists but dup_resolved is not True"
            )
            raw_group = raw[raw["FIPSCode"] == raw_fips]
            assert len(raw_group) == 2, f"{year}: expected 2 raw rows for FIPSCode {raw_fips}"
            expected_sum = pd.to_numeric(raw_group["C1b"], errors="coerce").sum()
            assert row.iloc[0]["returned_by_voters"] == pytest.approx(expected_sum), (
                f"{year}: {clean_fips} returned_by_voters does not equal the sum of both raw rows "
                "— duplicate resolution may have dropped one instead of summing"
            )


def test_usable_share_within_expected_range(interim: pd.DataFrame, wave: int):
    share = interim["usable"].mean()
    lo, hi = EXPECTED_USABLE_RANGE[wave]
    assert lo <= share <= hi, f"{wave}: usable share {share:.1%} outside expected [{lo:.0%}, {hi:.0%}]"


def test_usable_implies_rate_in_range(interim: pd.DataFrame, wave: int):
    usable_rows = interim[interim["usable"]]
    assert usable_rows["rejected_total"].notna().all(), f"{wave}: a usable row has a null rejected_total"
    assert usable_rows["returned_by_voters"].notna().all(), f"{wave}: a usable row has a null returned_by_voters"
    assert usable_rows["rejection_rate"].between(0, 1).all(), (
        f"{wave}: a usable row has rejection_rate outside [0, 1]"
    )


def test_unusable_rows_are_kept_not_dropped(interim: pd.DataFrame, wave: int):
    """Confirms the 'flag, don't drop' rule (03_clean_eavs.py's docstring)
    hasn't regressed into silent deletion of unusable rows."""
    assert (~interim["usable"]).sum() > 0, (
        f"{wave}: no unusable rows present — either data quality improved to "
        "100% (unlikely) or unusable rows are being dropped instead of flagged"
    )


def test_median_rejection_rate_by_wave(interim: pd.DataFrame, wave: int):
    median_pct = interim.loc[interim["usable"], "rejection_rate"].median() * 100
    expected_pct = EXPECTED_MEDIAN_RATE_PCT[wave]
    assert median_pct == pytest.approx(expected_pct, abs=MEDIAN_RATE_TOLERANCE_PCT), (
        f"{wave}: median usable rejection_rate {median_pct:.2f}% drifted from "
        f"expected {expected_pct:.2f}% — the 2020 dip pattern may have been lost"
    )
