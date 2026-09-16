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

| model | variant | estimate | se | p | n_obs | n_states |
|---|---|---|---|---|---|---|
| TWFE | interaction: treated x log_ballots | -0.00004 | 0.00104 | 0.9678 | 34,877 | 51 |
| Sun-Abraham | subsample: large | 0.00624 | 0.00310 | 0.0517 | 9,464 | 37 |
| Callaway-Sant'Anna | subsample: large | -0.00276 | 0.00541 | 0.6098 | 9,536 | 37 |
| Sun-Abraham | subsample: small | -0.00070 | 0.00149 | 0.6449 | 6,063 | 14 |
| Callaway-Sant'Anna | subsample: small | -0.00992 | 0.00069 | 0.0000 | 7,586 | 14 |
