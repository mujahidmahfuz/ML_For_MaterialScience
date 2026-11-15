# Methodology Review Report (Peer Reviewer 1) -- Phase 2 (paper-visible)

contract_id: reviewer/reviewer_full/v1 · Phase 1 record: `methodology_phase1.md` (scoring plan applied as committed; no dissent)
Manuscript: "Accuracy is not reliability: physics descriptors, calibration and chemical generalization in machine learning of magnetic materials" (draft of 2026-11-09)
Reviewer identity: statistician specializing in conformal prediction, calibration and grouped/clustered resampling for scientific ML. Blind spot: magnetism physics.
Review date: 2026-11-10 · Round 1

Material reviewed: manuscript.tex, references.bib (citations only), Tables 1-6 and S1-S3 (csv + notes), Figs 1-3 (viewed). To check whether the Methods describe what was done, I also read these result files and scripts: `results/rq1_physics_descriptors/matched_tiers/*`, `ms_cell_size_control/*`, `results/rq3_generalization/external_benchmark/{PLAN.md, subset_metrics_bootstrap.csv, similarity_spearman.csv}`, `label_provenance/*`, `scripts/pipeline/analysis/{phase7_aggregate.py, run_phase8_regression_uq.py, run_phase8_ordering_uq.py, run_phase8_leave_chemsys.py}`, `scripts/pipeline/config/phase7_config.yaml`, `final_checks/check1_curie_inference.py`. I ran no model fits.

---

## Dimension Scores

### D1: methodology_rigor
**Score: warn**

Applying my Phase 1 triggers: no headline claim rests on an unmatched comparison, on test-set reuse, or on calibration data that overlap the test set, so the block trigger does not fire. Several warn-level patterns are present:
- **Matched design (strength).** The Tier 1/2/3 comparison uses identical rows, splits, grids and metrics, with paired bootstrap draws (Methods "Statistical comparison"; `phase7_aggregate.py`). This is sound.
- **The stability rule is under-specified and differs from the code.** The manuscript says "'stable' means that the 95% bootstrap interval of a difference excludes zero" (Results, end of §2.1). The code (`phase7_aggregate.robustness_summary`) also requires that at least 70% of splits point the same way (`min_fraction_splits_positive: 0.70`). The interval is a formula bootstrap over the union of test formulas that holds the 10 fitted models fixed. It therefore leaves out training-set and refit variance, and the 10 splits are resamples of one pool, not independent replicates. Two verdicts depend on this choice. For XGBoost Ms Tier 2→3, the pooled CI [+0.002, +0.078] is called "stable improvement", but the across-split t-interval [−0.003, +0.085] includes 0. For Curie GB Tier 1→3, the pooled CI is [−31.3, +3.8] and the t-interval [−39.4, +4.5].
- **No multiplicity framing.** Table 2 alone has 18 tier contrasts (3 targets × 3 algorithms × 2 tiers), and the result files hold more (Tier 2→3, four metrics each). Two of the "stable" verdicts sit on the boundary: GB ordering Tier 1→2, upper limit −0.001; Ridge Ms per cell Tier 1→3, lower limit +0.002. That is about what one would expect by chance among 18 unadjusted 95% intervals.
- **Circular subgroup evaluation in RQ2.** The "hardest decile" in Table 3 and Fig. 2a,b is a decile of `sigma`, the same difficulty score that normalized conformal uses to scale its intervals (`run_phase8_regression_uq.py`, line 108). Normalized conformal is therefore evaluated on the axis it was built to equalize. Its 89.6% against 56% (split) and 63% (CQR) is partly true by construction.
- **Calibration data used twice for ordering.** The temperature is fitted on the calibration set (`run_phase8_ordering_uq.py`, line 124), and the conformal thresholds for the "prior-corrected + temperature" sets are then computed on the same calibration set. With a single parameter the effect is probably small, but the finite-sample guarantee no longer holds exactly.
- **Exchangeability under grouping is not discussed.** Calibration and test are formula-grouped, but nonconformity quantiles are taken over records. Records within a formula (and within a source paper) are dependent. The Curie inference file reports a design effect of about 20 (effective about 44 independent rows per test set). This is consistent with the 6-point split-to-split SD of split-conformal coverage, which is far larger than the roughly 0.5 points expected from i.i.d. sampling.
- **Pre-specification is overstated** (detail under D3 and W4).
- **Reproducibility (mostly strong).** Seeds are fixed (20267000+i), checksums are provided, the external-benchmark chain was re-run byte for byte, and the errors found are documented. Gaps: the model fits were not re-run for the package; XGBoost results depend on thread count; the repository DOI and licences are still TODO.

### D2: domain_accuracy
**Score: block**

The Phase 1 block trigger fired: "a misstatement of what a method guarantees that underpins a headline claim". The abstract states: "Conformal intervals reached 90% marginal coverage only with difficulty-normalized scores." Two problems follow:
- This contradicts Table 3 for the moment: split, normalized and CQR all have a 10-split mean of 90.0–90.1% and 10/10 splits within ±2 points.
- It misstates the guarantee for Tc. Split conformal promises marginal coverage in expectation over calibration draws, and it delivered that: a 10-split mean of 89.3%. What differs between methods is the variability of coverage conditional on the calibration set, and conditional or subgroup coverage. Neither is guaranteed by any of the three methods.

The RQ2 section heading ("marginal calibration is attainable") is correct; the abstract sentence is not. This is a block-level misstatement on an abstract-level claim, although it is easy to fix (W1).

Further warn-level accuracy issues:
- **Wrong chance reference.** Table 6 and the text compare provenance-transfer balanced accuracy 0.323 with "the three-class chance level of 0.333". But the MP-trained model can predict NM, which is never a scored class in the experimental test set (`ordering_cross_provenance_transfer.csv`: classes_scored = FM/AFM/FiM). In the reverse direction, 4,753 test rows were dropped. The Discussion's "at chance across label provenance" therefore rests on an inappropriate reference point and has no interval.
- **Count of resampling units.** Table 5 gives "69 (26)" papers and the text says "These 69 records come from only 26 papers". The primary pre-specified clustering (shared-DOI components) that produces the intervals has 18 clusters for that subset (81 for the blind subset, against "134" shown). The count shown is the first-DOI count from Amendment 2.
- **Verdict on an invalid fit.** Table 2 gives a verdict of "no meaningful improvement" to the Ridge Curie Tier 1→3 estimate (−825 K [−2938, +8.8]). That model is numerically unstable, so the estimate should be labelled not interpretable.

### D3: argumentative_coherence
**Score: warn**

The thesis (accuracy, physics gain, calibration and generalization are separate properties) follows from the results as a synthesis, and the paper consistently declines to read "CI includes 0" as equivalence for Tc. That care is commendable. Several claims are still stronger than their evidence:
- **"Fully explained."** Abstract: "the small per-cell gain was fully explained by unit-cell size." In fact the site-count scalar recovers +0.055 of the +0.079 μB/cell GB gain (about 70%). The Tier 3 increment beyond site count is +0.024 [−0.003, +0.050], an inconclusive result, not a zero. The paper's own rule for Tc ("not equivalence") is not applied here.
- **"Reproducible gain."** RQ1 calls the Tier 3 Ms per-cell gain "small, reproducible". Table 2 marks XGBoost as "not stable", and the final checks show that the XGBoost verdict flips with thread count.
- **Pre-specification claims.** "Before any error was examined" (Methods, External benchmark) and "Before the analysis we had fixed a wording rule" (Results) conflict with the audit plan's own disclosure. `PLAN.md` says the October subset-level MAE/R²/coverage results, including R² ≈ −0.18 for unseen systems, had already been seen when the plan and the 0.2 wording threshold were written. Amendment 2 was also made after the first bootstrap run (outcome-aware).
- **Curie Tier 3.** The point estimate is a 14 K degradation for GB (and 10 K for XGBoost). The abstract's "no practical gain" is accurate, but the possibility of a practical loss should appear wherever "no practical improvement" is stated.

### D4: cross_disciplinary_relevance
**Score: pass**

UQ terms (split, normalized and CQR conformal; Mondrian sets; prior correction; temperature scaling; cluster bootstrap) are named, cited to primary sources (Vovk, Lei, Romano, Papadopoulos, Saerens, Guo) and briefly defined in Methods. The six practical recommendations follow from the evidence. Generality is hedged ("likely for other property-prediction tasks"). The recommendations would gain from the fixes in W1–W3, but the interdisciplinary claims are not overreaching.

### D5: writing_and_structure
**Score: warn**

Methods are findable and compact. However:
- **Decision rules not spelled out in the manuscript.** The 70% sign criterion, the TOST/margin verdicts used for Curie, and which interval (pooled bootstrap or t) drives each verdict live only in the code and configuration files.
- **Mixed verdict rules in one column.** Table 2's verdict column mixes two rules: a 10 K margin for Curie and the stability rule for the other targets.
- **Missing intervals.** Fig. 2c and Table 4's per-class coverages have no intervals, and the provenance rows of Table 6 have none either.
- **Unclear resampling units.** Table 5's "papers" column does not match the resampling units.
- **Unresolved placeholders.** Open TODOs remain in the declarations, data availability and Supplementary Information.

---

## Failure Condition Checks

### F1 (severity 90): any mandatory dimension scores 'block'
fired: true. D2 (domain_accuracy, mandatory) = block, because the abstract misstates the conformal guarantee and contradicts Table 3 for Ms. Action: editorial_decision = reject_or_major_revision.

### F2 (severity 70): two or more mandatory dimensions score 'warn' or worse
fired: true. D1 = warn, D2 = block, D3 = warn (three mandatory dimensions at warn or worse). Action: major_revision. Note that the quantifier is "majority" across the panel; this is my reviewer-level evaluation.

### F3 (severity 60): any high-priority dimension scores 'block'
fired: false. D4 (high priority) = pass.

### F0 (severity 10): every mandatory dimension scores 'pass'
fired: false.

Precedence: F1 (90) is the highest-severity condition that fired, so the decision must be Reject or Major Revision. F2 (70) fired as well and points to Major Revision. The problems are fixable by reanalysis of existing outputs and by rewording, with no new data needed, so I choose **Major Revision** within F1's allowed set.

---

## Review Body

### Reviewer Information
- **Role**: Peer Reviewer 1 (Methodology)
- **Identity**: statistician; conformal prediction, calibration, grouped/clustered resampling
- **Review focus**: whether the matched-tier design isolates the effect of the added descriptors; how split-level and bootstrap uncertainty are combined into "stable" verdicts; whether the conformal and calibration coverage claims are stated correctly; how valid the paper-cluster bootstrap and the pre-specified wording rule are; and reproducibility.

### Overall Recommendation
**Major Revision** · Confidence: 4 (strong on the statistics and UQ; I defer to the domain reviewer on magnetism, e.g. the C1–C5 target rules).

### Summary Assessment
The manuscript measures, on one curated multi-source dataset, whether DFT descriptors improve composition-only models of magnetic ordering, Tc and the DFT moment (RQ1); whether conformal intervals and ordering probabilities are calibrated overall and by subgroup (RQ2); and whether skill transfers to unseen chemical systems, other label sources and an audited external Tc table (RQ3).

The design is unusually careful for this field:
- matched rows across tiers, paired bootstraps and ten pre-seeded grouped splits;
- composition-identity novelty, and a paper-cluster bootstrap for the external benchmark;
- a candid list of the errors the authors found in their own earlier analyses.

The qualitative conclusions are mostly supported. The statistical machinery around them, however, has several gaps:
- The stability rule as described is not the rule implemented, and its intervals leave out refit variance across the overlapping splits.
- There is no multiplicity framing across about 18 contrasts, several of which sit on the boundary.
- The "hardest decile" comparison favours normalized conformal by construction.
- The abstract misstates what split conformal guarantees.
- Pre-specification is claimed more strongly than the authors' own audit plan supports.
- Some reference points are inappropriate (three-class chance) and some resampling-unit counts are misreported (26 against 18 clusters).

None of these requires new data. All need reanalysis of saved predictions or rewording before the claims can be relied on, hence Major Revision.

### Strengths

**S1. A matched, paired tier design.** "For each target, a matched population... identical rows, splits, hyperparameter grids and metrics" (§2.1), with "the same formula-group bootstrap draws for both tiers (paired)" (Methods). This removes the population confound that affects most "physics-informed" comparisons. The site-count control for Ms per cell (Table 2 and the cell-size control) is exactly the kind of simple negative control the field lacks.

**S2. Inference on the dependence unit, and honest null reporting.** Formula-grouped splits and bootstraps internally, and source-paper clusters externally, with first-DOI and chemical-system sensitivity analyses (Table S2). For Tc the text says "an improvement larger than 3.8 K is excluded, while a degradation of up to about 30 K is not. We therefore report 'no practical improvement', not equivalence". This is correct handling of a non-significant result, backed by TOST columns in `curie_inference_table.csv`.

**S3. Subgroup-aware UQ.** Coverage is reported per class, per difficulty decile, per family and under source shift. The marginal-against-Mondrian contrast for ordering (AFM 57.7% / FiM 52.7% against 89.9–91.1%, Table 4) shows clearly that marginal coverage can hide failures on minority classes.

**S4. Composition-identity audit of the external benchmark.** Composition-level novelty, the copied-value check (1,200 records, R² 0.90 = label recall), exclusion categories fixed before errors were inspected, and a written wording rule (Table S1, `PLAN.md`) together set a high bar for external validation in materials ML.

**S5. Reproducibility package.** Fixed seeds, SHA-256 checksums, a byte-for-byte re-run of the external chain, the thread-count dependence of XGBoost stated openly, and a versioned claims register of withdrawn results (per-atom 14% → 2.9%).

### Weaknesses

#### W1: The abstract misstates the conformal guarantee and contradicts Table 3
**Problem.** The abstract says "Conformal intervals reached 90% marginal coverage only with difficulty-normalized scores." Table 3 shows all three methods at 90.0–90.1% mean coverage for Ms, with 10/10 splits within ±2 points. For Tc, split conformal and CQR average 89.3% and 89.4%, consistent with marginal validity. What fails is coverage stability across calibration draws (SD 6.0 and 5.8) and coverage on the hardest decile. The Results text ("only normalized conformal stayed close to nominal across splits") is closer to correct, but still blurs the difference between marginal and training-conditional coverage.

**Why it matters.** This is the paper's headline RQ2 statement. As written, it tells readers that split conformal is invalid, which is false and contradicts the paper's own Ms results.

**Suggestion.** Rewrite along these lines: "All three conformal methods achieved ~90% marginal coverage on average; for Tc, coverage of split conformal and CQR varied by ±6 points between calibration draws, and only normalized conformal kept hard cases near nominal." Also do the following:
- State that the guarantee is marginal and holds in expectation over calibration draws, under exchangeability.
- Report the theoretical training-conditional spread, e.g. a Beta(n+1−l, l) bound with n = the effective number of calibration units, next to the observed SD.

**Severity:** Critical (easily fixed).

#### W2: The stability rule as described is not the rule used, and its interval leaves out refit variance
**Problem.** The manuscript defines "stable" as "the 95% bootstrap interval of a difference excludes zero". The implemented rule also requires that at least 70% of splits point the same way (`phase7_config.yaml`: `min_fraction_splits_positive: 0.70`). The interval resamples test formulas with the 10 fitted models held fixed (`phase7_aggregate.paired_rows`). It therefore leaves out training-set and refit variance. The 10 splits are overlapping resamples of one pool, so a naive across-split t-interval would be anti-conservative too. Examples where the choice matters:
- XGBoost Ms Tier 2→3: pooled CI [+0.002, +0.078] ("stable"), t-interval [−0.003, +0.085].
- Ms Tier 1→3 XGBoost: the verdict flips with thread count.

**Why it matters.** RQ1's only positive finding (the Ms per-cell gain) and the Tier 2 "degradation" claims depend on verdicts near the boundary.

**Suggestion.**
- State the full two-part rule in Methods.
- Add a variance estimate that includes refits. Two options are the Nadeau–Bengio corrected resampled t-test (variance inflated by n_test/n_train for overlapping splits) or a nested bootstrap over formulas with refits on a subset of contrasts.
- Report both intervals in Table 2, and call a result stable only when both exclude 0.
- For XGBoost, average over at least 3 thread/seed realisations per split before aggregating.

**Severity:** Major.

#### W3: No multiplicity framing across the tier contrasts
**Problem.** Table 2 reports 18 contrasts with unadjusted 95% intervals, and the supporting files hold Tier 2→3 and four metrics each. Two of the five "stable" calls sit on the boundary: GB ordering Tier 1→2, upper −0.001; Ridge Ms per cell, lower +0.002. The Tier 1→3 per-atom and site-count analyses were added after the per-cell result was seen (Phase 8 follow-ups), but they are presented alongside the pre-specified contrasts.

**Why it matters.** Under the global null, about one of 18 intervals would exclude 0 by chance. Readers cannot tell confirmatory results from exploratory ones.

**Suggestion.**
- Declare a primary family: Tier 1→3, MAE or macro-F1, three targets.
- Report simultaneous intervals for that family, using max-|t| across the paired bootstrap draws or Holm on bootstrap p-values.
- Mark the site-count control, the per-atom target and the Tier 1→2 full-population results as exploratory or follow-up.
- Describe boundary results as "borderline".

**Severity:** Major.

#### W4: Pre-specification of the external benchmark is overstated, and the wording rule depends on the clustering
**Problem.**
- The Methods say the audit plan "was written before any error was examined", and the Results say "Before the analysis we had fixed a wording rule". `PLAN.md` itself records that the October subset-level results (MAE/R²/coverage per subset, including unseen-system R² ≈ −0.18) had been seen when the plan, and its "upper R² ≤ 0.2" threshold, were written. Amendment 2 was made after the first bootstrap run.
- For the blind + unseen-system subset, the pre-specified clustering yields only 18 clusters, not the 26 shown in Table 5 and the text. Percentile bootstraps with 18 clusters and a heavy-tailed statistic (R²) are unreliable.
- Under chemical-system clustering, the upper R² limit is 0.23, close to the 0.2 threshold (`subset_metrics_bootstrap.csv`). The verdict "much weaker, wide uncertainty" rather than "no skill" therefore depends on which clustering is used.
- R² is computed against each subset's own mean. Part of the R² "drop" between seen and unseen systems (−0.95) can come from different target variance within each subset rather than from larger errors. The MAE gap (+81 K [−27, +165]) is not resolved under paper clustering.

**Why it matters.** RQ3's headline sentence depends on this rule and on these intervals.

**Suggestion.**
- Use the plan's own wording: "written after subset-level results of an earlier, flawed analysis were known, but before any record-level error was linked to an audit flag or distance".
- Report the number of resampling clusters (18 / 81) in Table 5.
- Use a bootstrap better suited to few clusters, such as BCa or studentized cluster bootstrap, or a cluster permutation test for the seen/unseen contrast.
- Report the rule's verdict under all three clusterings.
- Add a skill score against a fixed reference, e.g. 1 − MSE/MSE(training-mean predictor), so subsets are compared on the same baseline.

**Severity:** Major.

#### W5: Circular difficulty decile and calibration data used twice in RQ2
**Problem.**
- The hardest decile is defined by `sigma` (`run_phase8_regression_uq.py`, line 108), the difficulty model that normalized conformal uses as its scale. Its near-nominal coverage there (89.6% against 56% for split) is largely a property of how the subgroup was defined.
- For ordering, the temperature T = 1.65 and the conformal thresholds are both fitted on the same calibration set (`run_phase8_ordering_uq.py`, lines 101–127).
- Calibration quantiles are computed over records, while exchangeability holds at the formula or paper level.

**Why it matters.** The recommendation to "report normalized or class-conditional conformal coverage by subgroup" is the paper's main practical UQ advice. Its supporting comparison favours one method by construction.

**Suggestion.**
- Define "hard" subgroups independently of any method's scale. Options: composition distance (as already done externally), family, high predicted value, label source, or a decile from a difficulty model fitted on a disjoint fold.
- Report all three methods on those subgroups. The family and high-value groups already exist in `uq_coverage_by_group.csv` and could be moved into Table 3.
- Split the calibration set into a temperature-fitting part and a conformal part, or state that the guarantee is approximate.
- Consider group-level conformal (one score per formula, or the hierarchical conformal procedure of Dunn, Wasserman & Ramdas), or at least discuss the design effect (~20 for Tc) as the reason for the large between-split variance.

**Severity:** Major.

#### W6: Overstatements and inappropriate reference points in the generalization and Ms claims
**Problem.**
- "Fully explained by unit-cell size" (abstract): site count recovers about 70% of the GB gain, and the remaining Tier 3 increment is +0.024 [−0.003, +0.050], which is inconclusive.
- The Ms per-cell gain is described as "small, reproducible" although XGBoost is "not stable" in Table 2.
- The provenance balanced accuracy of 0.323 is compared with a three-class chance level although the model can predict NM, a class that is never scored. The reverse direction drops 4,753 rows.
- Leave-chemical-system-out pairs the formula-grouped and chemsys-grouped schemes by split_id, but the two schemes have different test materials (`run_phase8_leave_chemsys.py`). The −0.028 therefore mixes novelty with differences in test composition, such as class mix.

**Suggestion.**
- Write "largely (≈70%) explained; the residual is not distinguishable from zero".
- Qualify "reproducible" by algorithm.
- For provenance, compare against a label-shuffled or prior-matched reference with a cluster-bootstrap CI, restricting predictions to the scored classes or reporting the NM leakage rate.
- For leave-chemical-system-out, evaluate both training regimes on the same chemical-system-held-out test rows: train once with those systems' other formulas available and once without. Report class-mix-standardized macro-F1.

**Severity:** Major.

### Detailed Comments

- **Research questions.** Clear and answerable. RQ2's "reliable and calibrated" should be split into marginal validity, conditional or subgroup validity, and efficiency (width or set size).
- **Design.** The matched-tier design is good, but the matched population (6,061 / 4,602 / 10,852) is not a random subset (materials with full DFT records). The Discussion acknowledges this; quantify it, e.g. Tier 1 performance on matched against unmatched rows.
- **Sampling and power.** `curie_inference_table.csv` contains minimum detectable effects (GB Tier 1→3: about 25 K at 80% power). Report these in the text: with an MDE of 25 K, "no practical improvement below 10 K" is not something this design can establish, which the authors partly concede.
- **Data handling.** Exclusions follow written rules, and the formula-spelling leakage (0.6% / 1.3%) is disclosed. Good.
- **Results presentation.**
  - Table 2's Ridge Curie Tier 3 row should read "not interpretable (unstable fit)". If clipping fixes it, report the clipped result.
  - Fig. 2a shows ranges across splits (normalized hardest decile about 59–100%), which is informative; mention in the text that the range, not only the mean, is wide.
- **Reproducibility.** Strong, apart from the open repository DOI and licence, the model fits not being re-run for the package, and XGBoost thread dependence (see W2).
- **Methodological fallacies checklist.**
  - Multiple comparisons without correction (W3).
  - Absence of evidence read as evidence of absence ("fully explained", W6).
  - A subgroup defined by the method under test (W5).
  - Partly post hoc pre-specification (W4).
  - No overfitting or leakage problems beyond those disclosed.

### Questions to Authors
1. When both the 10-split pooled bootstrap and a refit-aware interval (e.g. Nadeau–Bengio) are used, how many of the five "stable" verdicts in Table 2 survive? Does the XGBoost Ms per-cell verdict survive averaging over thread/seed realisations?
2. What are the coverages of split, normalized and CQR conformal on a hard subgroup defined independently of `sigma`, e.g. the top decile of composition distance or of the predicted Tc?
3. Was the 0.2 R² threshold in the wording rule chosen with knowledge of the October unseen-system interval? What does the rule conclude under chemical-system clustering (upper limit 0.23) and with a few-cluster-robust bootstrap on 18 clusters?
4. Why does prior correction raise ECE from 0.059 to 0.093? Is this top-label ECE? Please report classwise ECE, which is more sensitive to AFM/FiM.

### Minor Issues
- Abstract: "error of 103 K [79, 154]": give the metric (MAE) and the interval type.
- Table 5 note: separate the "papers" count from the resampling clusters, and give coverage intervals.
- Table 4 / Fig. 2c: add bootstrap intervals for per-class coverage.
- Methods: state ECE as top-label or classwise, and the binning scheme (15 equal-width bins is given; good).
- Conclusion: "more than 100,000 labelled materials". Give the exact union count, because targets overlap.
- Placeholders in the declarations, author contributions, AI-use statement and Supplementary Information need to be resolved before submission.

### Rubric Scores (0–100, quality_rubrics.md)

| Dimension | Score | Descriptor | Notes |
|---|---|---|---|
| Originality (20%) | 72 | Adequate | Joint evaluation of physics gain, UQ and generalization on matched data is useful, though no single method is new |
| Methodological Rigor (25%) | 64 | Adequate (low) | Strong design; W2, W3 and W5 are real gaps |
| Evidence Sufficiency (25%) | 70 | Adequate | Claims mostly backed by saved outputs; some intervals rest on few clusters |
| Argument Coherence (15%) | 68 | Adequate | Thesis coherent; several overstatements (W1, W4, W6) |
| Writing Quality (15%) | 74 | Adequate | Clear and compact; decision rules are hidden in code |
| **Weighted average** | **69.1** | Minor Revision by rubric | Overridden by contract F1/F2 → Major Revision |

---

## Editorial Decision

**Major Revision.** Contract F1 fired (D2 = block) and so did F2 (D1, D2 and D3 at warn or worse). F1 has the highest severity and limits the decision to Reject or Major Revision. The design is sound and every issue can be fixed with existing saved outputs or by rewording, so Major Revision is the appropriate choice. The rubric average (69) would suggest Minor Revision, but the contract's failure conditions are the governing authority.
