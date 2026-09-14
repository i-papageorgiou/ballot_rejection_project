"""
07_figures.py — Derive the panel-based JSON data the Week 5 dashboard
(docs/index.html) reads directly. No model fitting happens here — that's
06_estimate.R's job (see docs/data/model_comparison.json etc., authored
alongside that script). This script only summarizes the panel itself:
the rejection-rate distribution by state, and the county-level values
for the choropleth.

Choropleth scope decision (see PROJECT_PLAN.md's Week 5 section for the
full reasoning): EAVS jurisdictions are counties in most states, but 7
states report at the town/municipality level instead (confirmed via the
ratio of jurisdiction-count to 5-digit-FIPS-prefix-count: Wisconsin is
1,861:1, the New England states range 8:1 to 32:1, every other state is
~1:1). For a normal county-reporting state, the panel's 10-digit `fips`
string's first 5 characters ARE the real Census county FIPS (confirmed:
'0603700000' -> '06037' = Los Angeles County). Wisconsin's town-level
FIPS are a synthetic '00000...' prefix with no county encoding at all —
there is no cheap way to recover the county for these 7 states without
an external, unvalidated town-to-county crosswalk, so they are excluded
from the choropleth (grayed out client-side) rather than mapped
incorrectly or silently dropped without explanation.

Usage:
    python src/07_figures.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PANEL_PATH = ROOT / "data" / "processed" / "panel.parquet"
DOCS_DATA = ROOT / "docs" / "data"

WAVES = (2016, 2018, 2020, 2022, 2024)

# The 7 states confirmed to report at town/municipality level, not
# county — see module docstring for the verification method.
TOWN_LEVEL_STATES = ("WI", "NH", "ME", "MA", "CT", "VT", "RI")


def load_usable() -> pd.DataFrame:
    panel = pd.read_parquet(PANEL_PATH)
    return panel[panel["usable"] & panel["in_scope"]].copy()


def build_state_distribution(u: pd.DataFrame) -> dict:
    """Per-state, per-wave rejection_rate distribution summary."""
    rows = []
    grouped = u.groupby(["state_abbr", "year"])["rejection_rate"]
    stats = grouped.agg(
        median="median",
        p25=lambda s: s.quantile(0.25),
        p75=lambda s: s.quantile(0.75),
        n="count",
    ).reset_index()
    for _, row in stats.iterrows():
        rows.append({
            "state": row["state_abbr"],
            "year": int(row["year"]),
            "median": round(float(row["median"]), 5),
            "p25": round(float(row["p25"]), 5),
            "p75": round(float(row["p75"]), 5),
            "n": int(row["n"]),
        })
    return {"waves": list(WAVES), "rows": rows}


def build_county_choropleth(u: pd.DataFrame) -> dict:
    """Most-recent-wave county rejection rate, county-reporting states only."""
    mappable = u[~u["state_abbr"].isin(TOWN_LEVEL_STATES)].copy()
    mappable["county_fips"] = mappable["fips"].str[:5]

    latest_wave = max(WAVES)
    latest = mappable[mappable["year"] == latest_wave]

    # Aggregate to county level (sum counts, not average rates) in case
    # a county has multiple jurisdiction rows for the same wave.
    agg = latest.groupby(["county_fips", "state_abbr"]).agg(
        rejected_total=("rejected_total", "sum"),
        returned_by_voters=("returned_by_voters", "sum"),
        jurisdiction_name=("jurisdiction_name", "first"),
    ).reset_index()
    agg["rejection_rate"] = agg["rejected_total"] / agg["returned_by_voters"]

    counties = [
        {
            "fips": row["county_fips"],
            "state": row["state_abbr"],
            "name": row["jurisdiction_name"],
            "rejection_rate": round(float(row["rejection_rate"]), 5),
        }
        for _, row in agg.iterrows()
        if row["returned_by_voters"] > 0
    ]

    return {
        "wave": latest_wave,
        "counties": counties,
        "excluded_states": list(TOWN_LEVEL_STATES),
        "excluded_reason": (
            "These 7 states report EAVS data at the town/municipality "
            "level, not the county level. Their jurisdiction FIPS codes "
            "either don't encode a real county (Wisconsin) or would "
            "need an external, unvalidated town-to-county crosswalk to "
            "aggregate correctly (New England) — see PROJECT_PLAN.md's "
            "Week 5 section. Shown gray on the map, not silently "
            "omitted."
        ),
    }


def main() -> int:
    DOCS_DATA.mkdir(parents=True, exist_ok=True)
    u = load_usable()

    state_dist = build_state_distribution(u)
    (DOCS_DATA / "state_distribution.json").write_text(json.dumps(state_dist, indent=2))
    print(f"wrote {DOCS_DATA / 'state_distribution.json'} ({len(state_dist['rows'])} rows)")

    choropleth = build_county_choropleth(u)
    (DOCS_DATA / "county_choropleth.json").write_text(json.dumps(choropleth, indent=2))
    print(
        f"wrote {DOCS_DATA / 'county_choropleth.json'} "
        f"({len(choropleth['counties'])} counties, wave {choropleth['wave']}, "
        f"{len(choropleth['excluded_states'])} states excluded)"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
