# Devil's Advocate Reviewer -- Phase 2 Report

Manuscript: "Accuracy is not reliability: physics descriptors, calibration and chemical generalization in machine learning of magnetic materials" (manuscript.tex, draft 2026-11-09), with Tables 1-6, S1-S3, Figs 1-4.
Contract: reviewer/reviewer_full/v1 (used verbatim; generated_at 2026-11-09T15:29:00Z). Phase 1 commitment: `devils_advocate_phase1.md` (applied without dissent).

## Dimension Scores

### D1: methodology_rigor
**Score: warn**
Strengths are real: matched rows/splits/grids across tiers, ten prespecified formula-grouped splits, paired formula-group bootstrap, paper-cluster bootstrap for the external benchmark, a written audit plan with logged amendments, and a candid errors section. My Phase 1 warn triggers fire, but no block trigger does:
- Forking paths without multiplicity control: 3 targets x 3 algorithms x 2 tier contrasts (Table 2, 18 intervals) plus per-atom, site-count, provenance, family, decile and source-shift analyses, five dataset versions (v1.0-v1.4) and six documented corrections. "Stable" = 95% CI excludes zero, uncorrected (Methods, Statistical comparison). Borderline "stable" results are interpreted both ways (Ridge Ms +0.055 [+0.002, +0.099] counted as a gain; GB ordering Tier 2 -0.029 [-0.057, -0.001] reported as a loss).
- Outcome-informed curation: the Curie rules C1-C5 and the ordering rule O1 were introduced after earlier results had been seen. Methods states that comparisons "were written into configuration files before the corresponding models were fitted", but this covers the analyses, not the dataset versions. Every correction listed in "Errors found and corrected" moved the results toward the paper's thesis (Tier 2 ordering gain removed; per-atom gain cut from 14/9/6% to 2.9/2.8/6.0%; blind-set error raised from the October value). The corrections look genuine, but the audit seems to have been asymmetric: nulls and degradations were not hunted with the same energy (see Issue M3).
- Power: the matched Curie population is 4,602 of 29,740 records (15%) and matched ordering is 6,061 of 79,125 (7.7%). The intervals (Curie GB Tier 1->3 [-31.3, +3.8] K; ordering logistic +0.024 [-0.008, +0.058]) cannot exclude gains that would matter, yet no ordering equivalence margin is defined.
No leakage path plausibly produces the headline numbers (the 0.6%/1.3% formula-spelling leak is disclosed), so this is not a block.

### D2: domain_accuracy
**Score: warn**
- "Physics descriptors" as operationalised (Results, Tier 3 list; Methods, Descriptors) exclude every magnetism-specific DFT output: DFT site moments, magnetic species, total magnetization and ordering energy. The project record shows these p3 magnetism columns were deliberately removed from predictors (decision D3), but the manuscript never says so. For experimental Tc, DFT moments and exchange-related outputs are the physics a domain reader expects "physics-informed" to mean. The generic phrasing ("Physics descriptors add little beyond composition", RQ1 heading and Fig. 1 caption) therefore misdescribes the test.
- The cross-provenance ordering result (Results, RQ3; Table 6) is called "below the three-class chance level of 0.333". The underlying file shows the MP training set is 51% NM and 1.6% AFM. The experimental test set has essentially no NM and 29% AFM, and it is scored only on FM/AFM/FiM while the model can still predict NM. In the reverse direction, 4,753 NM rows were dropped and the dummy (accuracy 0.79) beats every model (accuracy 0.16-0.20). The 0.333 reference is not the chance level for a four-way predictor scored on three classes under severe prior shift. MP's known under-identification of AFM ground states (the authors' own reference horton2019ordering) is a domain explanation that is not discussed.
- Target definitions (Ms per cell vs per atom; Curie vs Neel screening) are otherwise handled carefully, and the YTiO3/ZrZn2-type false positives are disclosed.

### D3: argumentative_coherence
**Score: warn**
The core thesis is internally consistent and mostly hedged in Results. However, several Abstract, Discussion and Conclusion sentences outrun the evidence (Phase 1 warn triggers: thesis largely expected a priori; scope of negatives stated generally; ranking and generalization sentences beyond the results):
- "Accuracy, gains from physics descriptors, calibration and generalization are therefore separate properties" is weakly falsifiable. No criterion is given for what "not separate" would look like. Two of the four Discussion pairings are either textbook-expected (marginal conformal sets under-cover minority classes, a known property; vovk2013conditional is cited) or self-induced (the prior-correction miscalibration follows from the authors' own choice of balanced class weights, and a temperature fix brings ECE to 0.016).
- "None of these properties can be inferred from another" (Discussion) is contradicted by the authors' own data: error rises with distance (rho 0.28), interval width rises with distance (388->529 K), and external blind coverage stays at 89.5%. These properties co-vary; they are not independent.
- "In-distribution accuracy is the least informative of the four properties" (Conclusion) is not derived from any analysis; no ranking of informativeness was measured.
- "Accuracy fell substantially in unfamiliar chemistry" (Conclusion) rests on 69 records from 26 papers. Every internal leave-chemical-system-out test is small or null (ordering -0.028 F1; Ms not stable; Curie +2.7 K [-16.8, +22.2]).
- Abstract: "Conformal intervals reached 90% marginal coverage only with difficulty-normalized scores" contradicts Table 3. For Ms, all three methods are within +/-2 points in 10/10 splits, and Curie split conformal averages 89.3%; the failure is variance/subgroup coverage, not marginal coverage.
- Abstract: "the small per-cell gain was fully explained by unit-cell size". The residual beyond site count is GB +0.024 [-0.003, +0.050] (not stable is not the same as zero), and the abstract omits the surviving per-atom gain (Ridge +6.0% [5.1, 6.8]).
None of these alone overturns a headline conclusion once reworded, so this is not a block, but together they amount to a systematic overstatement pattern.

### D4: cross_disciplinary_relevance
**Score: pass**
The six practical recommendations (Discussion) are concrete, are each tied to a specific finding, and transfer to other property-prediction tasks (string-based novelty, collector defaults, thread-count seeds, cluster-level resampling). Conformal terminology is briefly defined for materials readers. The "so what?" answer is incremental but real: the measurements are integrated on one dataset with dependence-aware intervals. The weak points (no discovery-use demonstration, implications for screening asserted rather than tested) are warn-level at most and are not central to the claimed contribution.

### D5: writing_and_structure
**Score: warn**
- Unexplained baseline inconsistencies: Table 6 gives "familiar" Curie MAE 99.2 K and ordering F1 0.712, while the text and abstract give 76 K and 0.727. Presumably these are ten-split versus frozen-split figures, but this is never stated, and readers will see a 23 K discrepancy in the headline model.
- Fig. 1b shows Curie Tier 3 as a *degradation* (GB -14.3, XGB -9.7 K; the axis reads "reduction in MAE"). Table 2's verdict "no meaningful improvement" hides that the point estimates are worse, not neutral.
- Multiple \todo placeholders remain (affiliations, funding, data DOI, licences, SI assembly, AI disclosure). The SI that carries S1-S3 and the claims register is not yet assembled.
- Otherwise the structure is clear and numbers are traceable to the tables.

## Failure Condition Checks

### F1 (severity 90): any mandatory dimension scores 'block'
fired: false. D1, D2 and D3 all score warn; no mandatory dimension scores block.

### F2 (severity 70): two or more mandatory dimensions score 'warn' or worse
fired: true. D1, D2 and D3 (all mandatory) score warn.

### F3 (severity 60): any high-priority dimension scores 'block'
fired: false. D4 (high priority) scores pass.

### F0 (severity 10): every mandatory dimension scores 'pass'
fired: false. No mandatory dimension passes.

Precedence: F2 is the highest-severity fired condition, so editorial_decision = major_revision.

## Review Body

### Devil's Advocate Review

**What the paper does well.** This is an unusually honest computational study. It uses matched populations, repeated grouped splits, cluster bootstraps, a pre-written external audit, and a public list of the authors' own errors. Recommendations (iii)-(vi) alone would improve much of the field.

### Strongest Counter-Argument

The central claim, that accuracy, physics-descriptor gains, calibration and generalization are "distinct properties", is close to true by construction, and where it is tested the evidence is either expected or partly self-generated. Any four different metrics computed on different data slices will differ; distinctness would be news only if the field believed one implied the others, and the paper cites work (tran2020uq, kapoor2023leakage, meredig2018extrapolation, li2023critical) showing it already does not. Look at the four pairings in turn:
- Accuracy vs calibration: the miscalibration is produced by the authors' choice of balanced class weights and fixed by one temperature parameter.
- Marginal vs class-conditional sets: the under-coverage of minority classes by marginal sets is a theorem-level expectation of marginal conformal prediction.
- Accuracy vs physics: the negative result is for DFT descriptors that exclude every magnetic output. They are joined by formula to a single lowest-energy polymorph and are tested on a non-random 8-15% subpopulation. Here Curie point estimates actually get worse (-14 K), which is the signature of a mismatched, noisy join, not of physics being redundant.
- Accuracy vs generalization: this rests on 69 external records from 26 papers, an R^2 interval spanning [-0.93, 0.66], and an MAE gap that is not resolved under paper clustering. The internal leave-chemical-system-out tests show almost nothing for Curie and Ms.
The cross-provenance "at chance" result reflects a label-prior shift (51% NM vs ~0% NM) scored against an inappropriate chance line. Meanwhile, the data show these properties co-moving: error, interval width and coverage all track chemical distance. A sceptic would conclude that the paper has shown careful evaluation hygiene. It has not shown that the four properties are independent axes, or that physics descriptors as a class are uninformative.

### Issue List

#### CRITICAL
| # | Dimension | Issue Description | Location |
|---|-----------|-------------------|----------|
| - | - | None. No headline conclusion is invalidated outright: each overreach below can be fixed by narrowing the wording or adding analyses. | - |

#### MAJOR
| # | Dimension | Issue Description | Location |
|---|-----------|-------------------|----------|
| M1 | D2/D3 Overgeneralization | "Physics descriptors add little beyond composition" generalizes from 24 non-magnetic DFT scalars, joined by reduced formula to the most stable polymorph, to "physics descriptors". Magnetism-specific DFT outputs were removed from the predictors, and this is not disclosed. The Limitations caveat ("apply to the descriptors we tested") is contradicted by the RQ1 heading, the Fig. 1 caption and the Abstract. Required: disclose the exclusion and its rationale (leakage for MP-labelled ordering/Ms), retitle RQ1 as "non-magnetic DFT descriptors", and ideally run Curie (experimental labels, where leakage is not an issue) with DFT moment/magnetic-species descriptors. | Sec. RQ1 heading; Fig. 1 caption; Abstract; Methods "Descriptors"; Limitations |
| M2 | D3 Alternative explanation | The Curie Tier 1->3 point estimates are degradations (GB -14.3 [-31.3, +3.8] K; XGB -9.7 [-24.1, +3.5] K). Adding features to a tree ensemble on identical rows rarely costs 10-14 K unless the features are noisy relative to the target, which is exactly what a polymorph/sample mismatch would produce (Discussion admits that experimental Tc "may refer to a different structure, a doped sample or a thin film"). This is a more parsimonious explanation than "composition already fixes the information", and it predicts the null. Test it: restrict to records whose DFT structure matches the experimental phase (MAGNDATA / ICSD-linked) or to MP-labelled targets, and report Tier 3 vs Tier 1 there. | Results RQ1 Curie; Table 2; Discussion "Why physics descriptors did not help" |
| M3 | D1 Cherry-picking / forking paths | Every disclosed correction (JARVIS default FM, per-atom denominator, string-novelty, DOI normalizer, non-replicating Tier 2 gain) moved results toward the thesis. No equivalent audit of negative or null results is reported (e.g. the Curie Tier 3 degradation, the ordering GB Tier 2 loss). Add a statement on which results were audited and why, report the full analysis grid (versions x targets x algorithms) in the SI, and apply a multiplicity-aware criterion (e.g. Holm across Table 2) or explicitly label Table 2 as exploratory. Distinguish analysis prespecification from dataset-version decisions taken after results were seen (v1.3 rules). | Methods "Statistical comparison", "Errors found and corrected"; Table 2 |
| M4 | D3 Logic chain | "In-distribution accuracy is the least informative of the four properties, and calibrated distance-aware uncertainty is the most needed" is not supported by any measurement of informativeness. Normalized conformal is not distance-aware, and its coverage fell only to 0.85 [0.72, 0.93] in the farthest quartile. Remove the ranking or support it, e.g. by showing that in-distribution accuracy fails to rank models by external blind performance. | Conclusion |
| M5 | D3 Data-conclusion mismatch | Abstract: "Conformal intervals reached 90% marginal coverage only with difficulty-normalized scores." Table 3 shows Ms split/normalized/CQR all at 90.0-90.1% (10/10 splits within +/-2 points) and Curie split conformal at 89.3% mean. The supported claim concerns split-to-split variance and hardest-decile coverage, not marginal coverage. The RQ2 heading itself says "marginal calibration is attainable". | Abstract; Table 3; Sec. RQ2 heading |
| M6 | D2/D3 Alternative explanation | Cross-provenance ordering "at chance" (Results RQ3; Discussion "at chance across label provenance") compares a four-way classifier, scored on three classes after dropping NM, with a three-class chance level of 0.333. The training prior is 51% NM / 1.6% AFM; the experimental test prior is about 0% NM / 29% AFM. In the reverse direction the majority dummy (accuracy 0.79) beats all models. This is prior/label-space shift plus MP's own AFM under-identification (horton2019ordering), confounded with chemistry differences between the slices. "The pooled headline score ... [reflects] agreement with the labelling convention of each source" is one interpretation among several. Report prior-corrected / NM-masked transfer and the same-composition overlap analysis (compositions labelled in both sources) before drawing it. | Results RQ3 internal tests; Table 6; Discussion |
| M7 | D3 Overgeneralization | "Accuracy fell substantially in unfamiliar chemistry" (Conclusion) and "None of these properties can be inferred from another" (Discussion) overreach. Internal leave-chemical-system-out: Curie +2.7 [-16.8, +22.2] K (5/10 splits worse), Ms not stable, ordering -0.028 (about 4% relative). External: 69 records / 26 papers, MAE gap +81 [-27, +165] K under paper clusters. Meanwhile, error, width and coverage co-vary with distance, so the properties are correlated, not mutually uninformative. Reword to "accuracy in unseen chemical systems is weaker and poorly constrained; distance predicts part of the degradation". | Conclusion; Discussion opening paragraph |
| M8 | D3 Selective abstract | Abstract: "the small per-cell gain was fully explained by unit-cell size". The residual beyond site count is +0.024 [-0.003, +0.050] for GB (unresolved, not zero). The surviving per-atom gain (Ridge +6.0% [5.1, 6.8]; up to 7.9% on verified subsets) is omitted from the abstract even though it is the only stable positive physics result. Report it, or the abstract cherry-picks toward the thesis. | Abstract; Results RQ1 Magnetic moment |

#### MINOR
| # | Dimension | Issue Description | Location |
|---|-----------|-------------------|----------|
| m1 | D5 | Table 6 "familiar" baselines (Curie 99.2 K, ordering 0.712) do not match the text and abstract (76 K, 0.727). State which split or average each figure uses. | Table 6; Results dataset section |
| m2 | D3 | "Accuracy vs calibration" pairing: the miscalibration arises from the authors' balanced class weights. Say so in the Discussion, or drop it as evidence of distinctness. | Discussion |
| m3 | D1 | No practical-equivalence margin for ordering or Ms, yet the abstract says "no practical gain for ordering". Define one (e.g. 0.02 macro-F1) or say "no detectable gain". | Abstract; Methods |
| m4 | D3 | The SHAP "attribution is not benefit" argument is sound, but with correlated features a 40% physics share may simply reflect split-order arbitrariness. A conditional/grouped importance or a drop-group test would make the point quantitative. | Results "Attribution is not benefit" |
| m5 | D1 | Matched populations are a non-random 8-15% subset, yet Tier 1 performance on the matched subset is never shown next to the full population, so readers cannot judge whether the subset is "easier" or more saturated. | Table 2; Table 1 |
| m6 | D5 | Remaining \todo placeholders (affiliations, data DOI, licences, AI-use disclosure, SI assembly) must be resolved before submission. | Front matter; Declarations |
| m7 | D3 | "More than 100,000 labelled magnetic materials" (Conclusion) sums overlapping targets. Give the unique-formula count. | Conclusion |

### Ignored Alternative Explanations/Paths
1. **Descriptor-target mismatch (noise injection)** as the cause of the Tier 3 null and of the Curie degradation (M2). It is more parsimonious than "composition already contains the information" and is testable on structure-matched subsets.
2. **Saturation / ceiling on the matched subset.** Materials with complete DFT records are well-studied, MP-dominated compositions where Tier 1 may already be near the label-noise floor. If so, no descriptor could help; the null would then reflect label noise, not descriptor redundancy.
3. **Representation, not information.** Formula-joined scalars from one polymorph cannot express structure-property coupling; structure-aware models (CGCNN/ALIGNN/MACE embeddings) or magnetism-specific DFT outputs are the natural alternative path. The Limitations sentence acknowledges graph models but treats this as peripheral, when it is the main competing route to "physics-informed".
4. **Prior shift and label semantics** for cross-provenance ordering (M6), rather than "labelling convention". A shared-composition comparison between the MP and experimental labels would decide it.
5. **R^2 on small, low-variance subsets.** A negative R^2 on 69 records can arise from a narrow Tc range within that subset even with moderate MAE. Report the subset's target SD, or a scale-free comparison against a seen-system subset matched on Tc range.

### Missing Stakeholder Perspectives
- Experimental magnetism researchers, for whom Tc refers to a specific phase or sample. The paper never asks whether the external or text-mined labels match the DFT structure being described.
- Database curators (MP, JARVIS, NEMAD). The collector-default finding and the MP AFM under-identification bear on their pipelines, but the paper frames them only as user-side hazards.
- Screening and discovery users: no decision-level evaluation (e.g. precision of top-k shortlists, or the cost of interval under-coverage at high Tc) translates the calibration findings into consequences.

### Unexamined Premise
The paper assumes that "physics-informed" means appending DFT scalars to a composition table. If physics enters through structure, magnetic exchange, or model constraints rather than through extra columns, then RQ1 tests a specific engineering choice, not the premise of physics-informed ML, and the title's implied contrast ("accuracy is not reliability" because "physics descriptors" do not help) loses one of its pillars.

### Observations (Non-Defects)
- The pre-registered wording rule for the unseen-system R^2 (claim "no skill" only if the upper limit is <= 0.2) is exemplary, and the authors obeyed it against their own interest.
- The finding that 80% of a published external "test" set overlaps the training compositions, and 48% duplicates training values, is independently valuable to the community, arguably more so than RQ1.
- The thread-count-as-seed observation for XGBoost is a useful reproducibility warning.
- Class-conditional conformal sets restoring about 90% coverage per class at a modest set-size cost (1.34 -> 1.57) is a practical, transferable result even if theoretically expected.

## Editorial Decision

**Major Revision.** F2 fired (D1, D2 and D3 all warn); F1 and F3 did not fire. No CRITICAL issues. The empirical work is sound and unusually transparent. The revision should (a) narrow the "physics descriptors" claim to the non-magnetic, formula-joined DFT descriptors tested, and test the mismatch explanation; (b) correct the abstract on marginal coverage and the per-cell/per-atom moment result; (c) remove or support the "least informative" ranking, the "none can be inferred from another" claim and the "fell substantially" claim; (d) reanalyse cross-provenance transfer with an appropriate chance baseline; and (e) add multiplicity handling and disclose which dataset-version decisions were made after results were seen.
