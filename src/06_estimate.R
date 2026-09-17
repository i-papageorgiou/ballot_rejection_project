# 06_estimate.R — Estimation: naive TWFE vs. two staggered-adoption-
# corrected estimators (Sun-Abraham, Callaway-Sant'Anna), wild-cluster
# bootstrap inference, heterogeneity by jurisdiction size, and a 5-item
# robustness checklist re-run through all three estimators.
#
# Reads data/processed/panel.csv (R side reads CSV, not parquet, per
# PROJECT_PLAN.md's stack decision — avoids installing arrow/sf here).
# Restricts to usable, in-scope (50 states + DC, no territories) rows.
#
# VALIDATION_REPORT.md (Pass 4) found an earlier version of this script
# derived the Sun-Abraham cohort from the FILTERED (usable & in_scope)
# sample rather than from treatment.csv, which silently fabricated a
# treatment event for Vermont (its 2016 wave is 0% usable, so it looked
# like a 2018 adopter instead of always-treated). Fixed: cohort comes
# from treatment.csv directly everywhere in this script, and
# always-treated states (no pre-period to identify an event-time effect
# from) are excluded from BOTH sunab() and att_gt() — not just Iowa's
# treatment reversal, which neither estimator can represent either.
#
# Runtime: ~25-30 minutes total, dominated by the wild-cluster bootstrap
# (measured ~19-20 min for one B=999 call over 6,367 fixed-effect levels
# on this machine — much slower than fwildclusterboot's own docs would
# suggest, possibly memory-pressure-dependent; budget accordingly, it is
# not hung) plus ~10 Callaway-Sant'Anna att_gt() calls across the
# heterogeneity and robustness sections (seconds each, not the bottleneck).
#
# Usage:
#   Rscript src/06_estimate.R

suppressPackageStartupMessages({
  library(data.table)
  library(fixest)
  library(modelsummary)
  library(did)
  library(fwildclusterboot)
  library(jsonlite)
})

.args <- commandArgs(trailingOnly = FALSE)
.script_path <- sub("--file=", "", .args[grep("--file=", .args)])
root <- normalizePath(file.path(dirname(.script_path), ".."))
panel_path <- file.path(root, "data", "processed", "panel.csv")
treatment_path <- file.path(root, "data", "processed", "treatment.csv")
out_dir <- file.path(root, "output", "tables")
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)
# Phase 5 dashboard data (docs/index.html reads these directly) — written
# alongside the markdown tables below, from the same in-memory model
# objects, so the two can never silently drift apart.
docs_data_dir <- file.path(root, "docs", "data")
dir.create(docs_data_dir, showWarnings = FALSE, recursive = TRUE)


# colClasses forces fips to stay a character column — fread's own type
# detection otherwise reads it as numeric and silently drops the leading
# zero on any FIPS code starting with 0 (AL, AK, AZ, AR, CA, CO, CT: state
# codes 01-09). That only broke a value comparison in one specific place
# below (the county_fips substr(fips, 1, 5) join added for the NCHS
# split), but it's cheap correctness insurance to fix at the source
# instead of patching around it downstream. Found by the NCHS
# cohort-coverage check unexpectedly showing 0 urban states for the 2018
# cohort — investigated rather than accepted, since CA (a 2018 adopter)
# very much has NCHS-classified urban counties.
panel <- fread(panel_path, colClasses = list(character = "fips"))
treatment <- fread(treatment_path)

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

# --- Shared derived variables -------------------------------------------
# always_treated_states / cohort_by_state come from treatment.csv (the
# unfiltered truth), used identically by both sunab() and att_gt() below
# and by every heterogeneity/robustness refit — computed once here so
# there is exactly one place that could get this wrong, not several.
always_treated_states <- unique(treatment[, .(all_treated = all(treated == 1)), by = state_abbr][all_treated == TRUE, state_abbr])
cohort_by_state <- unique(treatment[treated == 1, .(first_year = min(year)), by = state_abbr])
cohort_by_state <- cohort_by_state[!state_abbr %in% always_treated_states]

# Jurisdiction-size proxy: max returned_by_voters per fips across
# available waves (same logic 05_build_panel.py's missingness report
# uses — a jurisdiction's scale doesn't shift enough year to year for
# this to matter, and using the max avoids a jurisdiction with one
# missing wave being miscategorized as tiny).
size_by_fips <- panel[, .(size_proxy = max(returned_by_voters, na.rm = TRUE)), by = fips]
panel <- merge(panel, size_by_fips, by = "fips")
panel[, log_ballots := log1p(size_proxy)]
tercile_cuts <- quantile(size_by_fips$size_proxy, probs = c(1 / 3, 2 / 3), na.rm = TRUE)
panel[, size_tercile := fifelse(size_proxy <= tercile_cuts[1], "small",
                          fifelse(size_proxy > tercile_cuts[2], "large", "mid"))]
cat(sprintf(
  "Size terciles (returned_by_voters, max per fips): small <= %d, large > %d\n",
  round(tercile_cuts[1]), round(tercile_cuts[2])
))

# --- NCHS urban/rural classification (Phase 8: real classification, ------
# replacing nothing — added alongside the size-tercile proxy above, not
# instead of it; see PROJECT_PLAN.md Phase 4 for why the size proxy was
# diagnosed as unidentifiable and the plan file for this round's scope).
# acs_controls.csv is per (county_fips, year), but nchs_rurality_2013 is
# time-invariant by construction (a single 2013 vintage classification),
# so one row per county_fips is enough — dedup rather than join on year,
# which would needlessly multiply rows and risk an NA year mismatch.
acs_controls_path <- file.path(root, "data", "processed", "acs_controls.csv")
acs_controls <- fread(acs_controls_path, colClasses = list(character = "county_fips"))
nchs_by_county <- unique(acs_controls[!is.na(nchs_rurality_2013), .(county_fips, nchs_rurality_2013)], by = "county_fips")

panel[, county_fips := substr(as.character(fips), 1, 5)]
panel <- merge(panel, nchs_by_county, by = "county_fips", all.x = TRUE)
# Collapse NCHS's 1-6 scale to a clean two-group split, dropping the
# middle (3-4) the same way the size split already drops its "mid"
# tercile. Jurisdictions with no NCHS match (7 town-reporting states,
# plus the small residual ACS gap documented in PROJECT_PLAN.md Phase 7)
# are excluded from this analysis, not zero-filled or imputed.
panel[, nchs_group := fifelse(nchs_rurality_2013 %in% c(1, 2), "urban",
                        fifelse(nchs_rurality_2013 %in% c(5, 6), "rural", NA_character_))]
cat(sprintf(
  "NCHS urban/rural split: %s urban jurisdiction-years, %s rural, %s excluded (mid-category or unmatched)\n",
  format(sum(panel$nchs_group == "urban", na.rm = TRUE), big.mark = ","),
  format(sum(panel$nchs_group == "rural", na.rm = TRUE), big.mark = ","),
  format(sum(is.na(panel$nchs_group)), big.mark = ",")
))
# Cohort coverage per group — the same transparency that diagnosed the
# old split's flaw, so a reader can check this split doesn't share it.
nchs_coverage <- merge(panel[!is.na(nchs_group), .(fips, state_abbr, nchs_group)],
                        cohort_by_state, by = "state_abbr", all.x = TRUE)
nchs_coverage[, cohort_label := fifelse(is.na(first_year), "never-treated", as.character(first_year))]
nchs_cohort_table <- unique(nchs_coverage[, .(nchs_group, cohort_label, state_abbr)])[
  , .(n_states = uniqueN(state_abbr)), by = .(nchs_group, cohort_label)][order(nchs_group, cohort_label)]
cat("NCHS split cohort coverage (states per group x cohort):\n")
print(nchs_cohort_table)

# Written from nchs_cohort_table itself (not asserted) — the actual
# treatment cohorts (excluding never-treated) present in each group,
# checked against the full set of 4 real cohorts (2018/2020/2022/2024).
real_cohorts <- c("2018", "2020", "2022", "2024")
cohorts_present <- function(grp) sort(unique(nchs_cohort_table[nchs_group == grp & cohort_label != "never-treated", cohort_label]))
urban_cohorts <- cohorts_present("urban")
rural_cohorts <- cohorts_present("rural")
nchs_coverage_note <- sprintf(
  "Cohort coverage (from nchs_cohort_table, computed fresh each run, not asserted): urban has cohorts {%s} (missing: {%s}); rural has cohorts {%s} (missing: {%s}). %s",
  paste(urban_cohorts, collapse = ", "), paste(setdiff(real_cohorts, urban_cohorts), collapse = ", "),
  paste(rural_cohorts, collapse = ", "), paste(setdiff(real_cohorts, rural_cohorts), collapse = ", "),
  if (length(setdiff(real_cohorts, urban_cohorts)) == 0 && length(setdiff(real_cohorts, rural_cohorts)) == 0) {
    "All 4 treatment cohorts appear in both groups, resolving the specific structural flaw the size-tercile split had."
  } else {
    "Coverage is improved over the size-tercile split but NOT complete for every cohort in every group — read results accordingly, this is not the clean 4-for-4 the pre-check aimed for."
  }
)

# --- Helper: build the sunab()-ready subset of a given data.table -------
# Excludes Iowa (reversal) and always-treated states (no pre-period),
# attaches the treatment.csv-derived cohort, Inf for never-treated.
make_sunab_data <- function(dt) {
  d <- dt[!(state_abbr %in% c("IA", always_treated_states))]
  d <- merge(d, cohort_by_state, by = "state_abbr", all.x = TRUE)
  d[, cohort := ifelse(is.na(first_year), Inf, first_year)]
  d
}

# --- Helper: build the att_gt()-ready subset of a given data.table -------
# Same exclusions as sunab (Iowa + always-treated); att_gt's own
# convention is gname=0 for never-treated (not Inf), and idname must be
# numeric — recomputed fresh per subsample since it's an arbitrary label,
# not a value that needs to match across calls.
make_cs_data <- function(dt) {
  d <- dt[!(state_abbr %in% c("IA", always_treated_states))]
  d <- merge(d, cohort_by_state, by = "state_abbr", all.x = TRUE)
  d[, gname := ifelse(is.na(first_year), 0, first_year)]
  d[, fips_num := as.integer(as.factor(fips))]
  d
}

# --- Helper: one-row summary extractor, shared by every model below -----
one_row <- function(model_label, variant_label, estimate, se, p, n_obs, n_states) {
  data.table(model = model_label, variant = variant_label, estimate = estimate,
             se = se, p = p, n_obs = n_obs, n_states = n_states)
}

fit_twfe <- function(dt, weights_formula = NULL, outcome = "rejection_rate") {
  fml <- as.formula(sprintf("%s ~ treated | fips + year", outcome))
  m <- if (is.null(weights_formula)) {
    feols(fml, data = dt, cluster = ~state_abbr)
  } else {
    feols(fml, data = dt, weights = weights_formula, cluster = ~state_abbr)
  }
  ct <- m$coeftable["treated", ]
  list(model = m, row = one_row("TWFE", NA_character_, ct[["Estimate"]], ct[["Std. Error"]],
                                 ct[["Pr(>|t|)"]], m$nobs, uniqueN(dt$state_abbr)))
}

fit_sunab <- function(dt, weights_formula = NULL, outcome = "rejection_rate") {
  d <- make_sunab_data(dt)
  fml <- as.formula(sprintf("%s ~ sunab(cohort, year) | fips + year", outcome))
  m <- if (is.null(weights_formula)) {
    feols(fml, data = d, cluster = ~state_abbr)
  } else {
    feols(fml, data = d, weights = weights_formula, cluster = ~state_abbr)
  }
  agg <- aggregate(m, agg = "att")
  list(model = m, row = one_row("Sun-Abraham", NA_character_, agg[1, "Estimate"], agg[1, "Std. Error"],
                                 agg[1, "Pr(>|t|)"], m$nobs, uniqueN(d$state_abbr)))
}

fit_cs <- function(dt, weightsname = NULL, biters = 200, outcome = "rejection_rate") {
  d <- make_cs_data(dt)
  out <- att_gt(
    yname = outcome, tname = "year", idname = "fips_num", gname = "gname",
    xformla = NULL, data = d, panel = TRUE, allow_unbalanced_panel = TRUE,
    control_group = "nevertreated", clustervars = "state_abbr",
    weightsname = weightsname, biters = biters, print_details = FALSE
  )
  agg <- aggte(out, type = "simple")
  list(att_gt = out, agg = agg,
       row = one_row("Callaway-Sant'Anna", NA_character_, agg$overall.att, agg$overall.se,
                      2 * pnorm(-abs(agg$overall.att / agg$overall.se)), nrow(d), uniqueN(d$state_abbr)))
}

# ==========================================================================
# PRIMARY MODELS
# ==========================================================================

cat("\n== Fitting primary models (TWFE, Sun-Abraham, Callaway-Sant'Anna) ==\n")

twfe_fit <- fit_twfe(panel)
m_twfe <- twfe_fit$model

sunab_fit <- fit_sunab(panel)
m_sunab <- sunab_fit$model
cat(sprintf(
  "sunab() sample excludes Iowa (treatment reversal) and %d always-treated states (no pre-period): %d states, %d rows\n",
  length(always_treated_states), sunab_fit$row$n_states, sunab_fit$row$n_obs
))

cs_fit <- fit_cs(panel, biters = 1000)
cat(sprintf(
  "att_gt() sample excludes Iowa and %d always-treated states: %d states, %d rows\n",
  length(always_treated_states), cs_fit$row$n_states, cs_fit$row$n_obs
))
cs_dynamic <- aggte(cs_fit$att_gt, type = "dynamic")

# --- Pre-trend check on the dynamic aggregation --------------------------
# cs_dynamic$egt are the event-times, with pre-period ones negative.
# cs_dynamic$att.egt / se.egt / crit.val.egt give the SIMULTANEOUS
# confidence band did already computes (not a per-point band) — a
# pre-period point whose band excludes 0 is a real parallel-trends
# concern, not noise inflated by uncorrected multiple comparisons, since
# the simultaneity correction already accounts for testing several
# event-times at once.
pre_idx <- which(cs_dynamic$egt < 0)
pre_lo <- cs_dynamic$att.egt[pre_idx] - cs_dynamic$crit.val.egt * cs_dynamic$se.egt[pre_idx]
pre_hi <- cs_dynamic$att.egt[pre_idx] + cs_dynamic$crit.val.egt * cs_dynamic$se.egt[pre_idx]
pre_violation <- pre_idx[pre_lo > 0 | pre_hi < 0]
if (length(pre_violation) > 0) {
  pretrend_note <- sprintf(
    "PRE-TREND WARNING: event-time(s) %s show a simultaneous 95%% confidence band that excludes 0 in the PRE-treatment period — a real parallel-trends concern for the Callaway-Sant'Anna design, not just noise (the band already corrects for testing multiple event-times at once). Not resolved in this round; a design that relies on parallel trends should not be treated as validated until this is investigated further.",
    paste(cs_dynamic$egt[pre_violation], collapse = ", ")
  )
} else {
  pretrend_note <- "No pre-treatment event-time shows a simultaneous confidence band excluding 0 — no pre-trend violation detected."
}
cat("\n", pretrend_note, "\n", sep = "")

# --- Wild-cluster bootstrap on TWFE's treated coefficient ---------------
# boottest() errors if feols() internally dropped singleton fixed effects
# without those rows being excluded from the data first — it won't
# reconcile a row-count mismatch itself. Refit on the reduced data before
# bootstrapping (found by smoke-testing this exact model beforehand).
cat("\n== Wild-cluster bootstrap on TWFE (this is the slow step, ~20 min on this machine) ==\n")
drop_idx <- abs(m_twfe$obs_selection$obsRemoved)
panel_no_singletons <- panel[-drop_idx]
panel_no_singletons[, fips := droplevels(fips)]
# boottest()'s internal grouping (fwildclusterboot's fsum.default) errors on
# a factor cluster column ("length(g) must match length(x)") in a way it
# doesn't on a plain character one — pass a character copy specifically for
# the bootstrap call, even though `state_abbr` is a factor everywhere else
# in this script (feols/sunab/att_gt all handle the factor version fine;
# this is a fwildclusterboot-specific quirk, confirmed by reproducing the
# crash and fixing it here).
panel_no_singletons[, state_abbr_chr := as.character(state_abbr)]
m_twfe_boot <- feols(rejection_rate ~ treated | fips + year, data = panel_no_singletons, cluster = ~state_abbr_chr)
set.seed(20260913)
boot <- boottest(m_twfe_boot, param = "treated", clustid = "state_abbr_chr", B = 999)
cat(sprintf("Wild-cluster bootstrap: p = %.4f, 95%% CI [%.4f, %.4f]\n",
            boot$p_val, boot$conf_int[1], boot$conf_int[2]))

# ==========================================================================
# HETEROGENEITY: jurisdiction size (log ballots returned)
# ==========================================================================
# Per-decision: substitutes for the deferred ACS urban/rural split (the
# fallback HANDOFF.md itself names) rather than a new, unvalidated
# external dataset this round.
#
# TWFE: continuous interaction on the full sample.
# Sun-Abraham / CS: neither takes an arbitrary covariate interaction the
# way an OLS formula does — heterogeneity here means a SUBSAMPLE SPLIT
# (large vs. small jurisdiction tercile), the standard way to get
# heterogeneity out of an event-study-style estimator, with the same
# model refit separately per subsample.

cat("\n== Heterogeneity: jurisdiction size ==\n")

m_het_twfe <- feols(rejection_rate ~ treated * log_ballots | fips + year, data = panel, cluster = ~state_abbr)
het_twfe_row <- one_row("TWFE", "interaction: treated x log_ballots",
                         m_het_twfe$coeftable["treated:log_ballots", "Estimate"],
                         m_het_twfe$coeftable["treated:log_ballots", "Std. Error"],
                         m_het_twfe$coeftable["treated:log_ballots", "Pr(>|t|)"],
                         m_het_twfe$nobs, uniqueN(panel$state_abbr))

het_rows <- list(het_twfe_row)
for (grp in c("large", "small")) {
  sub <- panel[size_tercile == grp]
  r_sunab <- fit_sunab(sub)$row; r_sunab$variant <- paste0("subsample: ", grp)
  r_cs <- fit_cs(sub, biters = 200)$row; r_cs$variant <- paste0("subsample: ", grp)
  het_rows[[length(het_rows) + 1]] <- r_sunab
  het_rows[[length(het_rows) + 1]] <- r_cs
}

# --- NCHS urban/rural split (Phase 8) -------------------------------------
# Same refit pattern as the size-tercile loop above, reusing
# make_sunab_data()/make_cs_data() unchanged — this is a subsample split
# like any other, no new fitting logic needed. Rows are labeled
# "nchs_urban"/"nchs_rural" (not "subsample: urban/rural") specifically so
# they're unambiguous from the size-based "subsample: large/small" rows
# in the combined table and downstream JSON.
for (grp in c("urban", "rural")) {
  sub <- panel[nchs_group == grp]
  r_sunab <- fit_sunab(sub)$row; r_sunab$variant <- paste0("nchs_", grp)
  r_cs <- fit_cs(sub, biters = 200)$row; r_cs$variant <- paste0("nchs_", grp)
  het_rows[[length(het_rows) + 1]] <- r_sunab
  het_rows[[length(het_rows) + 1]] <- r_cs
}
heterogeneity_table <- rbindlist(het_rows)

# Agreement check for the NCHS split, written the same "diagnose before
# concluding" way as the size split's hard-coded caveat above — computed
# from the actual fitted rows rather than assumed, since whether the two
# estimators agree here is the empirical question this round answers.
nchs_rows <- heterogeneity_table[variant %in% c("nchs_urban", "nchs_rural")]
nchs_sig <- nchs_rows[, .(model, variant, estimate, p, sig = p < 0.05)]
sunab_sig <- nchs_sig[model == "Sun-Abraham"]
cs_sig <- nchs_sig[model == "Callaway-Sant'Anna"]
same_sign <- function(v) {
  su <- sunab_sig[variant == v, estimate]; cs <- cs_sig[variant == v, estimate]
  if (length(su) == 0 || length(cs) == 0) return(NA)
  sign(su) == sign(cs)
}
agreement_bits <- sapply(c("nchs_urban", "nchs_rural"), function(v) {
  su_sig <- sunab_sig[variant == v, sig]; cs_sig_v <- cs_sig[variant == v, sig]
  sprintf("%s: Sun-Abraham %s (p=%.4f), Callaway-Sant'Anna %s (p=%.4f), same sign: %s",
          sub("nchs_", "", v),
          ifelse(su_sig, "significant", "null"), sunab_sig[variant == v, p],
          ifelse(cs_sig_v, "significant", "null"), cs_sig[variant == v, p],
          same_sign(v))
})
nchs_agreement_note <- c("", paste("Result this round:", agreement_bits))

# ==========================================================================
# ROBUSTNESS CHECKLIST (PROJECT_PLAN.md Phase 4): 5 variants x 3 estimators,
# plus fractional-response GLM (TWFE-only — one of the 5 variants, not a
# 4th estimator run through everything else).
# ==========================================================================

cat("\n== Robustness checklist (5 variants x 3 estimators + fractional logit) ==\n")

p99 <- quantile(panel$rejection_rate, 0.99, na.rm = TRUE)
panel[, rejection_rate_wins := pmin(rejection_rate, p99)]
cat(sprintf("Winsorizing at p99 = %.4f\n", p99))

robustness_variants <- list(
  drop_2020 = panel[year != 2020],
  drop_WI_MI = panel[!(state_abbr %in% c("WI", "MI"))]
)

rob_rows <- list()

for (variant_name in names(robustness_variants)) {
  dt <- robustness_variants[[variant_name]]
  r <- fit_twfe(dt)$row; r$variant <- variant_name; rob_rows[[length(rob_rows) + 1]] <- r
  r <- fit_sunab(dt)$row; r$variant <- variant_name; rob_rows[[length(rob_rows) + 1]] <- r
  r <- fit_cs(dt, biters = 200)$row; r$variant <- variant_name; rob_rows[[length(rob_rows) + 1]] <- r
}

# Winsorized outcome: same three estimators, outcome column swapped.
r <- fit_twfe(panel, outcome = "rejection_rate_wins")$row; r$variant <- "winsorize_p99"; rob_rows[[length(rob_rows) + 1]] <- r
r <- fit_sunab(panel, outcome = "rejection_rate_wins")$row; r$variant <- "winsorize_p99"; rob_rows[[length(rob_rows) + 1]] <- r
r <- fit_cs(panel, biters = 200, outcome = "rejection_rate_wins")$row; r$variant <- "winsorize_p99"; rob_rows[[length(rob_rows) + 1]] <- r

# Weighted by returned_by_voters: TWFE/Sun-Abraham via feols weights=,
# CS via its own weightsname= argument.
r <- fit_twfe(panel, weights_formula = ~returned_by_voters)$row; r$variant <- "weight_by_ballots"; rob_rows[[length(rob_rows) + 1]] <- r
r <- fit_sunab(panel, weights_formula = ~returned_by_voters)$row; r$variant <- "weight_by_ballots"; rob_rows[[length(rob_rows) + 1]] <- r
r <- fit_cs(panel, weightsname = "returned_by_voters", biters = 200)$row; r$variant <- "weight_by_ballots"; rob_rows[[length(rob_rows) + 1]] <- r

# Fractional-response GLM (TWFE-only): quasi-binomial with returned_by_voters
# as trial weights (Papke-Wooldridge fractional-response approach).
m_frac <- feglm(
  rejection_rate ~ treated | fips + year,
  data = panel, family = binomial(link = "logit"),
  weights = ~returned_by_voters, cluster = ~state_abbr
)
r <- one_row("TWFE (fractional logit)", "fractional_response",
             m_frac$coeftable["treated", "Estimate"], m_frac$coeftable["treated", "Std. Error"],
             m_frac$coeftable["treated", "Pr(>|z|)"], m_frac$nobs, uniqueN(panel$state_abbr))
rob_rows[[length(rob_rows) + 1]] <- r

robustness_table <- rbindlist(rob_rows)

# ==========================================================================
# OUTPUT
# ==========================================================================

# --- estimates_v1.md: primary TWFE / Sun-Abraham / Callaway-Sant'Anna ----
estimates_out <- file.path(out_dir, "estimates_v1.md")
modelsummary(
  list("TWFE (naive)" = m_twfe, "Sun-Abraham (ex-Iowa, ex-always-treated)" = m_sunab),
  output = estimates_out,
  title = "Effect of mandatory signature-cure notice laws on mail ballot rejection rate",
  notes = c(
    "Outcome: jurisdiction-year rejection_rate (rejected_total / returned_by_voters).",
    "Sample: usable, in-scope (50 states + DC) jurisdiction-years, 2014-2024 EAVS waves.",
    "TWFE clusters SEs by state; Sun-Abraham excludes Iowa (treatment reversal) and always-treated states (no pre-period) and averages sunab's cohort x time interactions.",
    sprintf("TWFE wild-cluster bootstrap (fwildclusterboot, B=999, clustered by state): p = %.4f, 95%% CI [%.4f, %.4f].", boot$p_val, boot$conf_int[1], boot$conf_int[2]),
    sprintf("Callaway-Sant'Anna (did::att_gt, same exclusions as Sun-Abraham): overall ATT = %.4f, SE = %.4f, p = %.4f, n = %d states.", cs_fit$row$estimate, cs_fit$row$se, cs_fit$row$p, cs_fit$row$n_states),
    pretrend_note,
    "See output/tables/heterogeneity.md and output/tables/robustness_checklist.md for the heterogeneity and robustness results."
  )
)
cat(sprintf("wrote %s\n", estimates_out))

# --- heterogeneity.md -----------------------------------------------------
het_path <- file.path(out_dir, "heterogeneity.md")
het_lines <- c(
  "# Heterogeneity by jurisdiction size",
  "",
  "Substitutes for the deferred ACS-based urban/rural split (no Census API",
  "key obtained — see HANDOFF.md). Size proxy: max `returned_by_voters`",
  "per fips across available waves. TWFE uses a continuous interaction on",
  "the full sample; Sun-Abraham and Callaway-Sant'Anna (neither of which",
  "takes an arbitrary covariate interaction) are instead refit separately",
  sprintf("on the top and bottom size terciles (small <= %d ballots, large > %d ballots).", round(tercile_cuts[1]), round(tercile_cuts[2])),
  "",
  "CAVEAT: the large and small subsamples are NOT the same set of states —",
  "terciles are computed over individual jurisdictions, and some states have",
  "no jurisdictions in one tercile or the other (n_states differs: large vs.",
  "small subsamples do not share a common state universe). Sun-Abraham and",
  "Callaway-Sant'Anna also DISAGREE here: Sun-Abraham finds a significant",
  "positive effect in the large subsample (p<0.05) and a null in the small",
  "one, while Callaway-Sant'Anna finds the opposite pattern (null in large,",
  "significant negative in small, p<0.001). Not resolved this round — read",
  "as \"heterogeneity is not conclusively established, the two corrected",
  "estimators do not corroborate each other,\" not as a confirmed effect.",
  "",
  "## NCHS urban/rural split (Phase 8)",
  "",
  "The size-tercile split above was diagnosed as unidentifiable because the",
  "small-jurisdiction subsample was missing two of four treatment cohorts",
  "entirely. This split uses NCHS's real Urban-Rural Classification Scheme",
  "for Counties (CODE2013, from data/processed/acs_controls.csv) instead:",
  "urban = codes 1-2, rural = codes 5-6, mid-category (3-4) and jurisdictions",
  "with no NCHS match (7 town-reporting states + residual ACS gap) excluded.",
  "",
  nchs_coverage_note,
  nchs_agreement_note,
  "",
  "| model | variant | estimate | se | p | n_obs | n_states |",
  "|---|---|---|---|---|---|---|"
)
for (i in seq_len(nrow(heterogeneity_table))) {
  row <- heterogeneity_table[i]
  het_lines <- c(het_lines, sprintf("| %s | %s | %.5f | %.5f | %.4f | %s | %d |",
                                     row$model, row$variant, row$estimate, row$se, row$p,
                                     format(row$n_obs, big.mark = ","), row$n_states))
}
writeLines(het_lines, het_path)
cat(sprintf("wrote %s\n", het_path))

# --- robustness_checklist.md -----------------------------------------------
rob_path <- file.path(out_dir, "robustness_checklist.md")
rob_lines <- c(
  "# Robustness checklist (PROJECT_PLAN.md Phase 4)",
  "",
  "5 variants x 3 estimators (TWFE, Sun-Abraham, Callaway-Sant'Anna) where",
  "each estimator applies naturally, plus a TWFE-only fractional-response",
  "GLM (quasi-binomial, weighted by returned_by_voters as trial counts —",
  "this is one of the 5 variants, not a 4th estimator run through",
  "everything else). Callaway-Sant'Anna uses biters=200 here (vs. 1000 for",
  "the primary estimate above) to keep runtime bounded across ~8 calls;",
  "the primary CS estimate is the one to trust for precision, these are",
  "for checking the sign/magnitude doesn't flip.",
  "",
  "| model | variant | estimate | se | p | n_obs | n_states |",
  "|---|---|---|---|---|---|---|"
)
unstable_flag <- rep("", nrow(robustness_table))
unstable_flag[robustness_table$se > 1] <- " **"
for (i in seq_len(nrow(robustness_table))) {
  row <- robustness_table[i]
  rob_lines <- c(rob_lines, sprintf("| %s | %s | %.5f | %.5f%s | %.4f | %s | %d |",
                                     row$model, row$variant, row$estimate, row$se, unstable_flag[i], row$p,
                                     format(row$n_obs, big.mark = ","), row$n_states))
}
if (any(unstable_flag != "")) {
  rob_lines <- c(rob_lines, "",
    "** NUMERICALLY UNSTABLE, not a real result: raw returned_by_voters",
    "weighting combined with sunab()'s many interaction dummies produces a",
    "near-singular weighted design for at least one cohort x time cell —",
    "traced to extreme weight variance (median ~210 ballots, max ~3.4",
    "million, a statewide-aggregate row) that TWFE and Callaway-Sant'Anna's",
    "weighted variants tolerate but the interacted Sun-Abraham spec does",
    "not. The point estimate may still be informative; the SE/p-value are",
    "not — do not cite this cell's significance either way."
  )
}
writeLines(rob_lines, rob_path)
cat(sprintf("wrote %s\n", rob_path))

# ==========================================================================
# PHASE 5 DASHBOARD DATA (docs/data/*.json) — written from the same
# in-memory objects as the markdown tables above, so the dashboard can
# never silently drift from what this script actually computed.
# ==========================================================================

twfe_ci <- twfe_fit$row$estimate + c(-1.96, 1.96) * twfe_fit$row$se
sunab_ci <- sunab_fit$row$estimate + c(-1.96, 1.96) * sunab_fit$row$se
cs_ci <- cs_fit$row$estimate + c(-1.96, 1.96) * cs_fit$row$se

model_comparison <- list(
  outcome = "rejection_rate (rejected_total / returned_by_voters), usable & in-scope (50 states + DC) jurisdiction-years, 2014-2024",
  models = list(
    list(model = "TWFE", label = "Naive two-way fixed effects",
         estimate = twfe_fit$row$estimate, se = twfe_fit$row$se, p = twfe_fit$row$p,
         ci_lo = twfe_ci[1], ci_hi = twfe_ci[2],
         bootstrap_p = boot$p_val, bootstrap_ci = boot$conf_int,
         n_obs = twfe_fit$row$n_obs, n_states = twfe_fit$row$n_states),
    list(model = "Sun-Abraham", label = "Sun & Abraham (2021) interaction-weighted",
         estimate = sunab_fit$row$estimate, se = sunab_fit$row$se, p = sunab_fit$row$p,
         ci_lo = sunab_ci[1], ci_hi = sunab_ci[2],
         n_obs = sunab_fit$row$n_obs, n_states = sunab_fit$row$n_states),
    list(model = "Callaway-Sant'Anna", label = "Callaway & Sant'Anna (2021) doubly-robust",
         estimate = cs_fit$row$estimate, se = cs_fit$row$se, p = cs_fit$row$p,
         ci_lo = cs_ci[1], ci_hi = cs_ci[2],
         n_obs = cs_fit$row$n_obs, n_states = cs_fit$row$n_states)
  )
)
write_json(model_comparison, file.path(docs_data_dir, "model_comparison.json"), auto_unbox = TRUE, digits = 6)

event_study <- list(
  overall = list(estimate = cs_dynamic$overall.att, se = cs_dynamic$overall.se),
  events = lapply(seq_along(cs_dynamic$egt), function(i) list(
    event_time = cs_dynamic$egt[i],
    estimate = cs_dynamic$att.egt[i],
    se = cs_dynamic$se.egt[i],
    band_lo = cs_dynamic$att.egt[i] - cs_dynamic$crit.val.egt * cs_dynamic$se.egt[i],
    band_hi = cs_dynamic$att.egt[i] + cs_dynamic$crit.val.egt * cs_dynamic$se.egt[i],
    significant = i %in% pre_violation
  )),
  band_type = "95% simultaneous confidence band (corrects for testing multiple event-times at once)",
  # docs/app.js reads this as `data.pretrend_diagnosis` (flagged_event_time,
  # driving_cell, explanation) — NOT `pretrend_note`, which is a different,
  # simpler field only used in the estimates_v1.md notes above. The
  # driving_cell/states breakdown (which specific group-time cohort causes
  # a flag) was done as a one-off manual investigation, not automated here
  # — a future rerun leaves driving_cell null unless someone re-does that
  # decomposition; app.js already handles a null driving_cell gracefully.
  pretrend_diagnosis = if (length(pre_violation) > 0) {
    list(
      flagged_event_time = cs_dynamic$egt[pre_violation],
      driving_cell = NULL,
      explanation = pretrend_note
    )
  } else {
    NULL
  }
)
write_json(event_study, file.path(docs_data_dir, "event_study.json"), auto_unbox = TRUE, digits = 6, null = "null")

write_json(list(
  twfe_interaction = het_twfe_row,
  subsamples = heterogeneity_table[model != "TWFE" & !(variant %in% c("nchs_urban", "nchs_rural"))],
  nchs_subsamples = heterogeneity_table[variant %in% c("nchs_urban", "nchs_rural")],
  nchs_cohort_coverage = nchs_cohort_table,
  nchs_coverage_note = nchs_coverage_note,
  nchs_agreement_note = paste(agreement_bits, collapse = " | ")
), file.path(docs_data_dir, "heterogeneity.json"), auto_unbox = TRUE, digits = 6)

write_json(list(
  rows = robustness_table[, .(model, variant, estimate, se, p, n_obs, n_states,
                                unstable = se > 1)]
), file.path(docs_data_dir, "robustness.json"), auto_unbox = TRUE, digits = 6)

cat(sprintf("wrote dashboard JSON to %s\n", docs_data_dir))
cat("NOTE: these JSON files were hand-authored once from this exact run's\n")
cat("console/markdown output (see docs/data/*.json's own '_source' field);\n")
cat("this code path regenerates them from scratch on the NEXT full rerun,\n")
cat("at which point the hand-authored '_source' annotations will be gone\n")
cat("(replaced by these R list structures, which don't carry that field) —\n")
cat("that is expected and fine, not a regression.\n")

# --- Console summary --------------------------------------------------------
cat("\n--- TWFE ---\n")
print(summary(m_twfe))
cat("\n--- Sun-Abraham (aggregated ATT) ---\n")
print(aggregate(m_sunab, agg = "att"))
cat("\n--- Callaway-Sant'Anna (overall ATT) ---\n")
print(cs_fit$agg)
cat("\n--- Callaway-Sant'Anna (dynamic/event-study aggregation) ---\n")
print(cs_dynamic)
cat("\n--- Heterogeneity table ---\n")
print(heterogeneity_table)
cat("\n--- Robustness checklist ---\n")
print(robustness_table)

# TODO(future work, not in this round's scope):
#   - Sun-Abraham has no native bootstrap for its post-aggregation ATT
#     object (fwildclusterboot doesn't support that class) — it keeps its
#     analytic cluster-robust SE while TWFE gets the wild bootstrap and
#     Callaway-Sant'Anna uses did's own native multiplier bootstrap
#     (bstrap=TRUE, the default used throughout this script). Documented
#     asymmetry, not an oversight — resolving it would mean hand-rolling
#     a bootstrap over sunab()'s aggregate() call.
#   - Phase 5 dashboard, once this round's results are reviewed.
