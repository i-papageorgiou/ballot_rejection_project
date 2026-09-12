"""
01_download.py — Acquire all EAVS waves and codebooks.

Downloads the five EAVS public-release data files (2016-2024) and their
codebooks into data/raw/. Idempotent: existing files with the expected size
are skipped, so re-running is a no-op.

Every URL below was verified live (HTTP 200) before being committed to this
script. Sizes are recorded so that a silent upstream change is caught here
rather than surfacing as a mysterious result three scripts later.

Note on the 2024 wave: the EAC published V1 in June 2025 and revised it to
V2 in February 2026. We use V2. Any figure produced from this repo refers to
the V2 revision.

Usage:
    python src/01_download.py [--force]
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

BASE = "https://www.eac.gov"
RAW = Path(__file__).resolve().parent.parent / "data" / "raw"

# Tolerance for the size check. The EAC occasionally re-serves a file with
# trivially different bytes; a large deviation means the file really changed.
SIZE_TOLERANCE = 0.02


@dataclass(frozen=True)
class Resource:
    """One downloadable file."""

    wave: int
    kind: str  # "data" or "codebook"
    url: str
    filename: str
    expected_bytes: int
    member: str | None = None  # file to extract, when the download is a zip

    @property
    def path(self) -> Path:
        return RAW / self.filename


RESOURCES: list[Resource] = [
    # ---- data ----
    Resource(
        2016, "data",
        f"{BASE}/sites/default/files/2023-12/EAVS_2016_for_Public_Release_nolabel_V1.1_CSV.zip",
        "eavs_2016.zip", 2_433_517,
        member="EAVS_2016_Final_Data_for_Public_Release_nolabel_V1.1_CSV.csv",
    ),
    Resource(
        2018, "data",
        f"{BASE}/sites/default/files/2019-10/EAVS_2018_for_Public_Release_nolabel%20v1.1.csv",
        "eavs_2018.csv", 23_398_380,
    ),
    Resource(
        2020, "data",
        f"{BASE}/sites/default/files/2023-12/2020_EAVS_for_Public_Release_nolabel_V1.2_CSV.zip",
        "eavs_2020.zip", 2_037_428,
        member="2020_EAVS_for_Public_Release_nolabel_V1.2_CSV.csv",
    ),
    Resource(
        2022, "data",
        f"{BASE}/sites/default/files/2023-12/2022_EAVS_for_Public_Release_nolabel_V1.1_CSV.zip",
        "eavs_2022.zip", 2_048_270,
        member="2022_EAVS_for_Public_Release_nolabel_V1.1_CSV.csv",
    ),
    Resource(
        2024, "data",
        f"{BASE}/sites/default/files/2026-02/2024_EAVS_for_Public_Release_nolabel_V2_csv.zip",
        "eavs_2024.zip", 2_119_187,
        member="2024_EAVS_for_Public_Release_nolabel_V2.csv",
    ),
    # ---- codebooks ----
    # 2016 is the only PDF; the rest are .xlsx with a machine-readable
    # "Variables" sheet that 02_build_crosswalk.py parses.
    Resource(
        2016, "codebook",
        f"{BASE}/sites/default/files/eac_assets/1/6/EAVS_Codebook_2016.pdf",
        "codebook_2016.pdf", 2_773_064,
    ),
    Resource(
        2018, "codebook",
        f"{BASE}/sites/default/files/eac_assets/1/6/2018_EAVS_Codebook.xlsx",
        "codebook_2018.xlsx", 43_611,
    ),
    Resource(
        2020, "codebook",
        f"{BASE}/sites/default/files/2021-08/2020_EAVS_Codebook.xlsx",
        "codebook_2020.xlsx", 47_906,
    ),
    Resource(
        2022, "codebook",
        f"{BASE}/sites/default/files/2023-06/2022_EAVS_Codebook.xlsx",
        "codebook_2022.xlsx", 55_776,
    ),
    Resource(
        2024, "codebook",
        f"{BASE}/sites/default/files/2025-06/2024_EAVS_Codebook.xlsx",
        "codebook_2024.xlsx", 59_688,
    ),
]


def fetch(res: Resource, force: bool = False) -> str:
    """Download one resource. Returns a short status string."""
    if res.path.exists() and not force:
        actual = res.path.stat().st_size
        if abs(actual - res.expected_bytes) / res.expected_bytes <= SIZE_TOLERANCE:
            return "skip (present)"
        print(f"    size drift: have {actual:,}, expect {res.expected_bytes:,} — refetching")

    # eac.gov rejects the default urllib agent.
    req = Request(res.url, headers={"User-Agent": "Mozilla/5.0 (research; EAVS panel build)"})
    with urlopen(req, timeout=180) as r:
        data = r.read()

    res.path.write_bytes(data)

    delta = abs(len(data) - res.expected_bytes) / res.expected_bytes
    if delta > SIZE_TOLERANCE:
        return f"WARNING got {len(data):,} bytes, expected {res.expected_bytes:,}"
    return f"ok ({len(data):,} bytes)"


def extract(res: Resource) -> str:
    """Extract the CSV from a zipped resource into data/raw/."""
    if res.member is None:
        return ""
    out = RAW / f"eavs_{res.wave}.csv"
    if out.exists():
        return f"    extracted: {out.name} (present)"
    with zipfile.ZipFile(res.path) as z:
        names = z.namelist()
        if res.member not in names:
            raise FileNotFoundError(
                f"{res.filename}: expected member {res.member!r}, found {names!r}"
            )
        out.write_bytes(z.read(res.member))
    return f"    extracted: {out.name} ({out.stat().st_size:,} bytes)"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="re-download even if present")
    args = ap.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    warnings = 0

    for kind in ("data", "codebook"):
        print(f"\n=== {kind} ===")
        for res in [r for r in RESOURCES if r.kind == kind]:
            status = fetch(res, force=args.force)
            if status.startswith("WARNING"):
                warnings += 1
            print(f"  {res.wave} {res.filename:24} {status}")
            note = extract(res)
            if note:
                print(note)

    print(f"\nRaw files in {RAW}:")
    for f in sorted(RAW.iterdir()):
        print(f"  {f.name:34} {f.stat().st_size:>12,} bytes")

    if warnings:
        print(f"\n{warnings} size warning(s) — an upstream file may have been revised.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
