# EIC Report (Phase 2, paper-visible)

Contract: `reviewer/reviewer_full/v1`, used verbatim (generated_at 2026-11-09T17:11:59Z). Phase 1 pre-commitment: `eic_phase1.md` (same folder). Scoring below applies the Phase 1 triggers without deviation, so there is no Scoring Plan Dissent section.

Material reviewed: `paper/manuscript/manuscript.tex`, `references.bib` (36 entries), Tables 1–6 and S1–S3 (.tex and .notes.txt), Figures 1–4 and S1 (.png). I also checked `paper/results/rq3_generalization/label_provenance/*.csv` and `results/claims/claims_register_v1.3.md` to confirm one interpretive point (W3). Everything else is reviewed as submitted.

---

## Dimension Scores

### D1: methodology_rigor — **warn**
The design is better than most submissions in this area. Comparisons are matched: Tier 1/2/3 use identical rows, splits, grids and metrics (Results, "A curated multi-source dataset…" and Table 2 footnote). There are ten pre-specified formula-grouped splits with seeds 20267000+i, a paired formula-group bootstrap, and a stated "stable" criterion. Methods, "Statistical comparison", says the decision rules were written into configuration files in advance. The external benchmark was audited under a written plan, uses a paper-cluster bootstrap, and fixed its wording rule in advance (the R² upper limit ≤ 0.2 for "no skill"). Nothing triggers a block: I see no train–test leakage capable of reversing the conclusions (the formula-spelling leak is quantified at 0.6–1.3% under Limitations), comparisons are matched, and a reproducibility package exists. The score is still warn, on these reporting and design gaps:
- **Provenance-transfer design.** The label-provenance test (Table 6, rows 4–5) confounds labelling convention with label-space and class-prior shift. The experimental slice has essentially no NM class (5 NM rows of 2,772 test rows in `ordering_provenance_slices.csv`), while the MP slice is 35% NM. In the reverse direction, 4,753 MP test rows were dropped because they belong to a class not seen in training. The design cannot support the conclusion drawn from it (W3).
- **Curie tier comparison.** For gradient boosting the Tier 1→3 point estimate is a 14.3 K *degradation* (Fig. 1b; Table 2), larger than the 10 K practical margin. The verdict column says only "no meaningful improvement", and the 10 K margin is not justified.
- **Normalized-conformal hardest decile.** For Tc, the across-split range is roughly 59–100% (Fig. 2a), but the text reports only the 89.6% mean.
- **Supplementary information and data deposit.** The SI is not assembled (`\todo` under "Supplementary information"), and the data/code DOI and upstream licences are still TODO. Several claims (family analyses, bias experiments, C5 sensitivity) currently point to nothing a referee can inspect.

### D2: domain_accuracy — **warn**
The physics is mostly handled with care. Examples: the per-cell moment is correctly identified as an extensive quantity (RQ1, "Magnetic moment"); Néel and ferroelectric contamination of text-mined "Curie" columns is recognised; Co's Tc is used as the upper physical bound; and the limitations admit that C1 removes Ti³⁺ ferromagnets such as YTiO₃. Nothing triggers a block. Two points trigger warn:
- **Nomenclature.** Tables 1–3 and 6 and Fig. 1c,d label the DFT total moment per cell "Ms". In magnetism, Ms denotes saturation magnetization, a volume- or mass-normalised quantity, and the paper itself treats that as a separate secondary target (Table 1, rows 4–5). This invites exactly the conflation the authors warn against.
- **Literature positioning.** The positioning against prior work on UQ and OOD in materials ML is thin, and as a result the contribution reads as more novel than it is. The Introduction cites Meredig 2018, Matbench, Tran 2020, Kapoor 2023 and Li 2023, and states that the properties "are, however, rarely measured together". It omits the closest antecedents an npj Computational Materials reader will know: benchmark studies of UQ for materials property prediction, OOD/leave-cluster-out benchmark studies (including one in this journal), calibration-after-bootstrap work for materials regressors, conformal prediction applied to materials properties, and the classic "accuracy on formation energy ≠ accuracy on stability" critique. The cross-provenance result is also interpreted as "agreement with the labelling convention of each source" (RQ3, second paragraph), which is not established (see D1 and W3).

### D3: argumentative_coherence — **warn**
The thesis is clear and repeated consistently (Introduction last paragraph; Discussion first paragraph; Conclusion). Null results get the same weight as positive ones, and the four pairwise dissociations in the Discussion are actually demonstrated rather than asserted. Nothing triggers a block: the central claim follows from the evidence. Several abstract and Discussion sentences, however, state findings more strongly or differently than the results show:
- **Abstract on conformal coverage.** "Conformal intervals reached 90% marginal coverage only with difficulty-normalized scores" is contradicted by Table 3. For the moment, all three methods average 90.0–90.1% and are within ±2 points in 10/10 splits. For Tc, split conformal averages 89.3%; its problem is variance across splits and hardest-decile coverage, not marginal coverage.
- **Abstract on cell size.** "The small per-cell gain was fully explained by unit-cell size" goes beyond the reported numbers. Site count recovers +0.055 of the +0.079 μB/cell gain, and the remaining +0.024 [−0.003, +0.050] is merely "not stable" (RQ1). The per-atom gain that survives (+2.9 to +6.0%) is not mentioned in the abstract.
- **Discussion on chance.** "An ordering model with macro-F1 0.73 was at chance across label provenance" holds for one direction only. The reverse direction has balanced accuracy 0.399, above the 0.333 reference (Table 6), and the 0.73 model is not the model evaluated in the transfer test.
- **Discussion on calibration.** "Intervals that were calibrated on blind external compositions lost coverage" is incorrect: the intervals were calibrated internally and *evaluated* on blind external compositions.
- **Conclusion.** "In-distribution accuracy is the least informative of the four properties" is a normative ranking that no analysis tests.
- **Novelty of the message.** The take-home message, as phrased, risks reading as a restatement of known lessons (Phase 1 warn trigger). The magnetism-specific findings (physics-descriptor null with a cell-size control; minority-class set coverage; audited external benchmark) are the sharper contribution, and the framing under-sells them.

### D4: cross_disciplinary_relevance — **pass**
- **Accessibility.** Key terms are defined in place: "stable" (end of the dataset subsection), chemical system, blind/unseen (Fig. 3 caption), composition distance (Methods), Mondrian sets, and the three conformal variants.
- **Practical value.** The six practices under "Practical recommendations" are concrete, actionable and tied to evidence in the paper.
- **Generality.** Claims about other property-prediction tasks are hedged ("and likely for other property-prediction tasks").
- **Minor gaps** (not warn level). ECE is used before it is defined in words. Total magnetization and 0 K DFT moments may be unfamiliar to ML readers, and Methods covers them only briefly.

### D5: writing_and_structure — **warn**
- **Prose and figures.** The prose is concise and plain, the structure follows npj conventions (Results–Discussion–Methods), and the figures are clean and legible with intervals throughout.
- **Incomplete submission.** There are 11 `\todo` items: affiliations, funding, the competing-interests confirmation, the data/code DOI, licences, CRediT, the AI-use disclosure, and the SI itself.
- **Internal pipeline labels.** "rule O1", "C1–C5", "rule set v1.4", "Analysis dataset v1.4 (frozen)" and "frozen split" (Tables 3–4) leak from the pipeline into the paper.
- **Cluster definition.** The Table 5 footnote defines papers as "first-listed DOIs", but Methods says the primary clusters are "records connected by any shared DOI", and Table S2 treats these as different clusterings.
- **Fig. 4 caption.** It says the figure covers "the 465 blind external records", but the figure also plots all primary records and an exact-match (distance 0) bin.
- **Fig. 3 caption.** It calls the subsets "nested", but the "seen" subsets are not nested within the blind ones.
- **Abstract length.** The abstract is about 240 words, likely above the venue's abstract limit.
- **"Errors found and corrected" (Methods).** This section is valuable, but it refers to unpublished "earlier analyses" that readers cannot see.

None of these makes the manuscript unfit for review, so the score is warn, not block.

---

## Failure Condition Checks

### F1 (severity 90): any mandatory dimension scores 'block'
- fired: **false**
- reason: D1, D2 and D3 are all warn; none is block.

### F2 (severity 70): two or more mandatory dimensions score 'warn' or worse
- fired: **true**
- reason: all three mandatory dimensions (D1 methodology_rigor, D2 domain_accuracy, D3 argumentative_coherence) score warn. Within this single EIC report the condition is met. The cross-reviewer "majority" quantifier is resolved at panel synthesis, not by me.

### F3 (severity 60): any high-priority dimension scores 'block'
- fired: **false**
- reason: D4, the only high-priority dimension, scores pass.

### F0 (severity 10): every mandatory dimension scores 'pass'
- fired: **false**
- reason: no mandatory dimension scores pass.

**Highest-severity condition fired: F2 → editorial_decision = major_revision.**

---

## Review Body

# Peer Review Report

## Manuscript Information
- **Title**: Accuracy is not reliability: physics descriptors, calibration and chemical generalization in machine learning of magnetic materials
- **Manuscript ID**: n/a (simulated review)
- **Review Date**: 2026-11-10
- **Review Round**: Round 1

## Reviewer Information
- **Reviewer Role**: EIC (Associate Editor, npj Computational Materials; ML-for-materials submissions)
- **Review Focus**: I assess (1) novelty relative to existing benchmark, UQ and OOD work in materials ML, (2) whether "accuracy, physics gains, calibration and generalization are distinct" is a genuine contribution, (3) fit for the readership, and (4) clarity of story and presentation. I leave statistical detail to Reviewer 1.

## Overall Assessment
- **Recommendation**: **Major Revision**
- **Confidence**: 4

### Summary Assessment
The authors assemble a multi-source magnetic-materials dataset (ordering 79,125, Tc 29,740 and DFT per-cell moment 87,513 records) and ask three questions:
- **RQ1.** Do DFT physics descriptors add to composition? Mostly no. A per-cell moment gain is largely a cell-size effect, and a modest per-atom gain remains.
- **RQ2.** Are uncertainties calibrated? Marginally yes; for hard cases, minority classes and shifted sources, not without normalized or class-conditional methods.
- **RQ3.** Do models generalize? They weaken with chemical distance and on an audited external Tc benchmark (blind MAE 103 K; R² −0.17 [−0.93, 0.66] in unseen chemical systems).

The empirical work is unusually careful. Matched tier comparisons, repeated grouped splits, cluster bootstraps, a pre-registered audit of the external benchmark and candid reporting of the authors' own corrected errors are all strengths this journal wants to encourage.

My concerns are editorial and interpretive. First, the headline thesis is close to established lessons in materials ML (Meredig 2018; Bartel et al. 2020; UQ and OOD benchmark studies), and the paper does not engage the closest antecedents. The magnetism-specific findings are the stronger contribution and should lead. Second, several sentences in the abstract and Discussion state results more strongly or differently than the tables do. Third, the label-provenance test is confounded by class-space shift and is over-interpreted. Fourth, the submission is incomplete: the SI is missing, data deposit and licences are pending, and there are 11 TODOs.

All of these are fixable without new science except W3 and, optionally, W4. The contract's failure-condition precedence (F2) gives Major Revision, which is also my substantive judgement.

## Strengths

### S1: Matched, pre-specified tier comparison with a simple physical control
RQ1 compares tiers on identical materials, splits and grids over ten pre-specified splits (Table 2; Methods, "Statistical comparison"). The single-scalar site-count control that recovers the per-cell moment gain in all ten splits is the kind of simple, falsifying control that "physics-informed" claims in this field rarely receive. The point that "Attribution is not benefit" (40% and 36% SHAP share for descriptors that add no accuracy) is a useful, quotable caution.

### S2: An audited external benchmark that changes the conclusion
The audit of the 2,500-record external Tc table (Table S1; RQ3, "External benchmark") shows that 80% of records were already in the training repository by composition and 48% carry identical values. An apparent R² of 0.90 is therefore label recall. Defining novelty by composition rather than by formula string, clustering by source paper, and fixing the "no skill" wording rule in advance are exemplary. Recommendation (iii) will save other groups from the same trap.

### S3: Subgroup-level calibration evidence
Table 4 and Fig. 2c show cleanly that marginal 90% ordering sets cover AFM and FiM only 57.7% and 52.7% of the time while overall coverage looks nominal, and that Mondrian sets fix this at a cost of +0.23 classes in set size. Table 3's hardest-decile column makes the same point for regression. This is directly useful to practitioners.

### S4: Transparency about errors and dependence structure
The "Errors found and corrected" section, the cluster-level bootstraps, the honest framing of the Tc Tier 3 comparison as "not equivalence", and the XGBoost thread-count finding (Recommendation vi) set a high bar for reporting.

## Weaknesses

### W1: Novelty is positioned against too narrow a literature; the general thesis is under-differentiated from known lessons
**Problem**: The Introduction (paragraph 2) cites 5 methodological antecedents and claims the properties "are, however, rarely measured together". The Discussion's central sentence ("None of these properties can be inferred from another, so each has to be measured directly") restates a widely held position: OOD-extrapolation failure (Meredig 2018), accuracy that does not translate to the downstream task (Bartel et al., npj Comput. Mater. 2020, on formation energy vs stability), UQ benchmark studies for materials property prediction (e.g., Varivoda et al. 2023), OOD benchmark studies (e.g., Omee et al., npj Comput. Mater. 2024), recalibration of materials regressors (e.g., Palmer et al., npj Comput. Mater. 2022) and forward/leave-cluster-out CV (e.g., Xiong et al. 2020). None of these is cited. (The authors should verify the exact bibliographic details.)
**Why it matters**: Without this positioning, readers will judge the paper as a restatement. Its real novelty is (a) the matched, controlled negative result for DFT descriptors in magnetism, (b) minority-magnetic-class set coverage, and (c) the audited external benchmark showing near-total overlap between public Tc compilations. That novelty is diluted.
**Suggestion**: Add a focused related-work paragraph engaging these works and stating precisely what is new: same data, same models, all four properties, dependence-aware intervals, audited external test, magnetism-specific findings. Lead the abstract and Conclusion with the magnetism findings. Present the general thesis as a corollary, not the discovery. Consider a title that signals the domain-specific contribution.
**Severity**: Major

### W2: Abstract and Discussion sentences that do not match the tables
**Problem**:
(a) Abstract: "Conformal intervals reached 90% marginal coverage only with difficulty-normalized scores." Table 3 shows all three methods at a 90.0–90.1% mean for the moment (10/10 splits within ±2 points) and split conformal at 89.3% for Tc.
(b) Abstract: the per-cell gain was "fully explained by unit-cell size". The residual +0.024 [−0.003, +0.050] is unresolved, not zero, and the surviving per-atom gain is omitted.
(c) Discussion: "An ordering model with macro-F1 0.73 was at chance across label provenance." The reverse direction has balanced accuracy 0.399 > 0.333, and the transfer models are not the 0.73 model.
(d) Discussion: intervals "calibrated on blind external compositions". They were calibrated internally.
(e) RQ1 and the abstract: "no practical gain" for Tc. The GB point estimate is a 14.3 K degradation (Fig. 1b), above the 10 K margin.
(f) Conclusion: in-distribution accuracy is "the least informative of the four properties". This is not tested.
(g) RQ2 section heading: "subgroup … coverage is not [attainable]". Normalized and class-conditional methods do attain it (Table 3, 89.6%/88.8%; Table 4, 88.3–91.6%).
**Why it matters**: A paper whose message is "do not over-claim" must not over-claim in its own abstract. Referees will find these mismatches quickly.
**Suggestion**: Rewrite (a) as "only normalized conformal kept Tc coverage near nominal across splits and in the hardest decile". Change (b) to "largely explained", and add the per-atom result in one clause. For (c), report both directions and drop "at chance" in favour of "near or below a balanced-accuracy reference of 0.333 in one direction". Correct (d). Report the sign of the point estimate in (e). Soften (f) to a recommendation. Retitle (g) as "…subgroup and shifted coverage need normalized or class-conditional methods, and fail under source shift".
**Severity**: Major

### W3: The label-provenance result is confounded and over-interpreted
**Problem**: RQ3 concludes that the pooled ordering score reflects "agreement with the labelling convention of each source". The provenance slices differ in label space and class priors, not only in convention. The experimental slice has about 5 NM rows (FM 10,760 / AFM 5,197 / FiM 1,679), while the MP slice is 35% NM with only 996 AFM. Scoring is restricted to FM/AFM/FiM, and 4,753 MP test rows were dropped in the reverse direction. An MP-trained four-class model that predicts NM on experimental FM/AFM/FiM materials is guaranteed to be wrong for reasons unrelated to convention. The populations also differ chemically. Finally, the within-provenance comparison (0.637 four-class vs 0.784 three-class) is not like for like.
**Why it matters**: This is one of the four headline dissociations (Discussion, "Accuracy versus generalization"), and as designed it cannot separate labelling convention from prior shift and population shift.
**Suggestion**: Re-run the transfer restricted to the shared label space: train both models on FM/AFM/FiM only, and add prior correction to the target-domain priors. Report a materials-matched comparison, i.e. formulas present in both provenances with both labels, and the raw agreement rate of MP and experimental labels on those formulas. That agreement rate is the direct test of "convention". If the effect survives, the claim is strong and novel. If not, reframe it as label-space and prior shift.
**Severity**: Major

### W4: RQ1's generality is limited by the model class and the matched subpopulation
**Problem**: RQ1 tests only tabular composition and DFT scalar descriptors with tree and linear models, on matched subsets of 4,602–10,852 materials restricted to those with a full MP/JARVIS record (acknowledged in Limitations and "Why physics descriptors did not help"). The readership's default "physics-informed" models are structure-based GNNs and pretrained universal-potential embeddings.
**Why it matters**: The title and abstract present "physics descriptors add little" without that qualifier. Readers will discount the result as an artefact of how physics was injected.
**Suggestion**: Either (i) add one structure-based baseline (e.g., a crystal-graph model or frozen embeddings from a pretrained universal model) on the Tier 3 matched set with the same splits, or (ii) scope the claim explicitly in the title, abstract and Conclusion to "scalar DFT descriptors with tabular models". Option (ii) is acceptable; option (i) would make RQ1 a much stronger contribution.
**Severity**: Major (scoping alone resolves it to Minor)

### W5: Submission completeness and presentation
**Problem**: The submission has gaps throughout:
- 11 `\todo` items remain, including affiliations, funding, data/code DOI, licence verification, CRediT and the AI-use disclosure.
- The SI is not assembled, although the text relies on it for Tables S1–S3, the family analyses, the bias experiments and the C5 sensitivity analysis.
- Pipeline labels (rule O1, C1–C5, v1.4, "frozen split") appear in the paper.
- "Ms" is used for a DFT per-cell moment.
- The Table 5 footnote cluster definition disagrees with Methods.
- The Fig. 4 and Fig. 3 captions are inaccurate (see D5).
- Table 2 has no verdict column for Tier 1→2.
- The abstract is about 240 words.
**Why it matters**: The paper cannot go to external referees without the SI, the data deposit and the disclosures. The nomenclature issue undermines domain credibility.
**Suggestion**: Assemble the SI and deposit data and code with a DOI, or state the licence constraints explicitly. Rename "Ms" throughout tables and figures to "m_cell (μB/cell)" or "total moment per cell". Replace internal codes with descriptive names, or define them in a Methods table. Align the Table 5 footnote with Methods and fix the figure captions. Shorten the abstract to the venue limit. Move the "Errors found and corrected" list into a short "Pitfalls" box framed as lessons with prevalence numbers, so it no longer depends on unpublished "earlier analyses".
**Severity**: Major (completeness) / Minor (presentation)

## Detailed Comments

### Journal Fit
- **Fit.** This sits squarely within npj Computational Materials' scope: data-driven materials science, ML methodology, reproducibility. The audience for the recommendations is broad.
- **Article type.** The paper fits best as a methodology and benchmarking Article with magnetism as the case study.
- **Required for fit.** The positioning in W1 and the scoping in W4.

### Originality
- **Adequate, not exceptional.** The general thesis is known in pieces. The integrated, dependence-aware, audited evaluation and the magnetism-specific nulls and controls are new, and they deserve the spotlight (W1).

### Significance
- **Practical impact.** Moderate to high for the magnetism-ML community. The finding that public Tc compilations overlap so heavily (80% by composition) and that apparent external R² ≈ 0.9 is label recall is likely to change how future Tc papers are evaluated.

### Structural Coherence
- **Structure works.** The chain RQ1 → RQ2 → RQ3 → Discussion is clean, and every RQ has a table and a figure.
- **Fixes needed.** The mismatches in W2 are the main coherence issue.

### Title & Abstract
- **Title.** Memorable, but it promises a general result where the evidence comes from one domain.
- **Abstract.** It needs the W2 corrections and must be shortened.

### Conclusion
- **Mostly faithful to the results.** Remove the untested "least informative" ranking. Add one sentence on what *would* make a magnetism model trustworthy for discovery, e.g., distance-aware intervals validated on the external benchmark.

## Questions for Authors
1. On formulas that carry both an MP-computed and an experimental ordering label, what is the raw agreement rate, and how does cross-provenance transfer change when both models are trained on the shared FM/AFM/FiM label space with prior correction?
2. For Tc, the gradient-boosting Tier 1→3 point estimate is a 14 K degradation. Is it the matched-population restriction (lowest-energy polymorph vs measured sample) that drives the degradation? Does training Tier 1 on the full population, with evaluation on the matched test set, change the RQ1 conclusion?
3. Can you show that normalized-conformal intervals, re-calibrated with a distance-aware or Mondrian-by-distance scheme, restore coverage in the farthest quartile of the external benchmark? This would turn a diagnostic finding into a constructive one.
4. How was the 10 K practical-relevance margin for Tc chosen, and was it fixed before the Tier comparisons were run?

## Minor Issues
- **ECE.** Define it at first use (Results, ordering calibration), not only in Methods.
- **Fig. 1b.** The arrow annotation "−825 (unstable fit)" should state "clipping removes this" or show the clipped estimate.
- **Fig. 2a.** State in the caption that bars are the across-split range, not CIs. This is already in the figure footnote; move it into the caption.
- **Table 6.** Explain why chance is three-class (no NM in the experimental slice).
- **Table 1 footnote.** "(97 in total)" should read 24 Tier 3 additions, to match the text.
- **Conclusion.** "More than 100,000 labelled magnetic materials" — state whether this counts records or unique formulas.
- **Methods, Descriptors.** "Taking the most stable polymorph": add one sentence on how this is chosen when sources disagree.

## Recommendation to Peer Reviewers
- **Reviewer 1 (statistics).** Please check the paired formula-bootstrap and the "stable" criterion across 3 algorithms × 2 tiers × 4 targets without multiplicity adjustment. Also check the cluster-bootstrap for the 69-record, 26-paper subset.
- **Domain reviewer.** Please assess curation rules C1–C5 and O1, and the per-atom moment denominator.
- **All reviewers.** Please weigh in on W3 (provenance confound).

## Rubric Scores (0–100, quality_rubrics.md)

| Dimension | Score | Descriptor | Notes |
|---|---|---|---|
| Originality (20%) | 63 | Adequate | Known general thesis; novel magnetism-specific controls and audit (W1) |
| Methodological Rigor (25%) | 76 | Strong | Matched, pre-specified, dependence-aware; provenance confound and missing SI (W3, W5) |
| Evidence Sufficiency (25%) | 68 | Adequate | 36 references; key UQ/OOD antecedents missing; strong internal triangulation |
| Argument Coherence (15%) | 68 | Adequate | Clear thesis; several abstract/Discussion mismatches (W2) |
| Writing Quality (15%) | 72 | Adequate | Plain, concise prose; TODOs, internal codes, caption errors |
| Significance & Impact (optional) | 74 | Good | Useful practices; benchmark-overlap finding likely to influence Tc work |
| **Weighted Average** | **69.6** | rubric mapping: Minor | Overridden by contract precedence (F2 → Major Revision); see below |

The rubric average (69.6) would map to Minor Revision. The contract's failure conditions are the only authority for the decision, and F2 fires, so the decision is Major Revision. I agree with it on substance: W3 needs re-analysis, and W5 (missing SI and data deposit) blocks external review as submitted.

---

## Editorial Decision

**Major Revision** (contract F2, severity 70: all three mandatory dimensions D1, D2 and D3 score warn; F1 and F3 not fired).

Required for re-review:
1. Reposition against UQ, OOD and benchmark antecedents, and foreground the magnetism-specific contributions (W1).
2. Correct the abstract, Discussion and section-heading statements listed in W2.
3. Re-analyse or reframe the label-provenance transfer on a shared label space with label-agreement evidence (W3).
4. Either scope RQ1 to tabular scalar descriptors or add a structure-based baseline (W4).
5. Submit the assembled SI, data and code deposit, and completed declarations, and fix the nomenclature and captions (W5).
