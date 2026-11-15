# Methodology Reviewer (Peer Reviewer 1) -- Phase 1 (paper-content-blind)

contract_id: reviewer/reviewer_full/v1 · mode: reviewer_full · stage: reviewer_full_review · baseline_version: v3.6.2 · panel_size: 5
generated_at: 2026-11-09T15:29:02Z
Metadata used: title "Accuracy is not reliability: physics descriptors, calibration and chemical generalization in machine learning of magnetic materials"; field "computational materials science / machine learning for magnetic materials"; word_count ~3,500.

## Contract Paraphrase

**D1 methodology_rigor (mandatory).** From a methodology standpoint, the study design must be able to answer the questions it poses: comparisons of feature sets must hold everything else fixed, evaluation must respect the grouped/clustered structure of materials data, uncertainty must be quantified at the right unit (split, group, cluster), multiple comparisons must be acknowledged, and uncertainty-quantification claims must state what guarantee is actually delivered and under which assumption. Data handling (exclusions, deduplication, leakage) and reproducibility affordances (seeds, nondeterminism, code/data availability) must reach the bar of a peer-reviewed ML-for-materials venue.

**D2 domain_accuracy (mandatory).** Statistical and ML terminology and results must be stated correctly (e.g. what conformal prediction guarantees, marginal versus conditional coverage, what a calibration metric measures), and prior work on conformal prediction, calibration and grouped validation must be represented faithfully. Reported numbers in text must agree with the tables, figures and result files. Magnetism-physics accuracy is outside my main expertise; I will flag only obvious issues.

**D3 argumentative_coherence (mandatory).** The thesis implied by the title ("accuracy is not reliability") must follow from the evidence: each claim of benefit, null, or failure must match the strength of the statistical evidence, null results must not be read as equivalence, and the decision rules used to label results must be applied consistently and not adjusted after seeing the data.

**D4 cross_disciplinary_relevance (high).** Methods vocabulary (conformal, CQR, temperature scaling, grouped bootstrap) must be defined well enough that materials scientists can use it, and claims of relevance to general scientific-ML practice must be supported by the evidence rather than asserted.

**D5 writing_and_structure (normal).** The methods must be described in a findable, ordered way; tables and figures must show intervals and sample sizes, with clear captions; and the manuscript must follow venue conventions.

## Scoring Plan

### D1: methodology_rigor
- dimension_id: D1
- what_to_look_for: matched design (identical rows, splits, hyperparameter search budget and seeds across feature tiers); whether the group unit for splits and bootstrap is stated and justified (formula, chemical system, paper cluster); how split-to-split variance and within-split bootstrap variance are combined into one "stable" decision; whether the stability/decision rule and the external-benchmark wording rule were pre-specified, and whether amendments are disclosed; multiplicity handling across targets × algorithms × tiers; conformal set-up (calibration set disjoint from training and test, exchangeability argued, normalized/CQR scores defined, class-conditional sets, temperature scaling fit on data disjoint from conformal calibration); exclusions decided blind to outcome; leakage checks; seeds, thread/nondeterminism disclosure, code and data availability.
- what_triggers_block: a central claim rests on a non-matched comparison or on test-set reuse for tuning or calibration; coverage claims are made with calibration data that overlap test or training data; uncertainty quantified at the wrong unit so that intervals are invalid for a headline claim; undisclosed post-hoc changes to decision rules; results not reproducible in principle (no seeds, no code, undisclosed nondeterminism that flips a headline verdict).
- what_triggers_warn: decision rule sound but its combination of split and bootstrap uncertainty is under-specified or heuristic; multiplicity acknowledged but not corrected or framed; exchangeability assumed without discussion for shifted subgroups; small cluster counts for a bootstrap without a caveat; documented nondeterminism that affects a secondary claim; minor gaps in reporting effect sizes or N.

### D2: domain_accuracy
- dimension_id: D2
- what_to_look_for: correct statement of the conformal guarantee (finite-sample, marginal, under exchangeability) versus conditional or subgroup coverage; correct description of CQR, normalized nonconformity, Mondrian/class-conditional sets, ECE and temperature scaling; correct attribution to primary references; agreement of text numbers with tables, figures and result files; correct use of R², MAE and macro-F1.
- what_triggers_block: a misstatement of what a method guarantees that underpins a headline claim (e.g. claiming conditional coverage from marginal conformal), or a headline number that contradicts the result files/tables.
- what_triggers_warn: imprecise terminology, missing primary citations for the methods used, isolated number mismatches in secondary results, unqualified ECE claims (binning not stated).

### D3: argumentative_coherence
- dimension_id: D3
- what_to_look_for: whether each of the paper's claims (physics descriptors help or not; calibration works or fails; generalization degrades) is graded by the evidence strength; absence of "no effect" read from "CI includes 0" without an equivalence bound; consistent use of the stability rule across targets; whether the overarching thesis is a synthesis of separate results rather than a tested claim; limitations matching the weaknesses actually present.
- what_triggers_block: the central thesis contradicted by the paper's own results, or a headline claim that depends on a reversal of the stated decision rule.
- what_triggers_warn: some claims over- or under-state their evidence (e.g. absence of evidence presented as evidence of absence; "stable" used loosely); a wording rule applied inconsistently; thesis framing broader than the evidence.

### D4: cross_disciplinary_relevance
- dimension_id: D4
- what_to_look_for: definitions of the UQ and resampling methods accessible to materials scientists; practical recommendations derived from results; whether claims of general relevance for scientific ML are scoped.
- what_triggers_block: interdisciplinary claims (e.g. "applies to all materials ML") that are unsupported and central to the paper's contribution.
- what_triggers_warn: jargon left undefined; generality claimed beyond one dataset/target family without caveat.

### D5: writing_and_structure
- dimension_id: D5
- what_to_look_for: method description locatable and ordered; tables show N, intervals and the uncertainty unit; figure captions self-contained; supplementary tables referenced; venue template followed.
- what_triggers_block: methods so scattered or omitted that the analysis cannot be reconstructed from the manuscript plus supplement.
- what_triggers_warn: key methodological details only in supplementary/code; tables or figures missing intervals or N; dense prose that hides decision rules.

[CONTRACT-ACKNOWLEDGED]
