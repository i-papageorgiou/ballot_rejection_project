# Project Handoff — Statistical Analysis Portfolio Project
### Prepared for a new working session (Claude Code, a fresh chat, or solo work)
**Target completion: mid-October 2026**

---

## 1. How to use this document

Paste this into a new session as the opening context. It is written to be self-contained: everything needed to start work is below, including the gap being closed, the recommended project, the data sources, the analytical design, the deliverables, and the failure modes.

---

## 2. The gap this project closes

Every current portfolio project is a **data engineering artifact**. None of them poses a research question, chooses a method, produces an estimate, or defends an interpretation. For data science hiring, policy research hiring, and pre-doctoral programs alike, that is the single most visible weakness in an otherwise strong profile.

**Success criteria — the finished project must:**

1. State a research question in one sentence.
2. Use public data that any reader can download and re-run.
3. Fit a model with a defensible identification strategy, not just a correlation.
4. Report uncertainty honestly, including where the design fails.
5. Produce a short written analysis (6–10 pages) that works as a **writing sample** for think tank applications.
6. Live in a clean, reproducible GitHub repository.
7. Be finishable in roughly five weeks of part-time work.

**A hard design constraint:** do **not** use the Democratic Erosion Lab data or the Law School election-law database. Both would require permission, may carry publication restrictions, and create ambiguity about what is the author's own work. Everything below uses public data with no gatekeeper. The substantive expertise from those positions is what transfers — not the data.

---

## 3. Recommended project

### Title (working)
*Administrative Burden at the Ballot Box: State Policy and Mail Ballot Rejection Rates, 2016–2024*

### Research question
Do state-level mail voting policies — signature cure procedures, witness or notarization requirements, drop box availability, no-excuse absentee eligibility — predict jurisdiction-level mail ballot rejection rates, and does any effect differ between large urban jurisdictions and small rural ones?

### Why this question
- It sits exactly on the seam between the two research assistantships already on the resume: election administration substance plus 50-state database construction.
- Rejection rates are a real and actively contested policy outcome. Every organization in the target list — Brennan Center, MIT Election Data + Science Lab, States United, Election Reformers Network, Vera-adjacent justice groups — works on questions in this family.
- The data supports genuine panel identification rather than a cross-sectional correlation.
- The heterogeneity angle (urban versus rural) is where the interesting finding usually lives, and it is under-covered relative to the main effect.
- It reuses the existing county-level mapping skill for a figure, which strengthens the portfolio story rather than diluting it.

### Primary data source
**Election Administration and Voting Survey (EAVS)**, U.S. Election Assistance Commission. Biennial since 2004, jurisdiction-level, covering voter registration, list maintenance, mail and UOCAVA voting, polling place operations, and election technology. The 2024 wave was released on June 30, 2025 with a 100% response rate from all 50 states, five territories, and D.C., and is described by the EAC as the most comprehensive source of election administration data in the country.

- Landing page: `https://www.eac.gov/research-and-data/studies-and-reports`
- Use waves **2016, 2018, 2020, 2022, 2024**. Earlier waves have worse coverage of the mail-ballot items.
- Each wave ships a data file plus a codebook. **Read the codebook for every wave before merging anything.** Question numbering shifts between waves.

### Supporting data
| Source | Use | Where |
|---|---|---|
| **Cost of Voting Index (COVI)** | State-year measure of voting difficulty, updated through 2024 by Pomante; captures registration rules, ID laws, early voting, and absentee procedures | Published in *Election Law Journal*; replication data typically posted with the article |
| **State Democracy Index 2.0** (Grumbach) | State-year electoral democracy scores, 2000–2023, Bayesian factor-analytic measure plus an additive alternative; includes a public codebook and a separate democracy-indicator file | `https://democracypolicylab.berkeley.edu/state-democracy-index/` |
| **Census ACS 5-year** | Jurisdiction demographics — median income, education, age, race, rurality | `censusdata` or `tidycensus` package |
| **MIT Election Data + Science Lab** | County-level returns for turnout denominators and partisan context | Harvard Dataverse |
| **Voting Rights Lab / NCSL / Ballotpedia** | Hand-coding the specific policy changes used as treatment | Public trackers |

### Unit of analysis and panel structure
Jurisdiction-year. Roughly 6,000+ reporting jurisdictions per wave, five waves. Treatment (state policy) is assigned at the state level, which has direct consequences for inference — see Section 7.

### Outcome variable
`rejection_rate = rejected mail ballots / mail ballots returned by voters`

Construct this from EAVS Section C. Be explicit and consistent about the denominator. Returned-and-not-counted is not the same as transmitted-but-never-returned, and the definitions have shifted across waves.

### Design

**Main specification — two-way fixed effects:**

```
rejection_rate[i,t] = β · Policy[s(i),t] + γ · X[i,t] + α[i] + δ[t] + ε[i,t]
```

with jurisdiction fixed effects `α[i]`, wave fixed effects `δ[t]`, jurisdiction-level controls `X`, and standard errors clustered at the state level.

**Preferred specification — staggered difference-in-differences on one policy.** Pick a single well-defined policy with clean adoption timing (a statutory signature cure notice requirement is the best candidate) and estimate an event study. Because adoption is staggered across states, **do not rely on plain two-way fixed effects for the causal claim** — it is biased under treatment effect heterogeneity. Use a modern estimator:
- R: `did` (Callaway–Sant'Anna), `fixest::sunab` (Sun–Abraham), or `didimputation`
- Python: `differences` or `pyfixest`

Report the naive TWFE estimate alongside the corrected one and explain the difference. Doing this well is itself a strong signal to anyone evaluating the work.

**Heterogeneity:** interact treatment with jurisdiction size (log ballots cast) and with an urban/rural classification. Report the interaction with the same care as the main effect.

**Robustness checklist:**
- Drop 2020 and re-estimate. The pandemic wave is an outlier in every direction.
- Drop Wisconsin and Michigan, which report at municipality rather than county level and contribute thousands of very small jurisdictions.
- Winsorize or trim rejection rates at the 99th percentile.
- Weight by ballots returned as an alternative to unweighted.
- Compare a linear model to a fractional logit or beta regression, since the outcome is a bounded proportion with mass near zero.

### Deliverables
1. **GitHub repository** — structure in Section 6, fully reproducible from raw downloads.
2. **Written analysis, 6–10 pages** — question, data, method, results, limitations, policy implication. This is the writing sample. Write it for a policy audience, not a seminar.
3. **Three to four figures** — an event study plot, a coefficient plot with confidence intervals, a distribution of rejection rates by state, and a county-level choropleth. The map reuses existing skills and is the figure most likely to get screenshotted into a portfolio.
4. **A README** that a hiring manager can read in ninety seconds and understand the question, the finding, and the method.

---

## 4. Alternates

Use one of these if the primary project stalls on data problems.

### Alternate A — Democratic backsliding and administrative performance
Merge the State Democracy Index 2.0 (state-year, 2000–2023, with a public codebook containing `democracy_mcmc` and `democracy_additive` scores) against EAVS administrative outcomes: provisional ballot rates, wait times, poll worker shortages, registration rejection rates. Question: does a state's measured democratic performance predict how well its elections are actually administered, or are the two independent?

More descriptive and less causally identified than the primary project, but faster, and it maps directly onto the Democratic Erosion Lab experience. Good fallback if the EAVS policy hand-coding proves too slow.

### Alternate B — Pretrial risk assessment and fairness metrics
Use a public pretrial or risk-assessment dataset to evaluate calibration and error-rate balance across demographic groups, connecting to the Colonial Community Corrections experience. Strong substantive fit for Vera, Urban's Justice Policy Center, Measures for Justice, and the Brennan Center's justice program.

**Caution:** the ProPublica COMPAS/Broward County dataset is extremely well-trodden. Analyzing it adds little unless the angle is genuinely new. Prefer a state or county that publishes its own pretrial data, and verify data availability before committing. Higher risk than the primary project.

---

## 5. Timeline

Five weeks, part-time, starting the week of September 1.

| Week | Milestone | Definition of done |
|---|---|---|
| **1** | Data acquisition and codebook reading | All five EAVS waves downloaded; codebooks read; a written one-page memo listing every variable needed per wave and where the definitions diverge |
| **2** | Cleaning and panel construction | A single tidy jurisdiction-year panel with consistent FIPS identifiers, missingness handled and documented, and ACS controls merged. **This is the hardest week — budget accordingly.** |
| **3** | Policy coding and descriptives | The treatment variable hand-coded and sourced, with a documented coding sheet; descriptive figures and summary tables produced |
| **4** | Estimation | Main TWFE spec, event study with a modern estimator, heterogeneity, and the full robustness checklist |
| **5** | Writing and packaging | Draft written, figures finalized, README written, repo cleaned, one faculty member asked to read the draft |

If Week 2 runs long, cut the heterogeneity analysis before cutting the robustness checks. A clean result with honest limitations beats an ambitious one with a fragile foundation.

---

## 6. Repository structure

```
ballot-rejection-analysis/
├── README.md                 # question, finding, method, how to reproduce
├── requirements.txt          # or renv.lock
├── data/
│   ├── raw/                  # untouched downloads, gitignored if large
│   ├── interim/
│   └── processed/
│       └── panel.parquet
├── codebooks/
│   ├── eavs_variable_crosswalk.md   # wave-by-wave variable mapping
│   └── policy_coding_sheet.md       # every treatment coding decision, with sources
├── src/
│   ├── 01_download.py
│   ├── 02_clean_eavs.py
│   ├── 03_merge_controls.py
│   ├── 04_build_panel.py
│   ├── 05_estimate.R
│   └── 06_figures.R
├── output/
│   ├── figures/
│   └── tables/
├── writeup/
│   └── analysis.pdf
└── run_all.sh
```

**The `codebooks/` directory is the differentiator.** The resume already claims documentation of schema, variable definitions, and update procedures. This is where that claim gets demonstrated publicly rather than asserted.

Python for cleaning and R for estimation is a reasonable split and shows range. A single-language project is also fine — do not add a language just to show off.

---

## 7. Known failure modes

These are specific and will come up. Reading this section before starting will save most of a week.

**EAVS missingness is severe and non-random.** Jurisdictions use negative sentinel codes for "not applicable," "data not available," and "does not apply" rather than blanks. Check the codebook for the exact values in each wave and convert them to `NA` explicitly. Never let a sentinel code enter an arithmetic operation. Missingness correlates with jurisdiction capacity, which means listwise deletion drops precisely the under-resourced jurisdictions the analysis is about. Document the pattern and address it — a paragraph on non-random missingness is a strength in the writeup, not an admission of weakness.

**Jurisdiction identifiers are not stable.** Wisconsin and Michigan report at the municipality level, producing thousands of tiny jurisdictions. Some New England states report at the township level. Alaska uses house districts. FIPS matching will fail for a meaningful share of rows. Build an explicit crosswalk, count exactly how many jurisdictions fail to match, and report that number.

**Variable definitions shift across waves.** Question numbering changes between 2016 and 2024, and some concepts are split or merged. The crosswalk file is not optional.

**2020 is an outlier in every dimension.** Mail voting volume, policy churn, and rejection rates all move. Handle it explicitly rather than hoping the year fixed effect absorbs it.

**Treatment is assigned at the state level, so effective sample size is roughly 50, not 6,000.** Cluster standard errors at the state level. With few clusters, consider wild cluster bootstrap (`fwildclusterboot` in R). Reporting jurisdiction-clustered errors on a state-level treatment is the single most common error in work of this type and an experienced reader will spot it immediately.

**Staggered adoption breaks plain two-way fixed effects.** Covered in Section 3. Do not skip this.

**Scope creep is the main schedule risk.** The temptation will be to add turnout, provisional ballots, wait times, and a second outcome. Resist. One outcome, one treatment, one heterogeneity dimension. The project's value is completion and defensibility, not breadth.

---

## 8. Explicit non-goals

- Not a causal claim stronger than the design supports. If parallel trends fail, say so and present the result as descriptive.
- Not a novel methodological contribution. Correct application of standard methods is the goal.
- Not a dashboard or web app. The map is one static figure. Building an interactive tool is a different project and would consume the entire timeline.
- Not a partisan argument. Every target organization in the application plan is nonpartisan or bipartisan, and the writeup will be read by people who care about that. Describe policy effects, not parties.
- Not a replication of the Democratic Erosion Lab or Law School work. Different data, different question, independently defensible as the author's own.

---

## 9. What to say about this project in applications

**Resume bullet, roughly:**
> Analyzed jurisdiction-level mail ballot rejection rates across five federal elections (2016–2024, ~30,000 jurisdiction-year observations) using EAVS administrative data; estimated the effect of state signature cure requirements with a staggered difference-in-differences design, finding [result] with heterogeneity by jurisdiction size.

**In an interview,** the useful thing to be able to discuss is not the finding but the missingness problem, the clustering decision, and why plain two-way fixed effects was the wrong estimator. Those three conversations are what separate someone who ran a regression from someone who understands what they ran.

**For a writing sample,** submit the written analysis rather than the repo. Include the repo link in the cover letter.

---

## 10. First action

Download all five EAVS waves and their codebooks, then write the one-page variable memo before touching any analysis code. That memo determines whether the rest of the project takes four weeks or nine.
