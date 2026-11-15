# Peer Review Report — Peer Reviewer 3 (Perspective)

contract_id: reviewer/reviewer_full/v1 · mode: reviewer_full · phase: 2 (paper-visible) · generated_at: 2026-11-09T17:12:01Z
Phase 1 commitment: `perspective_phase1.md` (same folder). I scored against it as written, so there is no Scoring Plan Dissent section.

## Dimension Scores

### D1: methodology_rigor — **warn**
Evidence against the Phase 1 triggers:
- Block triggers did not fire. Splits are grouped by formula, and chemical-system-out splits are added (Results, "All splits group records by reduced formula"; Table 6). Overlap between the external benchmark and training is measured by composition identity. The 1,998/2,500 compositions already held and the 1,200 identical values are disclosed, and conclusions are drawn from the 465 blind records (Table 5). A package exists that rebuilds the tables and figures, with checksums (paper/README.md).
- Warn triggers fired:
  - (a) Upstream redistribution licences are unverified. Data availability carries two `\todo`s, and paper/README.md says "redistribution licences have not yet been verified".
  - (b) The external benchmark has no licence and is not redistributed, yet three result files contain its compound names and values.
  - (c) The multi-hour RQ1/RQ2 fits were not re-run for the package (README "Not re-run for this package").
  - (d) XGBoost results depend on thread count (Recommendation vi), so exact reproduction of XGBoost numbers requires 16 threads.
  - (e) The formula-spelling leak (0.6%/1.3%) is disclosed but not fixed.
- No code licence or repository DOI has been chosen yet (Code availability `\todo`).

### D2: domain_accuracy — **warn**
- No interpretation-changing factual error found.
  - Target definitions are handled carefully: Curie versus Néel temperatures, and moment per cell versus per atom (Methods, "Magnetic moment").
  - The C4 rationale (1,400 K, above Co's Tc) is correct.
  - Conformal and calibration terms are used correctly.
- Warn trigger fired: key adjacent literature is missing. The bibliography (37 entries) covers conformal basics, Matbench, leakage and one OOD critique (li2023critical). It omits:
  - **Materials-ML OOD and redundancy benchmarks:** Omee et al. 2024 (npj Comput. Mater.) on OOD benchmarks; Li et al. 2024 MD-HIT (npj Comput. Mater., DOI 10.1038/s41524-024-01426-z) on dataset redundancy.
  - **UQ benchmarking in materials:** Varivoda et al. 2023 (Appl. Phys. Rev., DOI 10.1063/5.0133528).
  - **How UQ is used in active learning or design:** Lookman et al. 2019 (npj Comput. Mater. 5, 21).
  - **General-ML work on the exact failure reported in Fig. 4:** conformal prediction under covariate shift (Tibshirani, Barber, Candès & Ramdas, NeurIPS 2019); selective prediction / abstention (Geifman & El-Yaniv, NeurIPS 2017); distribution-shift benchmarks (Koh et al., WILDS, ICML 2021).
  - **Data stewardship:** the FAIR principles (Wilkinson et al. 2016, Sci. Data).
- Minor terminology issue: Table 6 and the text call 0.333 the "three-class chance level". Ordering is defined as four classes (FM/AFM/FiM/NM), so a reader cannot tell which class is missing in the provenance-transfer test.

### D3: argumentative_coherence — **warn**
- Block triggers did not fire. The central thesis (accuracy, physics gain, calibration and generalization are separable) is directly supported, pair by pair, in the Discussion's first paragraph. The pre-registered wording rule for R² (an upper limit ≤ 0.2 is needed before "no skill" may be claimed) is honoured.
- Warn triggers fired (overreach in the Discussion and Conclusion):
  - (a) "in-distribution accuracy is the least informative of the four properties, and calibrated distance-aware uncertainty is the most needed" (Conclusion). The paper ranks these properties without measuring usefulness for discovery. No screening, ranking or decision outcome is evaluated, and no distance-aware UQ method is tested. The paper only shows that normalized conformal widens "not enough".
  - (b) "likely for other property-prediction tasks" (Practical recommendations) has no supporting argument.
  - (c) The title and Introduction frame the work around "physics-informed" ML. What is tested is narrower: appending 24 DFT scalar descriptors to tabular boosted trees, which the Limitations acknowledge.

### D4: cross_disciplinary_relevance — **warn**
- Block triggers did not fire. The practical framing is not misleading, and the Limitations hedge it appropriately.
- Warn triggers fired:
  - The implications are not operationalized. None of the six recommendations tells a discovery team which candidates to trust, when to abstain, or how to fold intervals into acquisition. All six are about evaluation practice.
  - The link to selective prediction, active learning and covariate-shift conformal methods is absent (see D2).
  - The shared-upstream-compilation finding (48% identical values) is reported as a local audit result ("Both datasets draw on the same upstream compilations"), not as the field-wide provenance problem it is.
- The definitions of coverage, marginal versus class-conditional sets, and chemical system are clear enough for adjacent-field readers. That clarity keeps D4 from going lower.

### D5: writing_and_structure — **warn**
- The prose is clear and number-dense, and the RQ1–RQ3 structure works. Figures 1–4 are readable, with intervals and nominal lines.
- Warn triggers fired:
  - Draft placeholders remain: affiliations, funding, data DOI, licences and the AI-use statement are all `\todo`. The Supplementary Information is "to be assembled", although the main text relies on Tables S1–S3.
  - Minor figure/text mismatches:
    - The Fig. 4 caption says "For the 465 blind external records", but the panels also plot "All primary records" and an exact-match bin 0.
    - Fig. 2c shows the frozen split (AFM 57.7%, FiM 52.7%), while the abstract quotes the 10-split means (57%, 55%).
  - The recommendations are a run-on single paragraph and are easy to miss.

## Failure Condition Checks

### F1 (severity 90; any mandatory dimension scores 'block')
fired: false. D1, D2 and D3 are all 'warn'; none is 'block'.

### F2 (severity 70; two or more mandatory dimensions score 'warn' or worse)
fired: true. All three mandatory dimensions (D1, D2, D3) score 'warn'. The quantifier is "majority" across reviewers; at my own reviewer level the condition is met.

### F3 (severity 60; any high-priority dimension scores 'block')
fired: false. D4 (high priority) is 'warn'.

### F0 (severity 10; every mandatory dimension scores 'pass')
fired: false.

Highest-severity fired condition: F2, so editorial_decision = major_revision.

## Review Body

### Manuscript Information
- **Title**: Accuracy is not reliability: physics descriptors, calibration and chemical generalization in machine learning of magnetic materials
- **Review Date**: 2026-11-09 · **Review Round**: 1

### Reviewer Information
- **Role**: Peer Reviewer 3 (Perspective / cross-disciplinary and practical impact)
- **Identity**: Materials-discovery practitioner (autonomous labs, materials data infrastructure) with a background in ML evaluation practice and data provenance.
- **Focus**: Whether the findings change what a discovery team does. Specifically: how the reported uncertainty would be used in screening and active learning, the field-wide data-provenance problem exposed by the benchmark audit, package usability and licensing, and how far the "physics-informed" lesson transfers.

### Overall Assessment
- **Recommendation**: Major Revision (by contract precedence, F2).
- **Confidence**: 4.

**Summary assessment.** The paper builds a curated multi-source magnetic dataset. On it, the authors test three properties of composition-based tree models: whether DFT descriptors help, whether conformal and calibrated uncertainty holds up by subgroup, and whether accuracy holds in unfamiliar chemistry. The headline results are clear.
- DFT descriptors give no practical gain for ordering or Tc, and the per-cell moment gain is a cell-size artifact.
- Marginal coverage hides subgroups at 50–60% coverage.
- Experimental Tc in unseen chemical systems is predicted much worse (R² −0.17 [−0.93, 0.66]).
- Ordering skill does not transfer across label provenance.

From a practitioner's standpoint this is unusually honest and useful work. The audit of the external benchmark and the published list of the authors' own errors are a model of good practice. The weakness is the last step. The paper says that distance-aware, calibrated uncertainty is "the most needed" for discovery, but it never shows what a discovery team should do with its intervals, distances or sets. It also does not connect to the literature that already addresses these questions: selective prediction, covariate-shift conformal methods, and UQ-driven active learning. In addition, the package cannot be deposited until licences are resolved. These problems are fixable without new large experiments, but together they need a substantive revision.

### Strengths

**S1: The external-benchmark audit is the paper's most transferable contribution.**
- Novelty is defined by composition, not by formula string.
- Exclusions were fixed before any errors were examined (Table S1, A1–A8).
- Clusters are bootstrapped by source paper.
- 1,200/2,500 values turn out to be identical to training labels, and the R² of 0.90 on them is correctly called "recall of training labels".

This exposes a failure mode, the "independent" benchmark that shares upstream compilations, which almost certainly affects other text-mined property benchmarks.

**S2: The negative results are fully reported.** The paper discloses:
- the JARVIS collector default "FM" label (15,493 rows);
- non-Curie transitions in the text-mined Tc column;
- the per-atom denominator from a different cell (25.4% of rows, with the 14%/9%/6% claim withdrawn);
- the string-based novelty test;
- the DOI-prefix bug;
- the single-split ordering gain that did not replicate.

This list (Methods, "Errors found and corrected") is directly reusable as a checklist by data-infrastructure teams.

**S3: The physics-descriptor comparison uses matched rows and a simple control.**
- Identical rows, splits and grids are used across tiers (Table 2, Fig. 1).
- The finding that one site-count scalar recovers the Tier 3 moment gain is exactly the control that "physics-informed" claims in other domains usually lack.
- The "attribution is not benefit" paragraph (SHAP gives 36–40% to non-helpful descriptors) is an important warning for interpretability-driven discovery narratives.

**S4: The calibration findings are decision-relevant.**
- Marginal sets cover AFM at 57.7% and FiM at 52.7%, while class-conditional sets reach about 90% at a set size of 1.57 (Table 4).
- Coverage drops under label-source shift (76.9–85.1%, Tc).

These map onto practical failure modes: a screening campaign looking for antiferromagnets would be systematically misled by marginal sets.

**S5: Hedging is calibrated to the uncertainty.** The pre-registered R² wording rule, and the explicit statement that a Tc degradation of up to about 30 K is not excluded, are good practice.

### Weaknesses

#### W1: The practical recommendations stop at evaluation hygiene and never reach the decision a discovery team makes
- **Problem**: Recommendations (i)–(vi) (Discussion) cover how to evaluate: matched rows, subgroup coverage, novelty by composition, cluster bootstrap, auditing collectors, thread seeds. None of them covers how to use the model.
  - The Conclusion asserts that calibrated distance-aware uncertainty is "the most needed", but no screening or selection outcome is evaluated.
  - The normalized 90% Tc intervals are 366–529 K wide (Table 3, Fig. 4b) against a target range of 1–1,400 K. That is roughly a third of the range, and the practical consequence is never stated: these intervals cannot discriminate candidates at a typical application threshold.
- **Why it matters**: A self-driving-lab or screening team reading this paper learns what not to trust, but not how to act. The paper's own data contain the answer.
- **Suggestion**: Add a short "use in screening" analysis on the 465 blind records. This needs no new models.
  - (a) Risk–coverage (selective prediction) curves, using composition distance and normalized interval width as abstention scores. Report MAE and coverage when abstaining on the farthest 25% or 50%.
  - (b) A threshold task, e.g. "is Tc > 300 K?" or top-k enrichment of high-Tc compositions, with and without abstention. Discovery is a ranking/threshold problem, not an MAE problem.
  - (c) An explicit operating rule, e.g. "trust intervals only below TV distance ≈0.03, where coverage stays near nominal (Table S3, Q1–Q2)".

  Then rewrite the recommendations into two groups: evaluation practice, and deployment practice.
- **Severity**: Major

#### W2: The paper is not connected to the general-ML literature on shift and abstention, or to UQ-driven active learning
- **Problem**:
  - Fig. 4 and Table S3 show coverage falling from 0.95 to 0.85 with distance. This is the textbook covariate-shift failure of exchangeable conformal prediction, and weighted conformal prediction (Tibshirani et al., NeurIPS 2019) is the standard remedy. Neither the failure nor the remedy is cited.
  - Selective prediction (Geifman & El-Yaniv 2017) and distribution-shift benchmarks (WILDS, Koh et al. 2021) are not cited.
  - In materials, the paper does not cite or position itself against Omee et al. 2024 (OOD benchmark), Li et al. 2024 (MD-HIT redundancy control), Varivoda et al. 2023 (UQ benchmark) or Lookman et al. 2019 (UQ in active learning and design).
- **Why it matters**: Adjacent-field readers will judge the RQ2/RQ3 conclusions against this literature. Without it, the paper looks like it is rediscovering known effects, when its real contribution is to quantify them for magnetism under a careful audit.
- **Suggestion**:
  - Add a related-work paragraph in the Introduction, and a Discussion paragraph that names covariate-shift conformal and Mondrian-by-distance calibration as next steps.
  - Optionally, run one cheap analysis: Mondrian (class-conditional) calibration with distance bins as the "classes", on the internal calibration split. It is the same machinery already used for ordering and would test whether the Fig. 4c drop is fixable.
- **Severity**: Major

#### W3: The data-provenance finding is under-sold, and the licence status blocks the package
- **Problem**:
  - The finding that 80% of the "independent" benchmark compositions, and 48% of its values, already sit in the training repository because both draw on the same compilations (RQ3, external benchmark) is a field-wide problem for text-mined property data. The paper treats it in one sentence.
  - Separately, the upstream redistribution licences are unverified, and the external table has no licence while three result files contain its values (Data availability `\todo`s; paper/README.md). There is also no code licence and no DOI yet.
- **Why it matters**:
  - Benchmark contamination through shared upstream sources undermines comparisons across studies (e.g. reported Tc MAEs in nelson2019curie, belot2023curie, abediorang2026curie may not be comparable).
  - A reproducibility package that cannot legally be deposited is not yet a reproducibility package.
- **Suggestion**:
  - (a) Add a Discussion paragraph on provenance lineage. Recommend that Tc/ordering datasets publish per-record upstream lineage (source compilation plus DOI) and a composition-key overlap report against common training corpora, framed with the FAIR principles (Wilkinson et al. 2016).
  - (b) Release the composition-key / normalized-DOI overlap checker as a standalone tool. It is already in the package (audit tests).
  - (c) Before acceptance, resolve every upstream licence. Where a licence forbids redistribution, ship IDs plus fetch scripts, as already done for the external table. Drop or hash the external compound names in the three result files, and choose a code licence and an archive DOI.
- **Severity**: Major (the deposit blocker is required before publication)

#### W4: Reproducibility is verified for tables and figures but not for the expensive fits, and the workspace path is fragile
- **Problem**:
  - paper/README.md states that RQ1/RQ2 fits were not re-run for the package; only the external-benchmark chain was reproduced byte-for-byte.
  - The pipeline must run inside a recreated original project layout (`setup_workspace.py`, commands such as `python ../../final/scripts/check1_curie_inference.py`).
  - XGBoost numbers depend on thread count.
  - No runtime or hardware estimates are given.
- **Why it matters**: An outside group, and in particular an automated-lab group that would want to re-train on its own data, needs a tractable path and known compute.
- **Suggestion**:
  - Provide a container or lock file.
  - Give a "smoke" configuration (one split, one target) with expected outputs and tolerances.
  - Report wall-clock and core counts per stage.
  - State the expected reproduction tolerance for XGBoost under a different thread count. Recommendation (vi) already quantifies this as about 25% of MAE in the mean prediction.
  - In the paper, distinguish "bit-reproduced" from "reproduced within tolerance" claims.
- **Severity**: Minor–Major

#### W5: The scope of "physics-informed" and the generalization to other domains are over-stated
- **Problem**:
  - The title, keywords and Introduction invoke "physics-informed" ML.
  - What is tested is 24 DFT scalar descriptors of the most stable computed polymorph, joined by reduced formula and appended to tabular models.
  - The Discussion's own explanations include a structure mismatch between DFT polymorph and experimental sample (doping, films), which is a provenance and matching issue rather than a test of physics content.
  - The recommendations claim relevance "likely for other property-prediction tasks" without argument.
- **Why it matters**: Readers in other property domains (battery, catalysis, thermoelectrics) may take away "physics descriptors don't help" rather than the more defensible "formula-joined DFT descriptors don't help tabular trees for these targets without matched structures".
- **Suggestion**:
  - Use "DFT descriptors" consistently, and define how this differs from physics-informed approaches such as constraints, physics-based losses, or structure-aware models.
  - Either justify the cross-domain claim, for instance by naming the two transferable mechanisms (the cell-size/extensivity confound and attribution ≠ benefit) as the parts expected to generalize, or remove it.
  - Soften the Conclusion's ranking of the four properties to what was measured.
- **Severity**: Minor

### Questions to Authors
1. In the provenance-transfer test, why is chance 1/3 for a four-class target? Is NM absent from the experimental labels? What are the class counts on each side?
2. What is the distribution of 90% interval widths, relative to typical decision thresholds (e.g. room temperature)? Would any candidate be confidently classified as above or below 300 K?
3. Can composition distance or the normalized difficulty score be used to abstain? What MAE and coverage result at 50% abstention on the blind set?
4. Is the label-provenance failure for ordering (macro-F1 0.284 MP→experimental) driven by MP's collinear-spin DFT convention (e.g. FiM/AFM assigned as FM), and could the authors give a per-class confusion? This matters for anyone training on DFT labels and validating in the lab.
5. Which upstream sources have licences that allow redistribution of derived values? What is the fallback plan for those that do not?
6. Would the authors publish the audited overlap table (composition key × source compilation) so that other Tc benchmarks can be checked against it?

### Detailed Comments (perspective-relevant)
- **Abstract**: Accurate and number-rich. Consider adding one sentence on the practical consequence for screening (see W1).
- **Introduction**: Add the related-work paragraph (W2).
- **RQ2**: The label-source shift results (76.9–85.1%; 83.5% for sets) deserve a sentence on what a lab should do, e.g. recalibrate on a small in-house labelled set.
- **RQ3**: Excellent audit. Bring Table S1's A6 flag (160 film/nano/pressure records) into the main text, because form-factor heterogeneity is a lab-relevant provenance issue.
- **Figures**:
  - Fix the Fig. 4 caption ("465 blind" versus the plotted all-records series and bin 0).
  - Note in the Fig. 2c caption that it shows the frozen split, while the abstract quotes 10-split values.
- **Back matter**: Resolve all `\todo`s; assemble the SI.

### Rubric Scores (0–100)
| Dimension | Score |
|---|---|
| Originality | 72 |
| Methodological Rigor | 78 |
| Evidence Sufficiency | 76 |
| Argument Coherence | 72 |
| Writing Quality | 68 |
| **Weighted (rubric formula)** | **73.9** |
| Significance & Impact (R3, reported separately) | 76 |

The weighted rubric score alone would map to Minor Revision. Under the sprint contract, however, the editorial decision is set by the failure conditions (F2), which gives Major Revision. The required changes are mostly analytic framing, related work and licensing, not new large experiments.

## Editorial Decision

**Major Revision.** F2 fired: D1, D2 and D3 all score 'warn'. F1 and F3 did not fire. The core results are sound and valuable. Revision should:
- (1) add a deployment-oriented screening/abstention analysis and recommendations (W1);
- (2) connect to the covariate-shift, selective-prediction and UQ-active-learning literature (W2);
- (3) resolve upstream and benchmark licences and frame the shared-compilation contamination as a field-wide provenance issue (W3);
- (4) firm up the reproducibility path (W4) and the scope of "physics-informed" (W5).
