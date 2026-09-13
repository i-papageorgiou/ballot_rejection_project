# Policy Coding Sheet — Statutory Signature Cure Notice Requirements

**Status: all 51 units coded, single table, no state left in an
unresolved tier.** The pilot (8 states) validated the methodology; five
further scaling passes progressively coded current status and adoption
timing for every remaining state, closing with a sixth pass that resolved
the last 3 units (Illinois, Massachusetts, Oklahoma) and corrected one
earlier entry (Mississippi — see below). What used to be four separate
tiers tracking in-progress research is now one table, since there's
nothing left to track separately. That table still carries each row's
`confidence` honestly — several entries are inferences rather than dated
citations, flagged as such, not smoothed over now that "everything is
resolved." See "What scaling found" for the process lessons and "Open
items" for the handful of residual judgment calls that remain even with
every row filled in (Iowa's reversal shape, Kansas's conflicting source,
Delaware's imprecise date, Pennsylvania's design decision).

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

**A definitional point the validation pass below made necessary to state
explicitly**: "signature defect" is deliberately broad — it covers a
*missing or invalid* signature as much as a *mismatched* one. This matters
because a separate NCSL product (Table 14, "How States Verify Voted
Absentee/Mail Ballots") classifies several states in this sheet as "Yes"
(GA, MD, NM, VT, DE, DC) as *not* conducting formal signature-matching
against a specimen on file. That is a true but narrower fact than this
sheet needs: several of those states still have a statutory notice-and-cure
right for a *missing or improperly executed* signature, which counts under
this project's definition even though it isn't a mismatch cure. See the
per-state notes in the coding table and the validation report
(`codebooks/policy_coding_validation.md`) for exactly what evidence
supports each of those six rows.

## What scaling found

Three things, beyond what the pilot already surfaced:

1. **Ballotpedia's cure-tracking pages are not fetchable as static content**
   — `Cure_period_for_absentee_and_mail-in_ballots` and its dated snapshots
   (`Ballot_curing_rules_by_state,_2022` / `,_2024`) render their tables via
   JavaScript, so every direct fetch came back empty regardless of prompt.
   The comparison those dated snapshots would have enabled — diff the 2022
   table against the 2024 table to read off exactly which states switched
   and when, without researching each one's legislative history — had to be
   abandoned. Facts attributed to Ballotpedia below come from a search
   engine's indexed synopsis of that content, not a direct read, and are
   accordingly capped at Medium confidence.
2. **The national trend is bigger than any one state's story**: standing
   notice-and-cure laws went from roughly 18 states to 33 states + DC over
   the last several years, per NCSL (cited via secondary summary, not
   independently dated). That means the *median* current "Yes" state is
   more likely a recent adopter than a longstanding one — the opposite of
   what the pilot's FL/GA "predates the panel" cases might suggest. Treating
   the still-unresolved "Yes" states (16 remaining after two scaling passes)
   as probably pre-2016 by default would be the wrong prior; each genuinely
   needs its own check, not an assumption based on the pilot's early
   apparent pattern.
3. **A few states resist even a Yes/No determination from open web
   sources in reasonable time.** Alaska and Nebraska resolved on a second
   attempt (both confirmed **No** — Alaska's only cure process is a local
   Anchorage program, not statewide). **Oklahoma did not**, across three
   separate search attempts — left explicitly unresolved rather than
   guessed.
4. **A state can look like a settled "Yes" today and still be irrelevant
   to the panel.** Connecticut's notice-and-cure requirement — Public Act
   26-42 — was enacted in **2026**, after the panel's 2024 endpoint. It is
   correctly "Yes" on every current-status source and correctly `never`
   within the 2016-2024 window used here. This is the mirror image of
   California's pilot lesson: current status alone gets both the false
   positive (CA, looked always-on but wasn't) and this false-recency risk
   (CT, looks relevant but isn't) wrong without a date attached.
5. **Adoption-year research has a genuinely bimodal yield.** Some states
   turn up a specific, dated bill on the first targeted search (Nevada's
   AB4, New York's July/August 2020 law, Vermont's statute traced to 1977,
   Colorado's HB13-1303). Others resist it even across a couple of
   follow-up searches (Illinois, Minnesota, Montana, New Mexico, Rhode
   Island, Texas, Utah) despite a confirmed current "Yes" — the fact
   pattern doesn't split cleanly by how old or well-known the state's
   mail-voting system is; Washington and Oregon (both decades-old mail-vote
   states) did eventually resolve, while several much newer or smaller
   mail-voting programs (Illinois, Rhode Island) did not.
6. **A "current status" citation can bundle two different legal questions
   that need to be pulled apart.** Arizona's 2024 HB2785 codified detailed
   *signature-verification standards* (new §16-550.01) — but the underlying
   *cure right* NCSL cites (§16-550, whose own title is "cure period")
   turned out to be a separate, older provision once fetched directly.
   Coding the 2024 bill as Arizona's adoption event would have overstated
   how recent its cure right actually is. **Iowa turned out to be the
   sharpest version of this problem, and also the most interesting result
   of the whole exercise**: its 2017 signature-verification law was
   judicially enjoined starting Sept. 30, 2019 (*LULAC v. Pate*), and
   multiple 2026 sources describing Iowa Republicans' ongoing litigation to
   *reinstate* it (as of July-Aug. 2026) confirm the injunction has held
   continuously since. NCSL's current "Yes" citation is technically
   accurate (the statute is still on the books) but administratively
   misleading (it has not been enforceable since 2019) — a de jure/de facto
   gap that matters enormously for a design built on administrative
   outcomes. Iowa is coded in the table as a genuine **treatment reversal**:
   treated for the 2018 wave only, reverting to untreated from 2020 onward
   — not a single `first_treated_wave` value, but exactly the kind of
   detail a snapshot table can never surface.
7. **Search-engine synthesis and direct primary-source fetches have
   different failure modes, and switching between them unblocked several
   states.** Two rounds of `WebSearch` alone left Delaware, Minnesota,
   Arizona, and five others stuck at "current status only." Fetching the
   actual statute page directly (Delaware's code title, Minnesota's
   Revisor site, Arizona's own `azleg.gov`) resolved four of those
   immediately — session-law history notes are exactly the kind of content
   a search engine's synopsis tends to drop. The reverse also happened:
   Justia's individual-section pages returned HTTP 403 to a direct fetch
   for six states (Montana, Rhode Island, Texas, Utah, Maine, New Mexico),
   where only a further *search* (not fetch) eventually got partial
   traction on some of them. Neither method dominates; both were needed.
8. **Pushing to resolve every last state caught a real error in earlier
   work, not just filled gaps.** Chasing Oklahoma turned up a claim that
   Mississippi is "one of three states (with Missouri and Oklahoma) that
   require a notary... but do not allow ballot curing" — flatly
   contradicting Mississippi's existing entry at the time. Following that
   thread rather than dismissing it as noise revealed the actual fact
   pattern: Mississippi's 2015 rule only required *notice* of a signature
   mismatch; the *cure opportunity* itself was added by the Secretary of
   State in **October 2020**, after litigation — meaning Mississippi's
   original "pre-2016" coding was wrong about the one thing that matters
   (whether a cure right, not just a notice, existed pre-panel). This is
   the clearest argument in the whole exercise for treating "confirmed"
   as provisional until deliberately re-tested, not as a status to stop
   checking once assigned. It also means the two remaining hardest states
   (Illinois, Massachusetts) were finally closed not with a new source but
   with a documented inference — old-style "show cause" statutory language
   for Illinois, a general-canvassing-sounding title for Massachusetts —
   after seven-plus attempts each turned up nothing more specific; that
   inference is flagged as such in the table, not disguised as a dated
   citation.

## Recency sweep of confirmed states

Checked every confirmed state for developments more recent than its recorded
`adoption_event`, since several already showed signs of ongoing legislative
activity. Run twice: once over the first 26 confirmed states, once more
over the 7 states confirmed in the fourth pass (Delaware, Minnesota,
Arizona, Texas, Utah, Montana, New Mexico). **None of the 33 states checked
required a coding revision** — no earlier adoption event was found
predating what's recorded, and no state's `first_treated_wave` changed
(one routine 2026 note: Arizona's standard per-election cure deadline was
reported as "July 26, 2026" for a specific 2026 election, consistent with
its existing 5-business-day rule, not a change to it). But several
post-panel (2025-2026) changes are worth carrying into the writeup as
context, since they show the policy landscape kept moving right up to the
present:

- **California**: AB 827 (2025) reset the cure-notification deadline to the
  22nd day after the election — a refinement of the existing 2018 right,
  not a new adoption.
- **North Dakota**: a 2025 law moved the ballot-*receipt* deadline to
  Election Day itself, removing the prior postmark grace period. Distinct
  from the cure/notice requirement (unaffected), but a related retrenchment
  in the same direction.
- **Ohio, Kansas, Utah** (plus North Dakota again): all passed 2025 laws
  ending the "postmark counts" rule for ballots arriving after Election
  Day, except military/overseas ballots. A meaningful administrative
  tightening across 4 of the panel's "Yes" states, entirely outside the
  2016-2024 window used here.
- **Indiana**: a 2025 change requires (rather than merely permits) software
  able to retract mail ballots from the vote tally — a procedural change,
  unclear relevance to cure specifically.
- General context: Ballotpedia counted 400+ election-related bills enacted
  in just the first seven months of 2026, and the Brennan Center's 2025
  year-in-review and subsequent monthly roundups confirm this is an
  unusually active period for state election law — a reason to expect this
  coding sheet will need periodic re-checking if the project's timeline
  extends, not just a one-time build.

What the pilot found, still true at scale:

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

## Final coding table — all 51 units

One table now, alphabetical by postal code. `confidence` still
distinguishes a dated citation (High/Medium) from an inference
(Low-Medium, explicitly marked "inferred") — resolving every row didn't
mean forcing every row to the same confidence level.

| state_abbr | mandatory_notice_cure | mechanism | adoption_event | first_treated_wave | notice_required | confidence | source |
|---|---|---|---|---|---|---|---|
| AK | No | none | No statewide cure process; only the City of Anchorage runs a local cure program. | never | No | High | [Alaska Div. of Elections](https://www.elections.alaska.gov/voter-information/absentee-and-early-voting/) |
| AL | No | none | No cure provision exists; a 2024-session bill (HB 97) to introduce one did not advance. | never | No | High | [Alabama Reflector, 2025](https://alabamareflector.com/2025/05/05/survey-of-11-alabama-counties-find-disparities-in-absentee-ballot-rejection/) |
| AZ | Yes | statute | §16-550's own title is "cure period," distinct from the new §16-550.01 (2024, HB2785) which codified *verification standards* only. **Confirmed directly in Pass 3**: SB1003 (2021), which also touched §§16-547/16-550, states in its own text that "the amendments made by this act... are clarifying changes only and do not provide for any substantive change in the law" — explicit legislative confirmation the cure right predates 2021 (and, combined with Arizona's ~30-year mail-voting history, comfortably predates 2016). | pre-2016 | Yes | High (upgraded — direct bill-text confirmation it predates 2021, no longer a bare inference) | [Ariz. Rev. Stat. § 16-550](https://www.azleg.gov/ars/16/00550.htm); [AZ SB1003 (2021), Ch. 343](https://www.azleg.gov/legtext/55leg/1R/laws/0343.htm) |
| AR | No | none | | never | No | Medium | [WebSearch synthesis](https://ballotpedia.org/Cure_period_for_absentee_and_mail-in_ballots) |
| CA | Yes | statute | SB 759 ("Every Vote Counts Act"), following *ACLU v. Padilla*-line ruling (Mar. 2018); signed by Gov. Brown Sept. 17, 2018, **with an urgency clause for immediate effect**. Predecessor 2015 AB 477 was opt-in only. **Corrected during Pass 2 validation**: previously credited a companion "AB 216 (2018)" with adding the notice mandate — AB 216 (2018) is actually an unrelated bill about prepaid postage on identification envelopes; SB 759 alone establishes both the notice and cure requirements. **Wave arithmetic independently re-verified and strengthened**: a source explicitly states SB 759 applied "beginning with the November 2018 election" — direct confirmation, not an inference from the signing date. | 2018 | Yes | High (upgraded — direct confirmation of in-force timing, citation error corrected) | [Cal. SOS press release on SB 759 signing](https://www.sos.ca.gov/administration/news-releases-and-advisories/2018-news-releases-and-advisories/governor-jerry-brown-signs-every-vote-counts-act-give-voters-opportunity-correct-mismatched-signatures-mail-ballots); [California Voter Foundation](https://calvoter.org/content/cvf-applauds-governor-browns-signing-sb-759) |
| CO | Yes | statute | HB13-1303 (2013 Voter Access and Modernized Elections Act) amended subsections (4)(b)/(5)(a) and added (6) of the cure statute. | pre-2016 | Yes | High | [ACLU of Colorado, HB13-1303](https://www.aclu-co.org/legislation/hb13-1303-voter-access-modernized-elections-act/) |
| CT | Yes (as of 2026 — outside panel) | statute | Public Act 26-42 (2026), implementing a Nov. 2024 statewide referendum. Previously one of 17 states with no cure period. **Postdates the panel entirely** — coded `never` for every 2016-2024 EAVS wave despite a current "Yes." | never (in-panel) | Yes | High | [Ballotpedia News, June 2026](https://news.ballotpedia.org/2026/06/23/connecticut-enacts-no-excuse-absentee-voting-four-other-election-bills-in-2026/) |
| DE | Yes (2024-2026 — likely at or past the panel edge) | statute | § 5509A established by "85 Del. Laws, c. 313, § 4" — directly confirmed as the **153rd General Assembly, 2024-2026 session**. Falls right at or after the panel's 2024 endpoint; treated conservatively as not confirmed-in-force for the 2024 wave. **Validated, and reinforced**: a fresh search independently states "Delaware does not have a cure process" — which reads as a stale/pre-2024 snapshot, not a contradiction, since it corroborates that Delaware's cure right is new enough that some sources haven't caught up to it yet. | 2024 or later (treat as outside panel pending exact date) | Yes | Medium | [Delaware code, § 5509A](https://delcode.delaware.gov/title15/c055/index.html); [Delaware General Assembly, session-law volume index](https://legis.delaware.gov/SessionLaws/Chapters?volume=166) |
| DC | Yes | statute | D.C. Law 24-342 (Elections Modernization Amendment Act of 2022) required the Board of Elections to promulgate signature-verification/cure rules. **Validated directly against the DC Board of Elections' own FAQ**, which explicitly confirms full signature comparison against the file and a cure process for both "signature mismatch" and "missing signature" — the strongest possible source (the agency itself). NCSL's separate Table 14 lists DC as *not* conducting signature verification at all; that appears to be simply wrong for DC, not a definitional nuance like GA/MD/NM/VT below. | 2024 | Yes | High (upgraded — direct agency confirmation) | [D.C. Law Library, Law 24-342](https://code.dccouncil.gov/us/dc/council/laws/24-342); [DC Board of Elections FAQ](https://www.dcboe.org/faqs/early-voting-and-election-day) |
| FL | Yes | statute | **Validated and substantially strengthened, Pass 2**: § 101.68 originally enacted in **1951**; the modern cure-affidavit comparison mechanism established by a **2001 amendment (Chapter 2001-40, §56)**; further refined by HB105 (2017, Chapter 2017-45, effective 6/2/2017 — clarifies which ID documents cure a mismatch, does not create the right) and by the 2019/2020 deadline extension. A 2017 bill initially looked like it might mean FL's cure right postdates 2016 — checked directly and it's a refinement of the 2001 mechanism, not a new adoption. | pre-2016 | Yes | High (upgraded — precise legislative lineage now confirmed back to 2001, not just "amended 2019/2020") | [Chapter 2017-45, Fla. Laws](http://laws.flrules.org/2017/45); [Fla. Stat. § 101.68, 2018 vs. 2020 text](https://www.flsenate.gov/laws/statutes/2018/101.68) |
| GA | Yes | statute | Ga. Code § 21-2-386's cure mechanism already appears in the 2010 Georgia Code — predates the panel; exact original enactment year not yet traced. **Validated**: NCSL's Table 14 lists Georgia as not conducting formal signature verification (GA's primary check is a driver's-license/ID-number match) — but Georgia's own statutory text, fetched directly, explicitly lets a voter cure "a failure to sign the oath, an invalid signature, or missing information" via affidavit. The two sources aren't in conflict once read precisely: GA doesn't do specimen-matching, but does have a real statutory notice-and-cure right for a missing/invalid signature, which is what this project's treatment definition requires. | pre-2016 | Yes | Medium | [Ga. Code § 21-2-386, 2010 text](https://law.justia.com/codes/georgia/2010/title-21/chapter-2/article-10/21-2-386) |
| HI | Yes | statute | Act 136 (signed June 25, 2019) established statewide all-mail voting with a built-in cure provision, effective starting the 2020 election cycle. | 2020 | Yes | High | [U.S. News, 2019](https://www.usnews.com/news/best-states/articles/2019-06-26/all-mail-balloting-becomes-law-in-hawaii) |
| ID | No | none | | never | No | Medium | [WebSearch synthesis](https://ballotpedia.org/Ballot_curing_rules_by_state,_2024) |
| IL | Yes | statute | No specific enactment date found despite **8+ attempts across three passes** (search, a `WebFetch` blocked by a TLS certificate error on `ilga.gov`, an elections.il.gov PDF 403, a final Pass 3 attempt returning only the same "18 states have this" framing with no date). Existence itself is solid (explicit 14-day cure deadline, consistently corroborated); the adoption year is not, and this project's tools have been unable to find it. Inferred pre-2016 from the statute's "show cause"-style language — an older drafting convention distinct from the "notice and cure" phrasing most 2019+ adopters use. **Formally the weakest-timed row in this table — existence is not in doubt, timing is.** | pre-2016 (inferred, low confidence — timing only) | Yes | Low (existence: effectively High; timing: unresolved after exhaustive effort, not for lack of trying) | [10 ILCS 5/19-8](https://law.justia.com/codes/illinois/chapter-10/act-10-ilcs-5/article-19/) |
| IN | Yes | statute | SB398, signed by Gov. Holcomb April 2021, following an Aug. 2020 federal district court ruling that the prior no-notice signature-match process was unconstitutional. | 2022 | Yes | High | [State of Elections (W&M), 2021](https://stateofelections.pages.wm.edu/2021/10/18/big-changes-indiana-election-law-curing-ballots-private-funds/) |
| IA | **Yes (2018 only) / No (2020-2024)** — a genuine treatment reversal | statute, then enjoined | A 2017 signature-verification law took effect in time for the 2018 wave, but was judicially enjoined starting Sept. 30, 2019 (*LULAC v. Pate*, Polk County). Multiple 2026 sources describe ongoing litigation by Iowa Republicans to *reinstate* the enjoined law (as of July-Aug. 2026), confirming the injunction has held continuously since 2019. NCSL's current "Yes" citation (§53.18(2), amended by 2021 Acts ch. 12) reflects the statute's text, not its enforceability. **Code as treated for 2018 only; untreated 2020, 2022, and 2024.** | 2018, reverts to never by 2020 | Yes (2018 only) | Medium (injunction timeline well-corroborated; the brief 2017-2019 window's actual administrative practice not separately confirmed) | [KCRG, July 2026](https://www.kcrg.com/2026/07/30/republican-national-committee-files-restore-signature-verified-absentee-ballots-iowa/); [Iowa Supreme Court, No. 22-0401](https://cdn.radioiowa.com/wp-content/uploads/2024/02/LULAC-ruling-PDF.pdf) |
| KS | Yes | statute | Substitute for SB130, signed by Gov. Laura Kelly, became **Chapter 36, 2019 Session Laws of Kansas** — exact statutory text confirmed: county election officers "shall attempt to contact each person who submits by advance ballot where there is no signature or where the signature does not match... and allow such voter the opportunity to correct the deficiency before the commencement of the final county canvass." **Validated and resolved**: an earlier pass flagged a contradicting source claiming Kansas "does not" have a cure provision; this direct bill-text confirmation across multiple independent sources supersedes it — that earlier claim was simply wrong. | 2020 | Yes | High (upgraded — resolved) | [Election Academy (U. Minn.), 2019](https://electionacademy.lib.umn.edu/2019/04/17/kansas-enacts-new-law-expanding-voting-access); [Kansas Legislature, SB130](https://www.kslegislature.gov/li_2020/b2019_20/measures/sb130/) |
| KY | Yes | statute | HB574, signed by Gov. Beshear **April 7, 2021**, **effective June 30, 2021** — part of the same package that introduced no-excuse early voting, "the largest election reform since 1891." **Validated, Pass 2**: exact signing and effective dates now confirmed directly; June 2021 is comfortably ahead of the Nov. 2022 election, consistent with the recorded wave. | 2022 | Yes | High (upgraded — exact dates confirmed) | [WYMT, Apr. 2021](https://www.wymt.com/2021/04/09/kentucky-sees-largest-election-reform-since-1891/); [Kentucky Today](https://www.kentuckytoday.com/state/election-reform-bill-a-stand-for-democracy-beshear-says/article_16fb3c8f-b839-5241-9996-79fa9d35de05.html) |
| LA | **Corrected** — Yes | statute | HB1074 (2022 Regular Session) enacted R.S. 18:1317, the same statute NCSL currently cites — became **Act No. 639, effective June 18, 2022**. **Corrected during validation**: originally coded `first_treated_wave=2024` on the assumption session timing put it after the Nov. 2022 election; a direct check found the confirmed effective date (June 18, 2022) is well *before* that November — the law was in force in time for the 2022 wave. | 2022 | Yes | High (corrected) | [Gov. Edwards bill-signing notice](https://gov.louisiana.gov/index.cfm/newsroom/detail/3733); [Louisiana Legislature, HB1074 enrolled text](https://legis.la.gov/legis/ViewDocument.aspx?d=1233557) |
| ME | Yes | statute | Enacted by **PL 2021, c. 273, §23 (NEW)** — confirmed directly from the statute's own history note, with no amendments since. | 2022 | Yes | High | [Maine statute, 21-A §756-A](https://legislature.maine.gov/statutes/21-a/title21-Asec756-A.html) |
| MD | Yes | statute | HB535/SB379, signed Apr. 24, 2023, effective Oct. 1, 2023. **Validated**: two independent sources confirm Maryland does not compare signatures against a specimen on file (envelope-signed only) — but HB535's own cure right is specifically for "failure to sign a mail-in ballot properly" (a missing/improper signature), not a mismatch, so it still satisfies this project's definition. | 2024 | Yes | High | [Democracy Docket](https://www.democracydocket.com/news-alerts/maryland-enacts-mail-in-ballot-pre-processing-and-curing-law/); [Maryland State Board of Elections, rumor control](https://elections.maryland.gov/press_room/rumor_control.html) |
| MA | Yes | statute | **The "wrong statute" worry is resolved, Pass 3**: § 94's actual text confirms it directly — "the clerk shall notify, as soon as possible, each voter whose ballot was rejected" — genuine mandatory notice-and-cure language, not a mismatch like Rhode Island's case. The remaining gap is narrower than previously stated: not "is this the right statute," but purely "what year was it enacted" — still unresolved after 5+ attempts across two passes. Inferred pre-2016 on the same "no evidence of a recent retrofit" basis as OH/MT, now with the existence question closed. | pre-2016 (inferred — timing only, not existence) | Yes | Medium (upgraded — existence confirmed via direct statutory text; timing remains an inference) | [Mass. Gen. Laws ch. 54, § 94](https://malegislature.gov/Laws/GeneralLaws/PartI/TitleVIII/Chapter54/Section94) |
| MI | Yes | constitutional amendment (2022 Ballot Proposal 2), implemented via administrative rule | **Corrected mechanism, Pass 2**: the cure right originates from voter-approved **2022 Ballot Proposal 2**, passed via the Nov. 8, 2022 ballot itself — not merely "an administrative rule under an existing statute" as previously described. Implementing signature-matching rules were filed Dec. 19, 2022, effective 7 days later (Dec. 26) — both dates **after** the Nov. 8, 2022 election, so 2022 is correctly coded untreated regardless of which date is used; further amendment in 2024 (Mich. Comp. Laws §§ 168.766, 168.766a). Wave call unchanged and now more solidly reasoned (the right didn't exist in any form until the same day as that wave's election). | 2024 | Yes | High (upgraded — mechanism corrected, wave logic strengthened) | [Michigan SOS signature cure guidelines](https://www.michigan.gov/sos/elections/voting/voters/signature-cure-guidelines); [Michigan Advance, 2026](https://michiganadvance.com/2026/04/02/why-ballot-curing-is-a-potential-secret-weapon-for-michigan-campaigns/) |
| MN | Yes | statute | The rejection-notification subdivision (203B.121 subd. 2) was already being amended in **2013** (2013 c 131 art 1 s 6), confirming it predates the panel; further amended 2015, 2021, 2023, 2024. **Validated, Pass 2**: Minnesota session laws without a stated effective date take effect Aug. 1 following enactment by default — meaning 2013 c.131 was very likely in force by Aug. 1, 2013, comfortably pre-2016 either way. | pre-2016 | Yes | High | [Minn. Revisor, 203B.121 history](https://www.revisor.mn.gov/statutes/cite/203B.121) |
| MS | **Corrected twice** — Yes | guidance (administrative rule) | A 2015 rule (1-Miss-Code-R-17-4.1) required *notice* of a signature mismatch only. The actual *cure opportunity* was added by Secretary of State Michael Watson in **October 2020**, following litigation — confirmed via contemporaneous news coverage dated Oct. 20 and Oct. 24, 2020, both describing the rule as already in force ahead of that year's election. Earlier coding of this row as "pre-2016" conflated the notice-only rule with the full right — corrected once already. **Second correction, Pass 2**: the first correction fixed the *fact* but miscalculated the *wave* — October 2020 is before the Nov. 3, 2020 election, so this should first-treat the **2020** wave, not 2022. Caught by a zero-cost arithmetic recheck (the row's own recorded date contradicted its own recorded wave), not new research — exactly the failure mode this validation pass was designed to catch. | 2020 | Yes | High (corrected; date is now dated to specific news coverage, not just a synthesis) | [Mississippi Today, Oct. 20 2020](https://mississippitoday.org/2020/10/20/new-rule-ensures-election-officials-will-inform-mississippians-of-problems-with-mail-in-ballots/); [WLBT/Action News 5, Oct. 24 2020](https://www.actionnews5.com/2020/10/24/one-absentee-ballot-mistake-gets-fix-mississippi-with-new-rule/) |
| MO | No | none | Requires notarization instead; no cure. | never | No | Medium | [MOST Policy Initiative](https://mostpolicyinitiative.org/science-note/ballot-signature-verification-curing-2/) |
| MT | Yes | statute | Not directly dated, but the neighboring section in the same statutory scheme (13-13-241) was amended by Chapter 571, Laws of 1979 — the absentee-ballot examination/notice framework this section belongs to traces at least that far back. | pre-2016 (inferred) | Yes | Low-Medium (inferred from a neighboring section, not §13-13-245 itself) | [MCA 13-13-241 history](https://archive.legmt.gov/bills/mca/title_0130/chapter_0130/part_0020/section_0410/0130-0130-0020-0410.html) |
| NE | No | none | | never | No | High | [Ballotpedia, Election administration in Nebraska](https://ballotpedia.org/Election_administration_in_Nebraska) |
| NV | Yes | statute | AB4 (signed Aug. 2020) established mandatory notice-and-cure; AB321 (2021) later extended the cure window to 6 days post-election. | 2020 | Yes | High | [The Nevada Independent](https://thenevadaindependent.com/article/legislature-must-make-ab4-permanent) |
| NH | No | none | | never | No | Medium | [WebSearch synthesis](https://ballotpedia.org/Cure_period_for_absentee_and_mail-in_ballots) |
| NJ | Yes | statute (contemporaneous litigation also present) | L. 2020 c. 70 established a pre-deprivation notice-and-cure requirement for mail and provisional ballots, amending N.J.S.A. 19:63-17 — a real, independently-confirmed session-law chapter, unlike North Dakota's original citation. **Investigated in Pass 3's mechanism audit**: *League of Women Voters of NJ v. Way* also produced a June 2020 preliminary injunction over the same subject, settled and dismissed Jan. 2021 — litigation and statute existed in parallel. Because the statute is independently confirmed as real (not just asserted), this is coded as `statute` with the litigation noted as a contributing factor, not reclassified the way North Dakota's row was before its own statute was confirmed. | 2020 | Yes | Medium | [N.J. cure guidance PDF, 2025](https://www.nj.gov/state/elections/assets/pdf/guidelines/2025/2025-0507-guide-nj-signature-verification-and-cure.pdf); [NCSL Table 15](https://www.ncsl.org/elections-and-campaigns/table-15-states-with-signature-cure-processes) |
| NM | Yes | statute | Not directly dated for the cure provision itself, but New Mexico's absentee-ballot framework traces to 1969 (Laws 1969, ch. 240) with no evidence found of a distinct recent retrofit adding the cure mechanism specifically. **Validated**: NCSL confirms NM does not compare signatures against a specimen (its own Table 14 entry describes outright rejection on a missing signature, no cure mentioned) — but NM's own statute (§1-6-14, read directly) explicitly requires the clerk to "immediately send the voter a notice to cure" a missing signature. Table 14 evidently doesn't capture every state's downstream cure step; the statute itself is the better source here. | pre-2016 (inferred) | Yes | Low-Medium (inferred on timing; the existence of the cure right itself is now Medium, confirmed against the statute text) | [N.M. Stat. § 1-6-14](https://law.justia.com/codes/new-mexico/chapter-1/article-6/section-1-6-14/) |
| NY | Yes | statute | Passed by the legislature in July 2020, signed by Gov. Cuomo Aug. 20, 2020. **Validated, Pass 2**: a source explicitly states the notification/cure requirement applied "beginning with the Fall 2020 election" — direct confirmation, not an inference from the signing date. | 2020 | Yes | High (upgraded — direct in-force confirmation) | [Governor's office, Aug. 2020 signing announcement](https://www.governor.ny.gov/news/governor-cuomo-signs-law-sweeping-election-reforms); [Gotham Gazette, 2020](http://www.gothamgazette.com/state/9853-new-york-absentee-voters-cure-ballots-under-circumstances-signatures-how-it-works) |
| NC | **No** (primary variable) / Yes (sensitivity variable) | litigation (consent decree, 2020) | Established via settlement of *NC Alliance for Retired Americans* litigation, not by statute — coded No on the primary (statutory-only) treatment; retained as a `mechanism=litigation` row for a robustness check that includes non-statutory cure regimes. | never (statutory) / 2020 (if litigation counted) | Yes | Medium | [NCSBE press release, 2020](https://www.ncsbe.gov/news/press-releases/2020/09/22/state-board-updates-cure-process-ensure-more-lawful-votes-count); [Democracy NC](https://democracync.org/research/codifying-and-improving-the-cure-process/) |
| ND | **Corrected — Yes** | statute (post-litigation codification) | **Resolved in Pass 3, after being flagged unresolved in Pass 2.** The June 2020 requirement was indeed a temporary federal court injunction (*Self Advocacy Solutions N.D. v. Jaeger*), scoped to that year's primary — not a lasting rule, and the doubt raised in Pass 2 about treating this like North Carolina's litigation-only case was reasonable to raise. But direct confirmation now shows the **North Dakota legislature's 2021 session independently repealed** the old signature-matching statutes (§§16.1-07-09, 16.1-07-12) and **created** a new, genuine statute — **§16.1-07-13.1, "Signature mismatch – Verification of signatures"** — via **S.L. 2021, ch. 164, §114**. This is a real, lasting legislative act responding to (not merely restating) the injunction, unlike North Carolina's situation. **Corrected wave**: since the lasting statutory mechanism dates to the 2021 session (not the 2020 injunction), first-treatment should be **2022**, not the previously recorded 2020 — North Dakota's own version of the Indiana pattern (2020 court ruling → 2021 legislative codification → first affects the 2022 wave). | 2022 (corrected from 2020) | Yes | High (corrected — specific session-law chapter now confirmed via two independent sources describing the same repeal-and-recreate action) | [North Dakota Century Code, Title 16.1, Ch. 16.1-07](https://ndlegis.gov/cencode/t16-1c07.pdf); [Self Advocacy Solutions N.D. v. Jaeger](https://www.courtlistener.com/opinion/9794800/self-advocacy-solutions-nd-v-jaeger/) |
| OH | Yes | statute | *Ne. Ohio Coalition for the Homeless v. Husted* (2016) upheld the state's existing 7-day post-election cure period as constitutional — confirms the law predates 2016; original enactment year not traced. | pre-2016 | Yes | Medium | [WebSearch synthesis, referencing the 2016 6th Cir. ruling](https://law.justia.com/codes/ohio/title-35/chapter-3509/section-3509-06/) |
| OK | No | none | Requires notarization instead of signature verification, like Missouri. The same source also named Mississippi as a third notary-only, no-cure state — which this table's MS row now contradicts (MS added an actual cure right in Oct. 2020); that source was likely describing Mississippi's pre-2020 status, not Oklahoma's, so it doesn't undermine Oklahoma's own "No." | never | No | Medium | [KOSU, July 2026](https://www.kosu.org/podcast/focus-black-oklahoma/2026-07-29/notarizing-democracy-why-oklahoma-makes-absentee-voters-take-an-extra-step) |
| OR | Yes | statute | Not tied to a specific cure-enactment date, but Oregon has run 100% mail elections statewide since 1998 (Ballot Measure 60) with no evidence found, across three targeted searches, of a later retrofit specifically adding the cure/notice provision — inferred rather than directly dated. **Reinforced, Pass 3**: independently confirmed that ORS 254.431 was *amended* in 2021 (extending the cure period to 21 days) — an amendment presupposes the underlying right already existed, consistent with (not proof of, but supportive of) the pre-2016 inference. | pre-2016 (inferred) | Yes | Medium (inferred, strengthened by the 2021-amendment logic) | [Oregon Measure 60, Ballotpedia](https://ballotpedia.org/Oregon_Measure_60,_Vote_by_Mail_for_Biennial_Elections_Initiative_(1998)); [ORS 254.431](https://oregon.public.law/statutes/ors_254.431) |
| PA | Partial | discretionary | No statewide signature-verification/cure requirement; individual counties may choose to cure. **Needs a design decision** (state-level `Partial` vs. a jurisdiction-level covariate) before it enters the treatment variable — see Open items; not resolved to a single `first_treated_wave` by design, not by omission. | n/a — see Open items | n/a | Medium | [Movement Advancement Project, signature cure map](https://www.lgbtmap.org/democracy-maps/signature_cure) |
| RI | Yes | guidance (administrative regulation) | Regulation 410-RICR-20-00-23 (uniform mail-ballot cure guidelines) has a confirmed effective date of **08/29/2018** — resolves the earlier statute-vs-regulation mismatch; the real mechanism is the regulation, not the § 17-20-26 statute NCSL cited. | 2018 | Yes | High | [RI Dept. of State regulation, effective 08/29/2018](https://rules.sos.ri.gov/regulations/Part/410-20-00-23) |
| SC | No | none | | never | No | Medium | [WebSearch synthesis](https://ballotpedia.org/Cure_period_for_absentee_and_mail-in_ballots) |
| SD | No | none | | never | No | Medium | [WebSearch synthesis](https://ballotpedia.org/Ballot_curing_rules_by_state,_2024) |
| TN | No | none | | never | No | Medium | [WebSearch synthesis](https://ballotpedia.org/Cure_period_for_absentee_and_mail-in_ballots) |
| TX | Yes | statute | The corrective-action process matches Texas's 2021 omnibus election law (SB1), which added the signature-verification-committee structure and correction process; SB1599 (2023) further revised the process. | 2022 | Yes | Medium | [Tex. SOS Advisory 2023-13 (SB1599)](https://www.sos.state.tx.us/elections/laws/advisory2023-13.shtml) |
| UT | Yes | statute | HB0036, effective **May 12, 2020** — comfortably before the Nov. 2020 election. **Validated, Pass 2**: independently confirmed as "in effect during the 2020 election" via a second source. | 2020 | Yes | High (upgraded — bill number and in-force status both independently confirmed) | [Utah Code, Title 20A Ch. 3a, effective 5/12/2020](https://le.utah.gov/xcode/Title20A/Chapter3A/C20A-3a_2020051220200512.pdf) |
| VT | Yes | statute | Statute traces to 1977, No. 269 (Adj. Sess.); amended 2015, 2017, 2019, 2021 — comfortably predates the panel. **Validated**: multiple independent sources confirm Vermont checks only that a signature is present, not that it matches a specimen — consistent with (not contradicting) a cure right that most likely addresses a missing signature rather than a mismatch; the 1977-dated citation is unaffected either way. | pre-2016 | Yes | High | [Vermont Legislature, 17 V.S.A. § 2547](https://legislature.vermont.gov/statutes/section/17/051/02547) |
| VA | Yes | statute | HB1800, passed in the Aug. 2020 special session, reinstituted the cure process in time for the Nov. 3, 2020 general election. | 2020 | Yes | High | [DCist, 2020](https://dcist.com/story/20/10/26/for-virginia-voters-who-mess-up-their-absentee-ballot-a-new-law-gives-them-a-second-chance/) |
| WA | Yes | statute | 2011 c 10 established the notice/cure requirement under RCW 29A.60.165. **Validated, Pass 2**: confirmed effective date **8/24/2011** (2011 1st Special Session), comfortably pre-2016. | pre-2016 | Yes | High (upgraded — exact effective date confirmed) | [Wash. Rev. Code 29A.60.165, session-law note](https://app.leg.wa.gov/RCW/default.aspx?Cite=29A.60.165) |
| WV | No | none | | never | No | Medium | [WebSearch synthesis](https://ballotpedia.org/Ballot_curing_rules_by_state,_2024) |
| WI | No (discretionary, not mandatory) | discretionary | Statute lets clerks "may" return a defective ballot for correction rather than requiring it — no uniform notice-and-cure obligation; a 2026 lawsuit (League of Women Voters of WI) seeks to make it mandatory. | never (as of coding) | No | High | [Votebeat, May 2026](https://www.votebeat.org/wisconsin/2026/05/26/absentee-ballot-curing-lawsuit-league-women-voters/) |
| WY | No | none | | never | No | Medium | [WebSearch synthesis](https://ballotpedia.org/Ballot_curing_rules_by_state,_2024) |

## Open items before this feeds the estimation code

Every one of the 51 units now has a row with a `first_treated_wave` value
(or an explicit "n/a — design decision pending" for Pennsylvania). What's
left is not missing data but residual judgment calls — several rows are
inferences rather than citations, and inferences should be checked before
they anchor a result, not trusted just because a row exists for them.

- **Illinois and Massachusetts are inferred, not dated, and are the two
  weakest rows in the table.** Illinois's `pre-2016` rests on statutory
  phrasing style alone, after 7+ research attempts across two passes found
  nothing more specific (a TLS certificate error blocked `ilga.gov`
  directly; a 403 blocked the elections.il.gov PDF). Massachusetts rests on
  the same kind of inference with an added risk — § 94's title suggests a
  general canvassing provision, so the citation itself might be wrong, the
  same failure mode Rhode Island turned out to have (resolved there;
  unresolved here). If either state's exact classification matters to a
  headline result, these two rows are where to spend further verification
  effort, not the ones already carrying a High/Medium-confidence citation.
- **Iowa's treatment-reversal shape needs a design decision, not just a
  data point.** Every other state in the table is a single step function
  (untreated, then treated from some wave onward, or vice versa never).
  Iowa is untreated → treated (2018) → untreated again (2020-2024) — the
  panel-building or estimation code needs to represent this as a
  time-varying indicator per wave, not a single `first_treated_wave`
  scalar, or Iowa will be miscoded no matter which single value is chosen.
  Also worth flagging in the writeup as a substantively interesting case in
  its own right (a state whose statutory signature-verification regime
  became judicially unenforceable mid-panel).
- **Mississippi's row was corrected mid-project** (see "What scaling
  found" #8) — from "pre-2016" to "2022," after chasing an unrelated
  Oklahoma lead surfaced a direct contradiction. Worth a second look before
  it anchors a result, precisely because the correction came from a lucky
  cross-reference rather than a planned check — there is no principled
  reason to believe every other row's original coding is equally free of a
  similar error, only that no other contradiction happened to surface.
- **Pennsylvania's county-optional design decision** — state-level `Partial`
  vs. a jurisdiction-level covariate — should be made deliberately, not
  defaulted, since PA is a large state whose classification could matter to
  the results either way.
- **Kansas's conflicting source** — one search result flatly contradicted
  the specific bill history it had just described in the same answer. The bill-history version is more likely correct (it's concrete and
  verifiable against a real bill number), but this should get a primary-source
  check before Kansas anchors any result.
- **Delaware's exact date within its 2024-2026 session** is still open —
  confirmed to be the 153rd General Assembly but not narrowed further, so
  it's coded conservatively as at-or-past the panel edge rather than a
  confirmed 2024 wave. Low-stakes either way (it barely touches the panel
  regardless of the exact date within that range) but worth a quick pin-down
  if Delaware's row is ever inspected closely.
- **Ballotpedia's dated snapshot pages are unusable via fetch** — if the
  2022-vs-2024 diff approach is worth another attempt, it would need a
  different retrieval method (e.g., the Wayback Machine's cached HTML, or a
  tool that renders JavaScript) rather than a repeat of the same fetch.
- **Wisconsin and Michigan's large jurisdiction counts** (thousands of small
  WI/MI jurisdictions per `PROJECT_PLAN.md`'s robustness checklist) make
  both states' coding decisions unusually consequential — already resolved
  above, but worth a second independent check given the stakes.
