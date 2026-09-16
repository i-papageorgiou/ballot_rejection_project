"""
Shared fixtures for the pipeline validation suite.

These tests check committed artifacts (codebooks/crosswalk.yaml,
data/interim/eavs_<year>.parquet) from outside src/03_clean_eavs.py, so a
regression here is caught even if that script's own inline validate() gate
is weakened or removed. Nothing here re-runs the pipeline or touches
data/raw/, except test_known_duplicates_were_resolved, which reads the raw
CSVs once to independently re-derive the one value the pipeline computes by
summing (see its own docstring).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
CROSSWALK_PATH = ROOT / "codebooks" / "crosswalk.yaml"

WAVES = (2014, 2016, 2018, 2020, 2022, 2024)


@pytest.fixture(scope="session")
def crosswalk() -> dict[int, dict]:
    waves = yaml.safe_load(CROSSWALK_PATH.read_text())["waves"]
    return {w["wave"]: w for w in waves}


@pytest.fixture(scope="session", params=WAVES)
def wave(request) -> int:
    """Parametrizes any test that takes it, once per EAVS wave."""
    return request.param


@pytest.fixture(scope="session")
def interim_by_wave() -> dict[int, pd.DataFrame]:
    return {year: pd.read_parquet(INTERIM / f"eavs_{year}.parquet") for year in WAVES}


@pytest.fixture(scope="session")
def interim(wave: int, interim_by_wave: dict[int, pd.DataFrame]) -> pd.DataFrame:
    return interim_by_wave[wave]
