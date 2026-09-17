# Heterogeneity by jurisdiction size

Substitutes for the deferred ACS-based urban/rural split (no Census API
key obtained — see HANDOFF.md). Size proxy: max `returned_by_voters`
per fips across available waves. TWFE uses a continuous interaction on
the full sample; Sun-Abraham and Callaway-Sant'Anna (neither of which
takes an arbitrary covariate interaction) are instead refit separately
on the top and bottom size terciles (small <= 137 ballots, large > 1333 ballots).

CAVEAT: the large and small subsamples are NOT the same set of states —
terciles are computed over individual jurisdictions, and some states have
no jurisdictions in one tercile or the other (n_states differs: large vs.
small subsamples do not share a common state universe). Sun-Abraham and
Callaway-Sant'Anna also DISAGREE here: Sun-Abraham finds a significant
positive effect in the large subsample (p<0.05) and a null in the small
one, while Callaway-Sant'Anna finds the opposite pattern (null in large,
significant negative in small, p<0.001). Not resolved this round — read
as "heterogeneity is not conclusively established, the two corrected
estimators do not corroborate each other," not as a confirmed effect.

## NCHS urban/rural split (Phase 8)

The size-tercile split above was diagnosed as unidentifiable because the
small-jurisdiction subsample was missing two of four treatment cohorts
entirely. This split uses NCHS's real Urban-Rural Classification Scheme
for Counties (CODE2013, from data/processed/acs_controls.csv) instead:
urban = codes 1-2, rural = codes 5-6, mid-category (3-4) and jurisdictions
with no NCHS match (7 town-reporting states + residual ACS gap) excluded.

Cohort coverage (from nchs_cohort_table, computed fresh each run, not asserted): urban has cohorts {2018, 2020, 2022, 2024} (missing: {}); rural has cohorts {2018, 2020, 2022, 2024} (missing: {}). All 4 treatment cohorts appear in both groups, resolving the specific structural flaw the size-tercile split had.

Result this round: urban: Sun-Abraham null (p=0.1216), Callaway-Sant'Anna null (p=0.3733), same sign: FALSE
Result this round: rural: Sun-Abraham null (p=0.0721), Callaway-Sant'Anna null (p=0.8158), same sign: FALSE

| model | variant | estimate | se | p | n_obs | n_states |
|---|---|---|---|---|---|---|
| TWFE | interaction: treated x log_ballots | -0.00004 | 0.00104 | 0.9678 | 34,877 | 51 |
| Sun-Abraham | subsample: large | 0.00624 | 0.00310 | 0.0517 | 9,464 | 37 |
| Callaway-Sant'Anna | subsample: large | -0.00276 | 0.00541 | 0.6098 | 9,536 | 37 |
| Sun-Abraham | subsample: small | -0.00070 | 0.00149 | 0.6449 | 6,063 | 14 |
| Callaway-Sant'Anna | subsample: small | -0.00992 | 0.00069 | 0.0000 | 7,586 | 14 |
| Sun-Abraham | nchs_urban | 0.01204 | 0.00749 | 0.1216 | 1,671 | 25 |
| Callaway-Sant'Anna | nchs_urban | -0.01127 | 0.01265 | 0.3733 | 1,678 | 25 |
| Sun-Abraham | nchs_rural | 0.00553 | 0.00295 | 0.0721 | 7,369 | 28 |
| Callaway-Sant'Anna | nchs_rural | -0.00113 | 0.00483 | 0.8158 | 7,407 | 28 |
