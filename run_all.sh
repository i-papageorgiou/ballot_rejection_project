#!/usr/bin/env bash
# run_all.sh — Rebuild the entire pipeline from raw downloads to
# first-cut estimates, in one command.
#
# Referenced by PROJECT_PLAN.md's Verification section; written to make
# that claim true (VALIDATION_REPORT.md Defect 4 — this file didn't
# exist despite being cited as the reproducibility check).
#
# Requires: the anaconda python3 distribution (pyarrow, pandas, etc. —
# see requirements.txt / README.md's setup note; the system python3 on
# macOS lacks pyarrow and will fail step 3 onward), plus the R packages
# listed in README.md for the final step.
#
# Usage:
#   bash run_all.sh

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

PYTHON="${PYTHON:-python3}"

echo "== 1/7: download raw EAVS waves + codebooks =="
"$PYTHON" src/01_download.py

echo "== 2/7: derive variable crosswalk =="
"$PYTHON" src/02_build_crosswalk.py

echo "== 3/7: clean + validate each wave =="
"$PYTHON" src/03_clean_eavs.py

echo "== 4/7: independent pytest suite =="
"$PYTHON" -m pytest tests/ -q

echo "== 5/7: code the 51-state treatment variable =="
"$PYTHON" src/04_build_treatment.py

echo "== 6/7: stack panel + join treatment =="
"$PYTHON" src/05_build_panel.py

echo "== 7/7: TWFE, Sun-Abraham, Callaway-Sant'Anna, bootstrap, heterogeneity, robustness (~25-30 min, dominated by the wild-cluster bootstrap step) =="
Rscript src/06_estimate.R

echo "== done: data/processed/panel.{parquet,csv}, output/tables/{estimates_v1,heterogeneity,robustness_checklist}.md =="
