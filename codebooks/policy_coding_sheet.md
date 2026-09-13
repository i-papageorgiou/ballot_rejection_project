# Policy Coding Sheet — Statutory Signature Cure Notice Requirements

**Status: pilot (8 of 51 units coded).** This document defines the coding
methodology and demonstrates it on a deliberately varied pilot batch before
scaling to all 50 states + DC. See "What the pilot found" below for why a
pilot came first.

## Treatment definition

Per the project's design (`PROJECT_PLAN.md` §Week 3, `Project_Handoff_...md`
§"Preferred specification"), the treatment is a **statutory requirement that
election officials notify a voter of a signature defect on their mail
ballot and give them an opportunity to cure it before the ballot is
rejected.** Three words matter and are coded separately, because states
diverge on exactly these dimensions:

- **Statutory** — enacted by the legislature (a bill, codified into state
  election code). Excludes court-ordered/consent-decree cure processes and
  agency guidance issued without a statutory basis. These are coded but
  flagged `mechanism = litigation` or `guidance`, not counted in the primary
  treatment variable. Rationale: a court order can be reversed on appeal or
  apply to a single election cycle in ways a statute doesn't, and mixing
  the two would blur a design the handoff doc explicitly wants clean
  ("pick a single well-defined policy with clean adoption timing").
- **Mandatory** — clerks *must* notify and allow cure ("shall"). A state
  where clerks *may* do so at their discretion ("may," no uniform
  requirement) is coded `mandatory = No` even if some jurisdictions in that
  state do cure in practice — the EAVS panel is jurisdiction-level, so
  within-state non-uniformity would otherwise contaminate the state-level
  treatment assignment.
- **Notice** — the voter must be told about the defect, not merely permitted
  to fix it if they happen to find out. A state with a cure window but no
  notice obligation is coded `notice_required = No`; this is coded as a
  separate field because the handoff's design specifically wants the
  *notice* requirement, not curing in general.

## What the pilot found

Two things that change how the full build has to go:

1. **Current-status trackers (NCSL, Ballotpedia) answer the wrong
   question.** They report whether a state has a cure process *today* —
   useful for identifying the candidate list, but silent on *when* it was
   adopted, which is the one fact a staggered-adoption event study actually
   needs. California is the clearest case: it reads as a settled "Yes" on
   every current-status source, but its **mandatory statewide** notice+cure
   requirement only became law in 2018 (SB 759, following a March 2018
   court ruling; AB 216 added the notice mandate). Before that, curing
   existed only as a county option (2015 AB 477) or only in counties that
   opted into the Voter's Choice Act (2016). Treated as "always-on" by
   mistake, California would silently drop out of the identifying variation
   the design depends on.
2. **Adoption timing requires a second research pass per state** beyond the
   snapshot tables — legislative history (bill number, session, effective
   date) or litigation timeline. This is the actual Week 3 bottleneck the
   project plan anticipated ("the real bottleneck") — confirmed by this
   pilot, not just assumed.

## Wave-alignment rule

EAVS waves correspond to the November general election of even years. A
state is coded `treated = Yes` for a given wave if the requirement was in
legal force before that wave's November election — a law or rule that took
effect *after* that November is coded as first-treating the *next* wave.
(Michigan below is the case this rule matters for.)

## Columns

| Column | Meaning |
|---|---|
| `state_abbr` | Two-letter postal code |
| `mandatory_notice_cure` | Yes / No / Partial — the primary treatment variable per the definition above |
| `mechanism` | `statute` / `litigation` / `guidance` / `discretionary` |
| `adoption_event` | The specific statute, ruling, or rule and its date |
| `first_treated_wave` | Earliest EAVS wave (2016-2024) coded `treated=Yes`, or `pre-2016` (always-treated in-panel), or `never` |
| `notice_required` | Yes / No, separate from curing itself (see definition) |
| `confidence` | High / Medium / Low — see below |
| `source` | Citation(s), as markdown links |

**Confidence** reflects how well-corroborated the adoption date is: **High**
= a specific statute/bill with an independently-verified effective date
(2+ sources agree). **Medium** = status is well-corroborated but the exact
adoption date rests on one source or is approximate. **Low** = conflicting
or thin sourcing — flagged for a research follow-up before this state is
used in the final treatment variable.

## Pilot batch (8 states, chosen to stress-test the methodology)

| state_abbr | mandatory_notice_cure | mechanism | adoption_event | first_treated_wave | notice_required | confidence | source |
|---|---|---|---|---|---|---|---|
| CA | Yes | statute | SB 759 (2018), following *ACLU v. Padilla*-line ruling (Mar. 2018); AB 216 (2018) added the notice mandate. Predecessor 2015 AB 477 was opt-in only. | 2018 | Yes | Medium | [Cal. Elec. Code § 3019](https://www.ncsl.org/elections-and-campaigns/table-15-states-with-signature-cure-processes); [CalVoter Foundation history](https://www.calvoter.org/sites/default/files/ballot_curing_hearing_march_2025_kim_alexander_testimony.pdf) |
| FL | Yes | statute | In force before 2016 (exact original enactment not yet traced); Fla. Stat. § 101.68 amended 2019/2020 extending the cure deadline from the day before the election to 5 p.m. the 2nd day after. | pre-2016 | Yes | Medium | [Fla. Stat. § 101.68, 2018 vs. 2020 text](https://www.flsenate.gov/laws/statutes/2018/101.68) |
| GA | Yes | statute | Ga. Code § 21-2-386's cure mechanism already appears in the 2010 Georgia Code — predates the panel; exact original enactment year not yet traced. | pre-2016 | Yes | Medium | [Ga. Code § 21-2-386, 2010 text](https://law.justia.com/codes/georgia/2010/title-21/chapter-2/article-10/21-2-386) |
| MI | Yes | statute (via administrative rule under existing statute) | Signature-cure notification rules took effect Dec. 19, 2022 — **after** the Nov. 2022 election, so 2022 is coded untreated; further amendment in 2024 (Mich. Comp. Laws §§ 168.766, 168.766a). | 2024 | Yes | Medium | [Michigan SOS signature cure guidelines](https://www.michigan.gov/sos/elections/voting/voters/signature-cure-guidelines); [Bridge Michigan, 2025](https://bridgemi.com/michigan-government/michigan-elections-faq-how-do-clerks-verify-absentee-ballot-signatures/) |
| ND | Yes | statute | First adopted for the June 2020 all-mail primary (N.D. Cent. Code § 16.1-07-13.1) — the first state to adopt notice-and-cure in the panel window. | 2020 | Yes | Medium | [NCSL Table 15](https://www.ncsl.org/elections-and-campaigns/table-15-states-with-signature-cure-processes) |
| NC | **No** (primary variable) / Yes (sensitivity variable) | litigation (consent decree, 2020) | Established via settlement of *NC Alliance for Retired Americans* litigation, not by statute — coded No on the primary (statutory-only) treatment; retained as a `mechanism=litigation` row for a robustness check that includes non-statutory cure regimes. | never (statutory) / 2020 (if litigation counted) | Yes | Medium | [NCSBE press release, 2020](https://www.ncsbe.gov/news/press-releases/2020/09/22/state-board-updates-cure-process-ensure-more-lawful-votes-count); [Democracy NC](https://democracync.org/research/codifying-and-improving-the-cure-process/) |
| AL | No | none | No cure provision exists; a 2024-session bill (HB 97) to introduce one did not advance. | never | No | High | [Alabama Reflector, 2025](https://alabamareflector.com/2025/05/05/survey-of-11-alabama-counties-find-disparities-in-absentee-ballot-rejection/) |
| WI | No (discretionary, not mandatory) | discretionary | Statute lets clerks "may" return a defective ballot for correction rather than requiring it — no uniform notice-and-cure obligation; a 2026 lawsuit (League of Women Voters of WI) seeks to make it mandatory. | never (as of coding) | No | High | [Votebeat, May 2026](https://www.votebeat.org/wisconsin/2026/05/26/absentee-ballot-curing-lawsuit-league-women-voters/) |

## Open items before scaling to all 51 units

- **42 states + territories remain uncoded.** The NCSL Table 15 fetch (see
  below) is a candidate list for current "Yes" status but every adoption
  date needs independent verification the way California's was — the
  snapshot table alone is not sufficient sourcing for a `first_treated_wave`
  value.
- **NCSL Table 15 full current-status pull** (for reference, not yet
  independently verified per-state): Arizona, California, Colorado,
  Connecticut, Delaware, DC, Florida, Georgia, Hawaii, Illinois, Indiana,
  Iowa, Kansas, Kentucky, Louisiana, Maine, Maryland, Massachusetts,
  Michigan, Minnesota, Mississippi, Montana, Nevada, New Jersey, New Mexico,
  New York, North Carolina, North Dakota, Ohio, Oregon, Rhode Island,
  Texas, Utah, Vermont, Virginia, Washington read "Yes" as of the table's
  Aug. 2026 update. States not listed there (implying "No" as of today) still
  need a positive confirmation each, the way Alabama and Wisconsin got one
  here — silence in a tracker is not itself a source.
- **Litigation-driven states to check individually**, per the ballot-curing
  history search: Arkansas, Pennsylvania, New Jersey, Texas, New York, Ohio,
  Mississippi, South Carolina — same statutory-vs-litigation judgment call
  North Carolina needed.
- **Pennsylvania is a known hard case**: cure is optional at the *county*
  level, no statewide requirement — needs its own coding convention (likely
  `mandatory_notice_cure = Partial`, and probably excluded from primary
  treatment the same way NC's litigation-based regime is, or handled as a
  jurisdiction-level rather than state-level covariate — worth a design
  decision before it's coded, not an ad hoc call in the middle of the table).
- **Wisconsin and Michigan's large jurisdiction counts** (thousands of small
  WI/MI jurisdictions per `PROJECT_PLAN.md`'s robustness checklist) make
  both states' coding decisions unusually consequential — worth prioritizing
  in the full build.
