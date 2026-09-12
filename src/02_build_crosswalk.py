"""
02_build_crosswalk.py — Derive the EAVS variable crosswalk from the EAC's
own codebooks, rather than transcribing it by hand.

2018, 2020, 2022, and 2024 codebooks ship as .xlsx with a "Variables" sheet
(columns VariableName, Label, ...). This script parses those sheets, finds
the mail-ballot transmitted/returned/counted/rejected variables and the
rejection-reason breakdown columns by matching their labels, and writes
codebooks/crosswalk.yaml.

The 2016 codebook is a PDF with no machine-readable variable table, and its
own labels do not disambiguate C4a (counted) from C4b (rejected) the way
later waves' labels do. Its row is written from the empirically verified
mapping in codebooks/eavs_variable_crosswalk.md (see the correlation/
exact-match test in 03_clean_eavs.py's validation gate) — not guessed here.

Usage:
    python src/02_build_crosswalk.py
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "codebooks" / "crosswalk.yaml"

# Label predicates used to identify each role from the codebook's own Label
# column. Word order varies by wave ("Mail Rejected Total" in 2022 vs.
# "Total Mail Ballots Rejected" in 2024), so these match on presence of the
# right words rather than an anchored phrase, while excluding the
# reason-breakdown rows (e.g. "Rejected Because Late") and drop-box/comment
# fields that would otherwise false-match.
_EXCLUDE = re.compile(r"because|comment|drop ?box|undeliverable|unreturned", re.I)

# Looser exclusion for the reason-breakdown match below: "because" is exactly
# what marks a reason row in 2024's phrasing ("Rejected Because Late"), so it
# must NOT be excluded there, unlike in the total/transmitted/returned/counted
# predicates above where it is the signal that a row is a reason, not a total.
_EXCLUDE_REASON = re.compile(r"comment|drop ?box|undeliverable|unreturned", re.I)


def _is_transmitted_total(label: str) -> bool:
    return bool(re.search(r"transmit", label, re.I)) and re.search(r"\btotal\b", label, re.I) and not _EXCLUDE.search(label)


def _is_returned_by_voters(label: str) -> bool:
    return bool(re.search(r"returned\b.*(by voters|for counting)", label, re.I)) and not _EXCLUDE.search(label)


def _is_rejected_total(label: str) -> bool:
    return bool(re.search(r"reject", label, re.I)) and re.search(r"\btotal\b", label, re.I) and not _EXCLUDE.search(label)


def _is_counted_total(label: str) -> bool:
    return bool(re.search(r"counted", label, re.I)) and re.search(r"\btotal\b", label, re.I) and not _EXCLUDE.search(label)


def _is_rejection_reason(label: str) -> bool:
    """A rejection-reason breakdown column: the exact complement of
    _is_rejected_total — mentions "reject" but is not the total itself.
    _Other/Comments companion columns are filtered separately in parse_wave,
    since VariableName (not Label) is what marks them.
    """
    return bool(re.search(r"reject", label, re.I)) and not re.search(r"\btotal\b", label, re.I) and not _EXCLUDE_REASON.search(label)


ROLE_PREDICATES = {
    "transmitted_total": _is_transmitted_total,
    "returned_by_voters": _is_returned_by_voters,
    "rejected_total": _is_rejected_total,
    "counted_total": _is_counted_total,
}


def parse_wave(year: int) -> dict:
    path = RAW / f"codebook_{year}.xlsx"
    df = pd.ExcelFile(path).parse("Variables", dtype=str).fillna("")
    df = df[df["VariableName"].str.match(r"^C\d", na=False)]

    found: dict[str, str] = {}
    reasons: list[str] = []
    for _, row in df.iterrows():
        name = row["VariableName"]
        label = re.sub(r"\s+", " ", row["Label"]).strip()
        for role, predicate in ROLE_PREDICATES.items():
            if role in found:
                continue
            if predicate(label):
                found[role] = name
        # Reason-breakdown columns: exclude the free-text "_Other" companion
        # and "Comments" fields, which carry the label word "reject" too but
        # are not count columns.
        if _is_rejection_reason(label) and not name.endswith(("_Other", "Comments")):
            reasons.append(name)

    return {
        "wave": year,
        "source": f"codebook_{year}.xlsx (Variables sheet)",
        **found,
        "rejection_reasons": reasons,
    }


def main() -> None:
    entries = []

    # 2016: no machine-readable codebook; use the verified mapping.
    # See codebooks/eavs_variable_crosswalk.md for the derivation
    # (C4b correlates 0.9927 with the sum of the C5a-C5v rejection-reason
    # columns and matches exactly in 91.4% of non-missing rows, vs. 0.857
    # for C4a; C4a is the *counted* total, not rejected, in this wave only).
    entries.append({
        "wave": 2016,
        "source": "empirically verified (see eavs_variable_crosswalk.md)",
        "transmitted_total": "C1a",
        "returned_by_voters": "C1b",
        "counted_total": "C4a",
        "rejected_total": "C4b",
        "rejection_reasons": [f"C5{c}" for c in "abcdefghijklmnopqrstuv"],
    })

    for year in (2018, 2020, 2022, 2024):
        entries.append(parse_wave(year))

    entries.sort(key=lambda e: e["wave"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as f:
        yaml.safe_dump({"waves": entries}, f, sort_keys=False, default_flow_style=False)

    print(f"wrote {OUT}\n")
    expected = {
        2016: dict(returned_by_voters="C1b", rejected_total="C4b", n_reasons=22),
        2018: dict(returned_by_voters="C1b", rejected_total="C4a", n_reasons=17),
        2020: dict(returned_by_voters="C1b", rejected_total="C4a", n_reasons=17),
        2022: dict(returned_by_voters="C1b", rejected_total="C9a", n_reasons=19),
        2024: dict(returned_by_voters="C1b", rejected_total="C9a", n_reasons=19),
    }
    print(f"{'wave':6}{'returned_by_voters':22}{'rejected_total':16}{'counted_total':16}{'n_reasons':11}match?")
    ok = True
    for e in entries:
        exp = expected[e["wave"]]
        n_reasons = len(e.get("rejection_reasons", []))
        match = (
            e.get("returned_by_voters") == exp["returned_by_voters"]
            and e.get("rejected_total") == exp["rejected_total"]
            and n_reasons == exp["n_reasons"]
        )
        ok &= match
        print(
            f"{e['wave']:<6}{e.get('returned_by_voters', '???'):22}"
            f"{e.get('rejected_total', '???'):16}{e.get('counted_total', '-'):16}"
            f"{n_reasons:<11}{'OK' if match else 'MISMATCH — check codebook label text'}"
        )
    if not ok:
        raise SystemExit(
            "\nCrosswalk did not reproduce the verified mapping. "
            "A codebook's label wording changed — inspect the Variables "
            "sheet by hand before trusting the panel."
        )


if __name__ == "__main__":
    main()
