# Editorial Decision Package

Manuscript: "Accuracy is not reliability: physics descriptors, calibration and chemical generalization in machine learning of magnetic materials" (draft 2026-11-09)
Simulated venue: npj Computational Materials · Mode: academic-paper-reviewer `full`, contract reviewer/reviewer_full/v1 (panel 5) · Round 1 · 2026-11-10

Reviewer reports (all in this folder; each wrote its Phase 1 scoring plan before reading the paper):
EIC = `eic_report.md` · R1 Methodology = `methodology_report.md` · R2 Domain = `domain_report.md` · R3 Perspective = `perspective_report.md` · DA Devil's Advocate = `devils_advocate_report.md`.
Panel check: 5 of 5 usable reports; every report has the required sections (Dimension Scores, Failure Condition Checks, Review Body, Editorial Decision); no Scoring Plan Dissent.

---

## Step 1: Scoring matrix

| Dimension (priority) | EIC | R1 | R2 | R3 | DA |
|---|---|---|---|---|---|
| D1 methodology_rigor (mandatory) | warn | warn | warn | warn | warn |
| D2 domain_accuracy (mandatory) | warn | **block** | warn | warn | warn |
| D3 argumentative_coherence (mandatory) | warn | warn | warn | warn | warn |
| D4 cross_disciplinary_relevance (high) | pass | pass | pass | warn | pass |
| D5 writing_and_structure (normal) | warn | warn | warn | warn | warn |

## Step 2: Failure conditions (panel-level)

| Condition | Severity | Quantifier | Fired? | Basis |
|---|---|---|---|---|
| F1: any mandatory dimension scores 'block' | 90 | any | **yes** | R1 scores D2 block (the abstract misstates the conformal guarantee) |
| F2: two or more mandatory dimensions score 'warn' or worse | 70 | majority (>= 4 of 5) | **yes** | all 5 reviewers have D1, D2 and D3 at warn or worse |
| F3: any high-priority dimension scores 'block' | 60 | any | no | D4 is never block |
| F0: every mandatory dimension scores 'pass' | 10 | all | no | |

## Step 3: Precedence

F1 has the highest severity of the fired conditions, so its action applies: **reject_or_major_revision**. Within that action, the choice is
**Major Revision**, for these reasons:
- All five reviewers independently recommend Major Revision.
- The Devil's Advocate reports **no CRITICAL issue** (no headline conclusion is invalidated).
- R1 states that its block-level item is fixable by rewording (R1 W1, "Severity: Critical (easily fixed)").

This does not soften F1: Reject is not chosen because no report supports it. The 0-100 rubric averages (69.1-73.9) would map to Minor
Revision. Under the contract, the failure conditions decide, and every reviewer notes this.

---

# Part 1: Editorial Decision Letter

**Decision: Major Revision**

Dear Dr Islam and Dr Hettiarachchi,

Five reviewers assessed your manuscript independently. All five praise the work as unusually careful and transparent, citing:
- the matched tier design with a site-count control;
- the composition-level audit of the external Curie benchmark;
- the subgroup-level calibration evidence;
- the public list of errors you found and corrected.

R2 and DA single out the benchmark-overlap finding as perhaps the most valuable result. All five also recommend Major Revision. The core
problem is that the paper's message is "do not over-claim", yet the abstract, Discussion and section headings state several results more
strongly than the tables show. Three further problems: the "physics descriptors" conclusion is broader than the descriptors tested; the
label-provenance result is confounded; and the submission is incomplete. Most issues can be fixed with outputs you already have, by
rewording, or with small new analyses. None requires new data collection.

### Consensus analysis

**Points of agreement**
- [CONSENSUS-5] Several abstract, Discussion and heading statements do not match the tables (EIC W2; R1 W1, W6; R2 W1;
  R3 W5; DA M4, M5, M7, M8). Specifically:
  - "90% marginal coverage only with difficulty-normalized scores" contradicts Table 3. All three methods average about 90% for the
    moment, and split conformal averages 89.3% for Tc.
  - "fully explained by unit-cell size" is inaccurate. The residual is +0.024 [-0.003, +0.050] (not resolved, not zero), and the
    per-atom gain that survives is omitted.
  - "at chance across label provenance" is not supported as stated.
  - "least informative of the four properties" was never tested.
  - "None of these properties can be inferred from another" is contradicted by the data: error, interval width and coverage co-vary with
    distance.
  - "Accuracy fell substantially" rests on 69 records from 26 papers.
- [CONSENSUS-5] The cross-provenance ordering test is confounded by a change of label space and class prior (EIC W3; R1 W6; R2 W3;
  R3 Q4; DA M6). The MP training set is about 51% NM. The experimental test set has almost no NM and is scored on FM/AFM/FiM only. 4,753
  MP rows are dropped in the reverse direction, and the "three-class chance 0.333" reference is not appropriate. Reviewers ask for the
  label-agreement rate on formulas labelled in both sources, and for a transfer on a shared label space with prior correction.
- [CONSENSUS-5] The submission is incomplete: the SI is not assembled, `\todo`s remain, data/code DOI and licences are missing, and the
  AI-use disclosure is absent (EIC W5; R3 W3; R1 minor; R2 minor; DA m6).
- [CONSENSUS-4] The RQ1 conclusion is broader than the test (EIC W4; R2 W1; R3 W5; DA M1, M2).
  - Tier 3 excludes every magnetic DFT output and all magnetic-sublattice geometry, and the manuscript never says so.
  - The values are formula-joined to the lowest-energy polymorph.
  - Only tabular models are used.
  - The Curie Tier 3 point estimates are degradations (GB -14.3 K, XGB -9.7 K), which suggests a mismatch between descriptors and target.
  - At minimum, rescope the conclusion to "generic (non-magnetic) DFT scalar descriptors with tabular models" and disclose the exclusion.
- [CONSENSUS-3] Positioning against the literature is thin (EIC W1; R2 W5; R3 W2). The paper needs UQ/OOD benchmark work, covariate-shift
  conformal prediction, selective prediction, and prior magnetic ML studies, with their results compared.

**Points raised by fewer reviewers but adopted as required** (verified against the reports and treated as substantive):
- R1 W2, W3 and DA M3: the stability rule in the text omits the 70%-of-splits criterion used in the code; the intervals hold fitted
  models fixed (refit variance is not included); there is no multiplicity framing over 18 contrasts; and borderline "stable" calls
  exist (-0.001, +0.002).
- R1 W4 and DA M3: pre-specification is overstated.
  - PLAN.md records that the October subset results (unseen-system R² about -0.18) were known when the 0.2 wording rule was written.
  - Amendment 2 came after the first bootstrap.
  - The headline subset has 18 resampling clusters, not 26.
  - Under chemical-system clustering the upper R² limit is 0.23, close to the 0.2 threshold.
  - The v1.3 curation rules were set after earlier results had been seen.
- R1 W5: the "hardest decile" is defined by the difficulty score that normalized conformal uses, so that comparison favours it by
  construction. Temperature and conformal thresholds share one calibration set.
- R2 W2: the target labelled "Ms" is a 0 K DFT total moment per cell, and it is near zero for both AFM and NM. Rename it, and make per
  formula unit (or per magnetic atom) the primary target.

**Points of disagreement**
- [SPLIT] Severity of the conformal misstatement: R1 scores it block (D2), while EIC and DA treat it as a warn-level overstatement.
  Resolution: all three agree it is wrong and must be corrected. The contract's "any" quantifier makes R1's block binding for the
  decision, and its fix is a rewording.
- [SPLIT] D4: R3 scores warn (no guidance for deployment and screening). The other four score pass. Resolution: R3's concern is taken as a
  suggested revision, not a required one, apart from the required literature item above.
- [SPLIT] How to address the RQ1 scope: EIC W4 offers either a structure-based baseline (GNN or pretrained embeddings) or rescoping;
  R2 W1 prefers a small magnetic-structure descriptor tier; DA M2 asks for a structure-matched subset test. Resolution: rescoping and
  disclosure are required. At least one of the three tests is strongly recommended, because it turns the null result into a test of the
  hypothesis a magnetism researcher would actually pose.

### Decision rationale
The empirical core is sound, and no reviewer found a fatal flaw (DA: no CRITICAL). The decision is driven by three things:
- the block-level misstatement in the abstract (contract F1);
- the agreement of all five reviewers on over-claiming and on the provenance confound;
- the incompleteness of the submission.

A revised version that fixes the required items below should be in a strong position.

### Summary of key issues (ranked)
1. The abstract and Discussion over-claim (CONSENSUS-5; includes the F1 block).
2. The RQ1 scope: magnetic and structural physics are excluded and not disclosed; the Curie Tier 3 degradation (CONSENSUS-4).
3. The cross-provenance ordering confound (CONSENSUS-5).
4. Statistical decision rules, multiplicity and pre-specification wording (R1, DA).
5. Completeness: SI, data and code deposit, licences, declarations (CONSENSUS-5).
6. Literature positioning and comparison with prior magnetic ML results (CONSENSUS-3).
7. Target definitions: the moment target name and normalization; residual Tc label noise; NM-driven ordering scores (R2).

---

# Part 2: Revision Roadmap

### Required revisions (must fix)
| # | Revision | Source | Type | Effort |
|---|---|---|---|---|
| RR1 | Rewrite the abstract, Discussion, Conclusion and RQ2 heading so they match the tables. (a) Say that all three conformal methods reach about 90% marginal coverage; for Tc, split and CQR vary ±6 points between splits, and only normalized conformal holds the hard cases. (b) Say "largely (about 70%) explained by cell size", and add the per-atom gain. (c) Remove or rescope "at chance across provenance". (d) Correct "calibrated on blind external compositions": they were calibrated internally. (e) Give the sign of the Curie Tier 3 point estimates (a degradation). (f) Remove the untested "least informative" ranking. (g) Replace "none can be inferred from another" with "correlated but not interchangeable". (h) Say "weaker and poorly constrained", not "fell substantially". | EIC W2; R1 W1, W6; DA M4, M5, M7, M8 | rewording | 1 day |
| RR2 | Rescope RQ1 to the descriptors actually tested, in the title, abstract, RQ1 heading, Fig. 1 caption and Conclusion. In Methods, list the excluded magnetic DFT columns and the reason for excluding them (leakage). Discuss the descriptor-target mismatch explanation for the Curie degradation. | EIC W4; R2 W1; R3 W5; DA M1, M2 | rewording | 0.5 day |
| RR3 | Rework the cross-provenance ordering test. (a) Report the label-agreement confusion matrix on formulas labelled in both MP and experimental sources. (b) Run the transfer on the shared FM/AFM/FiM label space, with prior correction. (c) Replace the three-class chance line with a prior-matched or label-shuffled reference, with a cluster-bootstrap CI. (d) Discuss the FM bias from MP's FM-initialized calculations (Horton 2019). | EIC W3; R1 W6; R2 W3; DA M6 | new analysis (existing data) | 2-3 days |
| RR4 | State the full stability rule in Methods: the bootstrap CI plus the 70%-of-splits criterion. Add a refit-aware interval (Nadeau-Bengio corrected t, or a nested bootstrap) and show both in Table 2. Declare a primary contrast family (Tier 1->3, three targets) with simultaneous or Holm intervals, label the follow-up analyses exploratory, and describe borderline calls as borderline. Average XGBoost over at least 3 thread/seed realisations. | R1 W2, W3; DA M3 | reanalysis of saved outputs (+ some refits) | 3-5 days |
| RR5 | Correct the pre-specification wording to match PLAN.md. Say which results were known when the rules were written, mark Amendment 2 as outcome-aware, and separate analysis pre-specification from dataset-version decisions made after results were seen (v1.3). Report 18/81 resampling clusters in Table 5. Give the wording-rule verdict under all three clusterings, and add a few-cluster-robust bootstrap. | R1 W4; DA M3 | rewording + small reanalysis | 1-2 days |
| RR6 | Remove the circularity of the hardest decile. Report all three conformal methods on hard subgroups defined independently of `sigma` (composition distance, family, high predicted value, label source). Split the calibration set between temperature fitting and conformal thresholds, or state that the guarantee is approximate. Discuss the design effect (about 20) caused by within-formula dependence. | R1 W5 | reanalysis | 1-2 days |
| RR7 | Rename the "Ms" target everywhere, including tables and figures (e.g. "m_DFT, total moment per cell, μB/cell"). Make per-formula-unit (or per-magnetic-atom) the primary moment target, or justify keeping per-cell. State the functional mix and how often MP used FM initialization. | R2 W2; EIC W5 | rename + reanalysis | 2 days |
| RR8 | Complete the submission. (a) Assemble the SI. (b) Resolve all `\todo`s. (c) Resolve upstream and benchmark licences, ship IDs plus fetch scripts where redistribution is not allowed, and drop or hash the external compound names in the three result files. (d) Add a code licence and an archive DOI. (e) Write the AI-use disclosure. (f) Shorten the abstract to the venue limit. | EIC W5; R3 W3; all minor | admin | 3-5 days |
| RR9 | Add a related-work paragraph and engage prior results. Cover UQ/OOD benchmarks (Varivoda 2023, Omee 2024), covariate-shift conformal (Tibshirani 2019), selective prediction, and prior magnetic ML (Long 2021, Merker 2022, Court & Cole 2020, Sanvito 2017). Add a short table of prior Tc and ordering results. Lead with the magnetism-specific contributions and present the general thesis as a corollary. | EIC W1; R2 W5; R3 W2 | writing | 2 days |

### Suggested revisions (should fix)
| # | Revision | Source |
|---|---|---|
| SR1 | Add one test that turns the RQ1 null into the hypothesis a magnetism researcher would pose. Options: a small magnetic-structure descriptor tier (magnetic-ion density, M-M distance, M-X-M angle, coordination) built from MP structures; a structure-matched Curie subset; or one structure-based baseline (GNN or frozen universal-potential embeddings). | R2 W1; DA M2; EIC W4 |
| SR2 | Estimate the residual label noise in Tc: hand-audit about 200 stratified records, and report the within-formula SD as a noise floor next to the 10 K margin. | R2 W4 |
| SR3 | Report ordering metrics on the subset with a magnetism-capable element, and per-class recall in the main text. | R2 W3 |
| SR4 | Add a deployment analysis on the 465 blind records: risk-coverage (abstention) curves by distance and interval width, a threshold task (Tc > 300 K or top-k), and an operating rule. Split the recommendations into evaluation practice and deployment practice. | R3 W1 |
| SR5 | Try Mondrian-by-distance or weighted (covariate-shift) conformal on the internal calibration split, to test whether the coverage drop in Fig. 4 can be fixed. | R3 W2; EIC Q3 |
| SR6 | Frame the 80%/48% benchmark overlap as a field-wide provenance problem: recommend per-record lineage, apply FAIR principles, and release the overlap checker. | R3 W3; DA observation |
| SR7 | Explain the baseline mismatch: Table 6 gives Curie MAE 99.2 K and ordering F1 0.712, while the text gives 76 K and 0.727 (ten-split vs frozen split). Show Tier 1 performance on matched vs unmatched rows. Report the minimum detectable effect (about 25 K) next to the 10 K margin. | DA m1, m5; R1 detailed comments |
| SR8 | Label the Ridge Curie Tier 3 row "not interpretable (unstable fit)", or report the clipped result. | R1 D2; EIC minor |
| SR9 | Make reproducibility easier: a container or lock file, a one-split smoke configuration with tolerances, and runtimes per stage. Distinguish "bit-reproduced" from "within tolerance". | R3 W4 |
| SR10 | Use matched leave-chemical-system-out test rows (both regimes evaluated on the same held-out systems). | R1 W6 |

### Revision checklist
#### Priority 1: Claims and framing (about 2 days): RR1, RR2, RR5 (wording part), RR9
- [ ] Abstract, Discussion, Conclusion and RQ2 heading corrected (RR1 a-h)
- [ ] RQ1 rescoped; excluded magnetic columns disclosed (RR2)
- [ ] Pre-specification wording aligned with PLAN.md (RR5)
- [ ] Related-work paragraph and table of prior results (RR9)
#### Priority 2: Analyses on existing data (about 1.5-2 weeks): RR3, RR4, RR5 (bootstrap part), RR6, RR7, plus SR1-SR3 if adopted
- [ ] Provenance label-agreement matrix and shared-label-space transfer (RR3)
- [ ] Refit-aware intervals, primary family, multiplicity, XGBoost seed averaging (RR4)
- [ ] Hard subgroups independent of `sigma`; calibration split (RR6)
- [ ] Moment target renamed and renormalized (RR7)
#### Priority 3: Completeness and presentation (about 1 week, in parallel): RR8, SR6-SR9
- [ ] SI, licences, DOI, declarations, AI disclosure, abstract length (RR8)

### Response letter
Answer each RR and SR item in the format comment -> response -> change made (page/line). Use
`academic-paper-reviewer/templates/revision_response_template.md`, or `/ars-revision-coach` to generate the skeleton.

**Note on references suggested by reviewers.** R2 says it confirmed that its 8 suggested references exist. The EIC asks the authors to verify
its suggestions (Bartel 2020, Palmer 2022, Xiong 2020). R3 names several more (Tibshirani 2019, Geifman & El-Yaniv 2017, Koh 2021,
Li 2024, Lookman 2019, Wilkinson 2016). The editor has not verified any of them: check each one before citing.

---

# Part 3: Reviewer report summaries

- **EIC (Major Revision; rubric 69.6).** Strengths: matched design and site-count control; audited benchmark; subgroup calibration;
  transparency. Weaknesses: novelty positioned too narrowly (W1); abstract and Discussion mismatches (W2); provenance confound (W3); RQ1
  generality (W4); completeness and nomenclature (W5).
- **R1 Methodology (Major Revision; F1 block on D2; rubric 69.1).** Strengths: matched paired design; inference at the level of the
  dependence; subgroup-aware UQ; audit; package. Weaknesses: conformal guarantee misstated (W1); stability rule differs from code and
  omits refit variance (W2); no multiplicity framing (W3); pre-specification overstated, 18 clusters not 26 (W4); circular hardest
  decile and calibration data used twice (W5); overstatements and wrong chance reference (W6).
- **R2 Domain (Major Revision; rubric 70.9).** Strengths: Tc curation; JARVIS default-label discovery; extensive-moment deconstruction;
  benchmark audit; calibrated null wording. Weaknesses: Tier 3 omits magnetic physics (W1); "Ms" mislabel and per-cell target (W2);
  ordering decomposition and provenance physics (W3); residual Tc label noise (W4); thin positioning, 8 confirmed missing
  references (W5).
- **R3 Perspective (Major Revision; rubric 73.9; D4 warn).** Strengths: benchmark audit as a transferable lesson; negative results
  disclosed; matched control; decision-relevant calibration; calibrated hedging. Weaknesses: no deployment guidance (W1); missing
  shift, selective-prediction and active-learning literature (W2); provenance finding under-sold and licence blocker (W3); expensive
  fits not reproduced (W4); scope of "physics-informed" (W5).
- **DA (Major Revision; no CRITICAL).** Strongest counter-argument: "distinct properties" is close to true by construction; two of the
  four pairings are expected or self-induced; the physics null rests on mismatched non-magnetic descriptors; the generalization claim
  rests on 69 records; the properties actually co-vary with distance. MAJOR issues M1-M8 (descriptor scope, mismatch explanation,
  asymmetric auditing and forking paths, untested ranking, conformal misstatement, provenance prior shift, overgeneralization, selective
  abstract). Observations: the wording rule was obeyed against the authors' interest, and the benchmark-overlap finding is independently
  valuable.
