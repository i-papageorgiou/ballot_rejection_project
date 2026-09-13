# 06_estimate.R — First-cut estimation: naive TWFE vs. a staggered-
# adoption-corrected estimator, side by side.
#
# Reads data/processed/panel.csv (R side reads CSV, not parquet, per
# PROJECT_PLAN.md's stack decision — avoids installing arrow/sf here).
# Restricts to usable, in-scope (50 states + DC, no territories) rows.
#
# This is a FIRST CUT, deliberately scoped (see HANDOFF.md's Week 4 next
# steps and PROJECT_PLAN.md's Week 4 section):
#   - fwildclusterboot wild-cluster bootstrap: NOT run here yet.
#   - Heterogeneity (log ballots returned x treatment, urban/rural): not here.
#   - Robustness checklist (drop 2020; drop WI/MI; winsorize p99; weight by
#     ballots returned; fractional logit vs. linear): not here.
# These are explicitly Week 4 "part 2" — see the TODO block at the bottom.
#
# Usage:
#   Rscript src/06_estimate.R

suppressPackageStartupMessages({
  library(data.table)
  library(fixest)
  library(modelsummary)
})

.args <- commandArgs(trailingOnly = FALSE)
.script_path <- sub("--file=", "", .args[grep("--file=", .args)])
root <- normalizePath(file.path(dirname(.script_path), ".."))
panel_path <- file.path(root, "data", "processed", "panel.csv")
out_path <- file.path(root, "output", "tables", "estimates_v1.md")

panel <- fread(panel_path)

# --- Sample restriction -----------------------------------------------
# usable: rejected_total/returned_by_voters both present, denominator > 0,
#   rate <= 1 (03_clean_eavs.py's own definition).
# in_scope: excludes the 5 U.S. territories, which have no treatment coding
#   (05_build_panel.py sets treated/sensitivity_treated to NA for them).
n_before <- nrow(panel)
panel <- panel[usable == TRUE & in_scope == TRUE]
cat(sprintf(
  "Sample: %s of %s panel rows (usable & in_scope): %d states, %d fips, waves %s-%s\n",
  format(nrow(panel), big.mark = ","), format(n_before, big.mark = ","),
  uniqueN(panel$state_abbr), uniqueN(panel$fips),
  min(panel$year), max(panel$year)
))
stopifnot(nrow(panel) > 0, all(!is.na(panel$treated)))

panel[, fips := as.factor(fips)]
panel[, year := as.integer(year)]
panel[, state_abbr := as.factor(state_abbr)]

# --- Model 1: naive TWFE ------------------------------------------------
# Two-way fixed effects (jurisdiction + year), state-clustered SEs.
# Known to be biased under staggered adoption with heterogeneous treatment
# effects (Goodman-Bacon / de Chaisemartin-D'Haultfœuille) — included as
# the naive baseline this design exists to correct, not as the headline
# estimate.
m_twfe <- feols(
  rejection_rate ~ treated | fips + year,
  data = panel,
  cluster = ~state_abbr
)

# --- Model 2: Sun & Abraham (2021) interaction-weighted estimator ------
# fixest::sunab() requires a single per-unit adoption cohort (never-treated
# coded as a sentinel, e.g. Inf or 0) — it cannot represent Iowa's
# treatment reversal (treated 2018 only, untreated again from 2020). Iowa
# is therefore EXCLUDED from this model only (kept in the TWFE model
# above), rather than let sunab() silently misassign it a cohort based on
# whichever wave happens to average out its 1/0/0/0/0 pattern.
sunab_data <- panel[state_abbr != "IA"]

# cohort = first treated year, or Inf for never-treated (sunab's convention)
cohort_by_state <- unique(sunab_data[treated == 1, .(first_year = min(year)), by = state_abbr])
sunab_data <- merge(sunab_data, cohort_by_state, by = "state_abbr", all.x = TRUE)
sunab_data[, cohort := ifelse(is.na(first_year), Inf, first_year)]

m_sunab <- feols(
  rejection_rate ~ sunab(cohort, year) | fips + year,
  data = sunab_data,
  cluster = ~state_abbr
)

cat(sprintf(
  "sunab() sample excludes Iowa (treatment reversal, not a single cohort): %d states, %d rows\n",
  uniqueN(sunab_data$state_abbr), nrow(sunab_data)
))

# --- Output ---------------------------------------------------------------
dir.create(dirname(out_path), showWarnings = FALSE, recursive = TRUE)

modelsummary(
  list("TWFE (naive)" = m_twfe, "Sun-Abraham (staggered, ex-Iowa)" = m_sunab),
  output = out_path,
  title = "Effect of mandatory signature-cure notice laws on mail ballot rejection rate (first cut)",
  notes = c(
    "Outcome: jurisdiction-year rejection_rate (rejected_total / returned_by_voters).",
    "Sample: usable, in-scope (50 states + DC) jurisdiction-years, 2016-2024 EAVS waves.",
    "TWFE clusters SEs by state; Sun-Abraham excludes Iowa (treatment reversal) and averages sunab's cohort x time interactions.",
    "This is a first-cut estimate. See src/06_estimate.R's header for what is NOT yet included: wild-cluster bootstrap, heterogeneity, and the full robustness checklist."
  )
)

cat(sprintf("wrote %s\n", out_path))
cat("\n--- TWFE ---\n")
print(summary(m_twfe))
cat("\n--- Sun-Abraham (aggregated ATT) ---\n")
print(aggregate(m_sunab, agg = "att"))

# TODO(Week 4 part 2), per PROJECT_PLAN.md / HANDOFF.md next steps:
#   - fwildclusterboot wild-cluster bootstrap (only ~50 effective clusters).
#   - Callaway-Sant'Anna via the `did` package, as a second corrected
#     estimator alongside sunab(), with the difference from TWFE explained.
#   - Heterogeneity: interact treated with log(ballots returned) and an
#     urban/rural classification (see HANDOFF.md's ACS caveat for how to
#     get the latter without live Census data).
#   - Robustness: drop 2020; drop WI/MI (municipality/township-level
#     reporting); winsorize rejection_rate at p99; weight by
#     returned_by_voters; fractional logit vs. linear specification.
