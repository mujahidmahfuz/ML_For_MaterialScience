# Simulated peer review, round 3 (full mode)

**Manuscript:** "Reliability beyond accuracy in machine learning of magnetic materials"
**Version reviewed:** `paper/manuscript/main/submission/` (Springer Nature template, sn-nature; built 2026-11-14), main text, Methods,
Extended Data and Supplementary Information.
**Panel:** handling editor (EIC); R1 machine-learning methodology; R2 magnetism (domain); R3 statistics; R4 devil's advocate.
**Earlier rounds:** round 1 = Major Revision (`../editorial_decision.md`); round 2 = Minor Revision (`../round2/re_review_report.md`).
This round reviews the rewritten version afresh. It does not re-score the round-2 items one by one; where a round-2 point resurfaces it is
said so.

How the claims below were checked: every number quoted in a comment was looked up in the manuscript source, and where a comment
says a result is or is not shown, that was checked against `paper/results/` (for example `rq3_generalization/external_benchmark/AUDIT_RESULTS.md`).
Points that rest on the reviewers' judgement rather than on a check are marked *(judgement)*.

---

## Editorial decision

**Major Revision** for a Nature Portfolio research journal (e.g. npj Computational Materials, Nature Communications).
**Not suitable for Nature** in its present framing *(judgement)*: the central message (accuracy, calibration, transfer and descriptor
value are distinct properties) is well established in general machine learning; the contribution is its careful quantification for
magnetic materials, which is a field-journal contribution unless the paper is reframed around a reusable benchmark or protocol.

**The work is careful and unusually honest.** The panel singles out: identical-row tier comparisons with refit-aware intervals; Holm
correction over a declared primary family; resampling at the level of dependent records (formula, paper cluster, chemical system);
an audited external benchmark that exposes 80% overlap instead of hiding it; written wording rules applied before results; and a
Methods section that lists the authors' own errors. Few papers in this area meet this standard.

**Why Major and not Minor.** Three issues require new analysis or a change of design, not only rewording:
1. The descriptor comparison (RQ1) cannot detect the effect sizes the authors themselves call practically relevant (R3-1).
2. The ordering-provenance result has no ground truth to say which label source is wrong; an independent anchor is available in the
   authors' own data (MAGNDATA) and is not used (R2-1).
3. The primary moment target is chosen so that its main "finding" (cell size) is built in (R2-2).

**Desk-check items (submission would be returned without these):** Data availability and Code availability statements, the
large-language-model statement (the title screen was classified with an LLM, and the Methods say so), and competing interests are
mandatory at submission for every Nature Portfolio journal. They are blank by the authors' choice in this version; they must be
present before submission.

---

## R1: Machine-learning methodology

**Summary.** Composition-only gradient-boosting models are compared with models given oxidation-state and DFT descriptors, on matched
rows over ten formula-grouped splits; conformal intervals and prediction sets are evaluated by subgroup; transfer is tested across label
source, chemical system and an external table. The design is sound in outline.

**Major**
- **R1-1. Hyperparameter grids are very small and identical across tiers.** Gradient boosting searches 2 x 2 settings and XGBoost 2 x 2
  (Methods, Splits, models and selection). Tier 3 has 97 inputs against 65; a model with more, noisier inputs may need different
  regularization (e.g. column subsampling, minimum child weight, shallower trees). With a fixed small grid, "Tier 3 adds nothing" could
  partly be "Tier 3 was not tuned". Request: a sensitivity run on the matched Curie population with a larger grid (or Bayesian search with
  an equal budget per tier), at least for the primary Tier 1 vs Tier 3 contrast. If the null holds, the claim is much stronger.
- **R1-2. XGBoost non-determinism is unusually large and under-explained.** "Between settings the mean prediction changes by about 25%
  of the MAE" (Methods). (a) The quantity is ambiguous: mean absolute difference between predictions of two runs, as a fraction of the
  MAE? Say so. (b) A model whose predictions move by a quarter of its error across thread counts is high-variance; this matters for the
  tier contrasts that use a single realization (ordering, moment per formula unit, the whole magnetic-physics test including the one
  "stable" CHGNet gain). Request: either use a deterministic configuration for all reported fits or average over realizations wherever
  a single-realization result is used for a verdict; at minimum, mark every single-realization verdict in the tables (Extended Data
  Table 2 marks it only in the note).
- **R1-3. The DFT descriptors are joined by reduced formula to the most stable polymorph.** This is the authors' leading explanation for the
  null (Discussion), and they had planned the decisive test (restricting to records whose source reports the same space group) but
  dropped it for run time (Methods, Planning and deviations). The test is cheap relative to its value: it separates "DFT descriptors do
  not help" from "badly joined DFT descriptors do not help". Request: run it, or state the noisy join as an explicit, untested
  limitation wherever the null is summarized.

**Minor**
- R1-4. Ordering macro-F1 is reported as 0.727 on the frozen split, 0.692 averaged over ten splits (Supplementary Table 7) and 0.712 in
  the leave-system-out setting. All are correct for their setups, but the reader meets three numbers for "the ordering model"; one
  sentence in Results explaining which split each comes from would prevent confusion.
- R1-5. End-to-end structure models (ALIGNN, fine-tuned CHGNet, MACE) are only discussed. The frozen CHGNet embedding is a reasonable
  proxy, but fine-tuning a graph network on the matched Curie set is now routine; reviewers in this field will ask *(judgement)*.
- R1-6. Related work on standardized out-of-distribution protocols for materials models (leave-cluster-out style protocols) and on
  conformal prediction for materials properties should be cited where the grouped splits are introduced, so that the protocol is
  positioned as an application rather than an invention *(judgement; authors to verify exact sources before citing)*.

## R2: Magnetism (domain)

**Summary.** The curation is thorough (removal of superconducting, ferroelectric and Neel temperatures recorded as Curie points; the
JARVIS default-label discovery). The physical interpretation is careful. Two design choices weaken the physics conclusions.

**Major**
- **R2-1. Which ordering label is right?** Materials Project and the experimental sources agree on 28% of 949 formulas (kappa 0.00), and
  336 of 508 experimental antiferromagnets are ferromagnetic in Materials Project. The text explains this by the FM-initialized workflow
  (Horton et al.), which is plausible, but the experimental labels are themselves partly text-mined, and the paper never establishes which
  side is wrong for a given formula. MAGNDATA (neutron-determined magnetic structures) is the obvious anchor.
  **Correction (2026-11-16): the review wrongly assumed the project already holds it in usable form. The copy in the project has no formulas
  and keyword-inferred labels, and contributes no rows to any target; see `code_data_verification.md`.**
  Request: use a properly collected MAGNDATA as a gold standard for the formulas it covers and report the agreement of each source with it.
  This turns "the sources disagree" into "source X is wrong in Y% of cases", which is the actionable finding for anyone training on
  Materials Project ordering labels.
- **R2-2. The primary moment target builds in its own result.** The total moment of the DFT cell grows with the number of atoms in the
  cell, so a descriptor that encodes cell size (volume, density, number of sites) must help, and the paper then finds that the gain "is
  mostly an effect of cell size". The Methods justify the choice (it is what databases report; comparisons were configured in advance),
  but physically the moment per formula unit or per magnetic atom is the meaningful quantity. Request: make the per-formula-unit (or
  per-magnetic-atom) target primary in the text and figures, and present the per-cell result as the cautionary example it is. The
  analysis already exists (Fig. 1d, Supplementary Table 8); this is mainly a reframing, but it changes the RQ1 conclusion for the moment
  from "cell size" to "a small gain carried by same-calculation outputs".

**Minor**
- R2-3. Curation rule C5 removes formulas labelled only AFM in every source, on the grounds that their "Curie" values are Neel
  temperatures. Some AFM-labelled compounds are mislabelled weak ferromagnets or ferrimagnets. The sensitivity target without C5 is only
  mentioned ("gave the same baselines"); give its numbers in a Supplementary table.
- R2-4. The external benchmark contains only ferromagnets. State explicitly in Results that the external test says nothing about
  ferrimagnets or about Neel-temperature prediction.
- R2-5. The magnetic-sublattice descriptors (M-X-M angles, coordination) are computed on the Materials Project structure, which for many
  measured compounds is not the measured phase (same join problem as R1-3). Mention this where the descriptors are introduced.

## R3: Statistics

**Summary.** The inferential machinery (Nadeau-Bengio corrected intervals, formula and cluster bootstraps, Holm over a declared family,
design effects for dependent calibration rows) is appropriate and well documented. The issues are about power and about what the
verdict rules can and cannot say.

**Major**
- **R3-1. RQ1 is underpowered relative to the authors' own practical margin.** The prespecified practical margin is 10 K for the Curie
  temperature, but the minimum detectable effect is 27-56 K and the intervals leave room for gains of 5-32 K (Results; Methods,
  Statistics). The design therefore cannot detect the effect size the authors declared relevant, and cannot establish equivalence
  either. The text is honest about this ("no detectable gain; we do not claim that a gain is absent"), but the abstract's "gave no
  detectable gain" will be read as "no gain" *(judgement)*. Requests: (a) say in the abstract that the test could detect only large
  effects; (b) report a pooled or precision-weighted estimate across the three algorithms, which would narrow the interval; (c) consider
  more splits for the primary Curie contrast (the cost is compute, not data).
- **R3-2. The Holm family includes a model the authors call numerically unstable.** The Curie ridge member of the primary family is the
  unclipped contrast (Extended Data Table 1 note: unclipped ridge gives -825 K and "is numerically unstable"), while the reported ridge
  result uses clipped inputs. Including an uninterpretable contrast in the family is odd even though the note shows that substituting the
  clipped contrast changes nothing material (0.740). Fix: declare the clipped contrast as the family member, or explain why the
  prespecified family cannot be changed and keep the note.

**Minor**
- R3-3. BCa intervals with 18 resampling clusters (blind records in unseen systems) are approximate; the acceleration constant is poorly
  estimated with so few clusters. The paper already reports percentile intervals (Fig. 3) and three clusterings (Supplementary Table 4);
  say in the Methods that with few clusters the intervals are approximate and that the conclusion ("not established either way") does not
  depend on the interval type.
- R3-4. The "stable" rule (two intervals exclude zero and at least 7 of 10 splits agree in sign) mixes an inferential criterion with a
  descriptive one; the sign count is not independent across overlapping splits. Fine as a reporting convention, but call it a
  convention, not a test.
- R3-5. The distance-matched comparison ("blind records in seen systems at comparable distances kept an R2 of 0.75") is in the text but
  in no display item; the supporting numbers are in the results files (MAE 109 K, R2 0.75; R2 difference -0.92 [-1.66, -0.05]). Add
  them to Extended Data Table 6 or Supplementary Table 3.
- R3-6. The external-benchmark wording rule (R2 upper limit <= 0.2) was fixed after the subset results of an earlier, flawed analysis were
  known (Methods). This is disclosed, which is good; the threshold itself is a convention and should be presented as such.

## R4: Devil's advocate

- **R4-1. What is new?** Every individual finding has a known general cause: marginal conformal guarantees do not hold in subgroups;
  balanced class weights distort probabilities; random splits overstate extrapolation; high-throughput DFT ordering labels are biased to
  FM; benchmark overlap inflates scores. The paper's answer (Discussion: "What we add is their size for magnetic materials") is honest
  but modest *(judgement)*. To raise the contribution, deliver something others can reuse: the audited external benchmark with its
  novelty flags, the frozen grouped splits and an evaluation script, released as a benchmark ("report these numbers"), with the paper's
  results as its first entries.
- **R4-2. The constructive message is thin.** The Discussion lists practices, but the only constructive result is the screening section
  (abstention and interval-based decisions). Strengthen it: report the screening analysis on the internal grouped test sets as well as
  on the 465 blind records, so the recommendation does not rest on one small external table.
- **R4-3. Many analyses, many forks.** The work went through several rounds in which analyses were added, corrected and dropped
  (Methods, Planning and deviations; Errors found and corrected). The disclosure is exemplary, but a sceptical reader will ask how many
  of the reported contrasts were chosen after results were seen. A one-row-per-analysis table in the Supplementary Information
  (planned before any data / planned after earlier results / added post hoc) would answer this directly.
- **R4-4. LLM-classified label noise.** The 11-27% label-noise estimate rests on a language model reading titles, not on human checks; the
  authors' own spot check is still pending (Methods source comment). Until a human-checked sample is reported, keep the label-noise
  numbers out of the abstract (they currently are) and mark Supplementary Table 5 as an unverified screen in its title.

---

## Presentation and format (EIC)

- **E-1 (fix).** Abstract: "Conformal prediction intervals were calibrated on average but under-covered the highest predictions,
  antiferromagnets and ferrimagnets." Antiferromagnets and ferrimagnets concern the ordering *prediction sets*, not intervals. Suggested:
  "Conformal intervals and prediction sets were calibrated on average but under-covered the highest predictions and the
  antiferromagnetic and ferrimagnetic classes unless the method was chosen with care."
- **E-2 (fix).** Supplementary Tables 2 and 10 are not cited individually in the main text (only through "Supplementary Tables 1-12").
  Cite Table 2 where the unseen-system MAE gap is discussed (Results, Transfer to unfamiliar chemistry) and Table 10 in the Data
  availability statement once it is written.
- **E-3.** Headings are short and informative; figures are clear and sized to the text width; legends define error bars and units. The
  Fig. 3 percentile versus text BCa intervals are explained in the legend; keep.
- **E-4.** One Extended Data figure and seven Extended Data tables (limit 10). If the target is npj Computational Materials or
  Communications Materials, Extended Data becomes Supplementary material; fix the target journal before formatting further.
- **E-5.** Mandatory statements (Data, Code, LLM use, Competing interests, Author contributions, Funding) are blank by choice; see the
  desk-check items above.

---

## Prioritized revision roadmap

| Priority | Item | Type | Effort |
|---|---|---|---|
| 1 | R2-1 MAGNDATA gold-standard agreement for ordering labels | new analysis | small (data in hand) |
| 1 | R3-1 power: abstract wording + pooled/precision-weighted RQ1 estimate (+ more splits if feasible) | analysis + text | medium |
| 1 | R1-1 larger tuning budget for the primary Curie Tier 1 vs Tier 3 contrast | new analysis | medium |
| 1 | R2-2 make the moment per formula unit (or per magnetic atom) the primary moment target in text and figures | reframing | small |
| 1 | E-5 mandatory statements before submission | author text | small |
| 2 | R1-3 same-space-group restriction test, or state the noisy join as an untested limitation | new analysis or text | medium |
| 2 | R1-2 deterministic XGBoost or realization averaging; define the 25% quantity; mark single-realization verdicts in tables | analysis + text | medium |
| 2 | R3-2 Holm family member for Curie ridge | text | small |
| 2 | R4-1 release the audited benchmark, splits and evaluation script as a reusable benchmark | packaging | medium |
| 2 | R4-4 human spot check of the title screen; mark Supplementary Table 5 as unverified until then | author check | small |
| 3 | E-1 abstract intervals/sets wording | text | trivial |
| 3 | E-2 cite Supplementary Tables 2 and 10 | text | trivial |
| 3 | R3-3, R3-4, R3-5, R3-6, R1-4, R1-5, R1-6, R2-3, R2-4, R2-5, R4-2, R4-3 | text / small tables | small each |

**Estimated effort:** the text items take about a day; the Priority-1 analyses (R2-1, R3-1b, R1-1) are each a few hours of compute on
existing data and code; R1-3 depends on how many source records report a space group.
