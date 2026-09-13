# Panel Missingness Report

## Overall

- Total jurisdiction-year rows: 32,305
- Usable rows: 30,621 (94.8%)
- Distinct FIPS across all waves: 6,480
- FIPS present in all 5 waves: 6,447

## Usable-row share by state (ascending — worst first)

Missingness is dominated by state, not jurisdiction size: some states simply don't report the rejected-ballot field in a given wave. Listwise deletion would drop these states' jurisdictions disproportionately.

| state | rows | usable share |
|---|---|---|
| AL | 335 | 19.7% |
| MP | 3 | 33.3% |
| MS | 410 | 59.8% |
| PR | 3 | 66.7% |
| ID | 220 | 73.2% |
| AS | 4 | 75.0% |
| VT | 1,232 | 79.4% |
| CT | 845 | 79.9% |
| VI | 5 | 80.0% |
| HI | 25 | 80.0% |
| AR | 375 | 82.1% |
| NM | 165 | 90.3% |
| TX | 1,270 | 90.5% |
| VA | 665 | 90.8% |
| NH | 1,600 | 92.8% |
| KS | 525 | 94.5% |
| IL | 542 | 94.8% |
| WV | 275 | 96.4% |
| ME | 2,492 | 97.1% |
| WI | 9,254 | 97.8% |
| UT | 145 | 97.9% |
| MA | 1,755 | 98.4% |
| CA | 290 | 99.0% |
| PA | 335 | 99.4% |
| NY | 310 | 99.7% |
| FL | 335 | 99.7% |
| RI | 195 | 100.0% |
| SD | 330 | 100.0% |
| OR | 180 | 100.0% |
| WA | 195 | 100.0% |
| OK | 385 | 100.0% |
| OH | 440 | 100.0% |
| NV | 85 | 100.0% |
| SC | 230 | 100.0% |
| TN | 475 | 100.0% |
| AK | 5 | 100.0% |
| NE | 465 | 100.0% |
| AZ | 75 | 100.0% |
| CO | 320 | 100.0% |
| DC | 5 | 100.0% |
| DE | 15 | 100.0% |
| GA | 795 | 100.0% |
| GU | 5 | 100.0% |
| IA | 495 | 100.0% |
| IN | 460 | 100.0% |
| KY | 600 | 100.0% |
| LA | 320 | 100.0% |
| MD | 120 | 100.0% |
| MI | 415 | 100.0% |
| MN | 435 | 100.0% |
| MO | 580 | 100.0% |
| MT | 280 | 100.0% |
| NC | 500 | 100.0% |
| ND | 265 | 100.0% |
| NJ | 105 | 100.0% |
| WY | 115 | 100.0% |

## Usable-row share by jurisdiction-size quartile

Size = each jurisdiction's largest observed `returned_by_voters` across its available waves (a jurisdiction's scale doesn't shift enough year to year for this to matter, and using the max avoids a jurisdiction with one missing wave being miscategorized as tiny).

| size quartile (returned_by_voters) | rows | usable share |
|---|---|---|
| (-0.001, 195.0] | 8,102 | 94.0% |
| (195.0, 857.0] | 8,049 | 94.3% |
| (857.0, 3595.0] | 8,072 | 93.8% |
| (3595.0, 3419212.0] | 8,071 | 97.2% |

