"""
08_merge_controls.py — County-level ACS demographic controls, deferred
since Week 2 (no Census API key existed until now).

Produces data/processed/acs_controls.csv (county x wave-year), completely
independent of panel.parquet and the numbered 01->07 pipeline — this is a
later script number than 05_build_panel.py, so wiring it into the panel
build would break the numbering-as-build-order convention the rest of
this pipeline keeps. Using these controls in 06_estimate.R (a real
urban/rural heterogeneity split, or as att_gt's xformla covariates) is
deliberately deferred to a follow-up round; this script only builds and
verifies the controls file itself.

Scope, same reasoning as the Week 5 choropleth's county-coverage decision
(see PROJECT_PLAN.md): merges at the county level (fips[:5]), which only
resolves to a real county for the 44 states + DC that report EAVS at true
county granularity. The 7 town/municipality-reporting states (WI + New
England) get acs_matched=False placeholder rows, not a silent absence.
Territories are out of scope entirely (standard ACS doesn't cover 4 of
the 5, and Puerto Rico's own ACS uses different variable codes not worth
a one-territory special case).

Variables (ACS 5-year detailed tables, confirmed live against every
vintage 2014-2024 before writing this, including 2020's COVID-era
vintage, which does NOT have a coverage gap for these tables):
  B19013_001E              median household income
  B01002_001E               median age
  B03002_001E/_003E/_004E/_012E   race/ethnicity: total, White non-Hispanic,
                             Black non-Hispanic, Hispanic (any race)
  B15003_001E + _022E..._025E     education: 25+ population, and
                             bachelor's/master's/professional/doctorate
Rurality: NCHS's Urban-Rural Classification Scheme for Counties (static
CSV, no API key), CODE2013 column — the scheme in general use for most
of the panel's actual span (2014-2022); not varied per wave since a
county's category rarely changes year to year.

Usage:
    python src/08_merge_controls.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
ENV_PATH = ROOT / ".env"
OUT_PATH = PROCESSED / "acs_controls.csv"

VINTAGES = (2014, 2016, 2018, 2020, 2022, 2024)

NCHS_URL = "https://www.cdc.gov/nchs/data/data-analysis/NCHSurb-rural-codes.csv"
NCHS_PATH = RAW / "nchs_urban_rural.csv"

# Same 7 states already excluded from the Week 5 choropleth (see
# src/07_figures.py) for the identical reason: EAVS reports them at the
# town/municipality level, so their jurisdiction FIPS doesn't resolve to
# a real county. Duplicated rather than shared via a new module for a
# 2-file usage, matching this project's existing tolerance for small,
# well-commented duplication (e.g. each script's own WAVES tuple).
TOWN_LEVEL_STATES = ("WI", "NH", "ME", "MA", "CT", "VT", "RI")

ACS_VARS = [
    "B19013_001E",
    "B01002_001E",
    "B03002_001E", "B03002_003E", "B03002_004E", "B03002_012E",
    "B15003_001E", "B15003_022E", "B15003_023E", "B15003_024E", "B15003_025E",
]


def _load_env() -> None:
    """Minimal .env parser (KEY=value lines) — no new dependency for
    something this small; python-dotenv isn't installed."""
    import os
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def _api_key() -> str:
    import os
    _load_env()
    key = os.environ.get("CENSUS_API_KEY")
    if not key:
        raise SystemExit(
            "CENSUS_API_KEY not set. Add it to .env at the repo root "
            "(CENSUS_API_KEY=...) — see HANDOFF.md for how to get one."
        )
    return key


def fetch_vintage(year: int, key: str) -> list[list[str]]:
    """One nationwide API call per vintage (for=county:*, no state
    filter — confirmed this works nationally, not just per-state).
    Cached to data/raw/acs_<year>.json so reruns don't re-hit the API."""
    cache = RAW / f"acs_{year}.json"
    if cache.exists():
        return json.loads(cache.read_text())

    url = f"https://api.census.gov/data/{year}/acs/acs5"
    params = {"get": ",".join(["NAME"] + ACS_VARS), "for": "county:*", "key": key}
    resp = requests.get(url, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    cache.write_text(json.dumps(data))
    return data


def parse_vintage(raw_rows: list[list[str]], year: int) -> pd.DataFrame:
    header, rows = raw_rows[0], raw_rows[1:]
    df = pd.DataFrame(rows, columns=header)
    df["county_fips"] = df["state"].str.zfill(2) + df["county"].str.zfill(3)
    for v in ACS_VARS:
        df[v] = pd.to_numeric(df[v], errors="coerce")

    out = pd.DataFrame({
        "county_fips": df["county_fips"],
        "year": year,
        "median_income": df["B19013_001E"].mask(df["B19013_001E"] < 0),
        "median_age": df["B01002_001E"].mask(df["B01002_001E"] < 0),
    })
    total_race = df["B03002_001E"]
    out["pct_white_nh"] = df["B03002_003E"] / total_race
    out["pct_black_nh"] = df["B03002_004E"] / total_race
    out["pct_hispanic"] = df["B03002_012E"] / total_race

    higher_ed = df[["B15003_022E", "B15003_023E", "B15003_024E", "B15003_025E"]].sum(axis=1)
    out["pct_bachelors_plus"] = higher_ed / df["B15003_001E"]

    return out


def fetch_nchs() -> pd.DataFrame:
    if not NCHS_PATH.exists():
        resp = requests.get(NCHS_URL, timeout=60)
        resp.raise_for_status()
        NCHS_PATH.write_bytes(resp.content)
    df = pd.read_csv(NCHS_PATH, dtype=str, encoding="latin-1")
    df["county_fips"] = df["STFIPS"].str.zfill(2) + df["CTYFIPS"].str.zfill(3)
    return df[["county_fips", "CODE2013"]].rename(columns={"CODE2013": "nchs_rurality_2013"})


def load_panel_counties() -> pd.DataFrame:
    """(county_fips, year, state_abbr) pairs actually present in the
    panel, so coverage can be checked against real jurisdictions rather
    than against every county ACS happens to report."""
    panel = pd.read_parquet(PROCESSED / "panel.parquet")
    panel = panel[panel["in_scope"]].copy()
    panel["county_fips"] = panel["fips"].str[:5]
    return panel[["county_fips", "year", "state_abbr"]].drop_duplicates()


def main() -> int:
    key = _api_key()
    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    frames = []
    for year in VINTAGES:
        raw_rows = fetch_vintage(year, key)
        frames.append(parse_vintage(raw_rows, year))
        print(f"{year}: fetched/parsed {len(raw_rows) - 1} counties")
    acs = pd.concat(frames, ignore_index=True)

    nchs = fetch_nchs()
    acs = acs.merge(nchs, on="county_fips", how="left")

    panel_counties = load_panel_counties()
    mappable = panel_counties[~panel_counties["state_abbr"].isin(TOWN_LEVEL_STATES)]
    excluded = panel_counties[panel_counties["state_abbr"].isin(TOWN_LEVEL_STATES)]

    merged = mappable.merge(acs, on=["county_fips", "year"], how="left")
    merged["acs_matched"] = merged["median_income"].notna()

    excluded_rows = excluded[["county_fips", "year"]].drop_duplicates().copy()
    excluded_rows["acs_matched"] = False
    # Every other column (median_income, pct_*, nchs_rurality_2013) is left
    # unset here — pd.concat aligns them to NaN automatically, avoiding the
    # dtype mismatch that comes from pre-filling with pd.NA on columns
    # that are float64 in `merged`.

    final = pd.concat(
        [merged.drop(columns="state_abbr"), excluded_rows],
        ignore_index=True,
    )

    # --- Verification -----------------------------------------------------
    coverage = merged.groupby("year")["acs_matched"].mean()
    print("\nCoverage (44 states + DC only, by wave):")
    for year, share in coverage.items():
        flag = "OK" if share >= 0.98 else "LOW — investigate"
        print(f"  {year}: {share:.1%} {flag}")

    race_sum = final[["pct_white_nh", "pct_black_nh", "pct_hispanic"]].sum(axis=1, skipna=True)
    over_100 = (race_sum > 1.0001).sum()
    assert over_100 == 0, f"{over_100} county-years have race shares summing over 100%"
    print(f"\nRace-share sanity check: 0 county-years exceed 100% (checked {len(final):,} rows)")

    final = final.drop_duplicates(subset=["county_fips", "year"]).sort_values(["county_fips", "year"])
    final.to_csv(OUT_PATH, index=False)
    print(f"\nwrote {OUT_PATH} ({len(final):,} rows)")
    print(f"  {final['acs_matched'].sum():,} matched, {(~final['acs_matched']).sum():,} unmatched (town-reporting states)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
