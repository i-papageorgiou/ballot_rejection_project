# Panel Missingness Report

## Overall

- Total jurisdiction-year rows: 38,830
- Usable rows: 36,825 (94.8%)
- Distinct FIPS across all waves: 8,393
- FIPS present in all 6 waves: 4,603
- Treatment join (src/04_build_treatment.py): 100% match on all 51 states + DC x 6 waves (see join_treatment() in this script for the assertion that enforces this). 5 U.S. territories (AS, GU, MP, PR, VI) are out of scope for the treatment variable (`in_scope=False`, `treated`/`sensitivity_treated` left null) — the coding sheet only covers the 50 states + DC.
- Outlier flag (VALIDATION_REPORT.md Defect 7): 33 usable jurisdiction-years have `rejection_rate == 1.0` exactly (implausible for any but a handful of ballots) and are marked `flagged_outlier=True`. Not removed from `usable` — see the flag_outliers() docstring in this script for why.

## Usable-row share by state (ascending — worst first)

Missingness is dominated by state, not jurisdiction size: some states simply don't report the rejected-ballot field in a given wave. Listwise deletion would drop these states' jurisdictions disproportionately.

| state | rows | usable share |
|---|---|---|
| AL | 402 | 16.4% |
| MP | 3 | 33.3% |
| MS | 492 | 60.6% |
| PR | 3 | 66.7% |
| VI | 6 | 66.7% |
| ID | 264 | 77.7% |
| AS | 5 | 80.0% |
| HI | 30 | 80.0% |
| VT | 1,478 | 81.0% |
| CT | 1,014 | 83.2% |
| AR | 450 | 85.1% |
| TX | 1,524 | 89.1% |
| NM | 198 | 89.4% |
| VA | 798 | 92.4% |
| NH | 1,920 | 92.6% |
| KS | 630 | 95.4% |
| IL | 652 | 95.7% |
| WV | 330 | 96.7% |
| ME | 2,993 | 96.8% |
| MA | 2,106 | 97.6% |
| WI | 11,166 | 97.7% |
| UT | 174 | 97.7% |
| IN | 552 | 98.7% |
| CA | 348 | 99.1% |
| NY | 372 | 99.5% |
| PA | 402 | 99.5% |
| FL | 402 | 99.8% |
| TN | 570 | 99.8% |
| SD | 396 | 100.0% |
| NV | 102 | 100.0% |
| WA | 234 | 100.0% |
| OR | 216 | 100.0% |
| OK | 462 | 100.0% |
| OH | 528 | 100.0% |
| SC | 276 | 100.0% |
| RI | 234 | 100.0% |
| AK | 6 | 100.0% |
| NE | 558 | 100.0% |
| AZ | 90 | 100.0% |
| CO | 384 | 100.0% |
| DC | 6 | 100.0% |
| DE | 18 | 100.0% |
| GA | 954 | 100.0% |
| GU | 6 | 100.0% |
| IA | 594 | 100.0% |
| NJ | 126 | 100.0% |
| KY | 720 | 100.0% |
| MD | 144 | 100.0% |
| MI | 498 | 100.0% |
| MN | 522 | 100.0% |
| MO | 696 | 100.0% |
| MT | 336 | 100.0% |
| NC | 600 | 100.0% |
| ND | 318 | 100.0% |
| LA | 384 | 100.0% |
| WY | 138 | 100.0% |

## Usable-row share by jurisdiction-size quartile

Size = each jurisdiction's largest observed `returned_by_voters` across its available waves (a jurisdiction's scale doesn't shift enough year to year for this to matter, and using the max avoids a jurisdiction with one missing wave being miscategorized as tiny).

| size quartile (returned_by_voters) | rows | usable share |
|---|---|---|
| (-0.001, 177.0] | 9,721 | 93.6% |
| (177.0, 844.0] | 9,698 | 94.4% |
| (844.0, 3561.0] | 9,706 | 93.9% |
| (3561.0, 3419212.0] | 9,700 | 97.4% |

