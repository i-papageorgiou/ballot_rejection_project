# Heterogeneity by jurisdiction size

<!-- Numbers below are from an actual run of src/06_estimate.R. The
     CAVEAT paragraph was appended by hand afterward (to avoid a
     redundant ~25 min rerun); the script itself now writes this same
     caveat automatically on any future run. -->

Substitutes for the deferred ACS-based urban/rural split (no Census API
key obtained — see HANDOFF.md). Size proxy: max `returned_by_voters`
per fips across available waves. TWFE uses a continuous interaction on
the full sample; Sun-Abraham and Callaway-Sant'Anna (neither of which
takes an arbitrary covariate interaction) are instead refit separately
on the top and bottom size terciles (small <= 325 ballots, large > 2150 ballots).

DIAGNOSED (via did::att_gt's raw group-time ATT table, before
aggregation): the disagreement between Sun-Abraham (significant positive
in large, null in small) and Callaway-Sant'Anna (null in large,
significant negative in small, p=0.0001) has an identifiable mechanical
cause, not an unexplained contradiction:
(a) the small-jurisdiction subsample has NO 2018 or 2024 cohort at all
    (only 2020/2022 survive the size filter, 9 treated states total),
    and one of its 8 group-time cells is an outlier by an order of
    magnitude (att=-0.045, SE=0.0215, vs. everything else under 0.012)
    — small jurisdictions have volatile rates from small denominators,
    and this one cell dominates a thin sample;
(b) the large-jurisdiction subsample's own cohort-level effects FLIP
    SIGN across periods within the same cohort (2024 cohort: +0.0162 at
    one post-period, -0.0038 at the next) — Sun-Abraham's
    interaction-weighted and Callaway-Sant'Anna's group-size-weighted
    averaging are not guaranteed to agree when underlying effects are
    this heterogeneous, so the disagreement is expected, not a bug in
    either estimator.
Conclusion: jurisdiction-size heterogeneity is unidentifiable with the
current cohort coverage, not merely uncertain — read as "not
establishable with this design," not as evidence for either pattern.
See PROJECT_PLAN.md's Week 4 section for the full diagnosis.

| model | variant | estimate | se | p | n_obs | n_states |
|---|---|---|---|---|---|---|
| TWFE | interaction: treated x log_ballots | 0.00098 | 0.00089 | 0.2745 | 30,523 | 51 |
| Sun-Abraham | subsample: large | 0.00691 | 0.00322 | 0.0388 | 6,113 | 37 |
| Callaway-Sant'Anna | subsample: large | -0.00452 | 0.00566 | 0.4248 | 6,119 | 37 |
| Sun-Abraham | subsample: small | -0.00170 | 0.00277 | 0.5471 | 9,673 | 22 |
| Callaway-Sant'Anna | subsample: small | -0.00967 | 0.00243 | 0.0001 | 9,703 | 22 |
