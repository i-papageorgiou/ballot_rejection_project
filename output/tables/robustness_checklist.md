# Robustness checklist (PROJECT_PLAN.md Week 4)

<!-- Numbers below are from an actual run of src/06_estimate.R. The **
     footnote on the weight_by_ballots/Sun-Abraham row was appended by
     hand afterward (to avoid a redundant ~25 min rerun); the script
     itself now flags any se > 1 this way automatically on any future
     run. -->

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
| TWFE | drop_2020 | -0.00182 | 0.00375 | 0.6300 | 24,215 | 51 |
| Sun-Abraham | drop_2020 | 0.00020 | 0.00268 | 0.9411 | 18,746 | 37 |
| Callaway-Sant'Anna | drop_2020 | -0.00317 | 0.00469 | 0.4983 | 18,842 | 37 |
| TWFE | drop_WI_MI | 0.00034 | 0.00255 | 0.8933 | 21,064 | 49 |
| Sun-Abraham | drop_WI_MI | 0.00636 | 0.00279 | 0.0294 | 14,149 | 35 |
| Callaway-Sant'Anna | drop_WI_MI | -0.00577 | 0.00381 | 0.1299 | 14,219 | 35 |
| TWFE | winsorize_p99 | -0.00053 | 0.00276 | 0.8479 | 30,523 | 51 |
| Sun-Abraham | winsorize_p99 | 0.00127 | 0.00245 | 0.6086 | 23,608 | 37 |
| Callaway-Sant'Anna | winsorize_p99 | -0.00306 | 0.00371 | 0.4087 | 23,689 | 37 |
| TWFE | weight_by_ballots | 0.00383 | 0.00362 | 0.2951 | 30,523 | 51 |
| Sun-Abraham | weight_by_ballots | 0.00034 | 265.43112 ** | 1.0000 | 23,608 | 37 |
| Callaway-Sant'Anna | weight_by_ballots | 0.00392 | 0.00313 | 0.2100 | 23,689 | 37 |
| TWFE (fractional logit) | fractional_response | 0.36499 | 0.29423 | 0.2148 | 25,910 | 51 |

** NUMERICALLY UNSTABLE, not a real result: raw returned_by_voters
weighting combined with sunab()'s many interaction dummies produces a
near-singular weighted design for at least one cohort x time cell —
traced to extreme weight variance (median ~210 ballots, max ~3.4
million, a statewide-aggregate row) that TWFE and Callaway-Sant'Anna's
weighted variants tolerate but the interacted Sun-Abraham spec does
not. The point estimate may still be informative; the SE/p-value are
not — do not cite this cell's significance either way.
