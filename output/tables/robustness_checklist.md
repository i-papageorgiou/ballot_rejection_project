# Robustness checklist (PROJECT_PLAN.md Phase 4)

5 variants x 3 estimators (TWFE, Sun-Abraham, Callaway-Sant'Anna) where
each estimator applies naturally, plus a TWFE-only fractional-response
GLM (quasi-binomial, weighted by returned_by_voters as trial counts —
this is one of the 5 variants, not a 4th estimator run through
everything else). Callaway-Sant'Anna uses biters=200 here (vs. 1000 for
the primary estimate above) to keep runtime bounded across ~8 calls;
the primary CS estimate is the one to trust for precision, these are
for checking the sign/magnitude doesn't flip.

| model | variant | estimate | se | p | n_obs | n_states |
|---|---|---|---|---|---|---|
| TWFE | drop_2020 | -0.00500 | 0.00426 | 0.2458 | 28,573 | 51 |
| Sun-Abraham | drop_2020 | 0.00017 | 0.00270 | 0.9495 | 21,707 | 37 |
| Callaway-Sant'Anna | drop_2020 | -0.00317 | 0.00423 | 0.4529 | 23,649 | 37 |
| TWFE | drop_WI_MI | -0.00245 | 0.00294 | 0.4100 | 25,335 | 49 |
| Sun-Abraham | drop_WI_MI | 0.00626 | 0.00277 | 0.0302 | 17,023 | 35 |
| Callaway-Sant'Anna | drop_WI_MI | -0.00577 | 0.00395 | 0.1439 | 17,094 | 35 |
| TWFE | winsorize_p99 | -0.00170 | 0.00257 | 0.5102 | 34,877 | 51 |
| Sun-Abraham | winsorize_p99 | 0.00126 | 0.00250 | 0.6166 | 26,565 | 37 |
| Callaway-Sant'Anna | winsorize_p99 | -0.00314 | 0.00342 | 0.3589 | 28,496 | 37 |
| TWFE | weight_by_ballots | 0.00200 | 0.00315 | 0.5294 | 34,877 | 51 |
| Sun-Abraham | weight_by_ballots | -0.00289 | 458.08956 ** | 1.0000 | 26,565 | 37 |
| Callaway-Sant'Anna | weight_by_ballots | 0.00394 | 0.00354 | 0.2656 | 28,496 | 37 |
| TWFE (fractional logit) | fractional_response | 0.21826 | 0.23165 | 0.3461 | 30,255 | 51 |

** NUMERICALLY UNSTABLE, not a real result: raw returned_by_voters
weighting combined with sunab()'s many interaction dummies produces a
near-singular weighted design for at least one cohort x time cell —
traced to extreme weight variance (median ~210 ballots, max ~3.4
million, a statewide-aggregate row) that TWFE and Callaway-Sant'Anna's
weighted variants tolerate but the interacted Sun-Abraham spec does
not. The point estimate may still be informative; the SE/p-value are
not — do not cite this cell's significance either way.
