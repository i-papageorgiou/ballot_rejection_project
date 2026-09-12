# EAVS Cleaning Validation Report

## National rejected-ballot total (exact match required)

| wave | expected | actual | match |
|---|---|---|---|
| 2016 | 318,728 | 318,728 | OK |
| 2018 | 430,196 | 430,196 | OK |
| 2020 | 560,826 | 560,826 | OK |
| 2022 | 549,824 | 549,824 | OK |
| 2024 | 584,463 | 584,463 | OK |

## rejected_total vs. sum of reason columns (band, not a point fixture)

| wave | corr | exact match | pass (corr>=0.95 and exact>=0.85) |
|---|---|---|---|
| 2016 | 0.9927 | 91.4% | OK |
| 2018 | 0.9602 | 94.1% | OK |
| 2020 | 0.9745 | 94.7% | OK |
| 2022 | 0.9997 | 95.5% | OK |
| 2024 | 0.9994 | 94.2% | OK |

## rejection_rate out-of-range violations (informational; expect <=2/wave)

| wave | violations |
|---|---|
| 2016 | 1 |
| 2018 | 0 |
| 2020 | 2 |
| 2022 | 4 |
| 2024 | 1 |

## Usable-row share (>=90% required)

| wave | rows | usable share | pass |
|---|---|---|---|
| 2016 | 6,467 | 90.7% | OK |
| 2018 | 6,460 | 96.2% | OK |
| 2020 | 6,458 | 97.5% | OK |
| 2022 | 6,459 | 95.3% | OK |
| 2024 | 6,461 | 94.2% | OK |

## Duplicate FIPS after resolution (0 required)

| wave | duplicate fips |
|---|---|
| 2016 | 0 OK |
| 2018 | 0 OK |
| 2020 | 0 OK |
| 2022 | 0 OK |
| 2024 | 0 OK |

